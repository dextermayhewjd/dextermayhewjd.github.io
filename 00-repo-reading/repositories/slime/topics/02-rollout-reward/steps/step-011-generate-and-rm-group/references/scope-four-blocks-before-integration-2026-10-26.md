# 调整前快照：四个独立代码块

保留 2026-10-26 的四段展示版本。用户随后要求在整体骨架内部划分阶段，现行版本见[当前 scope](../01-scope.md)。本页只保留当时材料，不维护当前进度。

---

# 01 · 阅读范围：一组生成任务怎样组织和交付

[步骤入口](../README.md) · [本步函数卡](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm_group.md) · [前一步](../../step-010-generate-and-rm/README.md)

## 1. 阅读目标

- **岗位目标**：对齐混元岗位的异步并发、任务与结果组织能力。
- **本步问题**：一个 group 怎样拆成多个生成任务，怎样收齐结果并保持原来的对应关系？
- **选定路径**：新输入 group、Coding Agent、evaluation=False、group_rm=False；先走正常路径，再按问题补失败与重试。

## 2. 指挥官函数

- 入口：[generate_and_rm_group:388–439](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L388-L439)。
- 调用者：[AsyncRolloutWorker._loop:214–223](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L214-L223)；本步只定位，不展开持续调度。
- 已读下游：[generate_and_rm](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md)，负责单次生成控制、后处理和奖励归属。

## 3. 核心骨架与统一阅读导航

### 3.1 整体位置

```text
AsyncRolloutWorker._loop（以后展开）
    → generate_and_rm_group（本步：一组任务）
        → 多个 generate_and_rm（前一步：各自生成与评分）
    ← 收回一组结果
    → 完成回调与结果队列（以后展开）
```

### 3.2 核心骨架：准备成员 → 创建任务 → 汇总结果 → 评分交付

下面四段按真实执行顺序分开展示，拼接后仍是原来的完整骨架。教学裁剪：采用新输入 group、evaluation=False、group_rm=False；保留关键业务分支，折叠旧分段列表的完整校验、确定性 seed 覆盖与 trace 包装。没有新建额外的阶段函数。

<a id="phase-1"></a>

#### ① 准备成员：哪些对象进入后面的生成（398–415）

入口已有 group 和公共 sampling_params；group 由调用者提供，本函数不负责从一个提示复制出多个输入。

```python
state = GenerateState(args)
if state.aborted:
    return group

for sample in group:
    if isinstance(sample, list):
        continue  # 此前需校验它是可保留的已完成分段结果
    if sample.session_id is None:
        sample.session_id = str(uuid.uuid4())
```

取得共享 state，检查是否已中止，给缺少 session_id 的新 Sample 补上标识。已有分段列表在完整源码中先校验，再保留；此处的 continue 省略了校验细节。

**本段产出**：可用于生成的成员已经带会话标识；group 的位置不变。

**先弄清**：这一段为什么只准备成员，还没有创建生成 Task？读完进入②。

<a id="phase-2"></a>

#### ② 创建任务：一个待生成成员对应一个 Task（417–425）

承接①的 group。tasks 以原组下标为键，保存本次真正需要启动的任务。

```python
tasks = {}
for idx, sample in enumerate(group):
    if isinstance(sample, list):
        continue  # 已完成的分段结果在前面校验过，保留它
    current_sampling_params = sampling_params.copy()
    # 本例未开启确定性采样，省略 seed 覆盖
    tasks[idx] = asyncio.create_task(
        generate_and_rm(args, sample, current_sampling_params, evaluation=evaluation)
    )
```

跳过已保留的分段列表；为每个新成员浅拷贝采样参数，然后创建 generate_and_rm 任务。确定性 seed 分支本例折叠。子函数负责单次生成的限流、后处理与奖励。

**本段产出**：`tasks = {原组下标: Task, ...}`。这不是结果列表。

**本段重点**：`idx` 如何把 Task 与原输入位置联系起来？读完进入③，不重新展开已读的 generate_and_rm。

<a id="phase-3"></a>

#### ③ 汇总结果：等待任务，并放回对应位置（427–430）

承接②的 tasks；每个 Task 最终可能返回一个 Sample，也可能返回 Sample 列表。

```python
results = await asyncio.gather(*tasks.values())
group = list(group)
for idx, result in zip(tasks, results, strict=True):
    group[idx] = result
```

gather 等待本次所有 Task，成功时按传入顺序给出 results；随后复制外层 group，按保存的 idx 将结果放回。没有给已保留的列表创建 Task，它们仍留在原位置。

