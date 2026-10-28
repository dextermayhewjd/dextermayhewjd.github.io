# 01 · 阅读范围：生成接入与奖励归属

[步骤入口](README.md) · [本步函数记录](02-short-term-memory/overview.md) · [上一主题](../../../01-coding-agent-rl/README.md)

## 1. 阅读目标

- **整体目标**：理解自定义 Agent 怎样接入 Slime 的生成与评分流程。
- **本步问题**：框架怎样通过共享 `state` 控制一次生成，接住结果，并决定后续评分？
- **阅读范围**：先跟一个新 `Sample`，沿 Coding Agent 返回样本列表的路径读通，保留生成准入、中止检查、名额释放和评分责任的边界。

## 2. 指挥官函数

- **本步入口**：[sglang_rollout.py::generate_and_rm](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L289-L380)，组织受控生成、资源释放、样本后处理与评分。
- **调用者**：`generate_and_rm_group:425` 为每个待生成 Sample 创建本函数的任务；本步只定位这一交接。
- **已读下游**：`examples/coding_agent_rl/generate.py::generate → _generate`，负责一次 Coding Agent 任务；此次从框架调用侧接回它。

## 3. 给出真正干活的核心骨架

### 3.1 整体位置：回到 Coding Agent 的调用方

```text
generate_and_rm_group
  └─ 创建任务：generate_and_rm(...)              ← 本步指挥官
       └─ 选中并等待：Coding Agent generate(...)
            └─ _generate(...)                  ← 前一主题的单题主线
```

- **进入**：`generate_and_rm_group` 将一份待生成的 `Sample` 交给本函数。
- **返回**：Coding Agent 交回样本列表，本函数先释放生成名额，再完成后处理与奖励检查，把结果交回 `generate_and_rm_group`。

<a id="execution-skeleton"></a>

### 3.2 核心骨架：共享状态 → 受控生成 → 结果处理 → 评分交付

以下采用用户确认的 **A 版：保留条件分支，简写条件与参数**。跟随一个新输入任务，使用 Coding Agent 自定义生成、`evaluation=False` 和列表返回；完整保留四段主线、资源范围、中止和评分交付。`...` 省略具体实参；`if ...` 省略的是“存在自定义生成器且签名包含 evaluation”的完整条件，含义由旁注说明。此骨架只供阅读，不是可执行脚本。路径优先级、条件和实参原文在 3.3 按需回查；已完成输入、部分续跑、日志与单个 Sample 评分分支仍暂时折叠。

```python
# 1. 共享状态与输入上下文
state = GenerateState(args)
queue_input = copy.copy(sample)  # 316：生成前，浅拷贝输入，供后面继承上下文
if hasattr(sample, "_queue_lease") or hasattr(sample, "_queue_receipt"):
    queue_input.queue_generation_requests = ...  # 318–325：旧记录 + 本次生成请求

# 2. 受控生成：获取名额、分批放行、检查中止
await state.semaphore.acquire()
try:
    await state.generation_pacer.wait()
    if state.aborted:
        sample.status = Sample.Status.ABORTED
        return sample

    with state.dp_rank_context() as _:
        generate_func = load_function(...)  # 本例用自定义生成器；无自定义时用 generate
        if ...:  # 自定义生成器的签名包含 evaluation
            generate_call = generate_func(..., evaluation=evaluation)
        else:
            generate_call = generate_func(...)

        if getattr(generate_func, "abort_mode", None) == "request":
            sample = await _run_request_abortable_generate(state, sample, generate_call)
        else:
            sample = await _run_server_abort_generate(state, generate_call)
finally:
    state.semaphore.release()

# 3. 结果处理：保持任务归属，运行样本后处理
sample = inherit_queue_context(queue_input, sample)
sample = await apply_rollout_sample_hooks(..., sample)
sample = inherit_queue_context(queue_input, sample)

# 4. 评分与交付：只给缺失奖励的结果补分
if args.group_rm:  # 当前：是否把评分留到调用者收齐整组后
    return sample

samples = sample  # 当前阅读路径：生成器返回列表
if any(sample.status == Sample.Status.ABORTED for sample in samples):
    return samples

samples_need_reward = [sample for sample in samples if sample.reward is None]
rewards = await batched_async_rm(..., samples_need_reward)  # 当前：进入批量评分分派
for sample, reward in zip(samples_need_reward, rewards, strict=False):
    sample.reward = reward
return samples
```

