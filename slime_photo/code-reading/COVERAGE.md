# 仓库阅读覆盖

以下记录路线计划涉及的部件和边界，不能据源码入口数量推断实现已覆盖。

## 仓库覆盖与缺口

这里记录计划覆盖范围。源码入口经过静态核对，00 的职责地图与 01 的完整任务主线有展开讲解；01 也串联 02 的请求与轨迹职责，仍不表示所有分支或用户掌握状态已确认。

| 领域 | 主要代码/材料 | 对应单元 | 预期覆盖 | 后续或外部缺口 |
| --- | --- | --- | --- | --- |
| Agent 组件 | `slime/agent/`、`examples/coding_agent_rl/` | 01、02 | 启动、模型协议、环境、上下文、轨迹、任务与评分 | CLI 内部工具循环、任意外部模型客户端 |
| 策略与评测 | `slime/rollout/`、`utils/eval_config.py`、多轮示例 | 03 | custom generate、RM、hook、过滤、数据集、结果合同 | 其他环境/策略按问题选读；不是所有示例已审计 |
| Trace、测试与复现 | `slime/observability/`、`tools/`、`tests/`、CI 与复现文档 | 04 | Trace 合同、真实埋点覆盖检查、日志、指标、回放、契约与 fake 测试 | 端到端埋点、GPU/模型/集群实测与实验管理实践 |
| 数据、并发与恢复 | `slime/data/`、`fully_async_rollout.py`、`utils/cleanup.py` | 05、07 | 缓冲、队列、传输、取消、背压、恢复与共同 checkpoint | straw-queue、共享存储等外部实现和故障实验 |
| 模型服务与调度 | `backends/sglang_utils/`、`slime/ray/serving.py`、`slime/ray/rollout.py`、`utils/health_monitor.py` | 06、07 | 部署、发现、资源布局、健康、服务所有权与权重更新 | SGLang 服务内部、所有部署拓扑与容量调优 |
| 容器与 Kubernetes | `docker/`、`scripts/`、Sandbox 合同 | 06 + 独立实践 | 定位构建依赖，定义环境操作和集群适配边界 | 本版本未定位到原生 Kubernetes 沙箱后端或集群 controller；需实际集群经验 |
| 训练与算法 | `train.py`、`backends/megatron_utils/`、SFT/校正示例 | 07 | 数据消费、基本 SFT/RL、策略版本、checkpoint 与权重发布 | 并行训练细节、全部算法推导和数值实验 |
| 独立 Rollout Buffer 与其他插件 | `slime_plugins/rollout_buffer/`、模型插件 | 05 对照；其余后置 | 区分独立 HTTP buffer、TrajectoryManager、主链数据队列 | 模型结构/算子/平台插件的具体实现 |
| 项目维护与跨语言 | README、`docs/`、`.github/`、`scripts/`、`docker/` | 00 定位，04/06 按需 | 配置、测试入口、启动与发布材料职责 | TypeScript/Rust/Go 协作与 AI 工具经验需独立项目材料 |

这条路线支持理解需求到接口、数据、验证和运行边界的映射。实际部署、算法协作、性能治理和 owner 经验还需要任务实践与可观察结果，不能由阅读文件数量代替。

