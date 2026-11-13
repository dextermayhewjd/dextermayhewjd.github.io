# Agent Lightning 三组件：从 Agent 执行到训练样本

[项目入口与唯一进度](../README.md#current-reading) · [此前 Kubernetes 阅读](../steps/step-002-build-job-spec/README.md)

本页保留 **Trainer、API Gateway、Rollout Controller 的通用交接地图**。具体哪些值得继续读，以[相对已读 Slime 的增量评估](slime-incremental-reading.md)为准；不把三组件的所有代码都列为下一阶段必读。SWE-smith 的具体 Agent loop 与挂载也不作为默认主线。

源码绑定本地提交 `0029dbb35c467799d35fee81d15d80264b0d1bd3`；以下是职责与入口定位，尚不表示已逐个阅读这些函数。

## 1. 三块内容分别在仓库哪里

| 组件 | 在这份代码里做什么 | 核心入口 |
| --- | --- | --- |
| **Trainer** | 接入 verl 的训练循环，取得并注册推理端点，提交 Agent 任务，收集轨迹/奖励并构建训练 batch，执行策略更新 | `agentlightning/verl/`：[`AgentLightningRayPPOTrainer._rollout:365`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/verl/trainer.py#L365)、[`_train_step:463`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/verl/trainer.py#L463)、[`fit:670`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/verl/trainer.py#L670) |
| **API Gateway** | 保存任务、模型端点和事件；代理 Agent 的模型请求并记录交互，向 Trainer 提供事件数据 | `agentlightning/server/`：[`llm_proxy:40`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/server/routes/proxy.py#L40)、[`forward_request:120`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/server/proxy.py#L120)、[`record_event:46`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/server/routes/events.py#L46) |
| **Rollout Controller** | 将已登记任务变成具体 Agent 执行，观察执行状态并回写 Gateway | `agentlightning/controller/`：已读的 [`K8sReconciler`](../steps/step-002-build-job-spec/03-long-term-memory/overview.md)；本地进程方式在 [`local_reconciler.py`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/local_reconciler.py) |

Trainer 内还有两个连接环节值得单独定位：

- [`AglRolloutManagerBase` / `AglRolloutManager`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/verl/agl_rollout_manager.py#L254)：通过 Gateway API 注册模型、提交任务、等待完成、获取事件。
- [`RolloutAdapter.get_train_data_batch:456`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/verl/rollout_adapter.py#L456)：将 `CompletedRollout` 中的交互序列与奖励转换为 verl 的 `DataProto`。这里还会根据配置按 transition 或 trajectory 组织样本。

## 2. 用一次 rollout 串起来

这是一条组件交接主线，跨服务部分通过 HTTP 完成，不是同一进程里逐层调用的函数链。

1. **Trainer 准备任务与模型端点。** `_rollout` 取得推理服务地址，交给 `register_model` 写入 Gateway；`_create_rollouts` 把数据集输入与执行配置组织为 `RolloutCreate`，提交 `/api/rollouts`。
2. **Gateway 登记任务，Controller 开始执行。** Gateway 建立 QUEUING 记录；已读的 Controller 查询任务并创建 Job 或本地进程，执行相应 Agent。
3. **Agent 按自己的 loop 工作，并向 Gateway 请求模型。** `AGL_OPENAI_BASE_URL` 把请求引到带 rollout ID 的代理 URL。Agent 的工具调用、上下文组织和循环由 Agent 执行端负责。
4. **Gateway 转发模型请求，同时保存交互。** `llm_proxy` 选择模型服务器并准备请求；`forward_request` 访问 `server.endpoint`，把响应交回 Agent；`_capture_event` / `record_event` 保存 `model_request` 事件。原始记录包含 request、response、模型版本、端点、耗时等信息。
5. **奖励与完成状态分别记录。** 奖励通过事件或相应 hook 机制提供；Controller 回写的 SUCCEEDED/FAILED 描述执行状态。任务成功状态本身不等于训练奖励或训练样本。
6. **Trainer 取回事件并形成可训练的数据。** `_build_completed_rollout` 取得原始与 triplet 形式事件，从模型请求中组装 token 序列、log probabilities 等，并关联奖励；`get_train_data_batch` 进一步组织 `prompts`、`responses`、mask、scores 等张量和任务标识。
7. **Trainer 进行更新。** `_train_step` 使用生成的 batch 计算相应优势、调用 `_update_actor` 等 verl 接口，并经 `checkpoint_manager.update_weights` 同步权重；`fit` 组织这些训练步。

当前最值得补齐的是第 3–6 项：**一个可替换 Agent 的模型交互，怎样变成可训练样本。** 这比继续研究具体示例的 Agent loop 更贴近本轮问题。

## 3. 具体 Agent loop 与框架的边界

SWE-smith 模板固定启动 `smith_agent.py`，属于该示例的选择。框架在 Kubernetes 模式接受 Job 模板，在本地模式接受 Agent 类配置；它并不要求所有任务都采用 SWE-smith 的同一套 loop。

需要分别考虑两项选择：

- **执行端**：启动哪个 Agent 程序或 harness，怎样传入任务、执行工具、报告奖励和结束。
- **训练对象**：Trainer 管理哪个可更新模型，推理端点怎样提供给 Gateway，模型调用的数据怎样转换为训练 batch。

因此，Codex/Claude 一类执行端可以作为后续接入目标，但不能仅凭“可替换命令”就认定已经兼容。当前源码的代理路由只接受 OpenAI 风格的 `chat/completions`、`completions`，`forward_request` 明确拒绝 `stream=True`。若所用执行端要求其他协议或流式响应，就需要对应适配；本轮未审计某个具体版本的 Codex/Claude 接口。

同样需要核对训练数据约定：执行端的模型调用要经过可关联 rollout/attempt 的入口，模型响应和奖励要能被后面的事件处理与样本转换使用。这些是可替换 Agent 接入时的框架问题，具体示例循环不是唯一答案。

## 4. 下一处推荐的阅读入口

此前建议先看 Gateway 的 `llm_proxy`。在回查用户已经读过的 Slime Adapter、轮次记录与训练闭环后，**不再把完整重读 Gateway 作为默认安排**；新增量与候选停止点见[对照评估](slime-incremental-reading.md#5-当前建议)。

来路已在前两步出现：`build_job_spec` 将代理 URL 写入 Agent 的环境变量；之后是 Agent 经 HTTP 发起请求，才进入 `llm_proxy`，不是 `build_job_spec` 直接调用它。

若以后需要回查 Gateway，这个入口可以解决请求身份、后端选择与转发的问题；`forward_request → _capture_event → record_event` 是事件记录路径。它们先作为定位信息，不自动展开。

Trainer 的 `_rollout` 与 `AglRolloutManager` 连接事件回收；`RolloutAdapter.get_train_data_batch` 处理样本构造。进一步核对 Slime 的完成组收集、活动任务保留与轨迹实现后，当前建议收束通读；trajectory 拼接、异步组收集和权重同步仅保留为具体问题触发的对照入口，不再据目录继续安排章节。

## 5. 依据与验证边界

- 本地 [README 的架构说明](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/README.md)与 [docs/05-basics.md](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/docs/05-basics.md)。
- 模型注册与任务提交：`agl_rollout_manager.py:293–303,380–429`；事件回收：`431–435,470–539`。
- 请求记录：`server/proxy.py:120–173,247–278`；事件存储与查询：`server/routes/events.py:46–66,241–260`；应用路由装配：`server/app.py:53–94`。
- 训练数据与更新：`trainer.py:365–461,463–668`、`rollout_adapter.py:456–933`。
- 本轮是固定版本源码与结构核对，没有运行完整 Agent、模型训练或验证任意外部执行端兼容性。
