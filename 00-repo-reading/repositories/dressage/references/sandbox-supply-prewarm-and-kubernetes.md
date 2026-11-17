# 从 Environment.start 到 Kubernetes 沙箱供给

2026-11-17：接续[接口地图](harbor-sandbox-interface-map.md)。本页保存用户新提出的系统问题与助手核对，不表示已实现适配、运行实验或完成 Agent Sandbox 既有步骤。

## 当前问题

用户希望借鉴 DeepSeek Elastic Compute（DSec），理解 Kubernetes 怎样承接沙箱系统、Agent Sandbox 是否支持预热、Environment.start 怎样取得为题目提前准备的环境，并在这一条链中学习 Kubernetes。

这次的观察单位是“一份环境需求怎样变成一个可用沙箱”，不是继续枚举 BaseEnvironment 方法。

## DSec 提供问题视角，Agent Sandbox 提供 K8s 实现路径

[DSec 原论文第 3 节](https://arxiv.org/html/2609.22978v1#S3)描述自己的 IAM、apiserver、placement engine、watcher、节点 edge 及运行时/3FS 体系。不能把该论文直接解释成 Kubernetes WarmPool 实现。其环境分层、镜像分发、资源密度、状态保留与训练协同提示了完整系统的问题范围；本轮先落实环境供给主线，不把这些都扩成必读前置。

[Agent Sandbox 官方说明](https://github.com/kubernetes-sigs/agent-sandbox/blob/main/README.md)明确提供 SandboxTemplate、SandboxWarmPool、SandboxClaim，以及负责实际沙箱资源协调的 Sandbox。底层隔离依赖配置的运行时，并非建一个 CR 就自动获得任意隔离能力。

## 同一个例子：一道题要跑三次

教学假设：题目 A 的仓库初始版本与依赖已经做成镜像 image-A，三次尝试需要三份互不污染的环境。以下名称、数量为示意，并非部署 YAML。

```text
运行前：应用侧知道将要使用 image-A
    → 选择模板 template-A（镜像 + 资源 + 运行配置）
    → 提前建立 pool-A，目标备用数 3
    → WarmPool controller 创建备用 Sandbox
    → Sandbox controller 协调 Pod
    → K8s scheduler 选择节点，kubelet/运行时启动容器
    → 观察到三份环境可用

某次 Trial 开始：Environment.start()
    → 按同一环境规格确定 pool-A
    → 经 Kubernetes API 创建本次的 SandboxClaim
    → Claim controller 分配兼容的备用 Sandbox
    → 等待 Claim 状态与实际执行通道可用
    → Environment 对象记住所分配资源，start 返回
    → Harbor 继续 Agent.setup / Agent.run

领取后：pool-A 的备用成员减少
    → WarmPool controller 按目标、容量与速率等条件补充

本次结束：Environment.stop()
    → 根据策略删除/保留本次 Claim 及相关资源
    → 使用过的环境不因此自动成为干净备用环境
```

这些 controller 通过 API 中的对象、状态和 watch 事件协同，不是 Environment.start 在同一 Python 调用栈中逐个调用 Go controller。资源不足或环境不兼容时，热领取可能失败或转入冷创建/等待路径，不能保证每次立刻可用。

三份备用只是教学目标；spec.replicas 不保证三份都 Ready，也不是整个系统最大并发数。已领取环境和备用环境会共同占用集群资源。

## “提前准备好”要分三层

| 准备层次 | 已经有什么 | 还不能据此推断什么 |
| --- | --- | --- |
| 镜像已构建 | 仓库初始内容、依赖等可复用材料 | 节点已经下载镜像、容器已经启动 |
| 沙箱已预热 | 模板所描述的环境已提前运行 | 题目专属动态文件和 Agent 安装都已完成 |
| 本次尝试初始化完成 | 按需要注入题目文件、配置、Agent 等 | 可以与其他尝试共享同一份可写状态 |

Kubernetes 不认识题目文本。应用/适配层要把题目映射为环境规格，并确定兼容的池；相同规格可复用同一池，不必每个题目 ID 都建一个池。要预热哪种规格、保留多少份、何时提前提交，是需求侧策略。

若直到第一次 start 才创建池，第一次请求仍可能冷启动。要隐藏第一批启动开销，应在 Trial 请求前提交池并观察就绪。预热增加驻留资源占用，不消除容量限制。

## 现成示例及证据边界

[官方 Harbor / Terminal-Bench 示例](https://github.com/kubernetes-sigs/agent-sandbox/blob/main/examples/harbor-terminal-bench/README.md)描述按题目镜像和 Pod 规格生成模板/池，在 start 中创建 Claim 并等待可执行；以 warm_replicas 配置预热数量。示例采用 Pod exec 与 tar 执行和传文件；它不是所有 SDK 的唯一访问方式。

示例文件是使用设计的依据。此前核对仍未取得它引用的完整 Harbor adapter 包，故不能声称本地已具备运行实现。Harbor BaseEnvironment.start 的接口返回 None；本轮图中的“取得环境”指适配对象建立并保存后续操作所需的连接/资源身份，不是要求它向 Trial 返回一个新 Sandbox 对象。

当前在线 controller main 与旧阅读固定提交分开：本轮在线核对用于说明机制，不覆盖既有函数卡的固定行号。

## 对应要学习的 Kubernetes 知识

| 当前问题 | Kubernetes 知识 | 现有阅读入口 |
| --- | --- | --- |
| 为什么 Python 发出请求后别的组件会行动？ | API、CRD、自定义对象、watch、controller/reconcile | [协调循环](../../kubernetes/01-architecture/reconciliation.md) |
| 谁把环境放到某台机器上？ | Pod、Node、scheduler、kubelet、容器运行时 | [Pod 与节点、就绪](../../kubernetes/03-workloads/pod-node-and-readiness.md) |
| 为什么创建成功还要等待？ | spec、status、Ready | [对象与状态](../../kubernetes/02-resource-model/objects-spec-status.md) |
| 两个 Trial 怎样各得一份，结束谁负责删？ | Claim 绑定、UID、ownerReference、并发更新 | [身份与所有权](../../kubernetes/02-resource-model/ownership-and-identity.md) |

建议下一处从“一份 Claim 如何取得环境”进入，再回查“池如何补充”。可复用既有 [Claim scope](../../agent-sandbox/topics/kubernetes-sandbox-control/steps/step-005-claim-ownership/01-scope.md) 与 [WarmPool scope](../../agent-sandbox/topics/kubernetes-sandbox-control/steps/step-004-warmpool-reconcile/01-scope.md)，不新增重复步骤。原 Step 003 尚未完成的状态写回问题保留，不因推荐新入口就标记完成。

## 核对来源

- [DSec 原论文](https://arxiv.org/html/2609.22978v1)，本轮只用架构与问题范围，不推断其采用 K8s。
- [Kubernetes components](https://kubernetes.io/docs/concepts/overview/components/)，API server、scheduler、kubelet 与运行时职责。
- [WarmPool controller](https://github.com/kubernetes-sigs/agent-sandbox/blob/main/extensions/controllers/sandboxwarmpool_controller.go)，成员统计、Ready 统计和补池分开处理。
- [Claim controller](https://github.com/kubernetes-sigs/agent-sandbox/blob/main/extensions/controllers/sandboxclaim_controller.go)，reconcileActive/getOrCreateSandbox、兼容候选领取与冷创建。


<a id="api-server-pressure"></a>

## 2026-11-17：高并发是否会压垮 Kubernetes API server

用户追问：“但是 k8s 原生的 api server 可能会被打爆吧？看一下 agent sandbox 是怎么解决的，如果碰到高并发的场景。”

结论：有这个风险，Agent Sandbox 没有绕开 Kubernetes 的控制面上限。预热把 Pod 创建从领取关键路径提前，但每次 Claim 的创建、绑定、状态、后续补池与删除仍会产生 API 流量。存活环境数量、每秒新建/销毁数、每秒命令数是不同指标；不能用并发环境数替代创建吞吐。

本轮依据在线 main 的代码与官方文档核对，未取得该 main 对应的固定 SHA，不能将这些新选项反写成旧固定版本已经具备，也没有进行压测。

### 已有的减压措施

| 措施 | 实际作用与边界 |
| --- | --- |
| 按池维护内存候选队列、缓存索引 | 少做候选扫描；领取最终仍需 API 写入及归属冲突保护，内存 pop 不等于完成全局绑定 |
| watch 事件过滤 | Claim controller 的池 watch 过滤 status-only 变化，避免每次池状态变化重新唤醒所有相关 Claim |
| expectations | 已发出创建但缓存尚未观察到时，不重复补同一缺额；防止缓存滞后引发重复创建 |
| MaxRefillRate | 按池令牌桶控制创建速度；不是集群总限额，多池流量仍会叠加 |
| ReplenishDelay | 把补池推迟到领取突发后；持续流量会反复重置延迟，可能耗空池，不能泛化为持续负载推荐 |
| 可选关闭 Events / observability annotation 专用写入 | 减少附加 API 写；需要接受相应持久化可观测信息的取舍 |
| 独立 watch 连接 | 降低写入突发对缓存事件交付的连接级干扰；多连接提升客户端可发并发，不会提高 etcd 的物理能力 |
| APF 配置 | 在服务端分开关键绑定写入、批量补池、事件流量，给关键路径保留并发容量；须运维侧显式应用，不是默认安装自带保证 |

来源：[内存队列](https://github.com/kubernetes-sigs/agent-sandbox/blob/main/extensions/controllers/queue/simple_sandbox_queue.go)、[Claim controller](https://github.com/kubernetes-sigs/agent-sandbox/blob/main/extensions/controllers/sandboxclaim_controller.go)、[WarmPool controller](https://github.com/kubernetes-sigs/agent-sandbox/blob/main/extensions/controllers/sandboxwarmpool_controller.go)、[配置](https://github.com/kubernetes-sigs/agent-sandbox/blob/main/docs/configuration.md)、[APF](https://github.com/kubernetes-sigs/agent-sandbox/blob/main/docs/apf-insulation.md)。

### 两种负载必须分开

```text
短突发：已经有一批 Ready 环境 → 集中领取 → 后续补齐
持续流：不断领取 + 不断补齐 + 不断回收 → 全链路持续写控制面
```

若领取速度长期超过实际补充 Ready 环境的速度，任何有限预热池都会耗尽。教学估算：原有备用 N，领取速率 λ，实际补充速率 μ，且 λ > μ 时，耗尽时间约 N / (λ - μ)。这是简化模型，忽略启动时延变化和失败，不是项目性能测量。

[官方性能文档](https://github.com/kubernetes-sigs/agent-sandbox/blob/main/docs/performance-tuning.md)记录了热领取突发与持续补池的不同瓶颈，也记录过 watch 延迟、etcd 增长和请求冲突。其 benchmark 依赖特定集群与配置，不能转换成任意集群的保证。该文档还报告某些写合并配置虽然减少冲突，却使持续负载延迟变差；不要把“有优化参数”当成全部打开就更快。

默认值同样重要：本轮 main 的 kube-api-qps=-1 表示未启用该客户端限流，max-refill-rate=0、replenish-delay=0 都不启用对应整形；APF overlay 需额外应用。不能声称默认部署已经进行了全局请求限速。

### 当前接入应该验证什么

建议先看“固定到达速率下，领取 p95/p99 与 Ready 备用数能否稳定”，同时观察 API 请求时延、429、409、APF 等待、controller 队列及 watch 延迟；再逐项调整。控制器 worker 数和 HTTP 连接数变大可能增加控制面压力。必要时增加控制面容量或按集群划分负载；仅把池拆成多个仍共用同一 API server，不等于解除控制面上限。

此前 Harbor 示例用 pods/exec 与 tar 执行命令和传文件，因此执行流量也可能经过 API server。以后选数据通道时要把生命周期操作与高频命令/文件 I/O 分开评估，不能只测 Claim 创建。当前没有据此更改后端或部署配置。

本轮先保留此系统边界；不自动新增性能专题或预建函数卡。


<a id="image-preparation-and-warm-pools"></a>

## 2026-11-17：预热是否避免大镜像下载

用户追问池中镜像是否提前准备、是否仍需下载大量内容，以及工业界怎样处理重型镜像。

需要区分：镜像在仓库中已构建；镜像内容在目标节点已缓存；使用该镜像的环境已经运行并可领取。WarmPool 管理第三层的备用环境数量，不负责自动把未定义的题目依赖做进镜像。首次填池、扩容到无缓存节点仍可能拉取大镜像。命中已运行环境通常不需为领取再拉一次镜像，但之后的 pip/npm/git、动态题目文件、挂载数据以及懒加载尚未读到的内容仍可能访问网络。

```text
镜像构建并发布 → 节点获得启动需要的镜像内容 → 启动并准备环境
                                                      ↓
                                                   池中待领
                                                      ↓
                                             start 为本次领取并等待可用
```

普通完整拉取把镜像下载等待放在启动前；预热把启动工作放到任务请求前。二者都不自动消除数据传输量。节点缓存是节点局部的，不能假设任意新节点都有镜像；同节点可复用已有内容，Always 拉取策略也不意味着每次重传全部内容。依据：[Kubernetes 镜像文档](https://kubernetes.io/docs/concepts/containers/images/)。

可组合的生产机制：

- 稳定依赖和环境材料提前构建/版本化；通过镜像缓存、节点预拉取减少重复准备。
- 对频繁使用、延迟敏感的环境保留适量热实例，付出驻留资源成本；由任务需求决定预热规格与数量。
- 大规模相同内容分发可采用 P2P，Dragonfly 是实际项目，但并非 Agent Sandbox 默认包含的能力。[Dragonfly](https://github.com/dragonflyoss/dragonfly)
- 大镜像可以通过懒加载缩短启动等待。GKE Image streaming 在按需提供内容的同时，后台拉取完整镜像并缓存，因此不能说它必然减少最终总下载量。[GKE 官方说明](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/image-streaming)
- DSec 将基础环境、workspace、工具层独立版本化，并以 EROFS/3FS 等机制按需取得内容；这是专门的平台设计，不能归为 Agent Sandbox 自带功能。[DSec 第 5 节](https://arxiv.org/html/2609.22978v1#S5)

上述是有资料依据的机制和可选取舍，不表示所有公司采用同一组合。对当前项目建议先测无缓存启动、节点缓存启动和预热领取三种耗时；根据实际瓶颈选优化，不把所有存储技术变成新必读范围。本轮只有文档核对，没有下载镜像或实际部署测量。
