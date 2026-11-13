# 04 · 本步理解形成过程

[本步入口](README.md) · [范围](01-scope.md) · [短期函数](02-short-term-memory/overview.md) · [累计快照](03-long-term-memory/overview.md)

## 前一步带来的模型

用户已经把 `_reconcile_once` 概括为检查 Job 是否存在、当前情况如何、是否需要修改 Gateway 记录；[原话与校准](../step-000-k8s-controller-entry/04-flow.md#reconcile-purpose-confirmation)留在 Step 000。此前各字段与分支的未知也一同继承。

随后用户明确选择 `_watch_jobs_loop`，已经开始阅读观察范围、`event_type` 与 Job 对象、`obj.raw` 的交接；[首次阅读记录](../step-000-k8s-controller-entry/04-flow.md#watch-jobs-loop-reading)继续保留在原处。当时尚无对本函数行为的个人复述。

<a id="step-001-created"></a>

## 2026-11-03 · 将已开始的事件接收问题独立建步

用户提出：

> 好的 那么是否应该考虑一下构建一下这样子的一个step 了呢?

本轮沿用前一轮已经确认的函数与范围，建立 Step 001“接收 Kubernetes Job 事件”。划界依据是从单轮状态核对，转到持续接收事件与交给处理函数；没有把 `_handle_job_event` 内部自动扩展成已经阅读的内容。

记忆处理按现行规则执行：Step 000 的 `03` 无函数条目，`02` 有 7 份卡片，全部完整继承至本步 `03`。其中包括 watch 的首次阅读卡，因为阅读已经实际发生；尚未有个人复述的状态如实保留。随后仅将 watch 从本步 `03` 调入 `02`，继续记录本轮的新问题。原话、首次接触、最近认识更新、源码版本与原始形成过程链接保持可追溯。

本次调整目录与导航，不算新增技术理解。Step 000 保留原卡与原始对话；本步继续采用两份数据的既有背景和就地注释，不启动 Hugo 或集群服务。

<a id="watcher-event-and-target"></a>

## 2026-11-03 · watcher 给出什么，下游更新哪一边

用户联系 namespace、label selector 与此前的 Job 列表查询，询问是否观察所有 Job；对 watcher、event_type、obj 明确表示不理解，又猜测 `.raw` 是处理 Job 数据、下游可能更新容器状态或本地目录。[完整原话](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._watch_jobs_loop.md#watcher-and-update-question)在本步短期卡保存。

助手确认筛选关系并补准：kr8s 是 Python 的 Kubernetes 客户端库，asyncio 是它的异步接口；观察目标仍是指定 namespace 且标签匹配的 Job。之前由列表推导式收集 Job，这里 watcher 持续提供事件，每项是一对事件类型与 Job 对象。`.raw` 是读取对象数据，未处理或修改容器。

沿同一 r1 例子核对下游合同：假定 Gateway 记录仍为 RUNNING，MODIFIED 事件携带 Complete/True 的 Job；处理函数从标签读任务 ID，并经 `_patch_status` 请求 Gateway 更新该 rollout 为 SUCCEEDED。没有在这条路径中修改 Kubernetes 容器或磁盘目录。此处只解释交接的用途与更新目标，未展开处理函数的完整分支或另建卡片。

本次只更新 Step 001 的短期卡、过程与入口，入步时的 `03` 快照及 Step 000 原卡保留。用户尚未确认这些补充，未访问真实服务。

<a id="handle-job-event-reading"></a>

## 2026-11-03 · 独立进入 _handle_job_event

用户明确提出：

> 那么我们是否需要看一下这里的handle job event 的内容了呢?

本轮从 watch 的 `obj.raw` 进入处理函数，按已发生的阅读选择建立[函数卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._handle_job_event.md)。沿用上一次 r1 的成功事件：从标签取 rollout ID 与 attempt ID，从条件取 Complete/True，再请求 Gateway 更新为 SUCCEEDED。正常场景假定 Gateway 原状态为 RUNNING；无真实请求。

为保持调用处可就近回查，完整调取 `_patch_status` 到本步 `02`，补成功事件的调用输入与请求体，保留原来的缺失 Job 场景、原话和未知。`03` 的七份入步快照不变；watch 父卡仅保留接收与交接，内部实现放在子卡。

处理函数的无任务标识、无条件、未成立或不匹配的条件、成功/失败回写与 return 按源码保留。与周期协调不同的计数兜底和中间转换情况只列为边界，本轮先走通成功路径；用户尚无对函数内部的个人复述。

<a id="polling-versus-event-feedback"></a>

## 2026-11-03 · 为什么两条路径都在更新 Gateway

用户明确表示想先知道 `_handle_job_event` 的职责，发现它与 `_reconcile_once` 中逐条匹配 rollout/Job 后更新 Gateway 的行为相似，询问功能是否混合。[完整原话](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._handle_job_event.md#overlap-question)保存在当前函数卡。

本轮确认共同点确实存在：成功/失败条件的识别与终态回写在两处各有实现，HTTP 请求共用 `_patch_status`。区别是周期路径主动查询本轮选中的任务与 Jobs，从任务找 Job，还承担创建、缺失 Job、RUNNING 及计数兜底；事件路径处理已经取得的一份 Job，从标签找任务，只按成立的 Complete/Failed 请求回写终态。`run()` 并行启动两条路径，二者不是直接调用关系。

用同一 r1 已完成场景在[本步职责对照](README.md#polling-and-job-events)展示两种到达同一回写的方式。事件及时到达时可较早反馈；事件未成功处理但任务仍被查询选中且 Job 尚在时，周期核对可以补齐。这是依据源码归纳的作用，未宣称所有失败时序都能恢复。

为就近比较，完整调取 `_reconcile_once` 到本步 `02`，保留原卡与 `03` 快照。说明重复更新可能被服务端状态转换检查拒绝，并将条件/计数、中间 RUNNING 与 Job 名写入等差异折叠保存。查阅的控制器配置文档与现有 K8s 单测没有提供两条路径可靠性的完整证明，本轮不把设计用途当作已运行保证。

用实际两个函数配合内存边界做了三组请求对照：RUNNING + Complete/True 时都请求 SUCCEEDED；QUEUING + Complete/True 时周期路径先请求 RUNNING 再请求 SUCCEEDED，事件路径直接请求 SUCCEEDED；只有 succeeded 计数时，周期路径可请求成功，事件路径不处理。该检查只观察请求内容，不模拟服务端转换校验；695 处本地链接与锚点通过核对。

用户识别的重叠与源码一致，职责分工和必要性的解释尚待反馈；未修改应用代码或运行集群。

<a id="overlap-scope-audit"></a>

## 2026-11-03 · 严格区分共同效果、覆盖差异与局部重复

用户要求再次仔细判断，避免顺着其猜测给出宽泛的“重复”结论。[完整原话](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._handle_job_event.md#strict-overlap-question)保存在函数卡。

本轮重新核对原始两函数、Gateway 的 VALID_TRANSITIONS 与 patch_rollout 校验。通过六组共有 Job 的起始数据和一组无 Job 情景作隔离验证：执行真实控制器函数与真实转换校验片段，数据源、HTTP 边界与持久化使用内存桩。结果表明，RUNNING + Complete/True 时两者可达到相同终态，但请求字段仍不同；QUEUING + Complete/True 时周期路径补 RUNNING 后可成功，事件路径的直接成功请求被拒绝；无终态条件、只有计数、缺少 rollout-id 标签，以及任务已处于终态时也有明显差异。

据此将[本步对照](README.md#polling-and-job-events)收紧为三个独立结论：业务效果有交集；整体覆盖和行为不等价；条件识别、终态映射及失败说明等部分规则确实在两处分别实现。此前“存在代码重复”的说法保留历史语境，本轮明确不把它扩大为整个函数等价、其中一条路径多余，或作者有意/无意重复的判断。

事件较早反馈、周期核对可补齐，是由现有行为归纳的配合作用；未通过作者设计文档确认动机，也未证明所有失败时序均能恢复。所有隔离校验通过，但未连接真实服务。用户尚未反馈是否理解本轮区分。

<a id="status-read-write-keys"></a>

## 2026-11-03 · 先追到具体读取 key 与写入 key

用户要求先看两处究竟查询哪个数据结构的哪个 key，并询问是否修改的不是同一个东西。[完整原话](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._handle_job_event.md#read-write-key-question)在函数卡中保留。本轮将宽泛的职责讨论折叠，优先展示实际取值表达式、数据层级和请求体。

核对结果：周期路径的 `job_status = job.get("status", {})` 加 `job_status.get("conditions", [])`，与事件路径的 `job.get("status", {}).get("conditions", [])`，读取同一种 Job.status.conditions 数据。两者都读取每条条件的 type、status，以及失败时的 reason/message；前者额外使用 Job 的 succeeded/failed 计数和 Gateway rollout.status.state。

两处调用同一 `_patch_status`，该方法使用注入的 AgentLightningAsyncClient 向 `/api/rollouts/{rollout_id}` 发送嵌套 status 的 PATCH。服务端从 body.status 取更新，复制到 rollout.status，再保存 `_rollouts[rollout_id]`。因此相同 ID 下共同写入的状态字段是 Gateway 的 status.state，而非 Kubernetes 的 condition.status；附带字段仍有不同。以成功回写为例，周期路径还发送 k8s_job_name 和 error_message=null，事件路径不提供这两项。

本轮重新核对源码与客户端初始化链；示例请求体依据模型包装与 exclude_unset 静态推导。当前解释器没有 Pydantic，未把本轮请求体展示说成运行序列化的输出，也未连接真实服务。用户尚未确认这些字段关系。

<a id="handler-first-pass-closeout"></a>

## 2026-11-03 · 核对单函数阅读的收束位置

用户询问 `_handle_job_event` 是否已经看完，并表示继续向下看。[原话](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._handle_job_event.md#first-pass-closeout)保存在函数卡。

助手按已确认的本轮范围评估：输入来自 `obj.raw`，标签定位任务，条件判断结果，公共接口回写 Gateway，再 return 回到 watch，这条主流程已讲解至末尾，可以先收束当前函数。此前关于具体读写 key 与职责对照的核对已经保存，不能因用户说“继续”而把所有说明写成个人已掌握。

返回位置是 `_watch_jobs_loop:306` 的 await；处理函数正常返回后，父函数继续 async for，等待下一条事件。下一小段可补父循环的停止检查、异常后的等待与重新观察，再收拢本步关系；这是本步内的接续方向，未创建下一步骤或新函数卡。重复事件、状态写入被拒及与周期路径的并发配合保留后续深入。

<a id="next-topic-job-runtime"></a>

## 2026-11-03 · 调整下一处重点：从状态观察转向 Job 如何启动 Agent

用户提出：

> 但是watch jobs loop外面的还有什么需要单独看的吗?
> 我觉得这一个部分是否不是特别重要
> 我们或许需要看一下别的内容?
> 这一个repo 的角度?

助手按本项目的 Kubernetes 与腾讯岗位学习目标重新评估：watch 剩余的停止检查、异常后重试，以及外层 run 的并发组织，当前先保留职责即可；它们在稳定性与故障恢复时仍有价值，但不是本轮必须继续深入的入口。前一轮提出补外层控制的安排作为候选保留，本轮不继续展开。

从 repo 主线看，已阅读的是 Controller 如何查询、对应并反馈任务状态，尚需补齐的是实际执行配置：任务输入如何进入 Job，Job 的 Pod 使用什么镜像、命令、环境变量和运行约束。推荐下一入口为骨架 [3] `build_job_spec:43`，从已读 `_create_job` 的 manifest 调用回查，并结合 `examples/swe_smith/job-template-openai.yaml` 的真实 Coding Agent 模板。

建议首轮只追“rollout 与模板 → Job manifest → 交回创建函数”：先定位 image、command、任务输入与关联 labels，再按问题补 Gateway 环境变量、超时及清理。模板的 resources、volumeMounts/volumes 是随后理解运行资源与文件来源的入口，不在本轮推荐中一次展开全部基础概念。源模板及训练脚本的 job_template_path 已静态核对，未执行模板、部署 Job 或建立下一步函数卡。

该入口是基于当前缺口的推荐，尚未把 Step 002 或 build_job_spec 记录预先生成；新范围在用户选入时再落地。函数中的状态判断、watch 重连与停止仍保留原有未知，不因暂缓而标为掌握。

<a id="step-002-scope-prepared"></a>

## 2026-11-03 · 按用户要求先生成 Step 002 scope

用户提出：

> 那么请先生成一下这里的这个step002 的scope吧

本轮沿上次已讨论的方向创建 [Step 002 · 从 rollout 与模板构造 Job 配置](../step-002-build-job-spec/01-scope.md)。scope 保留全局 [1]–[5] 的 Reconciler 骨架，将本步定位到 [3] build_job_spec，并按模板、渲染解析、身份与运行约束、Gateway 环境变量、返回提交处给出五个局部阅读入口。

真实输入采用 examples/swe_smith/job-template-openai.yaml，最小回查训练配置如何选择路径、Trainer 侧如何把模板文本放入 rollout 配置；这些是定位证据，不记为已展开 Trainer 阅读。字段细节与具体样本留待函数卡片，资源、挂载、重试与超时的深度按问题控制。

用户本次要求先做 scope，因此 Step 002 当前只包含范围文件；未预建新函数卡或复制累计快照。正式进入本步时再完整继承 Step 001 的 03 + 02，保留原话、未知与来源。本次仅静态核对源码与导航，没有真实运行。

<a id="step-002-breadcrumb-correction"></a>

## 2026-11-03 · Step 002 先交代当前函数与调用来路

用户指出：

> 我们当前看的内容是什么呢?
> 我们在看的具体的函数是哪一个?
> 我们在看的是create jobs?
> 还是在看什么?
> 这里的3.2没有最寻面包屑原则
> 我不知道这里是从哪里长出来的这个问题
> 同时这里的1其实step0
> 然后这里的watch jobs loop其实是这里的step01
> 对吧
> 那么我们这里要看到的是哪一个部分呢?

本轮确认问题来自 scope 定位：此前的旧 [1]–[5] 是函数路标，叠加 Step 000/001/002 容易误读；3.2 又直接给出内部语句，没有先恢复创建调用。修订为明确的步骤归属：Step 000 读周期协调与创建职责，Step 001 读 watch/事件处理，Step 002 回到 Step 000 的创建路径，打开此前作为接口使用的 build_job_spec。

[修订后的 3.2](../step-002-build-job-spec/01-scope.md#caller-breadcrumb) 从 `_reconcile_once` 的无 Job 排队分支接到 `_create_job:259`，在 `manifest = build_job_spec(rollout, self._config)` 右侧下钻；返回后仍由这一行的 manifest 接住，再继续提交。内部骨架移到 3.3，并写出真实函数头。模板改为取到 template 后的回查分支，读完返回当前函数，不再独立摆在阅读起点。

[旧 scope](../step-002-build-job-spec/references/history/2026-11-03-scope-before-step-breadcrumbs.md)保留，Step 002 仍只准备范围，没有预填函数记忆或个人理解。通用 skill 的面包屑规则保持不变，本轮是修正其在当前 scope 中的落实。

## 接下来要核对的关系

下一处范围已见 [Step 002 scope](../step-002-build-job-spec/01-scope.md)：从真实模板接入 build_job_spec，连接“管理任务状态”与“配置 Agent 执行”。当前尚未开始新的函数逐段阅读；已读部分可从本步 README 和函数卡回查。

## 源码与验证边界

- 本地源码 `/home/fredkeira/projects/agent-lightning`，HEAD `0029dbb35c467799d35fee81d15d80264b0d1bd3`；本次核对工作区干净。
- 本步没有新运行 Kubernetes/Gateway；此前静态与本地样例的验证边界随各卡完整继承。
