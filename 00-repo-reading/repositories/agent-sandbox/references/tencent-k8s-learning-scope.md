# 腾讯混元岗位导向：Agent Sandbox 的 Kubernetes 学习范围

[项目入口与唯一进度](../README.md#current-reading) · [完整岗位原文](../../../../slime_photo/code-reading/job-evidence/2026-10-28-user-provided-jd.md) · [原有材料索引](rl-environments-and-jd.md) · [与 Dressage 的分工](dressage-prewarm-comparison.md)

2026-11-04，用户明确要求“把这个作为目标”，并询问本仓库具体应该读哪些内容。本页固定已确认的目标，给出当前建议路线；具体 step 仍在实际开始时建立，不因列出函数就预建记忆或标记已掌握。

## 1. 已确认的目标

**理解并能够验证：一份 Agent 沙箱需求，如何在 Kubernetes 上成为可用环境，被任务领取和使用，并在失败或结束后正确回收。**

重点对应 JD 的 Kubernetes/容器化与集群实践要求，以及并发、资源、链路和行为一致性职责。Agent Sandbox 的角色是资源模型、控制器与环境运行基础设施；任务级前瞻、Agent 循环、轨迹与训练样本交接继续通过既有 Slime/Dressage 阅读承接。

这里管理的是沙箱工作负载及其生命周期，不要求重读 kube-scheduler、kubelet、etcd 或所有容器网络实现。Go 语法按读到的代码补充，不另开完整语言课程。

## 2. 核心路线：五项足够构成本仓库当前主线

这些是问题分组，不是预先创建的五个 Step，也不要求每个辅助函数逐行精读。

### 1. 一份 Sandbox 怎样成为运行中的环境

- **问题**：谁读取期望配置，谁创建和观察 Pod，谁提供网络入口和存储，什么时候才算 Ready？
- **先读**：用一份最小 Sandbox YAML 对照 [Sandbox API](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/api/v1beta1/sandbox_types.go)，从 [SandboxReconciler.Reconcile](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L366) 进入 [reconcileChildResources](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L507)。
- **按需下钻**：reconcilePod；reconcileService、reconcilePVCs 先看调用与对象归属；computeConditions 和 updateStatus 看观察结果如何对外表达。SetupWithManager 用于回查“哪些事件会再触发协调”。
- **停止标准**：能连起 Sandbox.spec → controller → Pod/Service/PVC → Sandbox.status，并解释一次 Reconcile 返回不等于容器已运行；知道调度和启动由 Kubernetes 原有组件完成。

### 2. WarmPool 怎样可靠维持备用数量

- **问题**：期望备用数与实际数不同，怎样补充或缩减？缓存还没看到刚创建的对象时，为什么不会重复扩容？
- **先读**：[SandboxWarmPool API](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/api/v1beta1/sandboxwarmpool_types.go)、[WarmPoolReconciler.Reconcile](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L435) → [reconcilePool](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L491)。
- **重点机制**：现有/Ready/terminating 数量的区别；创建和删除的 expectations；创建批次与补池限速；资源不足时的等待或重试。按具体问题回查 buildSandboxCR。
- **停止标准**：能解释“目标 3、当前 1”怎样推进，以及为什么已领取的环境不计入备用目标。这里研究协调一致性，不再把 Python wave 策略当作 RL 调度的核心方案。

### 3. Claim 怎样领取、绑定和回收环境

- **问题**：任务怎样定向领取正确池的环境，怎样避免并发重复分配，没命中时怎样处理，删除后谁回收？
- **先读**：[SandboxClaim API](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/api/v1beta1/sandboxclaim_types.go)、[reconcileActive](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L580) → [getOrCreateSandbox](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L2230)；归属交接看 [completeAdoption](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L1478)。
- **重点机制**：warmPoolRef 定向选择、热领取/未就绪/冷创建的边界、并发冲突与重试、OwnerReference 归属转移、Claim 状态与资源回收。清理以实际归属和删除策略为依据，不假定用完自动回到干净备用池。
- **停止标准**：能跟踪一个 Claim 从提出请求到取得 Sandbox 名称/Ready 状态，再到释放；能解释两个并发请求为何不能占用同一环境。

### 4. 环境怎样被访问，以及隔离边界在哪里

- **问题**：SDK 如何取得并访问已分配环境？控制器权限与沙箱内权限各是什么？限制网络或更换运行时会改变什么？
- **代表材料**：[Python SDK 的 Claim 创建与等待](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/clients/python/agentic-sandbox-client/k8s_agent_sandbox/sandbox_client.py#L126)、[安全模板示例](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/warmpool-quickstart/secure-sandboxtemplate.yaml)、[控制器 RBAC](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/k8s/rbac.generated.yaml)、[威胁模型](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/docs/security/threat_model.md)。
- **只选一条操作路径**：领取环境后执行一个命令，按实际连接方式看 Service/路由/Pod 入口；不先通读所有 SDK 和协议。
- **只选一种隔离配置**：先读懂 service account/RBAC、NetworkPolicy、securityContext/RuntimeClass 在当前配置中分别限制什么。gVisor 或 Kata 按本地可用条件选一例，不要求全部部署。
- **停止标准**：能解释“控制器能创建资源”与“沙箱内进程拥有权限”的区别；不把普通容器或创建 Sandbox CR 自动等同于强隔离。

### 5. 把源码理解落到一个部署与排障闭环

- **正常案例**：用 [warmpool-quickstart](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/warmpool-quickstart/README.md) 作配置参考，完成模板/池准备、领取、一次命令执行和释放，观察资源状态与归属。
- **配置校准**：示例 Claim 如果带额外 PVC 等覆盖可能走冷创建；要观察热领取，应按当前模板与 Claim 的实际兼容条件准备案例，不能仅凭池名判断命中。
- **故障案例**：选择一个可控问题，如镜像拉取失败或资源请求导致 Pod Pending，从 Claim/Sandbox/Pod 的状态、Events 和控制器日志定位原因；修正后验证恢复和清理。
- **并发观察**：少量并发 Claim 验证分配对象互不冲突，并观察备用池补充。先验证正确性，不直接对集群进行高压测试。
- **材料**：[排障文档](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/site/content/docs/getting_started/troubleshooting/_index.md)、[指标说明](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/docs/metrics.md)；确有瓶颈后再查 [性能调优](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/docs/performance-tuning.md)。
- **结束产物**：一份可复跑配置及操作记录，能说明正常链路、一次故障的证据、恢复步骤和资源回收结果。可复用已有等价集群实践，不要求为记笔记重复搭建。

## 3. 目前后置的内容

1. Python Fleet 的其他调度策略、全部 adapters 和完整训练循环；现有基本职责与接口已可作为背景。
2. HPA/KEDA、Kueue、APF 的全部方案；只有配额、突发争用或扩缩容问题实际进入研究时再选用对应例子。
3. 多云/复杂多集群、快照、暂停恢复的全部实现，以及每种隔离运行时。
4. Kubernetes 上游调度器、etcd、完整 CNI/CSI 和 Go 全语言体系。

原来的 12 组材料保留为索引，不另外形成十二项必读任务。测试、日志和性能观察贯穿上面五项，不新增另一套课程。

## 4. 下一次从哪里开始

建议新 Kubernetes 主题的第一步从 SandboxReconciler.Reconcile 定位，再展开 reconcileChildResources 的正常路径。当前先问：**已有一份 Sandbox，控制器怎样保证对应 Pod 存在，并把观察状态反馈出来？**

第一次只接通核心对象、Pod、状态与重新协调；服务、存储先说明用途，需要时再进入对应实现。不要同时追完 WarmPool、Claim、隔离和全部失败分支。

2026-11-05 用户授权不必延续 Slime 的跨主题规则，现已开启独立的 [Kubernetes 主题](../topics/kubernetes-sandbox-control/README.md)与[本主题 Step 000](../topics/kubernetes-sandbox-control/steps/step-000-sandbox-reconcile/01-scope.md)。旧 Fleet 步骤已归入 [Fleet 主题](../topics/fleet-environment-orchestration/README.md)，保留原内容；主题内独立编号，跨主题只按需引用旧材料，不自动整套继承。此前 Step 002 和跨主题合并的[方案](../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/agent-sandbox-topic-grouping-proposal.md)保留为讨论历史。

## 5. 记录与验证边界

- 固定源码版本：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1；本轮已核对上述入口和代表材料在本地存在。
- 这是学习选题和顺序，不是已掌握清单；各步开始时再确定当轮问题、短期卡与停止点。
- 本轮没有部署集群、改变资源、运行负载或宣称岗位能力已经达成。JD 中的实际集群经验需要真实证据，不能由文档生成替代。

<a id="helper-reading-depth"></a>

## 辅助函数读多深：沿用五项主线，不增加全函数通读要求

2026-11-05，用户询问其余小函数是否还需阅读，或对混元岗位可以跳过。判断依据是 JD 中的集群开发/部署/排障，以及并发、资源和行为一致性要求；JD 没有指定本仓库的必读函数名单。

1. **影响正确性的行为需要弄清。** 资源归属、就绪判断、创建冲突、失败与清理不能只记函数名；先理解输入、判断与结果，遇到对应主线时展开关键分支。函数很短也可能决定是否误用别人的资源。
2. **存储和网络等模块按场景深入。** 当前 reconcilePVCs 与 reconcileService 的职责、对象和交接已作为背景；后面真的研究挂载或访问问题时，再看相应创建、归属与异常路径，不要求现在通读全部实现。
3. **纯转换和辅助操作按接口理解。** NameHash 的具体哈希算法、格式化、日志等先知道输入输出和用途即可，除非实际问题落在它们身上。

当前读 reconcilePod 的理由，是把“协调资源”落到查询、组装、归属和 API 创建。sandboxOwnedPods 等辅助函数按当前查询所需理解，不另拆成一串必读步骤。后续仍沿五项范围推进，而不是以读完多少函数衡量岗位准备程度。
