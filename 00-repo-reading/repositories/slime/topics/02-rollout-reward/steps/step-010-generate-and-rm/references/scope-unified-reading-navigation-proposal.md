# Step 010 scope 候选：四段骨架与统一阅读导航

**状态：候选参考，尚未替换正式 scope。** [对照正式 scope](../01-scope.md) · [当前步骤](../README.md) · [提出背景](../../../../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#step010-scope-navigation-review)

主要保留现有 3.2 四段执行骨架，重排后面的材料。参考 [Step 001 的阅读图与导航表](../../../../../../../../.agents/skills/repo-reading-scope/references/step-001-reading-path.md)和 [Step 002 的按需回查](../../../../../../../../.agents/skills/repo-reading-scope/references/step-002-reading-path.md)；两份样例的具体函数与进度不移植到本步。

以下可直接作为完整 scope 候选阅读。图表给出 2026-10-26 当前入口；实时进度仍只以[路线](../../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)为准，材料存在不表示已掌握。

---

# 候选 scope：生成接入与奖励归属

[步骤入口](../README.md) · [本步函数记录](../02-short-term-memory/overview.md) · [上一主题](../../../../01-coding-agent-rl/README.md)

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

以下采用用户确认的 **A 版：保留条件分支，简写条件与参数**。跟随一个新输入任务，使用 Coding Agent 自定义生成、`evaluation=False` 和列表返回；完整保留四段主线、资源范围、中止和评分交付。`...` 省略具体实参；`if ...` 省略的是“存在自定义生成器且签名包含 evaluation”的完整条件，含义由旁注说明。此骨架只供阅读，不是可执行脚本。路径优先级、条件和实参原文在 3.4 按需回查；已完成输入、部分续跑、日志与单个 Sample 评分分支仍暂时折叠。

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
if args.group_rm:  # 是否把评分留到调用者收齐整组后
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

### 3.3 沿四段骨架的统一阅读导航

先在图里找所属阶段，再用同编号表进入函数卡。图是**阅读入口与回查关系**，真实执行顺序、两次继承和 finally 的嵌套以上方 3.2 为准。对象卡与方法卡已有内容可按需回顾，不要求每次从头读。

```text
① 状态与输入上下文
   1.1 Sample / GenerateState：任务数据与共享控制
   1.2 queue_input：生成前保存输入上下文
       输入有 lease/receipt 时，追加本次生成请求记录
       ↓
② 受控生成
   2.1 semaphore.acquire：取得名额
   2.2 generation_pacer.wait：分批放行；返回后检查 aborted
   2.3 dp_rank_context：进入/退出时维护 DP 计数
   2.4 选择生成函数 → 准备调用 → 选择等待包装 → 接收生成结果
       返回后退出 DP 上下文，再由 finally 归还 semaphore 名额
       ↓
③ 结果后处理
   3.1 inherit_queue_context：向生成结果传递输入上下文
       └─ 来源不清楚：回查 1.2 queue_input，再回到 3.1
   3.2 apply_rollout_sample_hooks：处理或替换结果
   3.3 再次 inherit_queue_context：复用 3.1 的方法卡
       ↓
④ 评分与交付
   4.1 group_rm：是否把评分交回组级调用者
       └─ True：本函数返回；组级评分交接按需回查
   4.2 False、列表无 ABORTED：筛选缺分样本 → batched_async_rm  ← 当前阅读入口
       └─ 返回奖励列表后，回到 4.3
   4.3 把奖励写回对应成员 → 返回完整结果列表
```

| 编号与入口 | 本处要看清什么 | 读完回到哪里 |
| --- | --- | --- |
| 1.1 [Sample](../02-short-term-memory/classes/slime/utils/types.py/Sample.md)、[GenerateState](../02-short-term-memory/classes/slime/rollout/sglang_rollout.py/GenerateState.md) | 输入任务数据与进程内共享控制分别由谁保存；按需回顾对象职责 | 父函数 316 保存输入上下文 |
| 1.2 [queue_input 来源](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L312-L325) | 在生成前浅拷贝输入；带凭证时在这份副本上追加请求记录 | 父函数 329 申请名额；从 3.1 回查时返回 353 |
| 2.1 [Semaphore.acquire](../02-short-term-memory/functions/Lib/asyncio/locks.py/Semaphore.acquire.md) | 等待一个生成名额；与归还名额的范围配对 | 父函数 332 等待 pacer |
| 2.2 [AsyncPacer.wait](../02-short-term-memory/functions/slime/utils/async_utils.py/AsyncPacer.wait.md) | 等待分批放行；aborted 判断仍留在父函数 | 父函数 333 检查中止，再到 337 |
| 2.3 [dp_rank_context](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/GenerateState.dp_rank_context.md) | 分配 rank 与使用期间的计数变化 | 进入时交到 338；with 结束后再执行 351 的释放 |
| 2.4 [生成委派阶段](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md)、[_run_server_abort_generate](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/_run_server_abort_generate.md) | 选函数、是否传 evaluation、选择等待方式；本例等待 Coding Agent 返回列表 | 父函数 349 接住结果，退出上下文、351 释放名额，继续 353 |
| 3.1、3.3 [inherit_queue_context](../02-short-term-memory/functions/slime/data/transport.py/inherit_queue_context.md) | 两次都从同一个 queue_input 向当时结果传递上下文；区别源对象与输出对象 | 第一次返回 354 调用 hook；第二次返回 358 判断评分责任 |
| 3.2 [apply_rollout_sample_hooks](../02-short-term-memory/functions/slime/rollout/sample_hooks.py/apply_rollout_sample_hooks.md) | 无配置时原样返回；有配置时可能修改或替换结果 | 父函数 355 再次继承上下文 |
| 4.1 [group_rm 分支](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md#group-rm-responsibility) | True 先返回，由组级调用者收齐后评分；False 在本函数继续 | False 接 361 的形状判断；True 的交接回查见 3.4 |
| **4.2 [batched_async_rm](../02-short-term-memory/functions/slime/rollout/rm_hub/__init__.py/batched_async_rm.md)** | 接收筛选后的列表；自定义整批委派或默认逐样本评分，返回奖励列表 | **父函数 369–370 写回 reward**；具体算分算法暂不下钻 |
| 4.3 [奖励写回与返回](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md#reward-list-branch) | 只写回缺分成员，再返回完整列表；已有 0 分仍是有效奖励 | 371 返回给 generate_and_rm_group，427–430 收集结果 |

#### 1.2 的最小前置：queue_input 为何没有丢失

`queue_input = copy.copy(sample)` 在生成前执行；之后 `sample = await ...` 可以接住新的结果对象。两次继承仍使用原先的 queue_input。浅拷贝保留已有属性，不会创建新的队列凭证，也不表示嵌套数据完全独立。字段何时附加的详细过程见[字段参考](queue-context-fields.md)。

### 3.4 阅读边界与按需回查

本步以“输入任务怎样受控生成、何时释放名额、结果怎样完成后处理和奖励交付”为边界。当前停在批量评分的分派与返回；具体评分算法、完整队列协议和组级调度不展开。完整函数解释与个人原话分别保留在[函数卡索引](../02-short-term-memory/overview.md)和[04-flow](../04-flow.md)，本页不追加历史阅读叙述。

<details>
<summary>生成选择：路径优先级、evaluation 与等待分支</summary>

下面均在父函数的同一个 with 主体里。dp_rank_context 只管理 rank 使用计数，不负责这些分派。

```python
custom_func_path = sample.generate_function_path or args.custom_generate_function_path
generate_func = load_function(custom_func_path) if custom_func_path is not None else generate

if custom_func_path is not None and "evaluation" in inspect.signature(generate_func).parameters:
    generate_call = generate_func(args, sample, sampling_params, evaluation=evaluation)
else:
    generate_call = generate_func(args, sample, sampling_params)

if getattr(generate_func, "abort_mode", None) == "request":
    sample = await _run_request_abortable_generate(state, sample, generate_call)
else:
    sample = await _run_server_abort_generate(state, generate_call)
```

先决定如何传参，再决定如何等待。evaluation 判断检查函数签名是否支持该参数，不是检查 evaluation 的值是否为 True。本例用 Coding Agent、evaluation=False、服务端等待包装；另一支保留[源码入口](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L258-L274)，不预建未读卡片。

</details>

<details>
<summary>评分的其他路径与本例边界</summary>

- group_rm=True：父函数 358–359 返回；[组级调用者 427–437](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L427-L437)收齐结果、未中止时评分。此对照按平坦 Sample 组理解，未验证分段列表组合。
- 列表含 ABORTED：361–364 提前返回；其他列表只给 reward is None 的成员补分。
- 单个 Sample：372–380 先检查 ABORTED，再在缺分时调用 async_rm。
- 正常 Coding Agent 训练结果通常已经带 reward；列表补分入口仍可能收到空列表。示意分数不是实际运行数据。

</details>

<details>
<summary>教学裁剪与暂缓内容</summary>

保留正常任务路径及当前问题所需分支。入口的已完成输入返回、部分续跑掩码、评估参数调整、日志与追踪包装不在主骨架展开；请求取消协议、评分算法和队列协议继续按后续实际问题进入。已有卡片中的未知和来源继续保留。

</details>

## 版本与来源

- Slime 源码固定为 18868a79b0b083a093798a94ed0f8cb4f71b9c14，候选稿基于[当前正式 scope](../01-scope.md)整理，正式文件未替换。
- 本文的四段执行骨架保留 A 版，后半部分采用统一编号的阅读图表；图中的回查是阅读动作，不是程序执行回跳。
- 方法来源：[scope skill](../../../../../../../../.agents/skills/repo-reading-scope/SKILL.md)、[局部导航 reference](../../../../../../../../.agents/skills/repo-reading-scope/references/local-call-context.md)、开头链接的 Step 001 与 Step 002 样例。
- 历史追问与旧稿仍从[当前步骤](../README.md)、[正式 scope](../01-scope.md)和[格式讨论](../../../../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#step010-scope-navigation-review)回查，不因本候选生成而覆盖。
