# Step 006 之后：按腾讯混元岗位复核剩余阅读

[项目入口与唯一进度](../README.md) · [已确认的接入顺序](integration-reading-plan.md) · [适配研究](agent-sandbox-harbor-integration-research.md)

2026-11-08 讨论快照。本文复核剩余重点，不另建实时进度，也不预创建后续 Step。岗位依据是用户 2026-10-28 提供、10-29 再次确认的 JD，不表示本日查询了招聘官网。

同日用户在接入讨论后再次明确：“主要的目标是腾讯的强化学习框架这个岗位”。当前优先完成原生主线的轨迹、Sample 和清理交接，再利用 Harbor/Agent Sandbox 做一项有限的扩展与验证案例。已读 Slime 的生成和训练闭环继续计入背景；并发、Trace 与 Kubernetes 以具体运行问题和证据补足，不转成全仓重读或完整平台建设。

## 1. 以哪份约定为准

1. **岗位能力边界**：以[用户提供的完整 JD](../../../../slime_photo/code-reading/job-evidence/2026-10-28-user-provided-jd.md)和[10-29 再确认](../../../../slime_photo/code-reading/job-evidence/2026-10-29-user-jd-reconfirmation.md)为准。重点是 Research Agent 框架的接入、维护、验证、运行稳定性和 Kubernetes 实践；训练视角服务于这些工作。
2. **当前接入顺序**：以 2026-11-07 确认的 [integration-reading-plan](integration-reading-plan.md) 为准：原生 generate 收尾 → Dressage Harbor 批量入口 → Harbor Trial → Environment/K8s → 模型与结果采集。
3. **不恢复旧的额外前置**：较早的“优先读原生异步 worker”是研究前的候选；当前 Harbor 路线不要求先读完原生 worker。Slime 也已明确[可以停止新增通读](../../../../slime_photo/code-reading/job-alignment.md#slime-reading-stop-20261101)，不把旧 P0 模块列表重新当作必读清单。

## 2. 目前已经走到哪里

这是核对日的阅读快照，不替代各项目的唯一进度：

| 项目 | 已有阅读基础 | 不能由此推断什么 |
| --- | --- | --- |
| Dressage | Step 000–006 已走过单次任务的身份、环境准备、注册和执行；已区分提交回复、后台执行、查询结果以及 CLI 输出和 Proxy 记录 | 不代表已读完轨迹到 Sample、外层回收，也不代表完成真实任务验证 |
| Slime | 已有生成接口、样本到训练以及 Step 017 正常训练闭环的阅读；后续以具体接入问题回查 | 不要求再从头通读 rollout、训练后端或底层通信 |
| Agent Sandbox | 已读 Sandbox 到 Pod 的创建及 Ready 普通路径；当前记录停在 updateStatus 的状态写回 | 不能把 WarmPool、Claim 或实际部署排障当作已经完成 |

来源：[Dressage](../README.md) · [Slime 当前接续](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续) · [Agent Sandbox 当前接续](../../agent-sandbox/README.md#current-reading)。

## 3. 下一段原生 generate 还剩什么

Step 006 结束的是“把题目交给 Agent，再取回调用结果”。此前确认的原生主线收尾仍有下面五个交接：

| 顺序 | 看什么 | 看清什么就够 |
| --- | --- | --- |
| 1 | execute_blackbox_cmds_for_stage，stage=after_agent | 复用已读命令执行机制；只补清调用时机和这次配置，不重读全部命令辅助函数 |
| 2 | ProxyClient.finalize_session | 哪个会话被收尾、交入哪些资料、请求完成后继续哪里 |
| 3 | ProxyClient.read_trajectory | 从 Proxy 取得哪份轨迹，与 CLI 结果有何区别；drain 对记录的含义 |
| 4 | multi_segment.expand_segments_to_samples | 一次执行如何得到若干 Sample，身份、token/logprob/mask 的来源及最小对应关系 |
| 5 | generate 的 finally 与清理入口 | 正常返回、失败和取消时谁承担会话及环境清理；安排回收与实际释放分开 |

这些是同一条原生主线的剩余部分，不等于必须新建五个 Step。先解释用途与交接，仅对影响当前问题的实现继续下钻。

**下一步候选范围**：Agent 已经结束，怎样给 Proxy 会话收尾并取回轨迹？以 generate:293–309 为定位骨架，after_agent 作短回顾，首个新的主要入口为 [ProxyClient.finalize_session:64](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L64)，然后接 [read_trajectory:115](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L115)。

这一轮可以先停在取得 trajectory_payload；Sample 转换与最终清理随后接续。这里提出边界，尚未开启新步骤或建立未读函数卡。

## 4. 岗位上还要补齐的重点

| 重点 | 对应 JD | 后续读哪里、做到什么程度 |
| --- | --- | --- |
| Agent 结果与训练/评测数据的交接 | 职责 1/2/5，要求 2/4 | 先完成上面的原生收尾。分清输出、轨迹、奖励、Sample；对所用字段能解释来源。完整 TITO、压缩和分段归一化在实际训练需要时选一例深入，不成为接环境前的全量前置 |
| 不同任务、Agent 与评测的接入 | 职责 2/3，要求 2/5 | 沿 Dressage Harbor 入口到 Trial.run，区分 Task、Agent、Environment、Verifier；能说明换任务、换 Agent、换评测分别改哪里 |
| Kubernetes 环境生命周期 | 要求 3，职责 4 | 沿 Agent Sandbox 当前状态写回继续 WarmPool、Claim；在 Harbor Environment 边界映射创建、就绪、exec、文件传输、停止和回收 |
| 并发、失败与资源所有权 | 职责 4，要求 1/5 | 在最终选用的执行路线追踪并发上限、超时、取消、重试和结果提交。用一次失败或取消验证环境能回收、结果不会重复提交；不必两套调度器同时精读 |
| 模型路由、结果采集与复现 | 职责 1/2/4，要求 2/5 | 知道请求经哪个代理、如何用任务/尝试/会话标识串起日志与结果。保留配置、版本、输入和运行证据。原来暂缓的完整 Trace 专题不自动恢复；当前只补接入与诊断所需的最小链路 |

这张表是能力与实践重点，不是五门新课程。优先把它们放进同一个已有项目，避免每个框架都重新实现一遍。

## 5. 接入工作如何体现这些能力

目标继续沿用现有 slime_api_data_collecting 项目。先核对并复用其中已有 K8s/预热能力，再在确实缺失的接缝补代码；本轮未重新审计该项目的工作区或宣称实现状态。

1. **先验证冷创建闭环**：一题与现成 Oracle/确定性执行路径，走通环境创建、命令、文件、Verifier 与删除。已有等价案例可以直接复用。
2. **接一个实际 Agent 与模型**：确认所选 Agent 的准备与执行、真实模型请求、结果和失败记录。再用同一道题切换另一个 Agent，验证接口确实可复用。
3. **补少量并发与预热**：验证独立领取、备用补充、未命中后的冷创建，以及取消/超时后的回收。
4. **留一份可复跑证据**：配置、任务与模型版本、一次成功、一次失败/取消、资源清理结果，以及一处明确的适配改动。实际需要时测量启动时间或吞吐，再谈优化效果。

真实集群与接入证据不能由源码阅读替代；也不能因为本次阅读没有运行记录，就断言用户以前没有实践。已有等价成果应优先复用。

## 6. 保留的技术边界

1. 原生 blackbox 路线和 Harbor 路线是两条执行入口。Harbor Trial 不再绕行整套 Paddock/BlackboxServer；已读原生知识用于理解和对照接口。
2. 原生 PrewarmScheduler 不会自动被 Harbor 使用。当前目标优先核对 Harbor Environment 与 Agent Sandbox WarmPool/Claim 的组合。
3. 商业模型 API 不能只替换一个 URL 就视为兼容 Dressage Proxy。会话收尾、轨迹读取和真实 token/logprob 可用性需要单独核对；API 评估闭环与训练可用性分别验收。
4. 既有固定版本的 Harbor 依赖与 Agent Sandbox 示例存在差异，沿[适配研究](agent-sandbox-harbor-integration-research.md)的版本证据处理，不能把文档中的类名当作已经可用的依赖。
5. 不将完整 Megatron、所有 Agent、所有 provider、多集群、全部隔离运行时和完整 Trace 平台升级为本岗位的额外前置。

本轮为已有岗位材料、阅读记录与固定源码的复核；没有重新查询招聘状态，没有创建后续 Step，没有执行框架、模型或集群实验。

<a id="coverage-audit"></a>

## 7. 对现有 scope 的岗位覆盖审查

2026-11-08，用户要求判断当前需要阅读的部分是否都涵盖。审查口径是已确认 JD、现有 Slime 阅读基础、Dressage 已读步骤和已准备 scope，以及 Agent Sandbox 当前主题；不把“目录里有文件”当作已经掌握。

**结论：主要能力方向已有对应，不需要继续增加框架或新 topic；但四处具体观察/验证要求还不够明确，不能直接宣称全部覆盖到位。** 下面只提出补强位置，尚未改写各步骤的正式 scope。

| JD 所需方向 | 已有落点 | 评估 |
| --- | --- | --- |
| 模型、工具、任务执行的完整链路 | 已读原生 Step 000–006；后续 Step 010–014；已有 Slime Coding Agent 阅读 | 主要职责有落点，继续复用已有知识，不重读所有 Agent |
| 上下文管理 | Slime 已读请求/轨迹背景；Dressage Step 007/014 的会话与模型入口 | 部分覆盖。当前 scope 更偏身份与路由，缺一个“工具返回后，下一次模型请求与记录怎样续接”的明确观察点 |
| 轨迹、奖励与训练交接 | Step 007/008/015；已有 Slime 样本到训练和 Step 017 正常闭环 | 主线覆盖，Dressage 分段后的奖励处理仍只作定位，需补最小语义对照 |
| 策略/Agent/评测扩展 | Step 012、013、017 | 接缝已覆盖；“能切配置”与“能维护一个组件并验证”仍应通过实际小改动区分 |
| 异步、并发、取消、资源回收 | Step 009、016、017；原有异步学习及已读 Task/Event 交接 | 已有明确案例范围，不要求通读调度器和事件循环 |
| Kubernetes 部署与排障 | Agent Sandbox 的资源、状态、WarmPool、Claim、访问专题；Dressage Step 013/017 | 阅读与验证方向齐备；尚需实际证据，已有等价经验可以复用 |
| 日志/Trace、复现、性能 | Step 015/017 的产物与版本记录；Step 016 的失败案例 | 日志与复跑已安排，具体定位过程及阶段耗时基线还不够明确；完整 Trace 专题仍保持暂缓 |
| 软件工程与协作迭代 | 环境或评测适配及 Step 017 | 可由同一个有限需求变更体现，需明确保留接口说明、自动验证和失败处理依据，不另造课程 |

### 7.1 上下文续接：补一个例子，不通读全部 TITO

- **建议位置**：Step 014 的一次模型请求旁，接回 Step 007 的记录结果；已有 Slime 对应背景先作简短回顾。
- **观察对象**：一次工具调用、工具结果、下一次模型请求中的上下文，以及 Proxy 保存的生成记录。
- **停止标准**：分清 Agent/模型生成内容、工具结果和历史上下文的来路；知道哪些位置形成训练信号。会话 ID 对齐不能代替这项理解。
- **边界**：不因此展开每种 CLI 的内部循环或完整上下文压缩算法。此前已掌握的同等内容可直接引用，只补 Dressage 实现差异。

### 7.2 分段奖励：补训练消费合同，不只停在字段写入

- **当前缺口证据**：Step 008 写明“奖励广播只定位后续合同”，Step 015 也排除了完整归一化。两者作为首轮界限合理，但共同留下了 Dressage 特有的分段语义空隙。
- **建议位置**：Step 008 说明段与轨迹归属，Step 015 补训练消费侧的小案例；不要将 reward_post_process 误画成 _bundle_samples 的直接子调用。
- **最小入口**：[reward_post_process](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/training/reward_post_process.py#L79)，必要时对照 [convert_samples_to_train_data](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/convert_samples.py#L89)。
- **停止标准**：用“一条轨迹两段、另一条一段”说明原始轨迹的奖励归属、processed reward/advantage 的广播、raw reward 与样本权重的区别；知道行为策略版本需要与训练消费约束对齐。无需深入所有估计器、loss 或通信实现。

### 7.3 故障定位与性能：补观察结果，不建设新平台

- **建议位置**：Step 016/017 的同一个失败及并发案例。
- **最小要求**：从一个 trial/attempt/session 找到对应日志和环境资源，区分镜像/环境未就绪、模型请求失败、Agent 非零退出和 Verifier 失败中的一种，并能指出证据链。
- **性能观察**：记录少量任务的环境就绪、排队、Agent 执行及收尾耗时；若比较冷创建与热领取，保留同类任务和条件。先有基线，再决定是否存在需要优化的瓶颈，不预设一定有性能收益。
- **边界**：不要求大规模压测、完整监控平台或恢复此前暂缓的 Trace 源码专题。

### 7.4 工程改动与自动验证：补一份可复用成果

- **建议位置**：Step 012/013 的有限任务、评测或环境适配需求，验证归入 Step 017。
- **最小要求**：一处明确的接口改动，配正常行为与一个相关失败情形的自动验证，记录预期输入输出、清理责任和取舍。可以复用现有项目中同等成果。
- **边界**：只切换配置可以证明复用能力，但不单独证明组件开发与维护能力；手工跑通也不能代替所有工程验证。

### 7.5 目前不用继续扩大什么

1. 已有 Slime 的生成/训练闭环计入基础，不因 Dressage 又出现 Sample 就从头重学；一种实际采用的 RL/评测流程即可承接 JD 的训练视角。
2. 不新增完整 Megatron、Kubernetes 调度器、所有 Agent、所有异步模式和完整 TITO 的必读要求。
3. Harbor–Agent Sandbox 的版本与适配缺失是实施风险，不是必须靠继续读更多框架解决的知识清单；它不应绑住所有岗位验证案例。
4. 计划覆盖、实际已读、用户掌握和真实运行证据分开登记。当前大多数后续步骤只有 scope，不能据本次审查登记为能力已经通过。

本轮建议保留三个主题和现有 Step 编号，只在上述现有步骤补少量观察/验收要求。是否据此改写正式 scope，后续按用户明确指令处理；当前阅读入口仍为 Step 007。