- **共享控制**：`state` 通常复用进程内缓存的同一对象；`semaphore` 管生成名额，`generation_pacer` 分批放行，`aborted` 决定此时是否继续生成。
- **资源边界**：名额覆盖启动等待和生成，由 `finally` 归还；hook 与评分在释放之后执行。
- **数据交接**：第一部分先保存 `queue_input`，第二部分的 `sample = await ...` 接住生成结果，第三部分再从同一个 `queue_input` 向结果继承上下文；后续按配置、状态与缺失奖励决定交付方式。

<a id="queue-input-handoff"></a>

#### 第一部分补读：queue_input 何时创建，后面交给谁

创建位置是 [generate_and_rm:316–325](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L316-L325)：**已取得 state，还没有申请 semaphore 名额，更没有调用生成器**。

```text
进入函数的 sample（待生成输入）
    ├─ copy.copy(sample) → queue_input（保留输入的上下文）
    │    └─ 输入有 lease 或 receipt 时：追加本次生成请求记录
    │
    └─ 交给生成器 → sample = await ...（此时 sample 可以指向新的结果列表）
                        ↓
       inherit_queue_context(queue_input, sample)  ← 353：给生成结果继承上下文
                        ↓ hook 可能再次替换结果
       inherit_queue_context(queue_input, sample)  ← 355：仍从同一份输入继承
```

- `queue_input` 是本函数内创建的局部对象；`copy.copy` 是浅拷贝，不是把输入放进队列，也不会申请新的队列任务。它保留输入当时已有的属性，但其中的嵌套可变对象仍可能共享，不能理解为完全冻结的历史快照。
- 只有输入带 `_queue_lease` 或 `_queue_receipt` 时，才在 `queue_input` 上记录本次的采样参数、生成函数路径和输入索引；已有请求历史也保留。具体字典内容暂时省略。
- 普通输入同样会创建 `queue_input`；输入没有的队列字段，不会因这次浅拷贝而出现，后面继承时会跳过。

当前从 `353` 回查这里，接清来源后回到 [inherit_queue_context 函数卡](02-short-term-memory/functions/slime/data/transport.py/inherit_queue_context.md)。六字段的具体来源仍见[字段参考](references/queue-context-fields.md)，不在 scope 中展开完整队列协议。

<a id="generation-dispatch-branches"></a>

### 3.3 with 主体的分支：选择生成器、准备调用、选择等待方式

分支写在 **generate_and_rm 的 `with state.dp_rank_context()` 主体**中。dp_rank_context 自身只管理 rank 计数；下列两种等待分支都处于同一个 DP 计数上下文内。

| 位置 | 判断及分支 | 当前 Coding Agent 路径 |
| --- | --- | --- |
| 338–339：选生成器 | 优先 sample.generate_function_path，再用 args.custom_generate_function_path；无自定义路径时用默认 generate | 使用全局路径加载 Coding Agent generate |
| 341–344：准备调用 | 自定义函数签名含 evaluation 时传该关键字，否则只传前三项实参 | 传 evaluation=False，得到 generate_call |
| 346–349：选等待方式 | abort_mode == request 时用 _run_request_abortable_generate；否则用 _run_server_abort_generate | else：进入本轮函数卡 |

两次条件判断按顺序执行：先决定怎样传参，再决定怎样等待。前一项不是 `if evaluation`：检查的是自定义函数是否声明 `evaluation` 参数；即使当前值为 False，也可以走传入该参数的分支。

