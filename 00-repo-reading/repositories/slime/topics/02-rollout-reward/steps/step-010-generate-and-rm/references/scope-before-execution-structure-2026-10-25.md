# 01 · 阅读范围：生成接入与奖励归属

[步骤入口](../README.md) · [本步函数记录](../02-short-term-memory/overview.md) · [上一主题](../../../../01-coding-agent-rl/README.md)

> 本轮源码回查补充：下方裁剪主要展示生成与评分的数据路径。完整函数骨架还应保留 `GenerateState`、生成准入、分批启动、中止检查与名额释放，见[完整执行结构](../../../../../../../../slime_photo/code-reading/chapters/03-strategy-evaluation/walkthrough.md#state-and-execution-skeleton)及[本轮问题](../04-flow.md#state-and-execution-skeleton)。

## 1. 阅读目标

- **整体目标**：理解自定义 Agent 怎样接入 Slime 的生成与评分流程。
- **本步问题**：框架怎样选中已读的 Coding Agent `generate`，它返回后是否还要再评分？
- **阅读范围**：先跟一个新 `Sample`，沿 Coding Agent 正常生成并返回样本列表的路径读通；其他返回分支随后对照。

## 2. 指挥官函数

- **本步入口**：[sglang_rollout.py::generate_and_rm](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L289-L380)，串起生成函数选择、等待、样本后处理与评分。
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
- **返回**：Coding Agent 交回样本列表，本函数完成后处理与奖励检查，再把列表交回 `generate_and_rm_group`。

### 3.2 核心骨架：选实现 → 等生成 → 后处理 → 补奖励 → 返回

以下是 `generate_and_rm` 的教学裁剪：已配置 Coding Agent，`evaluation=False`、`group_rm=False`，正常返回 `list[Sample]`，没有改变返回形状的额外 hook。先只看这条路径，调用参数用 `...` 省略。

```python
generate_func = load_function(...)                   # ① 取得配置指定的生成函数
generate_call = generate_func(...)                   # ② 准备本次 Coding Agent 调用
sample = await _run_server_abort_generate(...)       # ② 等待完整任务，接住生成结果
sample = await apply_rollout_sample_hooks(...)       # ③ 执行配置的样本后处理

samples = sample                                    # 当前路径：结果是样本列表
samples_need_reward = [sample for sample in samples if sample.reward is None]
rewards = await batched_async_rm(...)                # ④ 为缺少奖励的成员取得分数
for sample, reward in zip(...):
    sample.reward = reward                          # ④ 写回这些成员
return samples                                      # ⑤ 交回完整样本列表
```

- **与前一主题的连接在②**：等待期间，已读的 Coding Agent 完成单题任务；这里接住它的返回值。
- **本函数继续做③④⑤**：先后处理，再检查哪些样本缺奖励，最后返回完整列表。已有奖励的成员保留原分数。

### 3.3 沿骨架阅读：从①开始，读完回到下一行

| 骨架位置 | 本轮看清什么 | 源码入口与返回位置 |
| --- | --- | --- |
| ① 取得生成函数 | 配置的路径怎样对应到已读的 Coding Agent `generate` | [338–344 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L338-L344)；看清后接② |
| ② 调用并等待 | `generate_call` 怎样交给包装器等待，返回值由谁接住 | [346–349 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L346-L349)；取消内部暂不展开，返回后接③ |
| ③ 样本后处理 | hook 位于生成之后、评分之前 | [353–355 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L353-L355)；先按接口理解，继续④ |
| ④⑤ 补奖励并返回 | 挑出缺奖励的成员、写回分数、交回整个列表 | [361–371 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L361-L371)；回到 `generate_and_rm_group:427–430` 接收结果 |

具体输入输出与逐段说明见 [generate_and_rm 函数卡片](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md)。**停止位置**：能沿这五项说明一份任务怎样生成、后处理、补奖励并交回调用者；评分器内部留到 `rm_hub` 再读。

<details>
<summary>本轮剪掉了什么，以及其他路径何时再看</summary>

- **配置与运行控制**：本版省略路径优先级、参数签名检查、限流、分批启动、追踪及失败处理；完整执行骨架需补回运行控制，见页首校正。当前 Coding Agent 使用 `_run_server_abort_generate`，所以另一种等待包装不并排放入这条路径。
- **上下文传递**：源码在 hook 前后调用 `inherit_queue_context`，传递任务上下文。本轮先看生成与奖励的主干，队列身份和确认机制后续展开。
- **其他返回路径**：返回单个 Sample 时按 `reward is None` 调用 `async_rm`；`group_rm=True` 时交回调用者统一处理组评分。已有完成结果与 ABORTED 结果还各有提前返回，均未画进这条新任务正常路径。
- **奖励边界**：`0.0` 是已有分数，只有 `None` 才待补。当前 Coding Agent 的正常训练结果已带奖励，所以待评分列表通常为空；源码仍会调用 `batched_async_rm(args, [])`，并非完全跳过该入口。

</details>

## 版本说明

- 源码固定为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；本步卡片使用这一版本。
- [重排前的 scope](scope-before-core-skeleton-review-2026-10-25.md)完整归档；本轮按既有 scope skill 恢复“固定路径、真实调用、短注释、按需展开”的层次。
- [04-flow](../04-flow.md#topic-two-start)保存开始阅读的过程；本轮格式反馈见[骨架审阅记录](../../../../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#step010-core-skeleton-review)。
