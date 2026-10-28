> 2026-10-26 分块前快照。仅重算本文件移动后的相对链接，不作为当前 scope。

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

### 3.2 核心骨架

教学裁剪：主路径先取得状态、准备会话标识；省略已有分段列表的详细校验、确定性 seed 覆盖与 trace 包装。已有列表成员不创建新任务，原地保留在组的对应位置。

```python
state = GenerateState(args)
if state.aborted:
    return group

for sample in group:
    if isinstance(sample, list):
        continue  # 此前需校验它是可保留的已完成分段结果
    if sample.session_id is None:
        sample.session_id = str(uuid.uuid4())

tasks = {}
for idx, sample in enumerate(group):
    if isinstance(sample, list):
        continue  # 已完成的分段结果在前面校验过，保留它
    current_sampling_params = sampling_params.copy()
    # 本例未开启确定性采样，省略 seed 覆盖
    tasks[idx] = asyncio.create_task(
        generate_and_rm(args, sample, current_sampling_params, evaluation=evaluation)
    )

results = await asyncio.gather(*tasks.values())
group = list(group)
for idx, result in zip(tasks, results, strict=True):
    group[idx] = result

if not state.aborted and args.group_rm:
    rewards = await batched_async_rm(args, group)
    for sample, reward in zip(group, rewards, strict=False):
        sample.reward = reward
return group
```

### 3.3 阅读图与同编号导航

```text
① 准备：共享状态、session_id、可保留的旧结果
    ↓
② 分派：tasks[idx] = create_task(generate_and_rm(...))
    ↓
③ 汇总：gather → results → 按 idx 写回 group
    ↓
④ 交付：按 group_rm 判断本层评分，然后 return group
```

| 编号与入口 | 这次看清什么 | 返回与下一交接 |
| --- | --- | --- |
| ① [398–415](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L398-L415) | group 已由调用者提供；新成员补 session_id，旧分段结果可保留 | 417 创建 tasks 字典 |
| ② [417–425](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L417-L425) | 原组下标与 Task 配对；每个新成员一份采样配置 | 子调用回查已有 generate_and_rm 卡，任务结果交到 427 |
| ③ [427–430](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L427-L430) | 收齐任务结果后按 idx 放回，保持内层返回形状 | 433 判断本层评分责任 |
| ④ [433–439](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L433-L439) | False 直接交付；True 且未中止才组级评分 | 返回调用者注册的完成处理，队列在下一范围展开 |

本步讲解和个人反馈记入[函数卡](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm_group.md)与[04-flow](../04-flow.md)。既有 GenerateState、generate_and_rm、batched_async_rm 作为本步复用记录调入 02，不因此升级掌握状态。

### 3.4 停止位置与后置问题

先能说明“每个成员如何变成 Task、结果为何仍对应原位置、返回的 group 形状是什么”就停。gather 的完整异常/取消、重试恢复、seed 和 group_rm 与嵌套列表的组合按实际问题再看。上游创建 group、跨组并发、背压和完成队列不在本轮展开。

源码提交：18868a79b0b083a093798a94ed0f8cb4f71b9c14。本步不运行 Hugo、远端 Agent 或训练。
