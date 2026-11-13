# 04 · 本步理解形成过程

[本步入口](README.md) · [范围](01-scope.md) · [短期函数](02-short-term-memory/overview.md) · [累计记录](03-long-term-memory/overview.md)

## 开始前的范围与定位

此前用户要求先建立 scope，随后指出步骤编号与函数路标混淆、3.2 缺少调用来路。纠正为 Step 000 的 `_reconcile_once → _create_job`，从 manifest 赋值处进入 Step 002 的 build_job_spec；Step 001 watch 属于另一条运行路径。[原讨论](../step-001-watch-job-events/04-flow.md#step-002-breadcrumb-correction)继续保留。

<a id="build-job-spec-start"></a>

## 2026-11-03 · 用户明确进入 build_job_spec

用户表示：

> 那么当前应该看哪一个函数呢?
> 当前看一下这里的build job spec?

本轮沿用已经确认的 scope，从调用方 `manifest = build_job_spec(rollout, self._config)` 进入当前函数，先看第 45–47 行如何从 rollout 取得模板，缺少模板时如何停止。模板是已有 rollout 配置中的文本；本函数在这里没有按路径打开本地文件。

同时完成正式开始本步的记录准备：合并前一步 03 + 02 为八份累计函数卡，保留最近版本的原话、未知、源码与历史来源；把已读 `_create_job` 调入本步 02，并建立 build_job_spec 新卡。只创建实际需要的函数记录，Jinja/PyYAML 辅助接口未独立建卡。

卡片用同一 r1 教学场景定位整个函数的输入输出，保留完整骨架；具体展开先限于模板输入。后续阶段仅作位置标记，不把源码材料或文件建立视为用户已经理解。

<a id="template-env-url-image"></a>

## 2026-11-03 · 模板、两个 env、Gateway 地址与镜像

用户将开头概括为检查 Kubernetes Job 模板，询问是否需要补入基础资料，并对 env、向 Pod 传环境变量、LLM base URL 和镜像的关系提出猜测。[完整原话](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/build_job_spec.md#env-url-image-question)保存在函数卡。

本轮据原始 import 与赋值区分两个 env：49 行是 Jinja2 Environment 实例，用于文本模板渲染；87 行重新把同一变量名赋为 container.env 列表，向每个普通容器添加或覆盖 AGL_OPENAI_BASE_URL、AGL_EVENT_URL、AGL_KEY，保留其他项。它修改待提交的 Job/Pod 模板配置，没有把宿主环境变量全部复制到正在运行的容器。

地址核对：agent_base_url 选用 agl_server.agent_url 或回退到 agl_server.url，均为 Gateway 地址。拼接的 AGL_OPENAI_BASE_URL 被 Agent 作为 OpenAI 客户端入口使用；Gateway 的 llm_proxy 再选择模型服务器并使用 server.endpoint 转发。源码位置分别为 controller/k8s_reconciler.py:79–100、smith_agent.py:862–875、server/routes/proxy.py 与 server/proxy.py。本轮只核对这条合同，没有另建代理函数卡。

镜像来自真实模板的 image 字段，用 input.image_name 生成 :openai 引用；本函数不构建或拉取镜像。准备镜像的 pull_images.py 只定位，模板的 imagePullPolicy 说明与容器环境变量分工保存在通用基础资料。整个函数同时处理 Job 层元数据/生命周期和 Pod/容器配置，不把它缩成只处理容器。

已补充纯 Kubernetes 的 [Job 清单与 Pod 模板](../../../kubernetes/03-workloads/job-manifest-and-pod-template.md)、[镜像、命令与环境变量](../../../kubernetes/04-runtime-environment/container-image-and-env.md)。Jinja2 实例、AGL 字段和代理地址继续留在项目函数卡，避免把项目行为写成 Kubernetes 标准。

使用真实模板和原始函数的两个片段完成本地核对：Jinja 渲染生成预期镜像与任务文本；URL/env 片段为各容器补三项、覆盖同名项并保留其他项。没有执行 YAML 解析或完整函数，没有请求真实服务。用户已有的模板检查理解与其余尚待确认的校准分别记录。

<a id="k8s-note-boundary"></a>

## 2026-11-03 · 本轮知识应怎样归入 k8s 目录

用户询问：

> 这里的哪些部分需要记录在这里的k8s部分吗?

核对现有正文后，将归属写入[项目知识边界](../../references/kubernetes-integration.md#build-job-spec-knowledge-boundary)：已展开的 Job/Pod/容器层级、镜像/命令/env 及 Pod 内地址含义使用现有基础页；Namespace 与标签复用此前记录。运行重试、期限、清理、资源与挂载的通用机制，等具体阅读时再补到对应目录。

Jinja2 Environment、变量名复用、AGL 环境变量、Gateway 路径和本项目镜像生成逻辑继续保留在函数卡。这次是资料归类确认，没有将用户记为已掌握相关机制，也没有预生成未读主题正文。

<a id="total-and-parts-layout"></a>

## 2026-11-03 · 以总任务与连续阶段重新组织函数卡

用户要求确认 Kubernetes 知识是否已补充，已有内容不必重复；同时反馈 build_job_spec 很难直接理解，希望先讲清要解释什么，再考虑总分排版，并查看短期记忆 skill 的既有 reference。[完整原话](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/build_job_spec.md#layout-feedback)保存在函数卡。

核对结果：Job 清单/Pod 模板、镜像/命令/env、localhost 与可达性已在两份基础笔记中，Namespace/Labels 也已有记录，因此本次没有重复新增或改写这些基础正文。尚未逐项阅读的重试、资源和卷机制仍按此前边界等待实际问题。

匹配的 reference 是 BaseAdapter._run_turn 的“整次调用输入输出 → 按连续阶段说明交接”，并配合 breadcrumb-navigation-and-shared-infra 的调用来源与返回导航。当前卡片虽然有骨架，却把整个场景折叠、再按 env、URL、镜像等追问依次铺开；配置转换的阶段不够连贯，解释轻重没有围绕同一个总问题展开。

本轮重排为：先说明“将共享模板变成本次任务可提交的配置”，直接展示同一 r1 场景的输入与返回值节选，再保留完整骨架；内部按模板到 Job 字典、补任务身份与约束、补容器连接信息三个连续阶段组织。每段先写要回答的问题与交接，再放源码和说明；当前优先读第一段，后两段的详细代码及已讨论扩展折叠回查。原话、未知、来源和[重排前快照](references/history/2026-11-03-build-job-spec-before-total-parts.md)保留。

这次是既有 reference 在当前卡片的应用，不改变通用 skill、不新增函数阅读范围，也不作为用户已理解的证据；阅读效果等待后续反馈。方法层的记录见[总分排版讨论](../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#build-job-spec-total-and-parts)。

<a id="numbered-card-outline"></a>

## 2026-11-03 · 给总分结构增加层级编号与页首目录

用户提出：

> 能否考虑一下
> 1.把这里的模板如何变成这次任务的job字典
> 这种文字考虑一下层间给一下类似于1.1
> 2
> 2.1
> 或者在开头给出这里的层次?

本轮在函数卡页首加入可点击目录，正文同步使用“1 整体任务与数据 / 1.1 输入 / 1.2 输出 / 1.3 骨架；2 分阶段阅读 / 2.1 模板到字典 / 2.2 身份与约束 / 2.3 连接信息；3 返回调用方”。编号只描述卡片内部层级，不是 Step 编号，也不创建新的函数或阅读步骤。

原有函数记录栏目、面包屑、语句旁注和显式锚点保留。代码、数据、个人原话与认识时间均未因排版改变；[编号前快照](references/history/2026-11-03-build-job-spec-before-numbered-outline.md)保留原版面。当前观察点可以直接定位为卡片 2.1。

<a id="controller-closeout-and-pod-prerequisites"></a>

## 2026-11-03 · Controller 首轮覆盖与下一处阅读建议

用户询问：

> 好的 那么考虑一下继续吧
> 下一个我们需要看的是什么?
> 还是说目前这里的controller部分其实看的就差不多了?
> 这里其实整个如何开始构建一个pod什么的这里其实已经比较清楚了?
> 还有什么特别需要看的或者注意的吗?

按已经展开的讲解范围评估，Kubernetes Controller 的主干已覆盖：查询与匹配任务/Job、构造并提交 Job、周期协调和事件回写，可以阶段性收束，不必为“读完目录”继续展开每个辅助函数。此评估只说明讲解范围，不代表用户已确认所有细节，也不包括另一个 local runner 的完整实现。

补准对象边界：当前源码展示的是 Agent Lightning 构造并提交 Job；Pod 的创建由 Kubernetes Job 控制器承担，节点选择与容器启动由后续 Kubernetes 组件推进。已有[Job 生命周期总览](../../../kubernetes/00-overview/job-lifecycle.md)可用于回查，因此不能把“看过 manifest 构造”直接记为“完整验证 Pod 运行”。

推荐下一块围绕真实模板的启动前提：`command` 要执行 `/agl/agents/smith_agent.py`，这个文件怎样进入容器？源码路径为 `job-template-openai.yaml:19` 的启动命令，回查 `52–61` 行的 volumeMounts/ConfigMap 卷，再回查 `run.sh:104–106` 创建 ConfigMap 的命令。这里适合先形成一个完整文件交接，再看 Agent 的内部行为；目前只是候选定位，尚未建立新步骤或函数卡。

另外保留两类有价值的短补充：当前卡 2.2 中 Job/Pod 的重试、超时与清理约束，以及模板的资源请求/限制和 Agent 到 Gateway 的网络可达性。之后通过一次最小 Job 的提交、Pod 状态、事件和日志验证实际运行，比继续读取无关辅助机制更贴合当前 Kubernetes 目标；本轮没有执行任何集群命令。

<a id="framework-components-priority"></a>

## 2026-11-03 · 用户将下一主线转回框架三组件

用户反馈：

> 这个里面我觉得并不好?
> 1. 这里的agent loop是写死的 一般来说是需要考虑codex 还是claude这样子平台
> 2. 我更加想要理解的是一些别的内容
> Trainer: Runs verl and vLLM, builds training samples, and updates the policy.
> API Gateway: Proxies model requests and captures training data.
> Rollout Controller: Runs agents locally or as Kubernetes Jobs.
>
> 这些是否会比较重要?
> 请看一下这里在这个agentlightning
> 中是那些内容?

本轮将 SWE-smith 的固定 loop 与 ConfigMap 挂载建议降为具体部署示例，下一主线改为通用框架的任务、模型请求、事件和训练样本交接。没有继续展开该示例的 Agent 实现。

已根据本地 README、基础文档与实现建立[三组件源码定位](../../references/framework-components.md)：Trainer 的 _rollout / AglRolloutManager 连接任务提交与回收，Gateway 的 llm_proxy / forward_request / record_event 连接模型请求与事件，RolloutAdapter 将回收的记录转换为 DataProto，_train_step 连接策略更新。已读 Controller 作为执行一侧的背景。

同时区分示例与通用接入：K8s 模板中的 smith_agent.py 启动命令是该示例固定的，框架可用其他模板或本地 Agent 类。Codex/Claude 等具体执行端是否直接兼容仍需按协议核对；当前代理明确限制 chat/completions、completions 与非流式请求，不能直接把可替换启动程序当作任意协议已经支持。

建议下一处从 Gateway 的 llm_proxy 开始，承接已见过的 AGL_OPENAI_BASE_URL，经 HTTP 进入模型请求处理，再按需查看事件记录。用户本轮要求的是三组件定位与优先级判断，尚未创建新的步骤或函数卡。

<a id="slime-incremental-value-review"></a>

## 2026-11-03 · 根据已读 Slime 重新判断增量价值

用户表示：

> 我其实比较想要知道的问题是
> 这里本地其实已经处理过一边这里的slime部分的内容了
> 所以应该有一个adapter 这个是处理anthropic形式的请求还是openai的请求
> 然后会考虑对应的很多内容?
> 例如在每一次请求的时候怎么把记录保存下来
> 这以系列的内容
> 以及考虑一系列的拼接啊 什么相关的东西?
> 但是当前这个agent lightning怎么感觉好像只有一个k8s是值得借鉴的呢?
> slime里面把这里的发送给哪一个模型修改改为了发送给哪一个adpater service中的api?
> 这是我的理解
> 但是这里感觉很多东西都没有处理好的感觉
> 请看一下这里有什么比较适合我学习的内容还是其实差不多了就这些了呢?

本轮读取 Slime 的阅读约定、唯一进度、岗位安排与 Adapter/轨迹导出记录；源码比较使用学习版本 18868a79，通过 Git 读取，不把旧证据改写为本机 HEAD 540ea919。用户确实已经接触协议接入、请求记录、历史 token 与训练闭环；拼接、分段和 mask 的内层细节在原记录中仍有留白。

核对后保存[增量阅读评估](../../references/slime-incremental-reading.md)。Slime 通过 ANTHROPIC_BASE_URL 指向 Adapter，仍单独保留模型标识；Adapter 处理协议与请求前 token 准备，并在响应后记录轮次和前缀。Agent Lightning 的 Gateway 协议范围较窄，记录与拼接分散在 Gateway 和 Trainer 的 RolloutAdapter 中，不能把未在代理文件出现的逻辑直接判作不存在。

据此调整上一轮安排：Kubernetes 仍是最显著新增内容，不默认完整重读 Gateway 或训练器外壳。若继续，只选 trajectory 分支的精确前缀、mask 与不匹配拆段作为小范围对照；未完成组跨训练步与 Gateway pause/drain 作为另一个按需选项。它们与 Slime 已读内容有重合，不能宣传为全新机制或强制必读。

当前未创建新步骤、未恢复已经暂缓的 Slime 专题、未运行模型或集群。停止扩大源码阅读也是符合当前基础的一种选择，个人理解与运行证据继续分开。

<a id="slime-capability-overlap-audit"></a>

## 2026-11-03 · 再核对完成组数、未完成保留与轨迹的已有覆盖

用户提出：

> 我感觉绝大部分好像slime？都有了？
> 1.如何处理的部分slime里面应该已经记录下来了
> 2. 未完成的时候
> slime应该也可以是设置如果完成了多少组就开始更新
> proxy和app好像都有aiottp里面涉及
> 同时这里的记录轨迹部分slime也有trajectory?
>
> 这么看下来是否还有必要读这里的agent lightning
> 请仔细对比一下两个repo的实现把

本轮进一步核对 Slime 的 fully_async_rollout：消费者以 rollout_batch_size 为目标，仅取还需的完成组数；剩余完成结果留队，后台 active_tasks 不随消费者返回而关闭。组内生成先汇总，再由回调入完成队列；ABORTED/PENDING 结果交回重试。对照 Agent Lightning 按 data_id 集齐组、达到 target_finished_group_num 后返回其余 carry-over 记录，可确认核心能力已有覆盖，保存载体和具体控制方式不同。Slime Step 012/013 已读记录也明确包含该交接。

同时区分运行模式：Slime 普通 sglang_rollout.generate_rollout_async 在达标后 abort 剩余请求，并按 partial rollout 选项回收中断结果；不能把所有模式都概括成保留活动任务。模型更新方面，Slime 有 admission pause 和推理引擎暂停/恢复，Agent Lightning 通过 Gateway pause/inflight drain 协调；不是前者没有相应能力。

HTTP 与轨迹按实际业务核对：aiohttp/FastAPI 是底层工具，不能仅凭库名判断功能相同；Slime 的 Adapter 和 TrajectoryManager/SampleBuilder 已分别实现协议处理、请求记录、拼接、分段与 mask，Agent Lightning 则分成 Gateway 事件与 Trainer 端 RolloutAdapter。目标能力重合，具体数据结构和边界不同。

据此把[增量评估](../../references/slime-incremental-reading.md)的当前建议收紧为：可以收束 Agent Lightning 的默认源码通读，不再把轨迹合并或异步组收集安排成必读；保留 Kubernetes Job 管理与按具体问题回查的价值。这是学习必要性判断，不是两个系统完全等价或全部生产性质已验证的结论。未新增步骤，未运行真实模型、worker 或集群。

## 尚待反馈

模板检查已有初步复述。当前已按总任务和三个连续阶段重排，先看第一段能否帮助连接模板文本、填入任务和得到 Job 字典。两个 env、Job/Pod 配置层次、Gateway 与模型端点以及镜像边界仍待反馈，不把排版调整当成全函数已掌握。

## 证据与边界

- 固定源码提交为 `0029dbb35c467799d35fee81d15d80264b0d1bd3`；主要函数 `k8s_reconciler.py:43–101`，调用点 259。
- 样本采用仓库的 SWE-smith 模板与默认控制器配置，任务字段为教学构造。已隔离验证 Jinja 渲染和 URL/env 处理片段；未执行包含 YAML 解析的完整函数或访问 Kubernetes/Gateway。