## 第 0 章 全局职责与三种运行粒度

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 训练与生成总入口 | [train.py · main](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/train.py#L103) | locate | 只定位启动、资源准备和训练循环；训练算法留到 07。 |
| 任务数据合同 | [slime/utils/types.py · Sample](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/types.py#L107) | locate | 先辨认 prompt、reward、token、mask、状态和身份字段；字段转换在 02、03、07 展开。 |
| 分布式生成与评测入口 | [slime/ray/rollout.py · RolloutManager](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/rollout.py#L36) | locate | 类的角色与 generate/eval 入口；资源治理留到 06。 |
| 一个代码任务的组装 | [examples/coding_agent_rl/generate.py · generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L182) | locate | 只读调用骨架；执行和清理在 01 展开。 |

## 第 1 章 完整任务、Harness 与执行环境

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 任务生命周期 | [examples/coding_agent_rl/generate.py · generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L182) | trace | 分别追踪训练与 evaluation 分支；不是通用的独立任务平台。 |
| 调用方的模型入口准备 | [_AdapterService.__init__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L138)（examples/coding_agent_rl/generate.py） | trace | 细读 tokenizer/解析配置、Adapter 内部状态、HTTP 线程、监听/回连地址和进程复用；返回调用方继续任务、Session、环境和题目准备。 |
| 启动骨架 | [slime/agent/harness/common.py · BaseHarness.run](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L81) | trace | 配置和 CLI 启动可替换；CLI 内部工具循环在外部软件包。 |
| 沙箱操作合同 | [slime/agent/sandbox.py · Sandbox](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L28) | trace | 当前实现为 E2B；Kubernetes 后端需独立实现和验证操作语义。 |
| 长命令等待 | [slime/agent/sandbox.py · exec_and_wait](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L82) | explain | 区分等待超时、进程退出和外层环境回收，不能假设返回超时就已杀死进程。 |
| 补丁的独立评估 | [examples/coding_agent_rl/swe.py · run_evaluation](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/swe.py#L239) | trace | 评分环境与 Agent 工作环境分开；继续定位 _grade_scaleswe/_grade_swebench。 |

## 第 2 章 模型协议、上下文与训练轨迹

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 共享模型请求流程 | [slime/agent/adapters/common.py · BaseAdapter._run_turn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L318) | trace | 协议转换、模板编码、模型生成、解析、响应与轨迹记录；具体协议见旁边 openai.py/anthropic.py。 |
| 实际模型调用 | [slime/agent/adapters/common.py · call_sglang_generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L442) | trace | 原生 SGLang /generate；协议兼容不表示已经支持任意云 API。 |
| 输出与工具解析 | [slime/agent/parsing.py · parse_model_output](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/parsing.py#L25) | trace | 解析工具调用不等于执行工具；执行者是 CLI 或其他自定义 Agent。 |
| 会话轨迹与上下文分支 | [slime/agent/trajectory.py · TrajectoryManager](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L269) | trace | 第一遍看 record_turn/get_trajectory；token drift、分叉、mask 细节作为第二遍 explain 范围。 |
| 会话结束与训练样本导出 | [slime/agent/adapters/common.py · BaseAdapter.finish_session](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L245) | trace | 区分当前 HTTP 请求结束、会话关闭、Sample 导出和 cleanup-only drop_session。 |

## 第 3 章 策略接入、数据生成与评测合同

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 单样本生成与评分组合 | [slime/rollout/sglang_rollout.py · generate_and_rm](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L289) | trace | custom generate、异步等待、样本 hook 和 group_rm 分支；自定义函数可能扇出多个 Sample。 |
| 整批 rollout 返回合同 | [slime/rollout/base_types.py · call_rollout_fn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/base_types.py#L28) | trace | 训练/评估输出不同；本版本支持数据引用，不能只记成 Python Sample 列表。 |
| 可替换评分器 | [slime/rollout/rm_hub/__init__.py · async_rm](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/rm_hub/__init__.py#L55) | trace | 按样本、全局路径或远端评分分发；分组评分另看 batched_async_rm。 |
| 评测数据与参数 | [slime/utils/eval_config.py · EvalDatasetConfig](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/eval_config.py#L135) | trace | 先核对 eval_rollout_single_dataset 实际消费字段和结果合同；类中 timeout/early-stop/app_service 字段不能直接当作默认 runner 已实现的行为。 |
| 样本处理扩展点 | [slime/rollout/sample_hooks.py · apply_rollout_sample_hooks](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sample_hooks.py#L52) | trace | 同步/异步 hook 与样本身份传递；动态过滤和批次 hook 有不同位置。 |

## 第 4 章 Trace、结果分析、测试与复现

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 事件与 span 的组织 | [slime/observability/trace_utils.py · trace_span](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/trace_utils.py#L345) | trace | 自定义格式与跨边界 carrier；工具存在不表示所有示例已接好完整埋点。 |
| 实验日志与配置 | [slime/observability/logging_utils.py · configure_logger](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/logging_utils.py#L12) | locate | 继续读 init_tracking/finish_tracking；日志、指标与任务 Trace 分别定位。 |
| 正确率与结果统计 | [slime/observability/metric_utils.py · compute_pass_rate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/metric_utils.py#L14) | trace | 按题目分组和评分假设影响 pass@k 的解释。 |
| 轨迹时间线查看器 | [tools/trace_timeline_viewer.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tools/trace_timeline_viewer.py#L1) | locate | 输入适配、span 展示、离线分析；不当作现成的全链路在线监控。 |
| 扩展接口行为测试 | [tests/plugin_contracts/test_plugin_generate_contracts.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/plugin_contracts/test_plugin_generate_contracts.py#L1) | locate | 先读 fixture 与断言；测试未经本轮执行，不标为通过。 |

## 第 5 章 并发、任务数据、背压与恢复

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 持续运行的生成工作者 | [slime/rollout/fully_async_rollout.py · AsyncRolloutWorker](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_rollout.py#L78) | explain | 本地池的任务、完成队列与暂停；先读 _get_worker 分支，持久化 reader_config 模式还需 DistributedRollout。 |
| 批次生成与取消 | [slime/rollout/sglang_rollout.py · generate_rollout_async](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L476) | trace | 区分线程中的事件循环、进程/Ray 调度和服务端生成请求的取消。 |
| 持久化分布式生成 | [slime/rollout/fully_async_distributed.py · DistributedRollout.__init__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_distributed.py#L474) | trace | 从 _get_worker 的 reader_config 分支进入；每节点 worker、局部池、全局 demand/prefetch 与 worker 恢复。 |
| 任务领取与确认 | [slime/data/queue_data_source.py · QueueReader.get_samples](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L1068)、[slime/data/queue_data_source.py · RolloutQueueController.take](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L488)、[slime/data/queue_data_source.py · RolloutQueueController.complete](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L563) | trace | task、lease、result_ref 与 receipt；结果 accepted、训练 completed、checkpoint committed 分开理解。 |
| 任务数据源 | [slime/data/queue_data_source.py · QueueDataSource](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L1292) | trace | 这是 job-level reader/checkpoint 包装；具体租约与确认在 QueueReader/RolloutQueueController，外部 straw 语义另行核对。 |
| 结果打包与共享存储 | [slime/data/transport.py · pack_rollout_payload](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/transport.py#L350) | trace | Ray object-store 与 straw 数据引用两种路径；完成确认、接受批次和持久化 checkpoint 不等价。 |
| 共同清理预算 | [slime/utils/cleanup.py · Cleanup](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/cleanup.py#L9) | explain | 每项清理使用剩余时间；清理工具不是通用强制中断器。 |
| 恢复计划 | [slime/data/checkpoint.py · resolve_checkpoint](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/checkpoint.py#L237) | locate | 先辨认数据进度与模型/优化器状态的共同恢复边界，再看恢复实现。 |

## 第 6 章 模型服务、Ray 资源与容器边界

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 分布式资源布局 | [slime/ray/placement_group.py · create_placement_groups](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/placement_group.py#L123) | trace | Ray placement group 与 GPU 布局；不是 Kubernetes Pod 或集群调度器。 |
| 推理部署组装 | [slime/backends/sglang_utils/deployment.py · start_rollout_servers](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/sglang_utils/deployment.py#L79) | trace | 配置、router、engine group 和服务进程；模型内部算子后置。 |
| 外部模型服务发现 | [slime/backends/sglang_utils/external.py · discover_external_engines](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/sglang_utils/external.py#L95) | trace | 外部 SGLang 引擎信息与控制接口，不等同于任意 Chat Completions API。 |
| 模型服务所有权 | [slime/ray/serving.py · ServingCluster.__init__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/serving.py#L38)、[slime/ray/serving.py · ServingCluster.dispose](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/serving.py#L294) | trace | 服务与队列可以跨训练尝试保留；失败、detach、正常成功退出的政策不同。 |
| 生成服务管理与清理 | [slime/ray/rollout.py · RolloutManager.dispose](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/rollout.py#L160) | trace | 借用 ray/serving.py 中 ServingCluster 的模型服务，dispose 只清理自有资源；服务完整回收另由所有者负责。 |
| 容器构建参考 | [docker/Dockerfile](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/docker/Dockerfile#L1) | locate | 镜像、依赖与补丁；集群控制器、沙箱后端和网络存储仍需独立实践。 |

## 第 7 章 训练交接、策略版本与权重更新

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 生成、训练、保存与更新主循环 | [train.py · train](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/train.py#L13) | trace | 第一遍读职责与顺序；Megatron 张量并行和全部算法推导后置。 |
| 模型训练消费 | [slime/backends/megatron_utils/actor.py · MegatronTrainRayActor.train_actor](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/megatron_utils/actor.py#L449) | trace | 定位 reward、advantage、logprob、mask 的消费；不能假设所有字段在生成阶段已经算好。 |
| 权重发布 | [slime/backends/megatron_utils/actor.py · MegatronTrainRayActor.update_weights](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/megatron_utils/actor.py#L628) | trace | 暂停/版本/内存或磁盘更新；与 GPU/模型服务生命周期共同理解。 |
| 共同 checkpoint | [slime/data/checkpoint.py · save_checkpoint](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/checkpoint.py#L39) | trace | 模型/优化器状态与数据进度共同恢复；仅完成一次训练不等于可恢复 checkpoint。 |
| SFT 样本生成 | [slime/rollout/sft_rollout.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sft_rollout.py#L1) | locate | 审核后的轨迹可重新编码用于 SFT；需要概率信息的 RL 不能只用最终文本补齐。 |
