# Step 006 之后：主题划分与逐步阅读范围建议

[已确认的接入顺序](integration-reading-plan.md) · [岗位范围复核](post-step006-job-reading-review.md) · [项目唯一进度](../README.md)

2026-11-08，按用户要求细化后续每步的 scope；用户随后确认据此建立各步 scope，并将现有记录归入合适的 topic。现已按下述结构整理：[原生单任务闭环](../topics/01-native-agent-rollout/README.md)、[Harbor 接入与验证](../topics/02-harbor-integration/README.md)，以及原有的 [Agent Sandbox Kubernetes 主题](../../agent-sandbox/topics/kubernetes-sandbox-control/README.md)。未来步骤仅准备 01-scope.md，不表示已开始阅读、已掌握或已完成实现。

## 1. 不只一个 topic，但也不按每个组件开 topic

topic 围绕一个可以独立解释和验证的问题；step 围绕其中一次明确的交接。HTTP、Task、类和辅助函数本身不是拆 topic 的依据。

| 主题 | 完整问题 | 记录归属与建议编号 |
| --- | --- | --- |
| 1. 原生 Dressage 单任务闭环 | 一份题目怎样执行、成为训练样本，并结束资源使用？ | 已有 Dressage Step 000–006 属于这条主线；继续 Step 007–009 收尾 |
| 2. Dressage × Harbor 接入与验证 | 怎样复用任务、Agent、评测和采集能力，把现有项目接成一条可运行链路？ | Dressage 后续 Step 010–017；需要读取 Harbor 与现有项目时在 scope 标明仓库边界 |
| 3. Kubernetes 沙箱资源治理 | 环境如何创建、就绪、预热、领取、访问和回收？ | 复用 Agent Sandbox 已有 Kubernetes topic，沿它自己的 Step 003 继续，不在 Dressage 复制另一套控制器阅读 |

从整体目标看是三个主题；其中前两个在 Dressage 阅读主线中连续编号，第三个已经有独立项目和步骤。不存在“必须把三个主题全部读完才能做第一次验证”的要求。

原生执行与 Harbor 执行是两条路线。主题 1 提供已有对照，主题 2 不把整套 Paddock/BlackboxServer 再嵌进每次 Harbor Trial。主题 3 提供可复用的 K8s 能力，其与 Harbor 的连接点是 Environment。

## 2. 主题 1：用三步收尾原生主线

### Step 007 · 会话收尾与轨迹取得

- **核心问题**：Agent 已结束，怎样让 Proxy 完成本次会话的收尾并交出轨迹？
- **入口与范围**：[generate:293](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L293)；after_agent 只回顾已读命令机制，主读 [ProxyClient.finalize_session](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L64) 与 [read_trajectory](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L115)。必要时只追相应服务端路由和记录去向。
- **停止位置**：generate 拿到 trajectory_payload。能说明它与 call_payload 的区别、会话标识如何关联，以及 drain 的含义。
- **暂不展开**：Proxy 的所有模型协议、完整 TITO/压缩算法、轨迹日志写盘细节。

### Step 008 · 轨迹段成为 Sample

