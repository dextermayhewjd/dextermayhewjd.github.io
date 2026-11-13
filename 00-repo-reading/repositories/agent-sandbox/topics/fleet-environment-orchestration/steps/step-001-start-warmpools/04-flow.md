# 04 · Step 001 的实际阅读过程

## 2026-11-04 · 确认开始环境准备主题，先建立 scope

上一轮推荐：以 SandboxFleet.start_warmpools 为下一入口，从 setup 的调用位置接回，阅读资源计划怎样进入预热与就绪等待。

用户本轮明确要求：

> 好的
> 那么我们开始吧
> 开一下下一个step的scope吧

据此建立 Step 001，首读 start_warmpools:1144–1192；首轮聚焦 entries、预算分波和 wait，最多按问题下钻到 _warm_entries、_warm_entry 两层。资源接口与 Kubernetes 控制器保留整体位置，不在本轮继续展开。

已核对源仓库根目录 /home/fredkeira/projects/agent-sandbox，HEAD 为 37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1，工作区干净。建立 scope 是助手的静态准备；尚未把内部机制记成用户已理解，也未执行集群操作。

按前一步 03 + 02 继承五张函数/方法卡和一张类卡，完整保留原话、未知与来源，并重算相对链接。Step 000 原文件保持不变；其备用记录继续作为原步骤资料，不伪装成本步新读内容。当前 02 只有入口说明，待实际带读再建对应卡片。

<a id="setup-first-card"></a>

## 用户选择先打开调用方 setup

用户明确：

> 好的那么看一下吧
> 这里我是在fleet.setup()
> 中遇到的这个fleet start warmpools对吧
> 那么我是否可以理解为这里我需要掀开一个这里的这个fleet setup
> 然后在考虑一下别的部分呢?
> 掀开第一个函数卡吧

按这个选择，将 Step 000 备用区的 SandboxFleet.setup 卡复制到本步 02，保留原始版本、原话、认识时间与未知；原文件和本步 03 快照不变。卡片前面增加本轮的最小主线：preflight → plan → start_warmpools → return self，原完整七段代码与说明折叠保留。

当前只回查 setup 作为调用方：它完成检查与规划后调用 start_warmpools(wait=True, create_budget=create_budget)，后者返回后 setup 才返回同一个 Fleet，run_naive 才继续执行器。入口处退出清理注册、状态重置与可选预拉取仍在完整卡片中，未删掉或标为已理解。

scope 只移动当前标记到 setup 并链接新卡，原有全局图和后续入口保留；没有提前创建 start_warmpools 或更深层的函数卡，也没有执行集群操作。


## setup 的第一轮复述：plan 是否是策略

用户表述：

> 好的我简单理解一下这里的setup吧
> 这里的set up其实需要考虑一下teardown hooks
> 我的理解是删除的时候需要做的事情
> 这里在运行的时候初始化的时候先做这件事情其实也挺好的
> 然后考虑一下这里的preflight的内容
> (关于集群)
> 然后再看一下这里的这个plan我不知道是什么
> 人物配置的plan
> 是native 或者其他strategy的plan吗?
> 然后就是这里的start warmpools
> 我的理解应该是需要考虑加入预热的情况下的操作
>
> 我的理解准确吗?

用户已能沿 hooks、preflight、plan、start_warmpools 的顺序定位问题。助手校准：hooks 预先注册进程退出时的清理安排；preflight 检查集群及运行条件；plan 按镜像计算集群、模板、池与副本数量，是资源计划，不是运行策略；外层 run 已选择 naive。当前 setup 的 start_warmpools 调用不受 prepull 开关控制，prepull 只控制独立的镜像预拉取。

静态依据为 fleet.py:363–405 的退出处理入口、plan/_plan:810–869 的 PlanEntry 生成，以及 setup:1403–1423 的调用次序。具体规划算法仍不展开，未新增方法卡或更改当前阅读范围。

<a id="setup-section3-unified"></a>

## 第 3 部分合并为完整源码与单套编号

用户指出“这里三的源码对照我觉得反而是不用压缩的? 展开我觉得很好”，并明确认可现有 preflight、plan、start_warmpools、return self 的逐项说明，希望从工程和认知可用性的角度重构第 3 部分。

本轮判断：setup 较短，读者正对照真实源码，完整可见的函数体能帮助定位；此前简版四步与折叠完整版七步并存，同一调用的编号不同，增加查找负担。这里应统一对应关系，而不是继续删减语句或增加一套结构。

已将第 3 部分改为完整函数体 → [1]–[7] 同号解释 → plan/strategy 的必要对照 → 按需展开的辅助来源。用户认可的四段解释原文保留，编号对应完整源码的 [3]、[4]、[6]、[7]；退出注册、状态重置与可选预拉取也在同一顺序中可见。下一下钻点明确为 [6] start_warmpools。

