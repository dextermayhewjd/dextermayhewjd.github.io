# 相对已读 Slime，Agent Lightning 还值得读什么

[项目入口与唯一进度](../../README.md#current-reading) · [三组件地图](../framework-components.md) · [Kubernetes 岗位范围](../tencent-k8s-scope.md)

本页评估的是**相对已有阅读的增量价值**，不按两个仓库的目录各读一遍，也不作整体质量排名。

## 1. 先接回已经读过的内容

Slime 学习记录已包含以下链路，保留原有理解与未知：

- [Adapter 请求处理](../../../slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md)：协议转换、准备模型输入、调用 SGLang、解析并返回响应、记录轮次。
- [历史 token 前缀处理](../../../slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/_session_prompt_ids.md)：核对历史候选后复用原始模型 token，接上新后缀；不匹配时使用普通编码。
- [轨迹导出](../../../slime/topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/02-short-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.get_trajectory.md)：从会话树的路径组装 Sample；记录中保留了具体拼接、分段与 mask 算法尚未逐项展开的边界。
- [训练与权重更新主线](../../../slime/topics/04-training-data-updates/steps/step-017-generation-training-loop/README.md)：已读生成、训练、暂停/恢复与权重交接；不因跨仓库而默认重新学习这些职责。

用户对“把请求改发到 Adapter API”的理解方向成立。固定学习版本中，Claude Code 的启动配置同时保留了两个不同字段：

```python
"ANTHROPIC_BASE_URL": ctx.adapter_url,
"ANTHROPIC_MODEL": ctx.model_label,
```

前者决定请求先到哪个接入服务，后者是模型标识。`_AdapterService` 按 Agent 类型提供 Adapter 与地址；Adapter 再调用配置的 SGLang 后端。不是把“模型名称”与“服务地址”合并为同一件事。

## 2. 看起来缺少的处理，有些换了位置

| 问题 | 已读 Slime 路径 | Agent Lightning 当前实现 | 对本轮学习的价值 |
| --- | --- | --- | --- |
| 协议如何接入 | Anthropic/OpenAI Adapter，转换请求并组织对应响应 | Gateway 接受 OpenAI 风格请求，选择后端并转发 | 接入职责已熟悉，核对差异即可，不必完整重读 |
| 每次模型调用怎样记录 | `_run_turn → manager.record_turn`，关联会话树与 TurnRecord | `forward_request → _capture_event → record_event`，按 rollout/attempt 保存请求、响应和模型版本等事件 | 采集与训练分开的部署边界可对照，记录接口本身新增量有限 |
| 多轮如何进入训练样本 | 既有请求前的 `_session_prompt_ids`，也有请求后的轨迹树导出与 SampleBuilder | Trainer 侧 `RolloutAdapter.get_train_data_batch` 的 transition/trajectory 分支 | 可以只比较拼接条件、mask 与不匹配后的拆分 |
| 怎样训练并更新权重 | Step 017 已读正常训练闭环 | 基于 verl 的 `_train_step` 与权重同步 | 通用外层循环重合较多，优先级低于具体差异 |
| 任务怎样放到 Kubernetes | 原有 Slime 阅读更多在沙箱调用侧 | 直接生成、提交、观察 Job，并与 Gateway 状态协调 | 对当前目标最明显的增量；后续价值也包括部署与排障实践 |

因此，不能只看 Gateway 文件里没有会话树，就判定它没记录或没处理拼接。当前实现把部分样本组织放在 Trainer 侧。但也不能把这种职责移动描述成具备 Slime 所有协议适配与 token 修复能力。

## 3. 两个可选的小范围差异题

### A. 多轮 token 接不上时，训练样本怎样处理

首选入口是 [`RolloutAdapter.get_train_data_batch` 的 trajectory 分支](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/verl/rollout_adapter.py#L619)，先限定在约 619–734 行，不通读整份 Adapter。

这里先得到上一段 `prompt + response`，再检查后轮 prompt 是否以它为精确 token 前缀：

- 可以续接：把新增 observation token 接上，mask 为 0；新生成的 response token 接上，mask 为 1。
- 无法续接：先输出当前训练段，再从下一轮开始新段，不强行合成一个不连续序列。

这与 Slime 的关联要说完整：Slime 不仅在请求前尝试恢复历史 token，也在 `_SampleBuilder` 中处理追加、重对齐和分段；不能简化为“Slime 只在线处理、Agent Lightning 才有事后拼接”。Agent Lightning 的这个分支可以作为较集中的对照实现，补足先前未细读的内部规则，新增的是实现取舍，不是全新的概念。

**停止点**：用两轮构造数据说清楚“什么条件允许合并，哪些 token 算训练损失，无法合并时产出几段”。无需为此先读完整 Gateway、Trainer 或训练算法。

### B. 未完成的 Agent 跨训练步时，怎样与模型更新协作

入口为 [`AglAsyncRolloutManager.enqueue_and_wait_until_group_completed`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/verl/agl_rollout_manager.py#L599) 与 [`_pause_and_drain_gateway`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/verl/trainer.py#L171)。

只比较：按 data_id 保持同一输入的 rollout 组完整；收够完成组后，把其他组带到下一次；权重更新前在 Gateway 拒绝新模型请求并等待在途请求结束。这是与 Slime 已读暂停、恢复、权重同步的差异对照，不重开整套异步课程。

**停止点**：分清暂停的是模型请求入口还是 Agent 进程、哪些任务继续保留、何时能更新模型。若当前没有长任务跨更新的问题，这项可暂缓。

## 4. 可以确认的功能边界

当前 Agent Lightning 的 `llm_proxy` 仅允许 `chat/completions`、`completions`，`forward_request` 拒绝 `stream=True`；本轮没有找到对应的 Anthropic Messages 适配路径。它在协议接入层明显比已读 Slime 的 Anthropic/OpenAI Adapter 路径更窄。

当前 Gateway 主要转发和记录；token 化由模型服务完成，事件接口再提取返回的 token IDs 与 log probabilities。这里没有看到 Slime `_session_prompt_ids` 那种基于已保存历史、在发模型请求前修复 token 前缀的等价流程。相应复杂性可能体现在无法合并时的分段，而不是请求前的历史恢复。

以上是固定版本的代码事实，足以判断某些场景需要额外适配；不能据此推断“整个项目没有处理好”。协议范围、复用后端和数据组织方式不同，需按具体问题评估。

## 5. 当前建议

撤回把“完整读一遍 llm_proxy，再扩展整个 Trainer/Gateway”作为默认下一步的建议。三组件地图保留为定位材料，实际阅读采用增量原则：

- Kubernetes 是目前最明确的新增主线，已有源码阅读可以阶段性收束；真实运行与排障仍是另一类证据。
- 如果还想从这个仓库增加一项理解，优先选择 A 的多轮合并差异题，特别是 Slime 记录里尚未细读的 mask/分段边界。
- 如果该问题也已能独立说明，可以停止继续扩展 Agent Lightning 源码阅读。B 保留为具体长任务问题触发的选项，不制造必读章节。

当前只是评估与建议，不预建下一步或函数卡，不重置 Slime 的已读记录。

## 6. 版本与依据

- Slime 比较依据为学习记录对应的 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。本机实际 HEAD 为 `540ea919e45b8b929198abce008a103be9cfc779`；本次通过 Git 读取固定版本，不把历史笔记改标为当前 HEAD。
- Slime 关键位置：`slime/agent/harness/claude_code.py:86–116`、`adapters/common.py:93–136,387–475`、`adapters/anthropic.py:48`、`adapters/openai.py:48`、`trajectory.py:230–263,381–442,554–598`。
- Agent Lightning：`0029dbb35c467799d35fee81d15d80264b0d1bd3`；`server/routes/proxy.py:40`、`server/proxy.py:120–173,247–278`、`server/routes/events.py:125–176`、`verl/rollout_adapter.py:55–56,619–734`、`verl/agl_rollout_manager.py:599–689`。
- 本轮是源码与历史阅读记录对照，未运行模型、代理或训练，也没有验证外部 Codex/Claude 版本的完整兼容性。