**本段产出**：成员已经替换为生成结果的 group；内层列表不会被展开。

**本段重点**：即使完成先后不同，为什么结果还能对应原位置？读完进入④。

<a id="phase-4"></a>

#### ④ 评分与交付：本层是否还要评分（432–439）

承接③已经收齐的 group。

```python
if not state.aborted and args.group_rm:
    rewards = await batched_async_rm(args, group)
    for sample, reward in zip(group, rewards, strict=False):
        sample.reward = reward
return group
```

本例 group_rm=False，直接返回；只有开启组级评分且未中止时，才调用 batched_async_rm 并写回 reward。该组级写回按成员为 Sample 使用，嵌套结果的组合支持不在本轮假定为已验证。

**本段产出**：返回完整 group，交给调用者注册的完成处理。

**本段重点**：谁负责这次评分，结果返回到哪一层？到这里完成本轮外层交接，暂不进入完成队列。

### 3.3 按同一编号阅读：每段看什么、到哪里停止

```text
① 准备成员：group → 带 session_id 的可生成成员
    ↓
② 创建任务：成员及其 idx → tasks[idx]
    ↓
③ 汇总结果：tasks → results → 按 idx 写回 group
    ↓
④ 评分交付：group → 按配置评分或直接返回 → 调用者
```

| 分段与源码入口 | 本段看清什么就停 | 需要时回查 | 读完到哪里 |
| --- | --- | --- | --- |
| [① 准备成员](#phase-1) · [398–415](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L398-L415) | group 已存在；state 与 session_id 各有什么作用；旧列表保留位置 | [GenerateState](../02-short-term-memory/classes/slime/rollout/sglang_rollout.py/GenerateState.md)；完整旧结果校验见折叠区 | ②：417 创建 tasks |
| [② 创建任务](#phase-2) · [417–425](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L417-L425) | 每个新成员创建一个 Task，idx 保存对应关系，参数逐份复制 | [generate_and_rm](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md) 的输入输出；暂不重读内部全链 | ③：427 等待并接收 results |
| [③ 汇总结果](#phase-3) · [427–430](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L427-L430) | tasks、results、group 各是什么；按原位置回填，保持内层形状 | [本函数卡](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm_group.md)的结果对应说明 | ④：433 判断评分责任 |
| [④ 评分交付](#phase-4) · [433–439](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L433-L439) | False 时为什么可直接返回；True 分支由谁算分 | [batched_async_rm](../02-short-term-memory/functions/slime/rollout/rm_hub/__init__.py/batched_async_rm.md)，只回顾接口 | 439 返回调用者；完成处理后续再读 |

**本轮从①开始，②③是主要观察点。** 表中的回查是阅读动作，不改变上方源码执行顺序。每段产生什么、接给谁保留在这里；详细机制与个人反馈进入[函数卡](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm_group.md)和[04-flow](../04-flow.md)，不再另追加一条重复导航。

### 3.4 停止位置与后置问题

能说明“成员怎样变成 Task、结果为何仍对应原位置、返回的 group 形状是什么”即可结束这轮。gather 的完整异常/取消、重试恢复、seed 和 group_rm 与嵌套列表的组合按实际问题再看。上游创建 group、跨组并发、背压和完成队列不在本轮展开。

<details>
<summary>① 折叠的旧分段列表校验：保留不等于无条件接受</summary>

完整源码在准备循环中检查列表非空，每段状态必须是 COMPLETED 或 TRUNCATED；非组评分时每段还必须已有 reward。检查不通过会抛 ValueError。校验通过后，②跳过该列表并保留原位置。本例先用全是新 Sample 的输入，不展开重试恢复协议。

</details>

<details>
<summary>② 折叠的确定性采样参数</summary>

若开启 sglang_enable_deterministic_inference，源码在复制参数后取 state.group_sampling_seeds[idx]，写入 current_sampling_params["sampling_seed"]，再创建该成员的任务。它改变本次采样配置，不改变 tasks 按 idx 收集的主线。

</details>

源码提交：18868a79b0b083a093798a94ed0f8cb4f71b9c14。参考 [scope skill](../../../../../../../../.agents/skills/repo-reading-scope/SKILL.md) 的局部导航与 [Step 001 阅读图表](../../../../../../../../.agents/skills/repo-reading-scope/references/step-001-reading-path.md)；[分块前快照](scope-before-phase-split-2026-10-26.md)保留原稿。本步不运行 Hugo、远端 Agent 或训练。