完整旧卡保存在 [重构前快照](references/history/2026-11-04-setup-before-unified-section3.md)。本次只改 setup 卡的呈现，scope、继承记录和阅读范围不变，版式反馈不等于技术机制已掌握。

<a id="start-warmpools-entry"></a>

## 进入 setup 的第 [6] 项：start_warmpools

用户反馈：

> 好的 我觉得这里的逻辑没有问题
> 那么我们是否考虑做下一个部分的内容呢?

按既定导航进入 SandboxFleet.start_warmpools，新增本步第二张短期卡。沿用完整函数体与同号解释，当前聚焦预算读取、计划条目、分波提交和等待位置；_warm_entries 暂按接口理解，不同时展开线程分发或单池创建。

卡片将 plan 与 start_warmpools 分开：前者给出每个镜像池的放置和副本目标，后者按条目目标副本数分组提交。以预算 5、条目副本数 3/3/2 的教学输入说明循环；明确这不是默认 1000 配置下的真实运行，也不是新构造的业务函数。中间波强制等待、末波沿用 wait、超大单池独占一波、上一波的环境不会因提交下一波而自动删除，均按源码注明。

scope 只更新当前位置与卡片链接，前序路径保留。Step 000 与本步 03 未修改，没有创建后续辅助函数卡或运行集群任务。


## 回到基本概念：warm、warm pool、wave 与 RL 需求

用户反馈：

> 主要这里其实我都不是特别清楚
> 这里的warm到底在组队偶尔是什么呢?
> 以及这里的wave又是什么呢?
> 我其实不是特别理解
> 因为如果是agentic rl的话
> 那么这里的start warmpools
> 不是应该是根据一共load了哪些tasks
> 看到底执行了哪些还需要预热哪些这样子来决定的吗?
> 为什么这里还有这个warmpools呢?
> 其实我没有特别理解

此前过早从预算和分波循环开始，用户尚未明确 warm 的对象。助手本次先区分准备动作、备用环境池和临时提交批次，使用计划 A/B 各 2 副本、预算 2 的教学假设串起它们。

源码核对说明：load_tasks→plan→setup/start_warmpools→executor 是当前 naive 启动顺序，start_warmpools 此时不根据本批已完成任务进行需求预测。执行阶段的池内备用补充由 Kubernetes 控制器处理；持续 RL 的批次需求需训练侧提供，LookaheadWarmer 可管理已报告需求，和资源创建波次不是同一层。

解释补入当前函数卡，scope 只更新本轮问题为概念校准，没有改变完整阅读路径或切换到 LookaheadWarmer 的实现，也不将澄清自动记为用户已理解。


## 先解释预热池到底准备和维护什么

用户继续追问：

> 那么这里的这个预热池在做的是什么呢?
> 我其实没有特别理解这件事情

本次暂缓 wave 与预算，只解释具体对象：预热池按模板维护尚未被任务领取的备用沙箱环境。教学例采用备用目标 3：任务领取 1 个后，备用数变为 2，已领取环境用于任务，控制器再补充备用。这区分了基础环境就绪与题目开始执行，也区分备用目标与总运行数量。

对照仓库 warmpool-quickstart 的模板、池和 Claim 示例及已核对控制器职责，没有部署或领取真实环境。说明补入当前函数卡的入口背景；当前仍未确认用户理解，不进入新函数。


## 不同任务的环境如何分别预热

用户追问：

> 但是每一个任务可能需要的环境不一样?
> 这样子怎么预热呢?
> 我不是特别理解

当前结合 image_counts、_plan 与 _acquire_reserved 核对：预热前已有 Task 列表，image 字段提供环境镜像信息；同一镜像归到相应池，不同镜像分别形成计划和池。当前非复用路径按任务领取独立环境；共享镜像池不表示共享同一可变沙箱。题目文件或任务状态由领取后的初始化处理。

教学例子用 T1/T3 的 python-env:v1 与 T2 的 browser-env:v1 表示两种池，不将示例当作实际数据或副本数推导。若每题镜像不同也能按已知需求预热，但同时驻留成本增加；当前 Fleet 不自动将任意 metadata 差异解释成环境规格。说明补入当前函数卡，未新增分组算法卡或改变后续阅读范围。


## 从术语转回设计目的：独有镜像是否适合池化

用户明确要求：

> 对啊 我的理解就是 如果每一个人物需要的是不同的镜像 那么这里的预热池子的逻辑是什么 这里的fleet没有完全解释这个问题
> 或者说这里的这个fleet的start warmpool没有解决这个问题
> 我希望你告诉我的是当前的这个结构到底解决的是怎样的一个问题
> 我需要知道的是这个

此前答复连续解释了池、镜像分组与 wave，却没有正面回答全异且单次镜像下为何采用池。此次通过 _plan、compute_replicas、naive 调用顺序和 start_warmpools 确认：该路径提供已知需求的环境供给，当前函数组织计划提交，而不承担按训练进度决定保留哪些镜像的职责。每题镜像不同、仅用一次时，不存在跨不同镜像互用同一备用环境的收益，先准备全部环境也不保证整批更快，并可能出现额外备用补充。

