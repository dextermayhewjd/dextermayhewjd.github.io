# 01 · 阅读范围：一组生成任务怎样组织和交付

[步骤入口](README.md) · [本步函数卡](02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm_group.md) · [前一步](../step-010-generate-and-rm/README.md)

## 1. 阅读目标

- **岗位目标**：对齐混元岗位的异步并发、任务与结果组织能力。
- **本步问题**：一个 group 怎样拆成多个生成任务，怎样收齐结果并保持原来的对应关系？
- **选定路径**：新输入 group、Coding Agent、evaluation=False、group_rm=False；先走正常路径，再按问题补失败与重试。

## 2. 指挥官函数

- 入口：[generate_and_rm_group:388–439](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L388-L439)。
- 调用者：[AsyncRolloutWorker._loop:214–223](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L214-L223)；本步只定位，不展开持续调度。
- 已读下游：[generate_and_rm](02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md)，负责单次生成控制、后处理和奖励归属。

## 3. 核心骨架与统一阅读导航

### 3.1 整体位置

```text
AsyncRolloutWorker._loop（以后展开）
    → generate_and_rm_group（本步：一组任务）
        → 多个 generate_and_rm（前一步：各自生成与评分）
    ← 收回一组结果
    → 完成回调与结果队列（以后展开）
```

### 3.2 完整核心骨架：在同一流程中划分四段

从调用者提供的 group 开始，到返回这一组结果结束；①—④直接标在同一个函数体内。group 和 sampling_params 进入本函数时已经存在，本函数不负责从一个提示复制出多个输入。

以下是教学裁剪：采用新输入 group、evaluation=False、group_rm=False；保留关键业务分支，折叠旧分段列表的完整校验、确定性 seed 覆盖与 trace 包装。参数保留到能看清本步数据交接的程度。

```python
# ① 准备成员（398–415）：取得共享状态，补齐新成员的会话标识
state = GenerateState(args)
if state.aborted:
    return group

for sample in group:
    if isinstance(sample, list):
        continue  # 完整源码先校验旧分段结果，再保留它
    if sample.session_id is None:
        sample.session_id = str(uuid.uuid4())

# ② 创建任务（417–425）：待生成成员 → {原组下标: Task}
tasks = {}
for idx, sample in enumerate(group):
    if isinstance(sample, list):
        continue  # 旧分段结果不再生成，仍占据原位置
    current_sampling_params = sampling_params.copy()
    # 本例未开启确定性采样，省略 seed 覆盖
    tasks[idx] = asyncio.create_task(
        generate_and_rm(args, sample, current_sampling_params, evaluation=evaluation)
    )

# ③ 汇总结果（427–430）：等待 Task，按原组下标放回结果
results = await asyncio.gather(*tasks.values())  # 结果顺序对应传入的 Task 顺序
group = list(group)  # 复制外层容器，内层 Sample 列表不展开
for idx, result in zip(tasks, results, strict=True):
    group[idx] = result

# ④ 评分交付（432–439）：按配置补组级评分，再返回整组
if not state.aborted and args.group_rm:
    rewards = await batched_async_rm(args, group)
    for sample, reward in zip(group, rewards, strict=False):
        sample.reward = reward
return group
```

②委派给前一步读过的 generate_and_rm；③接回它返回的 Sample 或 Sample 列表；④将整组交回上层调用者。本例 group_rm=False，跳过组级评分。

### 3.3 对照骨架阅读

下面的编号对应上方代码中的四处注释；读每段时，只看清它接住什么、交出什么。

| 骨架分段与源码 | 数据交接 | 本段看清什么就停 | 按需回查 |
| --- | --- | --- | --- |
| <a id="phase-1"></a>① 准备成员 · [398–415](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L398-L415) | 已有 group → 新成员补齐 session_id | 这里准备对象，还没有创建生成 Task；旧分段列表保留位置 | [GenerateState](02-short-term-memory/classes/slime/rollout/sglang_rollout.py/GenerateState.md)；旧结果校验见下方折叠区 |
| <a id="phase-2"></a>② 创建任务 · [417–425](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L417-L425) | 待生成成员 → tasks[idx] | 每个成员怎样对应一个 Task；为什么保留 idx、逐份复制参数 | [generate_and_rm](02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md) 的输入输出；返回③接收结果 |
| <a id="phase-3"></a>③ 汇总结果 · [427–430](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L427-L430) | tasks → results → 按 idx 写回 group | 完成先后不同，结果为什么仍对应原位置；内层结果形状怎样保留 | [本函数卡](02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm_group.md)；返回④判断评分责任 |
| <a id="phase-4"></a>④ 评分交付 · [432–439](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L432-L439) | 收齐的 group → 按配置评分 → 返回调用者 | 本层何时评分，最后将什么交回上层 | [batched_async_rm](02-short-term-memory/functions/slime/rollout/rm_hub/__init__.py/batched_async_rm.md) 的接口；返回本层写回 reward、交付整组 |

**从①接入，重点观察②③的任务与结果对应，读到④返回为止。** 回查是阅读动作，不改变骨架的执行顺序。详细机制与个人反馈继续放在[函数卡](02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm_group.md)和[04-flow](04-flow.md)。

### 3.4 停止位置与后置问题

能说明“成员怎样变成 Task、结果为何仍对应原位置、返回的 group 形状是什么”即可结束这轮。组级评分写回直接访问成员的 sample.reward；本例走 group_rm=False，不预设 True 与嵌套列表的组合已可用。gather 的完整异常/取消、重试恢复、seed 和 group_rm 与嵌套列表的组合按实际问题再看。上游创建 group、跨组并发、背压和完成队列不在本轮展开。

<details>
<summary>① 折叠的旧分段列表校验：保留不等于无条件接受</summary>

完整源码在准备循环中检查列表非空，每段状态必须是 COMPLETED 或 TRUNCATED；非组评分时每段还必须已有 reward。检查不通过会抛 ValueError。校验通过后，②跳过该列表并保留原位置。本例先用全是新 Sample 的输入，不展开重试恢复协议。

</details>

<details>
<summary>② 折叠的确定性采样参数</summary>

若开启 sglang_enable_deterministic_inference，源码在复制参数后取 state.group_sampling_seeds[idx]，写入 current_sampling_params["sampling_seed"]，再创建该成员的任务。它改变本次采样配置，不改变 tasks 按 idx 收集的主线。

</details>

源码提交：18868a79b0b083a093798a94ed0f8cb4f71b9c14。参考 [scope skill](../../../../../../../.agents/skills/repo-reading-scope/SKILL.md) 的局部导航与 [Step 001 阅读图表](../../../../../../../.agents/skills/repo-reading-scope/references/step-001-reading-path.md)；[最初快照](references/scope-before-phase-split-2026-10-26.md)与[四块展示快照](references/scope-four-blocks-before-integration-2026-10-26.md)保留调整前材料，修改来由见[过程记录](04-flow.md#scope-integrated-phases)。本步不运行 Hugo、远端 Agent 或训练。