- **核心问题**：一份轨迹怎样变成一组训练样本，而不丢失原任务归属？
- **入口与范围**：[expand_segments_to_samples](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/multi_segment.py#L118)；必要下钻 [write_sample_from_segment](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/artifacts/samples.py#L291)。用一条轨迹、两段输出看 token、mask、logprob、parent_traj_id、segment_index 和奖励锚点的交接。
- **停止位置**：返回 Sample 列表，能指出哪些字段来自原 sample、哪些来自轨迹；知道奖励后处理还要接续，不能把所有段当独立答题。
- **暂不展开**：完整 reward 归一化、训练 loss 与后端实现。这里只定位奖励广播的后续合同，不重读 Slime 训练主线。

### Step 009 · 返回、异常与资源回收

- **核心问题**：generate 准备返回或被取消时，谁还持有环境和会话，谁负责释放？
- **入口与范围**：[generate 的 except/finally](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L348) → _discard_session_context → [schedule_terminate_paddock](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/lifecycle.py#L175)。正常返回先走通，再追一种取消场景；只在资源归属不清时回查 terminate 实现。
- **停止位置**：列清正常、失败、取消三类出口的返回物及清理责任；区分“安排后台清理”和“资源实际已释放”。主题 1 至此整体收束。
- **暂不展开**：所有失败类别、所有 provider 的释放细节和原生异步 worker 全部模式。

## 3. 主题 2：按接入问题组织，不重走一遍所有底层函数

### Step 010 · Slime 怎样交给 Dressage 的 Harbor 入口

- **核心问题**：接入 Harbor 后，哪一处替换了原来的单条 generate？
- **入口与范围**：训练脚本的 rollout hook → [generate_rollout_harbor_sync](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1257) → _run_harbor_rollout → _run_partition。只定位数据源、Job 创建、插件传入和返回对象。
- **停止位置**：画清 Slime → Dressage → Harbor 的交接；区分单条 custom generate 与整批 rollout hook。结果如何逐项转换留到 Step 015。
- **暂不展开**：全部分组调度、训练校验和 Slime 内部实现。

### Step 011 · 一次 Harbor Trial 的生命周期

- **核心问题**：一次尝试从环境准备到结果与清理，是谁组织的？
- **入口与范围**：[Trial.run](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L345) 的 _prepare、_run、_finalize 主干；对照 [DressageHarborPlugin.on_job_start](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L261) 只看注册了哪些生命周期回调。
- **停止位置**：能区分 Task、Trial、Agent、Environment、Verifier；知道 Dressage 在哪几个事件接入。此步保留主骨架，后面的步骤逐段进入它。
- **暂不展开**：插件内部路由配置、全部 Agent 和 Trial 队列机制。

### Step 012 · 换题目、换 Agent、换评测分别改哪里

- **核心问题**：同一道题怎样用不同 harness 运行，而不用复制整个执行流程？
- **入口与范围**：Job._init_trial_configs 与一份实际 Task 定义；沿 Trial 的调用定位 [BaseInstalledAgent.setup](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/agents/installed/base.py#L497)、一个 Claude 安装/运行入口及 [Verifier.verify](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/verifier/verifier.py)。
- **停止位置**：用一个例子列出 instruction、环境要求、Agent 选择、验证规则和奖励来源；换 Codex 时只核对差异。安装行为与任务镜像分开解释。
- **暂不展开**：所有 benchmark 格式、所有 CLI 输出解析器。Verifier 先看执行与读取奖励的边界，不通读每种评分算法。

### Step 013 · Harbor Environment 接到已有 K8s 能力

- **核心问题**：真正需要补的环境适配层有哪些方法和行为？
- **入口与范围**：Trial 的环境准备位置 → [BaseEnvironment](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py) 的 start、stop、exec、文件与目录传输 → [现有 UpstreamK8sSandbox](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/sandboxes/k8s/adapter.py:62)。
- **停止位置**：产出接口映射与缺口表，说明 image/resources、cwd/env/user、超时、退出码和清理责任。先以冷创建为基线；合同清楚后即可做一题 Oracle/确定性执行的局部验证。
- **暂不展开**：重写 Sandbox controller、所有集群优化。WarmPool 与 Claim 的内部机制转到主题 3，完成后回到本接口接入。

### Step 014 · 模型请求和采集接口怎样接上

- **核心问题**：Agent 请求会发到哪里，现有商业 API 后端能满足哪些 Dressage 合同？
- **入口与范围**：[模块函数 _inject_agent_routing](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1031) → Gateway 的代理创建 → ProxyClient；对照现有 api_backend。只追一个 Agent 的一次模型请求及其 session 关联。
- **停止位置**：画出请求往返路径，列出模型调用、finalize、read_trajectory 的协议差异与待适配项；分清 API 评估可用与训练 token/logprob 可用。
- **暂不展开**：完整多协议兼容、所有路由与安全策略、完整 Trace 平台。不能把改 URL 当成合同已经兼容。

### Step 015 · Trial 结果、奖励与轨迹怎样被提交

- **核心问题**：任务结束后，哪些结果被保存、哪些转换后交回 Slime？
- **入口与范围**：Trial._finalize 发出的 END → Dressage 插件 [_on_end / _finalize_attempt](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L742) → [HarborArtifactStore.commit_attempt](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L256)，再回 rollout 的 [_bundle_samples](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L624)。
- **停止位置**：用 trial/attempt/session 对上一份奖励、轨迹与结果产物；解释正常低分与运行失败的区别，以及 API-only 结果和训练输出的不同要求。
- **暂不展开**：所有产物格式、复杂重选策略和训练归一化细节。原生 Step 008 的字段知识复用，不重新逐个讲一次。

### Step 016 · 并发、取消与重试的一次完整案例

- **核心问题**：多个尝试运行时，一个失败或被取消的尝试怎样可靠退出？
- **入口与范围**：Harbor TrialQueue 的并发与重试入口、Trial._finalize；追 [Dressage 插件 _on_cancel](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L731) 到 _on_end 的一次实际路径，接回 Environment.stop 和产物提交。
- **停止位置**：知道谁限制并发、谁持有环境、谁关闭模型路由、谁提交结果；检查取消不生成可训练成功样本、重试不误用上次身份、结果不重复提交。
- **暂不展开**：所有失败组合、所有队列实现和 Dressage 原生 worker。先选一个可复现的取消/超时情形，其他情况按暴露的问题扩展。

### Step 017 · 最小整合与验证记录

- **核心问题**：现有项目是否真的能通过这些接口运行，并留下可说明的证据？
- **范围**：以 Step 013 的冷创建局部验证为基础，完成一题 + 一个 Agent + 模型请求 + Verifier + 结果与回收；再换一个 Agent，补少量并发、预热和一次取消/重试。
- **停止位置**：保存可复跑配置、输入与版本、成功和失败记录、环境回收证据，以及新增适配代码的职责。已有等价项目成果直接复用，不重复造实验。
- **性质**：这是实施与验证步骤，不是新增一轮全仓阅读；实际开始时再按差异、环境与调用成本确定执行范围。本轮只做范围规划，未执行部署或模型调用。

## 4. 主题 3：继续已有的 Agent Sandbox Kubernetes 主题

该主题已经有自己的 Step 000–003，编号与 Dressage 分开。当前步骤仍以 [Agent Sandbox 项目入口](../../agent-sandbox/README.md#current-reading)为准，下面仅给后续范围建议。

| Agent Sandbox 步骤 | 核心范围与入口 | 停止位置 |
| --- | --- | --- |
| 003 · 已在进行 | updateStatus：观察到的状态怎样写回 API，怎样处理版本冲突 | 区分内存状态、API 状态与下次协调；先收束已有步骤 |
| 004 · 建议 | [SandboxWarmPoolReconciler.Reconcile → reconcilePool](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L435)；备用数、Ready、terminating 与创建/删除观察 | 能解释目标 3、实际 1 时怎样补池，并区分已创建与已就绪 |
| 005 · 建议 | [SandboxClaimReconciler.reconcileActive → getOrCreateSandbox](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L580)，必要时进入 completeAdoption | 解释定向选池、热领取、冷创建、并发冲突、归属转移与释放；两个 Claim 不应误领同一资源 |
| 006 · 建议 | 从 SDK/已有适配器走一次执行与文件访问，核对实际 Service/连接方式、RBAC、网络与运行权限 | 能定位一种访问或权限故障，解释控制器权限与沙箱进程权限的区别；运行时隔离只选当前部署使用的一种 |

这里的部署排障与 Dressage Step 013/017 使用同一份实际环境即可。K8s 主题记录资源行为，整合步骤记录跨组件结果，不要求把同一个实验做两遍。不要把“Pod Ready”当成题目初始化和 Agent.setup 都已完成。

## 5. 实际执行顺序与范围控制

1. **现在先进入 Step 007 的候选问题。** 仍留在原生 generate，不跳去新执行器。
2. **007–009 收尾后，切换主题 2。** 010–012 建立 Harbor 的入口、生命周期和替换边界。
3. **013 是 K8s 主题的连接点。** 冷创建所需基础复用已有 K8s 阅读；预热和领取按主题 3 进入，随后回到 Environment 适配。完整整合前必须核对实际 WarmPool/Claim 行为，不要求在首次冷创建之前读完全部池实现。
4. **014–016 接通模型、结果与失败治理。** 各单元正常路径可以做局部验证，不能一直等到最后才发现协议不兼容。
5. **017 汇总整合证据。** 是对已有验证的补齐与串联，不是“前面读完才第一次运行”。

编号已用于本次准备的 scope，实际阅读时沿用这些边界；遇到一两处 helper，先放在父函数对应阶段，不为每个 helper 增加 Step。若一个步骤仍出现两个独立问题，再讨论拆分。预备 scope 不提前建立短期记忆、长期继承、形成过程或任务总结。

每个正式 scope 继续使用已确认的表达：3.1 交代该步在主题主线的位置；3.2 上方图表达真实执行关系、下方连续数字表达阅读顺序。返回与跨 HTTP/Task 切换明确列出，不再让小数编号同时表示两种关系。

未来如需单独深入训练数据一致性，可另开主题处理 TITO、一次上下文压缩、奖励广播与分段权重。但它不是接入 API 评估平台前必须完成的第四个主题；只有训练目标或实际问题需要时再确定范围。完整 Trace、所有 Agent 和所有原生异步模式同样保持后置。

## 6. 版本与证据边界

- 本轮核对的三个本地仓库工作区均干净：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c；Agent Sandbox 37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1；现有项目 151db30d1f4533773948695f4033ebe4353521d8。
- Harbor 沿用前次研究核对的 0.18.0 / 527d50deb63a5d279e8c20593c18a2cbc7f61f9e。入口依据见[研究证据](agent-sandbox-harbor-integration-evidence.json)；正式进入时仍需取得并核对这个固定版本，不把最新版行号混入。
- 规划阶段静态核对了上述本地关键符号与交接位置，没有把规划中的函数记为用户已读。随后按用户授权准备各步 scope，未运行集群或模型，未建立未读函数卡。
- 原 Step 000–006 已整体迁入 topics/01-native-agent-rollout/steps，保留目录后缀、内容、认识时间与历史来源；只重算链接，不重编号。Harbor 主题沿 Dressage 编号继续，K8s 主题仍独立编号。