完整说明补到项目 reference 的“每个任务独有镜像时，这套结构解决什么”，当前函数卡保留定位与引用。没有修改函数阅读顺序或将其他策略自动加入当前精读。


## 任务选择与环境领取的方向

用户追问：

> 或者 我更加想要知道的是 这里到底是如何做到让 任务端口是根据已经热好的内容来获得任务的 否则就会碰到到底是预热池子等命中 还是这里直接通过已经热好的池子来领取任务 这里是怎么做的呢 能看一下吗?

按请求核对 process_parallel → acquire/_acquire_reserved → SDK Claim → Claim controller 的接口与关键分支。当前是先选定 Task，再按 task.image 找计划中的 cluster/pool，通过 warmPoolRef 定向申请环境；不是观察现成环境反向挑选任务。控制器优先采用可用 Ready 候选，没有时可能采用未就绪候选并等待，或走模板冷创建；SDK 等到 Claim 已绑定且 Ready 才返回 handle，随后调用 process_fn。

完整接口、源码片段与冷暖路径保存在 [任务怎样领取预热环境](references/task-to-warm-pool.md)。这是为当前概念疑问所做的跨接口核对，不额外建立下一 Step 或批量创建函数卡；start_warmpools 的原阅读路径保留。


## 按用户要求比较本地 Dressage

用户问：“那么看一下本地的dressage吧 是否可能实现更加好呢?”

本次找到当前本地 /home/fredkeira/projects/Dressage，提交与既有阅读记录相同，工作区干净。重点核对异步 worker、PrewarmScheduler、PrewarmStore 和 blackbox_dispatch：Dressage 可以为后续的具体 sample 提前初始化环境，并按 session_id 精确交接；更贴近独有环境的任务前瞻。它仍按预取组 FIFO 派发，claim 会等待选定 session 的初始化，未实现只挑 Ready 任务。

结论、代码入口、provider 限制和局部实验记录见 [Dressage 对照](../../../../references/dressage-prewarm-comparison.md)。实验仅使用原始类定义与假的 provider，未调用 E2B 或集群；正式 pytest 测试因当前环境依赖不齐未运行。本次没有修改源码、创建 Dressage 新步骤或标记其函数已掌握。


## 对照后考虑将精读重心放到 Kubernetes 侧

用户问：

> 那么你觉得这里的agent_sandbox
> 是否可能更加适合的部分是看一下这里是如何控制k8s集群的部分呢?
> 感觉这里warmpool的机制或许不如dressage?

助手建议认可阅读投入的调整方向，同时区分层次：Dressage 的任务组前瞻适合研究 RL 任务需求；Agent Sandbox 的核心控制器、WarmPool controller 和 Claim 更适合研究 Kubernetes 工作负载及分布式资源生命周期。不能用 naive Python 示例与 Dressage 调度层的对比判断底层池协调机制整体优劣。

已核对核心 Sandbox 控制器的 reconcileChildResources 会协调 PVC、Pod、Service，并计算状态；WarmPool 的补充流程含期望数量、速率和缓存 expectations 等控制。下一入口建议 Reconcile→reconcileChildResources，先建立单个 Sandbox 的底层骨架。详见 [阅读投入建议](../../../../references/dressage-prewarm-comparison.md#reading-investment)。本轮只保存建议，既有 scope 和函数卡未改，也未创建新步骤。


## 对照完整 JD 确认 Kubernetes 方向的投入价值

用户继续询问 Kubernetes 内容是否更符合腾讯混元岗位。已回查完整岗位原文：Kubernetes/容器化及集群实践为明确要求，并发、资源和行为一致性为明确职责。建议将本仓库后续精读转向资源模型与控制器，以补充现有 Slime/Agent 链路；Python 任务级预热继续参考 Dressage，不将不同层实现简单排名。

[完整对照](../../../../references/rl-environments-and-jd.md#kubernetes-priority-for-tencent)保存投入边界：读源码不自动等于部署排障经验；复杂平台专题按需进入。当前仅确认选题依据，未迁移主题、创建新步骤或运行集群。


## 用户确认以 Kubernetes 沙箱工程能力为后续目标

用户说：

> 好的 把这个作为目标吧
> 那么你会考虑让我看哪些内容呢?
> 在这个agent sandbox的repo里面

据此将当前目标与五项主线保存到 [腾讯岗位导向范围](../../../../references/tencent-k8s-learning-scope.md)：单个 Sandbox 的创建与状态，WarmPool 的数量协调，Claim 的领取与回收，访问与隔离，一个部署排障闭环。下一入口建议核心 Sandbox 控制器，未创建控制器函数卡或提前运行实验。原 Step 001 未展开部分继续保留，不因改重心伪装成完成。