<details>
<summary>按需回查：完整条件与调用参数</summary>

```python
if custom_func_path is not None and "evaluation" in inspect.signature(generate_func).parameters:
    generate_call = generate_func(args, sample, sampling_params, evaluation=evaluation)
else:
    generate_call = generate_func(args, sample, sampling_params)

if getattr(generate_func, "abort_mode", None) == "request":
    sample = await _run_request_abortable_generate(state, sample, generate_call)
else:
    sample = await _run_server_abort_generate(state, generate_call)
```

</details>

- **本轮展开**：[_run_server_abort_generate](02-short-term-memory/functions/slime/rollout/sglang_rollout.py/_run_server_abort_generate.md)，看计数登记、等待结果与退出减回。进入时 generate_call 已存在，先按本例 Coding Agent 的协程对象理解。
- **保留另一支的位置**：[_run_request_abortable_generate:258–274](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L258-L274)，本轮不展开取消协议，也不建其卡片。
- **返回主线**：本轮方法先执行自身 finally 减回 active_server_generations，再返回 `349`；正常情况下离开 DP 上下文减回 rank 计数，随后 `351` 归还生成名额，`353` 继续结果处理。

### 3.4 沿骨架阅读：先看控制范围，再看范围内的调用

进入下面的导航前，先短回顾 [Sample 类卡](02-short-term-memory/classes/slime/utils/types.py/Sample.md)，再看 [GenerateState 类卡](02-short-term-memory/classes/slime/rollout/sglang_rollout.py/GenerateState.md)：一份任务数据怎样使用共享运行状态。[两个对象的整体定位](../../../../../../../slime_photo/code-reading/chapters/03-strategy-evaluation/walkthrough.md#sample-and-state)继续作为讲解参考。

| 骨架位置 | 本轮看清什么 | 源码入口与返回位置 |
| --- | --- | --- |
| 1. 状态与输入上下文 | `GenerateState` 共享哪些执行控制；[queue_input 何时创建、怎样交给后面使用](#queue-input-handoff) | [306–325 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L306-L325)；需要时回看[状态职责](../../../../../../../slime_photo/code-reading/chapters/03-strategy-evaluation/walkthrough.md#state-and-execution-skeleton)，再到 `329` 取得名额 |
| 2. 受控生成与释放 | 先辨认 acquire/try/finally 的范围，再看分批启动、中止检查、选函数与等待 | [329–351 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L329-L351)；上一段在 with 主体内的 `349` 调用 [_run_server_abort_generate](02-short-term-memory/functions/slime/rollout/sglang_rollout.py/_run_server_abort_generate.md)；分支定位见 3.3；[dp_rank_context](02-short-term-memory/functions/slime/rollout/sglang_rollout.py/GenerateState.dp_rank_context.md) 保留回查；前面的 [Semaphore.acquire](02-short-term-memory/functions/Lib/asyncio/locks.py/Semaphore.acquire.md) 与 [AsyncPacer.wait](02-short-term-memory/functions/slime/utils/async_utils.py/AsyncPacer.wait.md) 保留回查和未解问题；退出生成段后到 `353` |
| 3. 结果后处理 | 为什么 hook 前后都继承上下文，后续评分接收哪份结果 | [353–355 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L353-L355)；当前先在 `353` 进入 [inherit_queue_context](02-short-term-memory/functions/slime/data/transport.py/inherit_queue_context.md)，读清 source/output 和字段规则；返回 `354` 的 [apply_rollout_sample_hooks](02-short-term-memory/functions/slime/rollout/sample_hooks.py/apply_rollout_sample_hooks.md)，`355` 再用同一继承函数，然后到 `358` 判断评分责任 |
| 4. 评分与交付 | 组评分交回调用者，ABORTED 提前返回，其余只补缺失奖励 | [358–380 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L358-L380)；最终回到 `generate_and_rm_group:427–430` 接收结果 |

此前第三部分导航：生成器的 list[Sample] → `353` 继承输入任务上下文 → `354` 进入 apply_rollout_sample_hooks → 先看 paths 是否为空，再看列表递归与单个 Sample 的 hook 链 → `355` 再次继承上下文 → `358` 判断评分责任。当时先展开 inherit_queue_context，iter_samples 只按遍历接口理解；hook 的 `_apply_to_sample` 作为其下一层辅助，不自动深入业务 hook 或完整队列协议。

此前在 inherit_queue_context 内先补 source 上字段的来路：[六字段来源、用途与继承规则](references/queue-context-fields.md)。这只为理解当前拷贝服务，不预设已经读完各个队列模块。

进入第三部分时，`sample` 是接收返回值的变量名，当前内容为 list[Sample]；`queue_input` 是第一部分保存的输入快照。无配置 hook 时中间步骤原样返回；配置存在时，hook 可以更新或替换单个 Sample，因此保留前后两次上下文继承。

当前按用户指定进入第四部分 `group_rm`：先读 `357–359` 的开关与提前返回，再最小回查 `generate_and_rm_group:427–437` 的“收齐整组 → 评分 → 写回”。明确是否延后到组级评分，不展开组级调度或具体评分算法；False 路径接回当前函数的缺失奖励处理。用户随后要求先只看一条奖励路径，当前先读[列表补奖励分支](02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md#reward-list-branch)，其余对照折叠保留。此前交接详见[父函数卡的 group_rm 观察点](02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md#group-rm-responsibility)。

当前用户已明确进入 [batched_async_rm](02-short-term-memory/functions/slime/rollout/rm_hub/__init__.py/batched_async_rm.md)：从父函数 368 下钻到 rm_hub/__init__.py:99–110，先辨认 custom_rm_path 分派，再看默认路径逐项调用 async_rm、gather 收集。读清奖励列表怎样返回后，回到父函数 369–371 写回与交付；不继续下钻实际评分算法。两条路径的接口不同：自定义函数接整批，默认 async_rm 每次接单个 Sample。

具体输入输出与逐段说明见 [generate_and_rm 函数卡片](02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md)。**停止位置**：能说明任务怎样受控生成、何时释放名额，以及结果怎样完成后处理和评分交付；状态内部算法、队列协议与评分器实现按后续问题展开。

<details>
<summary>本轮剪掉了什么，以及其他路径何时再看</summary>

- **配置与执行实现**：路径优先级、参数签名检查、详细追踪与另一种生成包装暂不展开。当前 Coding Agent 使用 `_run_server_abort_generate`；共享状态、获取与释放关系已保留在骨架中。
- **输入处理**：部分续跑的旧响应掩码、已完成输入的直接返回、评估参数调整和队列生成请求的具体字典内容省略；queue_input 的创建与条件追加保留在骨架中，完整位置见源码 `296–325`。
- **其他返回形状**：单个 Sample 先检查 ABORTED，再仅在 `reward is None` 时调用 `async_rm`；当前骨架展示列表分支。
- **奖励边界**：`0.0` 是已有分数，只有 `None` 才待补。当前 Coding Agent 的正常训练结果已带奖励，所以待评分列表通常为空；源码仍会调用 `batched_async_rm(args, [])`，并非完全跳过该入口。

</details>

## 版本说明

- 源码固定为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；本步卡片使用这一版本。
- 本轮按用户确认，采用包含共享状态与执行控制的骨架，见[采用记录](04-flow.md#execution-skeleton-adopted)。
- [本次替换前版本](references/scope-before-execution-structure-2026-10-25.md)与[最初重排前版本](references/scope-before-core-skeleton-review-2026-10-25.md)完整归档，保留当时说明和来源。

- 2026-10-26 已按用户确认采用 A 版核心骨架，保留主体与分支、简写条件和参数；[采用前全文](references/scope-before-option-a-2026-10-26.md)与[采用记录](04-flow.md#option-a-scope-adopted)可回查。
