# 相对已读 Slime，Agent Lightning 还值得读什么

[项目入口与唯一进度](../README.md#current-reading) · [三组件地图](framework-components.md) · [Kubernetes 岗位范围](tencent-k8s-scope.md)

本页评估的是**相对已有阅读的增量价值**，不按两个仓库的目录各读一遍，也不作整体质量排名。

**本轮建议：可以停止把 Agent Lightning 作为连续通读任务。** 逐项核对后，用户指出的请求接入、记录与轨迹、收够完成组数、保留未完成工作，在 Slime 中都已有相应实现。Agent Lightning 的差别主要是后端选择、状态存放位置和组件划分；这些差别不自动构成新的必读内容。已读 Kubernetes Job 路径保留为主要补充。

这是按当前学习目标作出的建议，尚不把它写成用户已经决定终止学习，也不把任何未验证实现标为已掌握。

## 1. 先接回已经读过的内容

Slime 学习记录已包含以下链路，保留原有理解与未知：

- [Adapter 请求处理](../../slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md)：协议转换、准备模型输入、调用 SGLang、解析并返回响应、记录轮次。
- [历史 token 前缀处理](../../slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/_session_prompt_ids.md)：核对历史候选后复用原始模型 token，接上新后缀；不匹配时使用普通编码。
- [轨迹导出](../../slime/topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/02-short-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.get_trajectory.md)：从会话树的路径组装 Sample；记录中保留了具体拼接、分段与 mask 算法尚未逐项展开的边界。
- [训练与权重更新主线](../../slime/topics/04-training-data-updates/steps/step-017-generation-training-loop/README.md)：已读生成、训练、暂停/恢复与权重交接；不因跨仓库而默认重新学习这些职责。

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

<a id="completed-group-audit"></a>

### 2.1 完成多少组再训练：Slime 已有直接实现

用户已读的 [Step 013](../../slime/topics/02-rollout-reward/steps/step-013-completed-group-handoff/01-scope.md) 就包含本地 fully-async worker 的完成组领取和收集。它不是 Agent Lightning 才提供的能力。

Slime 的 [`_generate_rollout_async`](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L278) 以 `args.rollout_batch_size` 为目标，读取完成队列，仅把通过过滤的组计入 collected。核心条件为：

```python
target = args.rollout_batch_size
while len(collected) < target:
    ...
    for _gid, group in worker.get_completed_groups(limit=target - len(collected)):
        ...
        if verdict.keep:
            ...
            collected.append(group)
```

这是省略日志、过滤准备和传输细节的源码裁剪。`get_completed_groups` 只取调用方需要的组数，剩余完成组留在 output_queue；正在执行的组保存在独立后台 worker 的 active_tasks 中，消费函数返回不等于关闭 worker。组内的 `generate_and_rm_group` 等待其任务汇总后返回；ABORTED/PENDING 结果由完成回调交回重试，不直接当成可训练完成组。

Agent Lightning 的 [`enqueue_and_wait_until_group_completed`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/verl/agl_rollout_manager.py#L599) 则按 data_id 分组，检查组中全部 rollout 已进入终态，达到 `target_finished_group_num` 后返回，并把未选中的组记录放入 `new_carry_over_rollouts`。

两者都提供“够一批组就交给训练，其他工作保留”的能力。差异是 Slime 的后台任务/完成队列，与 Agent Lightning 的 Gateway 状态、外部进程/Job 和显式 carry-over ID 列表；不能把状态载体不同说成 Slime 缺少这个功能。

该结论限定于这里核对的 fully-async 路径。Slime 普通 `sglang_rollout.generate_rollout_async` 收够目标后会调用 abort，开启 partial rollout 时再收回部分结果；不能把所有运行模式都说成完全同样的保留方式。

### 2.2 更新模型前怎样暂停：目标已有覆盖，暂停层次不同

Slime 的 `train.py:88–93` 暂停 rollout admission、同步权重，再按原状态恢复；`RolloutManager.pause_rollout_admission` 对本地 worker 使用 `pause(drain=False)`，不以清空所有活动任务为条件。示例 Megatron 权重发布实现还会暂停推理引擎，按配置选择 abort 或 in_place，再发布权重并恢复。Agent Adapter 在启用 partial rollout 时也有续接被中断生成的代码。

Agent Lightning 的 `_pause_and_drain_gateway` 暂停 Gateway 的新模型请求并等待 inflight 降为零，再进行后续更新；外部 Agent 的未完成 rollout 可以保留。

暂停对象和机制并不等价，但“不要让模型更新与旧推理请求无序交叉、保留适当的未完成工作”已经属于用户读过的 Slime 能力范围。因此不再把它列为默认新增章节。

### 2.3 HTTP 服务和轨迹：不要把库名当成全部业务

Slime 通过 aiohttp 创建应用、注册 Anthropic/OpenAI 路由，并在 BaseAdapter 中处理会话、模型调用、响应与记录。Agent Lightning 使用 FastAPI 接路由、httpx 访问模型服务。**aiohttp/FastAPI 是实现所用的 HTTP 工具；协议转换、任务关联与轨迹记录仍是各项目自己的代码。**

记录也都有实现：Slime 的 TrajectoryManager 保存消息树和 TurnRecord，SampleBuilder 处理拼接、漂移和 mask；Agent Lightning 保存按 rollout/attempt 组织的事件，再由 RolloutAdapter 生成训练行。相应概念已覆盖，表示结构不同可留作参考，无需因此再完整通读第二套。

因此，不能只看 Gateway 文件里没有会话树，就判定它没记录或没处理拼接。当前实现把部分样本组织放在 Trainer 侧。但也不能把这种职责移动描述成具备 Slime 所有协议适配与 token 修复能力。

## 3. 可按具体问题回查的实现差异

以下两项保留为参考，**不再作为默认继续阅读任务**。它们都与 Slime 已有能力重合；只有出现具体问题时才值得回查。

### A. 多轮 token 接不上时，训练样本怎样处理

回查入口是 [`RolloutAdapter.get_train_data_batch` 的 trajectory 分支](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/verl/rollout_adapter.py#L619)，先限定在约 619–734 行，不通读整份 Adapter。

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

**收束 Agent Lightning 的默认源码阅读。** 不再为了找到差异而安排新的 Trainer、Gateway、轨迹合并或异步调度章节。

- 已读的 Kubernetes Job 构造、提交、观察与状态协调，保留为此次跨仓库学习的主要补充。
- 协议接入、每轮记录、轨迹转样本、完成组收集、暂停与模型更新，Slime 已有对应实现及阅读记录；有未知时可回到原有具体问题，不因为第二个仓库出现相似代码就重开课程。
- 本页保留差异和源码位置，后续若真的需要独立 Gateway、Kubernetes 进程隔离或迁移到 verl/vLLM，再按问题使用这些材料。
- 源码阅读收束与实际工程验证是两回事。这里不把停止扩展通读写成已经具备完整集群运行经验，也不强行安排用户未选择的实践。

本轮尚未新增 Step 或函数卡；是否继续由具体任务决定，而不是要求把仓库读完。

## 6. 版本与依据

- Slime 比较依据为学习记录对应的 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。本机实际 HEAD 为 `540ea919e45b8b929198abce008a103be9cfc779`；本次通过 Git 读取固定版本，不把历史笔记改标为当前 HEAD。
- Slime 关键位置：`slime/agent/harness/claude_code.py:86–116`、`adapters/common.py:93–136,387–475`、`adapters/anthropic.py:48`、`adapters/openai.py:48`、`trajectory.py:230–263,381–442,554–598`。
- Agent Lightning：`0029dbb35c467799d35fee81d15d80264b0d1bd3`；`server/routes/proxy.py:40`、`server/proxy.py:120–173,247–278`、`server/routes/events.py:125–176`、`verl/rollout_adapter.py:55–56,619–734`、`verl/agl_rollout_manager.py:599–689`。
- 补充组收集核对：`slime/rollout/fully_async_rollout.py:114–161,178–275,278–378`、`sglang_rollout.py:388–439,442–487,492–616`、`slime/ray/rollout.py:151–158`、`train.py:51–93`。本次确认以上相关核心文件在学习版本 18868a79 与本机 HEAD 间无差异，旧笔记仍保留原提交归属。
- 推理引擎权重同步边界参见本机 HEAD 下 `slime/backends/megatron_utils/update_weight/update_weight_from_distributed.py:103–143`；该处只用于核对有暂停/恢复机制，未新增底层权重算法阅读。
- [本轮完成组与学习必要性复核](../steps/step-002-build-job-spec/04-flow.md#slime-capability-overlap-audit) · [复核前的建议快照](history/2026-11-03-incremental-before-completed-group-audit.md)。
- 局部验证：抽取实际 `get_completed_groups` 方法，对含三组的内存队列调用 `limit=2`，确认返回两组且第三组仍留队。该验证仅覆盖领取边界，没有启动后台 worker。
- 本轮其余部分为源码与历史阅读记录对照，未运行真实 worker、模型、代理或训练，也没有验证外部 Codex/Claude 版本的完整兼容性。
