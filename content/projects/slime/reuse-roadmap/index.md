---
title: "Slime 全仓代码复用与项目路线"
linkTitle: "全仓代码复用与项目路线"
description: "面向 Agent 工程岗位，梳理 Slime 全仓可复用的执行、评测、Trace、数据队列、模型服务与训练能力，以及 API、Kubernetes 和自部署模型的接入边界。"
weight: 5
ShowToc: true
---

目标项目是在 Kubernetes 上运行 Agent 任务，先调用模型 API，随后接入自部署的 SGLang 或 vLLM 模型，最后按需要连接训练流程。Slime 值得复用的范围包括 Agent 执行、批量生成、评测、Trace、数据队列、故障恢复和模型服务管理，阅读范围应覆盖整个仓库。

工程上可以分成三个阶段：**API 驱动的执行与评测 → 自部署模型推理 → 原生 SFT 或 RL 训练**。前两阶段能够复用任务、工具、评分和结果分析流程；进入训练阶段还需要按训练方法准备 token、loss mask、必要的 logprob，以及权重更新链路。

源码基准为 [THUDM/slime 的 `2f2318653f6f794dddd321eff7c9d4b7b174643f`](https://github.com/THUDM/slime/tree/2f2318653f6f794dddd321eff7c9d4b7b174643f)，文件盘点范围为该版本的 657 个 Git 已跟踪文件。下文覆盖全仓结构及各模块关键入口，不表示逐行审计了全部文件。站内已有 Agent 动作讲解使用 `8c17b676cb57af1d17ee4402e91e9209af84b60b`，两者的版本边界应分别保留。

## 项目能力与岗位要求

| 岗位关注点 | 项目中应展示的行为 | 优先借鉴 Slime 的部分 |
| --- | --- | --- |
| Python 异步与并发 | 并发执行任务、限制请求量、取消超时任务、处理背压 | `rollout/`、`utils/async_utils.py`、`data/transport.py` |
| Agent 完整链路 | 模型请求、工具调用、上下文、执行结果和评分能够关联 | `agent/`、多轮示例、`rm_hub/`、`observability/` |
| Kubernetes 工程 | 环境创建、就绪检查、资源限制、失败排查和资源回收 | 在现有沙箱接口外补集群适配，复用上层任务逻辑 |
| 评测或训练经验 | 固定数据集、可比较的评分结果；后续连接 SFT 或 RL | `eval_config.py`、评分器、`train.py`、`backends/` |
| 稳定性与可维护性 | 重试、任务恢复、持久化、清理、契约测试 | `data/`、`cleanup.py`、`tests/` |
| 研发效能工具 | 按任务查看轨迹、错误、耗时和实验差异 | Trace、指标、离线时间线查看器 |

第一期就应完成一条可演示的任务链：提交任务，领取任务，创建执行环境，调用模型与工具，收集产物，评分，查看轨迹，最后释放资源。任务失败和服务重启后的行为也属于这条链。

## 全仓文件地图

```text
slime/                         174 个文件
├── agent/                      13：模型协议适配、Harness、沙箱、轨迹
├── rollout/                    22：生成、评分、评测、异步执行、过滤
├── data/                       10：数据源、队列、传输、归档、恢复
├── observability/              12：Trace、指标、日志、性能分析
├── ray/                         9：分布式调度、服务管理、训练恢复
├── backends/                   70：Megatron 训练、SGLang 推理
├── utils/                      37：配置、HTTP、并发、数据、权重同步等
└── __init__.py                  1

slime_plugins/                  26：模型适配、独立 rollout buffer
examples/                       70：Coding Agent、多 Agent、搜索、工具、蒸馏等
tests/                         140：配置、队列、恢复、Trace、插件契约与训练检查
tools/                          12：Trace 查看、模型转换等工具
scripts/                        68：模型配置、训练与推理启动配方
docker/                         51：镜像构建、依赖与补丁
docs/                           85：架构、扩展接口与使用文档
train.py                           原生训练总入口
其余文件                           README、包配置、CI、仓库开发配置等
```

其中，`backends/` 的实际实现是 Megatron 与 SGLang；`slime_plugins/models/` 主要补充模型结构、attention 和算子，不能将它理解成 Agent 工具插件目录。

## 现在就值得复用的代码

### Agent 执行与环境接口

从 [Sandbox 接口][sandbox]、[BaseHarness.run][harness] 和 [Coding Agent 入口][coding-generate] 看任务如何准备环境、安装 CLI、启动 Agent、收集结果并清理。

`Sandbox` 约定异步创建与释放、命令执行、文件读写，以及用户、环境变量、超时和幂等提示。E2B 是这个接口的一种具体实现。K8s 后端需要实现相同操作语义，并提供示例实际需要的 shell、用户、目录、工具链及网络连通性。

因此，仅让类具有同名方法还不够：命令退出码、超时、取消、文件传输和清理行为需要可验证。当前示例在环境创建和两条 SWE 评分路径中直接构造 E2B 后端；切换时应统一接入沙箱工厂，覆盖运行与评分两侧。

CLI 在沙箱中运行，模型适配服务在 Slime 一侧。采用 K8s 后端时，要同时验证 CLI 能够回连模型入口，服务端能够识别会话。站内可继续阅读 [Manage Sandbox](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/5-manage-sandbox/) 和 [Make API Calls](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/7-make-api-calls/)。

### 模型 API 客户端

[rollout_buffer 的 query_single_turn][api-client] 已经调用 `client.chat.completions.create()`，其 `BaseGenerator` 接收服务地址并补齐 `/v1`。这是现有 API 接入的起点。

该实现仍需适配实际服务：`model="custom"`、`api_key="test"` 写死，使用同步 SDK 与多进程，关闭流式输出，并包含针对原生推理服务的 `abort` 与续写处理。可保留消息和结果组织方式，再补齐可配置的模型与凭据、异步并发、明确的超时、取消、错误分类和重试。

`agent/adapters/openai.py` 与 `anthropic.py` 处理对应协议的请求格式，当前主链路最终调用 SGLang 的原生 `/generate`。这些文件名本身不代表已经具备通用的外部模型客户端。

统一模型接口时，先覆盖任务实际依赖的能力：消息、工具调用、生成内容、结束原因、用量和错误。自部署模型与托管 API 对工具、流式响应和参数的支持可能不同，应通过能力配置和契约测试表达差异。

### 评测配置与评分器

[EvalDatasetConfig][eval-config] 是适合优先复用的配置模块，支持数据集字段映射、采样参数、自定义生成与评分入口、任务超时和结果收集控制。可以保留这些配置语义，将其与训练命令行启动过程分开。

[评分分发器][reward] 支持按样本或全局选择自定义评分函数，也支持远程评分服务。F1、选择题评分等小函数较容易复用；数学和指令遵循评分有额外依赖，需要按任务选择。

评分分发器依赖 Slime 的 `Sample` 和参数对象，批量评分也需要补统一并发预算。对于 Coding Agent，优先展示测试是否通过、产物是否符合要求、失败原因是什么，再根据任务需要加入模型评分。

### Trace 与结果分析

[trace_utils.py][trace] 提供事件、span、父子关联、重试次数和跨边界传递的 trace 数据。它适合串起模型请求、工具执行、沙箱操作与评分，但当前属于自定义轨迹格式，没有现成的 OpenTelemetry 导出链路。

[metric_utils.py][metrics] 可以借鉴统计和 pass@k 计算；pass@k 需要按题目组织多次采样，并满足对应的二元评分假设。

[trace_timeline_viewer.py][viewer] 已有交互式时间线，可以作为执行分析界面的起点。当前输入来自 PyTorch rollout dump；API 项目若保存 JSON 轨迹，需要适配读取与转换层。工具的存在也不意味着 Coding Agent 示例已经自动接好全部 Trace，关键调用处仍要埋点。

## 并发与可靠性代码需要怎样适配

| 模块 | 可复用的机制 | 接入边界 |
| --- | --- | --- |
| [sglang_rollout.py][rollout] | 按样本生成、分组评分、并发收集、评测与取消 | 默认状态先加载 tokenizer，并依赖 SGLang 拓扑；仅替换生成函数不能消除这些依赖 |
| [fully_async_rollout.py][async-rollout] | 持续维护执行中的任务、结果背压、暂停和保存状态 | 绑定原生生成、样本分组与训练消费过程 |
| [sample_hooks.py][hooks] | 样本处理扩展点、任务上下文、同步或异步 hook | 输入输出仍使用 Slime 样本结构 |
| [data_source.py][data-source] | 数据游标、epoch、样本编号、缓冲与恢复 | 默认数据源加载本地 tokenizer，保存逻辑也依赖训练环境 |
| [queue_data_source.py][queue] | 租约、心跳、完成确认、失败回收、过期执行隔离 | 依赖 `straw-queue`、Ray 和 Slime 的数据约定 |
| [data/transport.py][transport] | 持久化数据引用、限制写入积压、取消时等待写入收尾 | 分布式使用需要配置共享存储与所有权管理 |
| [cleanup.py][cleanup] | 共用清理预算、逐项尝试清理、保留原始错误 | 每个清理动作需要自己使用剩余时间，工具不能强制中断任意操作 |

`utils/async_utils.py` 中的 `AsyncPacer` 用于分批唤醒等待者，缓解事件循环压力，不能当作并发上限或 API 限流器。`utils/http_utils.py` 的连接池与请求分发也主要按 SGLang 场景配置；接外部 API 时仍需要鉴权、状态码处理、重试和超时策略。

独立的 [rollout buffer][buffer] 可以借鉴生产者与消费者分离的方式，但它使用进程内数据结构，不具备完整的持久化任务状态、取消和多租户管理。它与 `slime/data/` 中依赖持久化队列的实现，应分别评估。

## 值得横向阅读的示例

| 示例 | 重点借鉴 | 需要替换或保留的边界 |
| --- | --- | --- |
| [coding_agent_rl][coding-generate] | CLI Harness、沙箱准备、工作区与评分 | E2B 构造点、SGLang 模型入口、SWE 任务约定 |
| [multi_agent][multi-agent] | 并行求解、改写、选择与分阶段评分 | 原生生成请求、tokenizer 与训练轨迹 |
| [retool][retool] | 工具调用、观察结果插入、轮数和上下文预算 | 本地子进程执行不能直接承担不可信代码隔离 |
| [search-r1][search] | 搜索服务适配、观察反馈、答案与格式评分 | 搜索工具可独立抽取，生成循环仍需要模型适配 |
| [tau-bench][tau] | 环境交互、状态、动作与结果组织 | 环境依赖、原生生成和 token mask |
| [strands_sglang][strands] | 外部 Agent 框架、工具限制与 hook 接入 | 当前模型适配器和轨迹依赖 SGLang |
| [geo3k_vlm_multi_turn][vlm] | 环境初始化、单步执行、关闭与多轮观察 | 多模态处理器、模型输入和训练张量 |

这些示例说明 Slime 的扩展范围包括工具、搜索、环境和多 Agent。采用其中的交互流程时，应分别确认模型调用、环境执行和训练数据收集的依赖。

## Kubernetes 的职责边界

该源码版本没有仓库内的 Kubernetes controller、Helm chart、CRD、RayCluster 或 RayService 配置，也没有 K8s 沙箱后端。Ray 资源调度和 Docker 镜像不能直接替代这些能力。

项目中的职责可以这样划分：

| 层次 | 负责什么 | Slime 能提供什么 |
| --- | --- | --- |
| Kubernetes 基础设施 | 工作负载、资源限制、网络、存储、服务发现、节点与容器生命周期 | 需要另外选择和配置集群部署方案 |
| 沙箱后端 | 创建与回收执行环境、命令执行、文件传输、就绪与超时 | `Sandbox` 接口及 E2B 实现可作为适配参考 |
| Agent 任务服务 | 排队、并发、模型与工具调用、状态、评分与结果 | 借鉴 Agent、rollout、数据与评测模块 |
| 可观测与恢复 | 调用关联、错误定位、产物保存、重试与任务恢复 | 借鉴 Trace、指标、队列与清理机制 |

为了减少重复开发，集群和沙箱的通用基础能力宜复用已有实现；项目自己重点实现适配层、任务语义和业务编排。具体开源后端仍需按命令与文件操作、隔离、启动延迟、并发容量和运维成本验证，Slime 源码本身不能给出后端选型结论。

需要展示大规模启动能力时，可测量从排队到环境就绪的耗时分布、同时创建数量、失败率、资源回收时间，以及达到资源上限时的背压行为。K8s 的使用本身不能证明启动性能。

## 自部署模型与训练阶段

### 接入自部署推理

通过统一的模型客户端调用 SGLang 或 vLLM，可以延续 API 阶段的 Agent、工具和评测逻辑。兼容接口不保证工具调用、流式输出和参数行为完全相同，仍需要实际服务的契约测试。

Slime 原生服务管理可以从 [external.py][external]、[deployment.py][deployment] 和 `sglang_config.py` 阅读，涉及外部 SGLang 引擎、多模型配置、路由和部署拓扑。

这里的 external engine 还需要服务信息、生成与相关控制接口。连接原生训练后，还涉及权重版本、暂停和权重更新；普通 Chat Completions API 不足以覆盖这些要求。外部服务的进程生命周期与故障重建，也需要外部部署系统接管。

### 连接原生训练

[train.py][train] 展示完整循环：创建训练模型，发布权重，生成 rollout，训练，保存 checkpoint，再次更新权重并评测。当前版本使用 Megatron 训练与 SGLang 推理，没有内置的完整 vLLM 后端或 FSDP 训练实现。

重点文件包括：

- `backends/megatron_utils/actor.py`、`model.py`、`loss.py`：训练执行、优化器与损失。
- `checkpoint.py`、`hf_checkpoint_saver.py`：恢复、保存与 HF 权重导出。
- `update_weight/`：显存、分布式通信、完整磁盘和增量磁盘权重更新。
- `slime_plugins/models/`、`scripts/models/`：具体模型结构与启动配置。
- `examples/on_policy_distillation/`：教师模型给定 token 序列的 logprob 与蒸馏。
- `examples/train_infer_mismatch_helper/`：训练与推理 logprob 差异及修正。

普通 API 返回的文本与任务评分，可以用于评测和数据积累。对于 SFT，审核后的完整消息轨迹可以按目标模型的模板重新编码并构造 loss mask，参见 `slime/rollout/sft_rollout.py`。进入原生训练时，需要按所选方法满足 [Sample][sample] 的数据约定；对于需要行为策略 logprob 的 RL 或离策略校正流程，最终文本的重新编码无法补齐生成时未保存的概率信息，也不能自动还原工具调用和轨迹切分。

## 阅读顺序与阶段交付

先阅读 `train.py` 和 `Sample`，弄清一份任务数据如何流过生成、评分、消费与更新。随后按项目阶段深入，避免阅读顺序完全由目录名称决定。

| 阶段 | 优先阅读 | 可演示的交付结果 |
| --- | --- | --- |
| API 执行与评测 | `agent/`、API 客户端示例、`eval_config.py`、`rm_hub/`、Trace、数据与清理 | K8s 环境中的完整任务链，含评分、轨迹、失败回收与结果保存 |
| 自部署模型 | `sglang_utils/`、Ray 服务管理、健康检查、异步 rollout | 同一批任务切换到自部署模型，比较正确率、延迟与吞吐 |
| 原生训练 | Megatron actor、模型、损失、checkpoint、权重同步、SFT/RL 示例 | 从任务轨迹到训练，再到模型更新和固定数据集复评 |

进入 Slime 的原生运行链后，优先利用已有[自定义接口][customization]：单样本生成使用 `--custom-generate-function-path`，评分使用 `--custom-rm-path`，数据源使用 `--data-source-path`。只有默认编排确实不满足需求时，再替换整个 rollout。API 阶段如果使用独立轻量执行器，也应保持这些扩展边界清晰。

验证方式可以从 `tests/test_eval_config.py`、`tests/observability/test_trace_utils.py`、队列与恢复测试，以及 `tests/plugin_contracts/` 借鉴。重点验证不同模型和沙箱后端遵守同一约定，以及超时、重复执行、服务重启和部分失败时的任务行为。

[返回 Slime 目录](/projects/slime/)

[sandbox]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L28
[harness]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L81
[coding-generate]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L182
[api-client]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime_plugins/rollout_buffer/generator/base_generator.py#L37
[eval-config]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/utils/eval_config.py#L135
[reward]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/rm_hub/__init__.py#L55
[trace]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/observability/trace_utils.py#L326
[metrics]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/observability/metric_utils.py#L14
[viewer]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tools/trace_timeline_viewer.py#L2359
[rollout]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/sglang_rollout.py#L289
[async-rollout]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/fully_async_rollout.py#L78
[hooks]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/sample_hooks.py#L37
[data-source]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/data/data_source.py#L16
[queue]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/data/queue_data_source.py#L49
[transport]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/data/transport.py#L370
[cleanup]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/utils/cleanup.py#L9
[buffer]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime_plugins/rollout_buffer/buffer.py#L216
[multi-agent]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/multi_agent/agent_system.py#L198
[retool]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/retool/generate_with_retool.py#L215
[search]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/search-r1/generate_with_search.py#L124
[tau]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/tau-bench/trainable_agents.py#L177
[strands]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/strands_sglang/generate_with_strands.py#L41
[vlm]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/geo3k_vlm_multi_turn/rollout.py#L315
[external]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/backends/sglang_utils/external.py#L195
[deployment]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/backends/sglang_utils/deployment.py#L79
[train]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/train.py#L13
[sample]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/utils/types.py#L107
[customization]: https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docs/zh/get_started/customization.md
