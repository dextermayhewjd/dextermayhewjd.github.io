# Slime 阅读与目标需求对照

[阅读目录](README.md) · [完整路线](repo-reading-route.md) · [源码入口清单](source-map.json)

目标岗位：[腾讯 · 混元 Agent 强化学习框架工程师（深圳/北京/上海）](https://careers.tencent.com/jobdesc.html?postId=2061654749727600640)，岗位 ID `2061654749727600640`。当前学习目标以用户在 2026-10-28 重新提供的[完整 JD](job-evidence/2026-10-28-user-provided-jd.md)为准。历史来源保留：2026-10-10 核对官网时标注更新日期为 2026-09-30，用户在 2026-10-19 提供的文本标注更新于 2026-10-12。不把用户提供的文本冒称当天重新核实的招聘官网状态，也不因官网后续变化自动更换已确认目标。

阅读目标：先能说明每个模块做什么、输入输出与扩展边界在哪里，再能把一个新策略、评测或运行问题映射到源码、验证和部署动作。这份对照供本目录阅读使用，公开网页保持技术路线表述。

Python 原生异步与并发的专项学习范围统一维护在 [学习规划](../../python-async-reference/learning-plan.md) 第 4.3–4.5 节：只展开原生机制，不承担完整岗位或通用工程化课程。三库 API 频次用于选例与检查遗漏；阶段性调用覆盖比例不作为岗位能力验收。既有源码阅读顺序仍以本目录的唯一路线为准。

<a id="jd-settled-plan-20261028"></a>

## 2026-10-28：现行阅读方向与投入边界

用户已要求敲定后续计划，统一入口为[现行阅读计划与约定](../../00-repo-reading/repositories/slime/slime后续阅读顺序/current-goal-slime-reading-order.md#reading-agreement-20261028)。复用已读 Coding Agent、生成/评分、worker loop 与结果交付，按“生成接口接入与验证 → Sample 到训练数据 → 生成训练闭环 → 关键失败处理”推进。Step 015 负责生成接口与验证；具体阅读和运行状态只由[唯一路线](repo-reading-route.md#当前接续)维护。

生成接入重点对应职责 2、3 和工程验证；数据与训练交接对应职责 5 及要求 4；失败处理对应职责 4 和并发、稳定性要求。评估配置、产物与复跑结合已有实现做验证；Kubernetes 继续作为明确的独立实践要求。Trace 按用户要求保持暂缓，不从能力范围中删除。QueueReader/straw、底层存储/恢复、完整训练算法内部与其他框架不列为当前必读，由具体问题触发。

已有阅读、独立实现和实际运行分别记录。下方是此前的复核与修正过程，保留其证据和当时判断，不作为另一套当前计划。

<a id="jd-full-role-review-20261028"></a>

## 2026-10-28：依据用户重新提供的完整岗位职责复核

本轮依据为[用户贴出的完整 JD](job-evidence/2026-10-28-user-provided-jd.md)，包含五条职责、六条要求和四条加分项；不冒称当天官网核验。此前“两块重点与一块概览”只足以表达近期入口，不能单独作为完整岗位准备清单。

[最新范围与检验目标](../../00-repo-reading/repositories/slime/slime后续阅读顺序/current-goal-slime-reading-order.md#full-jd-review-20261028)明确四部分：复用已读 Agent 主链来解释可替换组件的边界；完成一个策略/评估接入并能复跑比较；验证并发、资源与失败时的行为；理解 Sample 关键字段及生成、训练、权重更新和评估的交接。训练部分从“只扫调用顺序”修正为“说明关键数据的用途与对齐”，仍不要求通读算法、优化器或并行通信内部。实验复现不能只用队列恢复代表。

Trace 继续暂缓、待后续用真实诊断场景补齐；Kubernetes 是独立实践要求。加分项按实际成果呈现，不增加整仓或多语言必读清单。用户随后质疑队列优先级是否受粘贴内容影响；[本轮纠正](../../00-repo-reading/repositories/slime/slime后续阅读顺序/current-goal-slime-reading-order.md#step015-jd-priority-correction)将 QueueReader 保留为可选案例，优先候选改为生成扩展的接入与验证，直接对应职责 2、3。尚未确认或开启新 step；唯一状态仍见[当前接续](repo-reading-route.md#当前接续)。本轮为静态源码和范围核对，无新增运行或掌握判断。以下保留此前建议及其历史依据。

<a id="jd-straw-queue-review-20261028"></a>

2026-10-28 较早的剩余范围建议（已由上方完整 JD 复核补充）：用户再次询问还需阅读哪些代码。当时建议在已读 Agent、生成/评分和正常结果交付之上，集中于“队列生命周期与故障处理”“接口扩展及契约测试”两块重点，另对 BatchBuilder 与 train 主循环做交接层概览。[当时的具体文件、函数与停止位置](../../00-repo-reading/repositories/slime/slime后续阅读顺序/current-goal-slime-reading-order.md#remaining-code-scope-20261028)保留作快照；不将目录或建议当作新 step 已获确认。

## 2026-10-28：用户提出 straw 队列调度的选题评估

用户要求暂缓整个 Trace Step 014，并提供 PR #2426 的队列调度文档差异，询问其与岗位的对应。[具体评估及源码入口](../../00-repo-reading/repositories/slime/slime后续阅读顺序/straw-queue-jd-assessment-2026-10-28.md)已保存。

建议将下一处候选限定为 Slime Python 层“领取 group → 归还 partial → 另一 worker 续跑”，直接对应 JD 的并发编程、任务执行、模块化与稳定性治理。以一个跨 reader 续跑测试及一个丢回复场景核对行为；staleness 与训练背景按需补充，WAL、pack/GC 和完整训练恢复的内部实现暂不列入首轮。Kubernetes 仍需独立的部署与排障实践，Ray/straw 阅读不能替代它。

本次是用户主动提出方向后的评估，不将完整持久队列系统升级为所有候选人都必须深读的要求。用户尚未确认新的具体 step；暂停与后续确认只由[唯一路线](repo-reading-route.md#当前接续)维护。以下 2026-10-26 的岗位范围约束继续保留。

<a id="jd-primary-focus-20261026"></a>

## 2026-10-26：按用户重贴的任职要求收窄主要内容

用户指出上一轮推荐明显多于 JD 的主要要求，要求重新抓重点。上一版把“沿 Slime 完成训练与分布式实现闭环”提升成了近期必读，依据不足。本节修正投入顺序；下方旧方案保留为历史候选，不继续作为必读清单。

以用户本轮提供的六条任职要求和四条加分项为依据：Python/asyncio、Agent 核心链路、模块化与测试/日志/稳定性是主要源码学习方向；Kubernetes/容器及集群经验是独立的主要实践方向。第 4 条只要求了解所列训练或自动化评估方向中的至少一类，不能推出必须深读 advantage/loss、权重同步实现或所有分布式恢复细节。既有职责中的训练视角仍保留全景认识，深度按实际任务决定。

<a id="jd-minimum-sufficient-scope-20261026"></a>

### 范围复核：三项新增阅读放回完整岗位范围

用户进一步要求“不需要变多，但也不能变少”。三项是近期新增的深入阅读，不代表整个岗位只需读这三个局部。稳定范围为：复用已读 Agent 主链 + 三项新增深入 + 训练/评估的背景认识 + Kubernetes 实践。各项以可解释和可验证的行为判断是否充分，不按函数数量或阅读完成率推断胜任。

| 必须保留的范围 | 准备深度与检验方式 | 阅读处理 |
| --- | --- | --- |
| Agent 端到端链路 | 能从任务、上下文、模型/工具调用说到结果评估，说明 Harness、Adapter、外部 CLI 与环境的职责边界；知道替换一个组件会影响哪些输入输出 | 复用已读记录，暴露缺口才回查，不假定已读等于掌握 |
| Python 并发与任务治理 | 能解释限流、任务登记、完成结果、错误传播、取消与资源归还；用一个受控慢/失败任务检查实际行为 | 近期第 1 项；正常交付之后补关键失败场景，内部线程/队列细节按需 |
| 可维护的接口、Trace 与验证 | 能把一个小需求落为生成/评分接口改动，写有针对性的测试；从 Trace/日志定位一个问题并说明修正依据 | 近期第 2、3 项；阅读与动手一起完成，不以读懂测试文件代替编程能力 |
| 自动化评估及训练背景 | 能解释任务输入、评估依据、失败计入方式与结果复现；能概括轨迹/奖励如何交给训练、更新怎样影响后续生成 | 评估复用已读场景。训练只核对 BatchBuilder.convert 的输入输出与 train.py 主干，不逐字段展开，不深入 loss/权重同步实现 |
| 容器与 Kubernetes | 能实际部署同一最小服务/worker，并定位一次资源、服务连接或重启问题，保留操作与恢复证据 | 独立实践；理解服务/进程/Actor/Pod 的边界，完整 Ray 内部实现不作为前置 |

同一个小项目可以同时承载接口修改、测试、慢/失败任务、Trace 与容器部署，并留下需求、取舍、验证和复盘来支持第 6 条要求。加分项用于呈现已有 AI 编程工具/框架经验，跨语言阅读由具体问题触发，不另加必修范围。上述是覆盖主要要求的准备边界，不能保证仅凭读完材料就满足实际招聘标准。

### 近期只保留三项源码重点

| 建议顺序 | 入口 | 对应要求与停止位置 |
| --- | --- | --- |
| 1. 接完当前并发任务的结果交付 | `slime/rollout/fully_async_rollout.py`：`AsyncRolloutWorker._make_done_cb`、`get_completed_groups`；必要时短接 `_generate_rollout_async` 的收集段 | 对应要求 1、2、5。先跟踪正常结果从 Task 到队列再被取走；再选一个异常/取消场景理解影响与收尾，不扩成完整重试和队列系统。 |
| 2. 看任务怎样被追踪 | `slime/observability/trace_utils.py`：`trace_span`，按需回查 `bind_trace`；参考 `tests/observability/test_trace_utils.py:104` | 对应要求 2、5。用同一任务看阶段关联、耗时及异常结束的记录；能定位一个慢或取消案例即停，不读全部追踪设施。 |
| 3. 看扩展怎样被验证 | `tests/plugin_contracts/test_plugin_generate_contracts.py` 与 `test_plugin_path_loading_contracts.py`，回接已读的生成/评分接口 | 对应要求 1、5、6及框架经验加分项。选一个已有接口，说明输入输出和替换边界，再围绕一个小接入验证结果及失败行为；不重读所有奖励模型。 |

Coding Agent 的模型调用、工具、上下文、任务执行与评估已经有实际阅读记录，是岗位主线的一部分。按问题复用这些记录，补缺口即可；不把已读自动当作已掌握，也不重新开整套阅读。

### 与这三项并行的实践及选读边界

- Kubernetes/容器仍是正式要求，不能降成加分项。沿用已有 kubectl/简单部署基础，选一个小服务或 worker 完成部署和一次故障定位；在实际问题需要时再查 Slime 的资源/服务代码，避免先读完整 Ray 调度和 GPU 部署。
- 第 4 条优先围绕已读 Coding Agent 的自动化评估说明输入任务、执行、评估标准与结果；训练部分保留上表的交接层背景认识，不作为进入 Trace/测试的前置。
- `BatchBuilder` 深层转换、advantage/loss、权重同步实现、DistributedRollout/队列持久化恢复、TP/PP/EP 改为问题驱动选读。示例默认 straw 与本地 worker 不同仍是正确的边界事实，但不能因此把默认实现全量升级为岗位必读。
- AI 编程工具、跨语言和研发效能工具按已有项目经验说明及具体任务补充，不据加分项新增一整套课程。问题分析、协作与 owner 意识通过上述小任务的需求、取舍、验证和复盘呈现。

本节保存根据用户纠正提出的范围建议，不另维护实时步骤状态；实际已读位置、范围确认与实践证据只见[唯一进度](repo-reading-route.md#当前接续)。

<a id="jd-after-step012-20261026"></a>

## 2026-10-26：Step 012 之后的扩展方案（历史，已收窄）

> 该版投入范围已由[主要内容修正](#jd-primary-focus-20261026)收窄；下列训练内部和分布式实现作为候选参考，不是当前必读顺序。

用户再次要求核对腾讯混元岗位，并据此判断剩余的 Slime 阅读范围。本次重新获取[腾讯官方职位接口](https://careers.tencent.com/tencentcareer/api/post/ByPostId?postId=2061654749727600640&language=zh-cn)，HTTP/API 均为 200，职位仍为“混元Agent强化学习框架工程师（深圳/北京/上海）”，更新日期为 2026年10月20日。响应 SHA256 仍为 `ac5b276dc06fe3d204ffd23615691878761427d1d558aa6b8affde084c184c39`，与[当日原始证据](job-evidence/2026-10-26-tencent-2061654749727600640.raw.json)一致。源码 checkout 干净，本地 HEAD 与本次查询的官方 main 均为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。

JD 的职责 2、3、4 明确涉及复用组件、策略/评估接口与验证、并发资源及行为一致性；职责 5 要求结合训练视角，要求 3 单独提出 Kubernetes/容器集群经验。因此建议继续补齐数据与控制交接，再围绕一次具体扩展和故障深入。以下是助手的岗位映射建议，不是腾讯指定的源码书单，也不将源码核对记作用户已经阅读。

### 主线：先完成结果交接，再接通训练

| 顺序 | 固定版本源码入口 | 为什么读、读到哪里停 |
| --- | --- | --- |
| 1. 完成结果交付 | [AsyncRolloutWorker._make_done_cb:246](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L246) → [get_completed_groups:147](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L147) → [_generate_rollout_async:278](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L278) | 接上已读的 Task 注册点，跟踪一组正常结果从 Task 到队列再被限量取走。先停在正常交付；之后单独补一次异常或中止，不同时展开所有重试、线程和数据源实现。 |
| 2. 训练数据契约 | [BatchBuilder.convert:256](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/batch_builder.py#L256)，必要时回查 [_post_process_rewards:207](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/batch_builder.py#L207)，接回 [RolloutManager._generate:335](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L335) | 用一个样本看 tokens、response_length、reward、rollout_log_probs、loss_mask 怎样成为训练字段；再用同一 rollout 的两个片段理解分组身份与掩码。先看数据契约，存储与 DP 分发内部保留黑箱。奖励后处理/归一化不等同于再次调用奖励模型，避免与已读 group_rm 混淆。 |
| 3. 训练与生成闭环 | [train.py::train:13](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/train.py#L13)，按需进入 [MegatronTrainRayActor.train_actor:450](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/backends/megatron_utils/actor.py#L450) 与 [update_weights:629](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/backends/megatron_utils/actor.py#L629) | 第一轮接通取批次、训练、training_completed、暂停接纳、同步权重、恢复后续生成。下一轮只追一个当前配置的 advantage/loss 分支，回答哪些 token 参与优化、采样 logprob 怎样被使用；不读全后端。运行时完成与持久 checkpoint 提交是不同边界，恢复专题再细看。 |
| 4. 默认分布式路径与结果一致性 | [DistributedRollout.__init__:504](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_distributed.py#L504)、[RolloutScheduler._run:98](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_distributed.py#L98)、[_GenerationActor._produce:330](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_distributed.py#L330)；再按任务交接进入 [QueueReader.get_samples:1050](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/queue_data_source.py#L1050) 与 [publish_rollout_async:335](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/transport.py#L335) | 先画清 Ray Actor 之间与 Actor 内 asyncio 的边界，再沿一个 group 跟踪领取、生成、提交、消费；随后选 worker 退出或重试案例，检查身份与结果如何保留。队列完整存储实现暂缓。此处补读是因为示例默认 straw 走这条路径，并非 JD 点名要求 Ray。 |

第 4 项是第一轮闭环之后明确需要补的范围，不再只含糊标为“分布式按需”。但不把它提前变成第 1 项的前置。当前 Step 012 的本地 worker 模型仍然有用，不能据此声称已覆盖示例默认路径。以上各项可以按一个问题拆成多个 step；表中的序号不预占步骤或主题编号。

训练侧的定点入口是 [compute_advantages_and_returns:725](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/backends/megatron_utils/loss.py#L725) 与 [policy_loss_function:1128](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/backends/megatron_utils/loss.py#L1128)。它们在第 3 项完成控制骨架后另作局部阅读，不要求从 train 一次向下钻到底。当前先不展开各算法、TP/PP/EP、通信内核和所有权重传输实现。

### 配套：跟一个扩展或故障一起读

| 岗位能力 | 源码与验证入口 | 有限目标 |
| --- | --- | --- |
| 策略/评估接口与验证（职责 3；要求 5） | 已读 generate_and_rm、batched_async_rm 和 sample hooks；[test_plugin_generate_contracts.py](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tests/plugin_contracts/test_plugin_generate_contracts.py)、[test_plugin_path_loading_contracts.py:333](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tests/plugin_contracts/test_plugin_path_loading_contracts.py#L333) | 选一个自定义评分或生成插件，用真实调用链检查签名、结果类型、数量/顺序、已有 reward 及错误行为。已有测试是起点，新增验证围绕实际改动；不以运行旧测试冒充完成新接入。 |
| Trace 与故障定位（职责 1、2、4） | [bind_trace:238](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L238)、[trace_span:345](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L345)，跨进程时再看 export_trace/import_trace；[test_trace_closes_cancelled_spans_and_jsonl_roundtrips:104](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tests/observability/test_trace_utils.py#L104) | 用一次慢或取消任务连接 sample、阶段 span、错误与导出的记录。配合第 1/4 项展开；需要恢复时定点回查 test_fully_async_rollout.py、test_straw_fully_async_recovery.py、test_training_recovery.py，不通读全部追踪设施。 |
| 资源与部署（职责 4；要求 3） | [ServingCluster:35](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/serving.py#L35)、[create_placement_groups:123](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/placement_group.py#L123)、[start_rollout_servers 所在模块](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/backends/sglang_utils/deployment.py)、[docker/Dockerfile](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/docker/Dockerfile) | 先辨清谁拥有模型服务、队列、资源与清理责任，再做一个容器/Kubernetes 部署及服务连接或资源故障案例。Ray 的资源调度阅读不能代替 JD 要求的集群实际经历。 |

### 已读复用、黑箱与实践边界

Coding Agent 单任务、Harness/Adapter/轨迹转换、generate_and_rm、batched_async_rm、generate_and_rm_group 的既有记录按当前问题调用，不整套重读；group_rm 和所有内置 rm_type 不再作为继续主线的前置。某个接口已讲解与是否亲手完成接入分别记录。

沿用无本地 GPU 的条件：契约测试、受控慢/失败任务和最小容器服务可先用 CPU/替身完成，并明确其覆盖边界；完整模型训练、权重同步与 GPU 集群行为不能由此声称已验证。当前只是源码核对与阅读建议，没有运行这些新增案例。

近期首选仍是第 1 项的正常完成交付；唯一进度与范围确认见[当前接续](repo-reading-route.md#当前接续)。本次不创建 Step 013，不预写函数卡或已掌握状态。

<a id="jd-reading-decision-20261026"></a>

## 2026-10-26：重新核对 JD 后的具体阅读决策

用户指出 group_rm 两层评分条件已经讨论，要求具体按混元岗位决定接下来怎么读。本轮重新读取腾讯官方公开接口，HTTP/API 均为 200；职位仍为“混元Agent强化学习框架工程师（深圳/北京/上海）”，岗位更新日期为 2026年10月20日，要求一年以上工作经验。原始响应哈希与 2026-10-25 完全一致。[本轮字段及原文证据](job-evidence/2026-10-26-tencent-2061654749727600640.json)，[原始响应](job-evidence/2026-10-26-tencent-2061654749727600640.raw.json)，[官方职位入口](https://careers.tencent.com/jobdesc.html?postId=2061654749727600640)。

### 从职责推导投入重点

| JD 中的明确方向 | 对阅读与实践的含义 |
| --- | --- |
| 职责 2、3：统一组件，支持策略和评估接入，维护接口及验证 | 能说明扩展入口、Sample/reward 契约，并用一个实际接入和检查证明；不需要按目录通读所有评分算法 |
| 职责 4，要求 1、5：并发、资源、链路一致性、性能与稳定性 | 当前优先读持续调度、结果收集、背压、失败与取消；通过小实验验证行为 |
| 职责 1、2，要求 2、5：Trace、自动评估、实验复现 | 将追踪、日志与版本/配置保存用于前述实验；围绕一次慢或失败任务看证据 |
| 职责 5，要求 4：训练视角与工程化 | 继续连接 Sample、训练批次、训练调用与权重同步，第一轮不展开全部训练后端 |
| 要求 3：容器/Kubernetes 集群开发、部署或排障经历 | 源码阅读不能替代操作经历，需单独完成部署与一次故障恢复案例 |

这些是基于 JD 的阅读判断，不是对腾讯面试题目或内部实现的保证。加分项中的 AI 编程工具、Agent/Coding CLI、研发效能与跨语言能力保留原文依据，不将其全部升级为本轮必读课程。

### 对评分接入的明确收束

group_rm 的两层归属已经多次讲解，batched_async_rm 的自定义/默认分派也已有记录，后续直接复用这些卡片。未知可以继续保留，但不能因为“尚未亲手接入并验证”就把整段源码阅读重新退回评分入口。

修正上一条“先补评分接入例子再读 _loop”的推荐：**下一源码入口仍为 _loop；自定义评分与契约测试安排为配套实践。** async_rm 的优先级、单条/批量参数和具体评分器只在实践遇到缺口时定点回查，不作为进入调度主线的统一门槛。学习者的“大概理解”不被改记为全部机制掌握。

### 接下来的有限源码顺序

| 次序 | 源码入口 | 本轮要看清什么 | 停止位置 |
| --- | --- | --- | --- |
| 1 | [AsyncRolloutWorker._loop:178](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L178) | 怎样持续取组、限制在途组数量，并根据完成结果积压暂停接纳 | 能解释一次补任务和一次回收；线程启动与完整取消留后续 |
| 2 | [_make_done_cb:246](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L246) → [get_completed_groups:147](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L147) | 成功结果怎样排队，失败/中止怎样影响后续，消费后怎样腾出容量 | 跟踪一组成功结果，再补一种失败或取消情形 |
| 3 | [BatchBuilder.convert:256](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/batch_builder.py#L256)，接回 [RolloutManager._generate:335](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L335) | reward、tokens、loss_mask 等怎样被整理并交付训练侧 | 追踪一个样本的字段与形状，不铺开全部自定义转换 |
| 4 | [train.py::train:13](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/train.py#L13) | 取得 rollout 数据、调用训练、通知完成、同步权重与后续生成怎样相接 | 第一轮能串起闭环；优化器、Megatron 通信等按问题再展开 |

本轮开启 Step 012 时进一步核对实现选择：Coding Agent 示例脚本默认 ROLLOUT_DATA_TRANSPORT=straw，_get_worker 对带 reader_config 的数据源选择 DistributedRollout。本步按已确认入口先读本地 AsyncRolloutWorker._loop 作为持续调度的基础；上述顺序不表示该函数是默认 straw 配置的执行体。分布式对应关系后续按实际部署范围回查，见 [Step 012 的分支边界](../../00-repo-reading/repositories/slime/topics/02-rollout-reward/steps/step-012-async-rollout-worker-loop/01-scope.md)。

### 与主线配套的实际证据

- 在前两项阅读期间或收束后，选一个小的策略/评分扩展，验证可配置加载、单条或批量接口、结果数量与顺序、已有 reward 的处理。已有参考函数和 plugin_contracts 测试可作起点；当前没有完成这项实践。
- 用同一个任务制造一次慢、失败或取消，检查活跃任务、结果完整性和名额回收，并读相关 Trace。保存输入、配置、提交、运行命令和结果；没有测量时不声称吞吐提升。
- 在可用 Kubernetes 环境部署同一个最小 worker/服务，验证一次资源或服务连接问题及恢复。可先使用 CPU 任务或受控服务替身，和真实 GPU 训练证据区分。

不再因一次追问把“已读接口”“当前必读源码”“待做实践”混成新的长前置链。当前进度与是否开始下一步仍由[唯一路线](repo-reading-route.md#当前接续)维护；本段是岗位评估与建议，未自动开启后续步骤。

<a id="next-month-job-plan-20261025"></a>

## 2026-10-25：一个月内投递的岗位复核与接续建议

本轮再次从腾讯官方招聘接口取得同一岗位，返回 `Code=200`，标题为“混元Agent强化学习框架工程师（深圳/北京/上海）”，更新日期为 **2026年10月20日**，工作经验字段为“**一年以上工作经验**”。依据见[岗位页面](https://careers.tencent.com/jobdesc.html?postId=2061654749727600640)与[本轮取证元数据及要点](job-evidence/2026-10-25-tencent-2061654749727600640.json)。该记录证明本轮取得了职位信息，不额外推断招聘截止时间。

**用户本轮明确的条件**：计划一个月内投递或面试；用过 kubectl、部署过简单服务。继续沿用此前“本地无 GPU、以源码理解和可行的验证为主”的条件。以下是建议方案，尚未因此开启新步骤或实施项目。

### 岗位要求怎样落实到下一阶段

| 官方要求归纳 | 当前已有基础 | 接下来最需要补的证据 |
| --- | --- | --- |
| 职责 2、3：统一组件，支持策略与评测接入 | 已沿单题主线读过 Harness、Adapter、Sandbox、评分和 Sample 导出 | 从框架调用者看清插件契约，完成一个可配置的策略或评测接入及契约测试 |
| 要求 1、5，职责 4：Python 异步、并发、性能与稳定性 | 有 Python/asyncio 学习基础，读过局部等待、取消和清理 | 对同一小任务验证并发上限、超时、取消、失败状态和资源释放，给出测试与测量结果 |
| 要求 3：容器、Kubernetes 与集群实践 | 用户报告能用 kubectl，部署过简单服务 | 将任务 worker 与服务接口部署起来，亲手复现并定位一类资源或网络/重启故障，保存恢复过程 |
| 职责 1、5，要求 4：实验复现与训练视角 | 已读过 reward、token、logprob、mask 的生产端，并有训练基础概念 | 看清 Sample 到训练批次、训练调用与权重更新的交接；保存任务配置、版本、输入输出和复现方式 |
| 要求 6：问题分析、协作和 owner 意识 | 当前记录包含问题追踪和源码解释 | 用一项实际变更说明需求、边界、取舍、实现、验证和遗留风险，形成可展示的技术记录 |

- Kubernetes 与集群实践列在正式要求中；AI 编程工具、相关框架经验、研发效能工具和跨语言维护列在加分项中。
- 训练要求是了解所列流程中的至少一类，不能据此推出本月必须通读所有训练范式或 Megatron 底层；也不能据此保证面试不会问某个具体方向。
- 岗位对齐按“要求—代码能力—实际证据”判断，不使用函数数量或没有分母的“覆盖 60%–70%”估算。

### 建议围绕同一条接入任务推进四周

| 阶段 | 重点 | 最小产出 |
| --- | --- | --- |
| 第 1 周：接入与数据契约 | 从 `generate_and_rm` 接回已经读过的 Coding Agent，理解调用、返回的 Sample/list、奖励归属和失败结果；增加一个范围小的策略或评测扩展 | 一份接口说明；可配置的扩展；成功/失败及奖励不重复计算的测试 |
| 第 2 周：批量运行与可观测性 | 复用该任务，验证并发、超时、取消和资源清理；用已有 Trace 记录定位失败 | 可重复的故障用例；并发上限与结果完整性检查；一份耗时或吞吐测量 |
| 第 3 周：Kubernetes 实践 | 将同一个最小 worker 与服务接口部署到可用集群；无 GPU 时使用 CPU 任务与可控模型服务替身 | 部署配置；一类 Pod/资源/服务连接故障的排查、恢复与产物保存记录 |
| 第 4 周：训练交接与整理 | 短读 `BatchBuilder.convert`、`train.py` 的训练调用和权重更新；整理前面变更与故障证据 | 数据流图；能解释 reward/logprob/mask 如何被消费；可复现 README 和项目讲述材料 |

每阶段围绕同一个小任务递进，避免同时新开多个框架项目。普通模型 API 只能用于它实际支持的验证；SGLang 的 token/logprob 合同、参数训练和权重同步仍分别确认。替身验证、本地 Kubernetes 实践和真实 GPU 训练分别记录，不混为同一种运行证据。

### 推荐的下一处入口

**主入口：[slime/rollout/sglang_rollout.py::generate_and_rm，338–380 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L338-L380)。** 它直接承接已经读过的 `examples.coding_agent_rl.generate.generate`，并能回答岗位最关心的一组接入问题：

1. 自定义生成函数怎样被选中、装载和调用？
2. 返回 Sample 或 Sample 列表时，框架怎样接收；已有 reward 时谁还负责评分？
3. 失败状态和结果如何传出，怎样用测试确认接口接对？

将 `_generate:337–413` 的状态、失败返回和最终清理作为上述契约的必要回查收尾，不为完成函数清单继续无限下钻。配套从现有 [test_plugin_generate_contracts.py](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tests/plugin_contracts/test_plugin_generate_contracts.py) 与 [test_plugin_path_loading_contracts.py](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tests/plugin_contracts/test_plugin_path_loading_contracts.py) 入手；本轮只核对它们存在，尚未运行。

当前示例脚本使用 fully-async 入口；`fully_async_rollout` 复用 `generate_and_rm_group`。因此先看共同的 `generate_and_rm` 有直接衔接，之后再选择与真实运行方式对应的批量调度路径。

**Dressage 的位置**：保留为完成接口理解后的定点对照，围绕环境接口、阶段钩子与 reward registry 解释抽象取舍。当前不把整仓再读一轮放在最前面；遇到具体扩展需求时查它更容易形成可验证的设计结论。

实际下一步范围仍需在接续时确认；当前学习位置只以[唯一路线](repo-reading-route.md#当前接续)为准。

<a id="reading-order-jd-audit-20261025"></a>

### 对“Slime 后续阅读顺序”README 的明确评估

核对对象是 [Slime 后续阅读顺序](../../00-repo-reading/repositories/slime/slime后续阅读顺序/README.md)的四项阅读路线、测试和 Kubernetes 部分。结论：**作为源码学习路线，四个选题都直接对应 JD，第一入口也合理；作为一个月的完整岗位准备方案，目前的运行模式说明和实践完成标准还需要补齐。**

| README 项目 | 对应 JD | 评估与需要补准的边界 |
| --- | --- | --- |
| 策略与评测接入 | 职责 2、3；要求 5、6 | 直接对齐。`generate_and_rm` 与 RM 入口能说明扩展契约及评分责任，但读懂函数不等于做过接入；应以一个小扩展和契约验证收束 |
| 批量任务与并发控制 | 职责 4；要求 1、5 | 直接对齐。应标明所读调度模式；当前 coding 示例的 fully-async 关键路径也要覆盖 |
| Trace 与故障定位 | 职责 1、2、4；要求 2、5 | 直接对齐。基本 Trace 与日志应贯穿前两项；独立深入时应以分析一个失败或慢任务为目标，而不只读两个装饰/上下文函数 |
| 训练数据交接 | 职责 5；要求 4 | 直接对齐，当前深度合理。训练全景可先短看，详细转换放后面；需要接到实际消费端，不能把 `BatchBuilder.convert` 当成优化器训练本身 |
| 配套契约测试 | 职责 3；要求 5 | 选得合理，源码确有 GPU 数为 0 的替身测试。至少实际运行相关测试并验证自己的扩展，不把“阅读断言”当作工程产物 |
| Kubernetes 实践 | 要求 3 | README 已经列出，不能说遗漏。但缺少明确环境、故障场景及交付标准，尚不足以回应集群实践要求 |

**第 2 项的源码依据**：当前 [run_qwen38_27b_fully_async.sh:165–167](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/run_qwen38_27b_fully_async.sh#L165-L167) 配置 `fully_async_rollout.generate_rollout_fully_async` 和 Coding Agent 的自定义 generate。其后台 [AsyncRolloutWorker._loop:178–243](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L178-L243) 调用共同的 `generate_and_rm_group`，并有完成队列与接纳控制。README 列出的 `sglang_rollout.generate_rollout_async` 可作为基础批处理调度阅读，但不能单凭它解释当前示例的全部实际调度。完整 fully-async 文件仍可后置，活跃的关键路径需要明确接入。

**建议的有限调整**：

- 开始前短看 `Sample → 训练调用 → 权重更新 → 下一轮生成` 的全景，然后仍以 `generate_and_rm` 为首个深入入口；训练第 4 项无需整个前移。
- 保留“接入 → 批量运行 → 训练数据交接”的主顺序，测试和基本 Trace 从第一项就配套；第三项升级为真实的失败/慢任务定位练习。
- Kubernetes 从批量运行阶段同步推进一个有限案例，例如 worker 与 Service 的部署、资源限制、一次故障排查及结果保存。无 GPU 时可以使用 CPU 任务或服务替身，按实际环境描述产物。
- 给每项增加一个可检查结果：插件契约测试、并发/取消实验、失败 Trace、Sample 字段到训练输入的对应。原有“能说明”保留为理解目标，再补工程验证目标。
- Dressage 继续作为定点设计对照，岗位没有指定必须使用这个框架；一个月内优先利用已有 Slime 基础形成一项可验证扩展。

本轮核对了对应 Slime `18868a79` 的代码与测试文件，没有运行这些测试或替用户创建下一步。这里只记录评估和建议，未直接改写被评估 README 的四项主顺序。

<a id="hunyuan-priority-20261026"></a>

## 2026-10-26：评分接口之后优先补运行治理

用户再次明确“重点是为了对标腾讯的混元这个岗位”。继续沿用已确认 JD 与 2026-10-25 取证，不声称重新核查招聘状态。学习深度按岗位要求决定，不能由当前函数还调用了多少子函数决定。

评分部分优先掌握自定义评分的输入输出、批量/单条约定、已有奖励处理和失败传播；内置 math、F1 等算法实现按具体接入需要回查。生成与评分接口初步串起后，优先补成组并发、持续调度、背压、取消与结果一致性，并配套实际扩展或故障验证。具体下一入口及确认状态仍见[唯一进度](repo-reading-route.md#当前接续)，本段不另存学习进度。

<a id="current-reading-job-relevance"></a>

## 2026-10-21 再核对：当前读到的内容与岗位有多相关

用户本轮问题：“再对一下腾讯强化学习框架这个岗位吧”“我们当前看的内容有多少是和这个相关的呢？”

本轮通过腾讯官方招聘接口 `GET /tencentcareer/api/post/ByPostId`，以同一 `postId=2061654749727600640`、`language=zh-cn` 读取岗位，返回 `Code=200`，岗位名称仍为“混元Agent强化学习框架工程师（深圳/北京/上海）”，`LastUpdateTime` 为 **2026年10月20日**。[官方岗位入口](https://careers.tencent.com/jobdesc.html?postId=2061654749727600640)。这是本次取得的新证据；下方较早核对时的日期保留其历史语境。

**判断：目前选择的三个主要阅读块——Agent 模型请求、独立评测、轨迹导出——都直接对应岗位职责；当前覆盖集中在运行与数据交接层，不能据此推算岗位能力完成百分比。** JD 同时要求框架接入、并发与资源治理、集群经验和训练视角。以下是对当前学习材料的判断，不是对用户全部既有能力的评定，也不表示腾讯内部采用 Slime 或相同组件。

| 当前读的内容 | 对应岗位要求 | 相关性与当前边界 |
| --- | --- | --- |
| Step 1：`_run_turn`、消息与工具定义转换、tokenizer、SGLang 调用、解析与协议回复 | 职责 2；要求 2：模型调用、工具调用与上下文的统一封装 | **直接相关。** 已沿请求链讨论输入输出和实现交接；工具调用的解析与回复只是其中一段，外部 CLI 的工具执行循环未在这里完整展开 |
| Step 2：`run_evaluation`、`_grade_scaleswe`、补丁应用、执行评测与 Sandbox 生命周期 | 职责 1、3、5：自动化评估、评测接入和训练所需结果 | **直接相关。** 重点是代码改动如何得到 reward、环境如何回收；当前展开一个代表性评分分支，未运行真实远端评测，也不等于具备 Kubernetes 经验 |
| Step 3：`record_turn` 的回查、`get_trajectory`、`finish_session`，轨迹与奖励交成 Sample | 职责 1、2、5；要求 4：数据生成、结果收集与训练链路工程化 | **直接相关，且是当前与 RL 数据合同联系最紧的一段。** 卡片和构造例子已有部分证据，轨迹拼接、分段、mask 和训练侧消费仍需继续理解 |
| 当前回补：`sid`、`inflight`、`shutdown_session` | 职责 4；要求 1、5：异步并发、资源与结果一致性 | **直接相关的工程基础。** 要理解任务归属、关闭后拒绝新请求、等待与取消，以及导出前为什么先收尾；用户已明确状态含义仍需补清，不记成已掌握 |
| `json_response` 编码细节、`dataclasses.replace`、字典操作等局部机制 | 支撑上述接口与 Python 实现理解 | **辅助相关。** 读到能解释当前输入输出、副作用和关键错误即可；只有阻碍主线或排障时，再展开更深的库实现 |

这里的“直接相关”回答的是选题是否对准岗位。函数卡片数、阅读时长、局部测试通过或已生成文档，都不能换算成“已经达到岗位要求的百分之多少”。例如读清 Sandbox 接口与实际部署、排查 Kubernetes 是不同层次的证据。

从当前阅读记录看，仍需补的主要证据是：

1. **集群运行：** Kubernetes 中的部署、网络、资源、日志与故障排查，对应要求 3；当前 E2B 接口阅读尚未提供这类实践证据。
2. **完整实验与运行治理：** 真实任务链的 Trace、配置与结果复现，以及多任务负载下的并发限制、超时、取消和资源回收。已有本地 Task 与构造数据验证有帮助，但覆盖范围较小。
3. **训练侧的数据消费：** Sample 中的 token、logprob、mask 与 reward 怎样继续进入批次和训练计算，以及生成和权重更新怎样衔接；当前还停留在导出这一侧。
4. **实际扩展与维护：** 完成一次新评测或策略接入，说明接口变化，补验证并定位失败原因。读懂现有实现是基础，当前阅读记录尚未提供这类完整交付证据。

按当前目标的投入建议：先把 `sid` 与 `inflight` 收敛成能解释关闭逻辑的最小模型，回到 `finish_session` 的配置取出和已有轨迹导出问题；后续重点放在轨迹如何成为可训练的数据。JSON 编码等辅助细节不需要与这些问题投入相同深度。笔记格式有助于回忆，但反复修改格式本身不增加核心代码覆盖；格式稳定后，应逐步增加实际接入和失败验证。这些是本次建议，不据此开启新 step 或改写学习完成状态。

本节是岗位相关性的本次评估快照；具体已读事实、用户反馈和下一处入口仍只维护在[唯一阅读路线](repo-reading-route.md#当前接续)。

<a id="step-2-evaluation-choice"></a>

## 2026-10-21 核对：为什么 Step 2 先读独立评测

用户要求重新仔细核对 JD 后开启 Step 2。本轮再次读取上述同一岗位的腾讯官方页面，页面仍标注更新于 2026-09-30；此前用户提供文本的 2026-10-12 日期保留其来源，不合并为官网日期。官网职责与已有对照的重点一致，继续沿用已确认岗位目标。

| 核对的职责方向（概括） | 对 Step 2 的实际要求 |
| --- | --- |
| 职责 1、3：实验评估与不同评测方法接入 | 以 `run_evaluation` 的共同输入输出为入口，区分协议分派与具体评分规则 |
| 职责 2：把任务、结果与评估能力形成可复用组件 | 分清 SWE 任务层和 Sandbox 操作能力，定位更换评分方法所影响的接口 |
| 职责 4；要求 1、5：异步执行、资源与结果一致性 | 读清独立环境的生命周期、补丁状态、命令失败与异常传播；先保留关键边界，再按问题深挖重试 |
| 职责 5；要求 4：将训练需求落到工程链路 | 先解释 `reward` 的来源与含义，再连接已有轨迹和训练样本导出 |

因此 [Step 2](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-003-swe-evaluation/README.md) 定为“代码改动如何在独立环境中得到奖励”。第一遍选真实支持的 `scaleswe → eval_cmd` 分支，围绕接口和数据交接展开；不把阅读目标扩成安装某个数据集的全部工具。要求 3 中的 Kubernetes 部署排障能力仍需独立实践，本步理解 Sandbox 接口不能替代该证据。

本节记录选题依据，不保存第二份学习进度；实际掌握与运行状态继续见唯一路线。

## 当前学习条件与投入安排

2026-10-19 用户明确要求按这份 JD 分配学习时间，同时理解局部代码与全局框架。以下约束持续沿用，改变时再更新：

- 本地没有 GPU，当前以读明白为主，使用模型 API 辅助验证。真实训练与 Kubernetes 集群经验保留为后续实践，不作为开始阅读的前置条件。
- 用户自述已有 Learn Claude Code 的工具调用、任务执行与上下文管理基础，以及 asyncio 和预训练/SFT/RL 概念基础。沿用这些前置；遇到具体理解缺口再补，不重开完整基础课程，也不据此改写独立 Python 专题的掌握记录。
- 已读范围及当前接续只在[阅读路线](repo-reading-route.md#当前接续)记录，不在这里维护第二份进度。
- 用户认可 Learn Claude 的“基础骨架 → 新需求 → 增加机制”学习方式。Slime 先保留全局职责和数据合同，再在与目标工作相关的问题处深入；学习顺序是固定源码的逐步展开，不冒充项目历史。已读内容先短回顾，关键理解过程持续整理进 Hugo walkthrough。
- 2026-10-19 用户进一步明确：整体模型从岗位目标和基本框架开始，不以已读过 `generate()` 为知识前提；逐步记录每个模块的理解及目录/文件/函数，下一步继承前一步。方法复用于任意仓库，统一保存在根目录 [00-repo-reading](../../00-repo-reading/README.md)，Slime 记录在其项目子目录。
- 普通模型 API 可辅助理解推理、工具、评分、Trace 与并发；现有 Adapter 的 SGLang token/logprob 合同、训练权重更新和集群恢复另行核对，不能把普通聊天 API 视为完整 RL 训练替代。

下面是本轮助手提出的初始时间预算；用户已确认的是“由 JD 决定投入”，具体比例可继续调整，不冒称用户逐项确认、实际耗时或能力完成比例。每项同时包含必要阅读和小验证，不要求所有模块同等深入。

| 学习重点 | 初始预算 | 本阶段的投入边界 |
| --- | --- | --- |
| 全局职责与启动主线 | 5% | 短读框架入口、调用者和数据去向；以能定位组件为停止点，不反复重画完整地图 |
| 策略接入、生成与评测接口 | 25% | custom generate/RM、评测配置、样本处理和插件输入输出合同，优先理解算法需求接在哪里 |
| 并发、队列与稳定性 | 20% | 慢任务、并发预算、取消、积压、恢复和结果一致性，将已学 asyncio 用于具体运行问题 |
| Trace、测试与实验复现 | 15% | 关联任务各阶段、阅读断言、验证失败分支与保存复现依据；从首条主线配合使用 |
| 容器与 Kubernetes | 20% | 资源与服务边界、部署及排障；源码理解和实际集群验证分开记录 |
| 训练数据交接与权重更新 | 15% | Sample 到训练批次、策略版本、checkpoint 和权重同步；Megatron 并行及底层优化按需深入 |

这是时间安排，不新建课程编号或改变 00–07 的依赖关系。每次新单元说明本轮对应的岗位责任和停止点；用户追问暴露前置缺口时先解决缺口，再返回原交接。预算调整在这里说明理由，不要求读者为保持比例而跳过必要理解。

## 需求到阅读单元

“职责 / 要求 / 加分项”的编号对应用户提供的岗位文本。表中的覆盖是学习计划，不表示已经具备对应的工程经验。

| 要对准的能力 | 对应需求 | 阅读单元 | 源码关注点 | 读完要能回答 |
| --- | --- | --- | --- | --- |
| Research 任务、数据生成、评测与复现主链 | 职责 1；要求 2、4 | [00 全局职责](chapters/00-overview/README.md)、[01 任务执行](chapters/01-task-execution/README.md)、[03 策略与评测](chapters/03-strategy-evaluation/README.md)、[04 Trace 与验证](chapters/04-trace-validation/README.md) | `generate.py::generate`、`RolloutManager.generate/eval`、评测配置与结果合同 | 一次实验如何从任务和配置走到可追踪、可评测、可复现的结果？ |
| 模型、工具、任务与上下文的统一组件 | 职责 2；要求 2；加分项 2 | [01 任务执行](chapters/01-task-execution/README.md)、[02 模型与上下文](chapters/02-model-context/README.md) | `BaseHarness`、`Sandbox`、`BaseAdapter._run_turn`、解析器与 `TrajectoryManager` | 换 CLI、模型协议或环境时，哪些合同保持稳定，哪些实现需要适配？ |
| Agent 策略、评分与验证机制接入 | 职责 3；要求 5、6 | [03 策略与评测](chapters/03-strategy-evaluation/README.md)、[04 Trace 与验证](chapters/04-trace-validation/README.md) | `generate_and_rm`、custom generate/RM、sample hooks、`EvalDatasetConfig`、`tests/plugin_contracts/` | 新策略或评分方法接在哪里？输入输出、样本身份、分组与错误行为怎样验证？ |
| Python 异步、并发、性能与稳定性 | 职责 4；要求 1、5 | [05 并发恢复](chapters/05-concurrency-recovery/README.md)、[06 资源部署](chapters/06-serving-resources/README.md) | semaphore、异步任务池、输出队列、取消、`QueueDataSource`、数据传输、`Cleanup` | 慢任务、满队列、超时、重复结果或服务重启后，怎样保证结果完整和资源释放？ |
| 日志、Trace、结果分析与故障验证 | 职责 1、2、4；要求 5；加分项 3 | [04 Trace 与验证](chapters/04-trace-validation/README.md)，结合 01、05 的失败路径 | `trace_utils.py`、日志与指标、Trace Viewer、fake/恢复测试、复现配置 | 怎样关联一次任务中的模型、工具、环境和评分，并验证某次修复？ |
| 容器、Kubernetes 与集群排障 | 要求 3；职责 4 | [06 资源部署](chapters/06-serving-resources/README.md) + 独立集群实践 | Sandbox 操作合同、Docker、Ray 资源布局、模型服务发现/健康与清理 | 谁负责进程、Pod、网络、存储和 GPU？环境就绪、模型回连、取消与回收怎样实际验证？ |
| 训练视角与算法需求工程化 | 职责 5；要求 4 | [07 训练交接](chapters/07-training-handoff/README.md)，以前述 02、03、05、06 为基础 | `Sample`、`train.py`、actor/loss、checkpoint、权重更新、策略版本 | 生成时必须保留哪些训练信息？新策略怎样影响数据合同、损失消费与模型更新？ |
| 需求分析、沟通与持续维护 | 职责 3、5；要求 6 | 各单元的接口、失败路径与 review | 用源码说明输入输出、边界、兼容性、验证方法和未覆盖范围 | 能否把算法同事的需求写成具体接口改动、验收方法和排障记录？ |
| AI 工具、Coding CLI 与跨语言协作 | 加分项 1、2、4 | 01、02 的 CLI 集成 + 独立工具/项目阅读 | CLI 配置与协议、外部工具循环边界；按需阅读相关 TypeScript/Rust/Go 实现 | AI 工具的结果如何核对？外部组件出了问题，能否继续追到真实实现？ |

## 每次读一个部分，用四问保持对齐

1. **对应什么需求？** 从表中选择一行，说明这个模块承担的责任。
2. **接缝在哪里？** 找到调用者、输入输出、可替换接口和外部依赖。
3. **问题怎样暴露？** 选一个超时、取消、并发、上下文变化、评分失败或版本变化的情景。
4. **怎样证明理解？** 给出源码定位、可复述的调用/数据链，以及测试或实践方案；只有实际运行后才记录结果。

每章 `review.md` 可记录：需求编号、源码证据、已能解释的行为、待补实践。学习状态仍只在唯一阅读路线中更新，不在这里重复维护。

## 阅读优先级与仍需补的证据

00–07 保留为职责与依赖地图。当前从[唯一接续](repo-reading-route.md#当前接续)出发，建立基本端到端模型，再逐步展开框架入口与调用交接；已有任务链阅读用于按需提醒。随后按上表优先深入扩展/评测、Trace/验证和并发/恢复。06 的集群实践单独积累，07 先理解训练交接，再按算法需求深入。旧的 01→02→03 第一遍安排不覆盖用户明确报告的已读范围。

| 源码阅读可以建立的理解 | 还需要实践的证据 |
| --- | --- |
| Sandbox、Ray、模型部署与容器的责任边界 | Kubernetes 任务环境的创建/就绪、资源限制、网络与存储、日志与结果保存、故障排查、取消和回收 |
| 并发预算、背压、取消、恢复与结果合同 | 慢任务/满队列/服务重启实验，吞吐与延迟测量，结果完整性和资源回收检查 |
| Sample、SFT/RL 数据、策略版本和权重交接 | 一个小模型训练或自动化评测闭环，保存配置、数据与产物，比较并解释结果 |
| Harness、Adapter 和外部 CLI 的集成边界 | 真实 CLI/工具链的使用、调试、AI 生成代码核对，以及必要的跨语言修改 |
| 需求到接口、验证与失败处理的映射 | 至少一项具体变更的需求拆解、实现、回归验证和复盘记录 |

本文件只维护目标、投入与实践要求。当前已读范围、实际运行证据与源码基准统一见[阅读路线的当前接续](repo-reading-route.md#当前接续)，不从资料完成状态推断用户掌握。

具体文件/函数入口见[代码阅读名单](code-reading-list.md)。开始阅读前按 [README 的官方版本核对步骤](README.md#每次开始前确认源码与官方最新版本)记录差异；既有清单的固定提交不冒充当前 checkout。
