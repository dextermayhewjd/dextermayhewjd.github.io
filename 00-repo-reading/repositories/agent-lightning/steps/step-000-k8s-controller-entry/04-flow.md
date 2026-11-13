# 04 · 控制器入口的理解过程

[本地试读正文](README.md) · [范围](01-scope.md) · [函数索引](02-short-term-memory/overview.md)

<a id="start-confirmation"></a>

## 2026-11-03 · 确认开始，并先在本地 README 试读

前一轮已讨论从 `K8sReconciler.run` 定位周期协调和 Job 事件观察，用户随后表示：

> 好的那么我们开始吧
> 首先先记住的一点是
> 我们现在本地的readme 里面快速试错
> 不需要在本地的hugo中先建立网页

本步据此开始，采用本地 README 作为试读正文，scope 保存边界和导航，`02` 保存当前函数记录，`03` 初始为空。本阶段不建立 Hugo 页面，也不以 Hugo 预览或构建作为前置。该偏好已写入项目入口与仓库约定。

本步以前的个人表述继续引用[五个沙箱接口与 Kubernetes 管理的起点讨论](../../README.md#sandbox-and-k8s)，不把助手补充的细分关系写成用户已经掌握。

<a id="first-observation"></a>

## 2026-11-03 · 首个观察点：控制器与单条任务的关系

助手先补最小调用来路：`_run_controller` 在 k8s 分支用 API Gateway 客户端和配置构造 `K8sReconciler`，然后 `await reconciler.run()`。随后给出 `run` 的正常路径源码节选，保留 `asyncio.gather` 中的两个协程调用；日志与取消处理暂时折叠。

首个问题：**假设 Gateway 里有 10 条待执行 rollout，这条启动路径是否要为每条任务再调用一次 `run()`？从对象创建、函数参数与核心骨架判断，并说明理由。**

原提问意图是区分“启动一个持续工作的控制器”和“执行一条 Agent 任务”。用户没有回答此题，而是指出应先给出完整骨架；该题现已撤下，先按下面的范围修正继续。

助手的输入、组合方式与返回边界整理在 [K8sReconciler.run](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L126)。材料与函数卡已准备不代表阅读完成，当前不生成 `05-task-flow.md`。

<a id="scope-first-revision"></a>

## 2026-11-03 · 用户要求先给完整 Reconciler 骨架

用户原话：

> 是否应该先考虑一下
> 给出这里的k8s reconciler的骨架?
> 然后再考虑从一个函数往下深入?
> 请观察一下当前的slime中的过往的scope是怎么写的来作为参考呢?

助手对照 Slime Step 001、012、017 的 scope 后确认：既有组织方式先保留整体位置与完整工作关系，再给局部阅读入口与返回位置。前一版仅展示 `run` 的两个协程调用，任务读取、Job 匹配、创建与状态回写尚未连接，就提前进入了局部问题。

本次据此重写 [scope](01-scope.md) 与本地 README：保留 `run` 的启动位置，补齐 A 周期协调与 B 事件观察的完整职责骨架，展示关键业务分支，并把局部入口表放在骨架之后。`_reconcile_once` 仅作为整体清楚后的优先候选，没有新增其函数卡片或开始逐段精读。

原 [README](references/history/2026-11-03-readme-before-overview.md) 与 [scope](references/history/2026-11-03-scope-before-overview.md) 已保留快照；`run` 卡片继续作参考。此次是阅读材料与顺序的修正，不是用户新增的机制理解或运行证据。当前继续本地 Markdown，不处理 Hugo。

<a id="numbered-reading-map"></a>

## 2026-11-03 · 骨架需要编号，并与步骤和短期函数对应

用户原话：

> 我觉得3.1和3.2都还可以
> 但是这里我需要有一个标的
> 也就是1,2,3,4,5
> 我需要知道在当前的steps中
> 我应该从哪些代码先开始看
> 我觉得这一点会比较重要
> 以及这里第二入口什么的应该和我们需要了解的步骤或者当前step的短期函数
> 或者接下来几个步骤的短期函数挂钩才对
> 否则的话
> 第一个图或许还能够看
> 但第二张图就不知道顺序是什么了

这是用户对呈现与导航的反馈，不是对所有函数机制的理解确认。本轮保留已认可的 3.1、3.2 结构，在第二张图、源码节选、导航表与 README 上统一加 [1]–[5]；A/B 仍表示并发路径，编号表示学习时的进入顺序。

助手将 [1] `_reconcile_once` 标为当前 Step 000 的首读目标；[2] `_create_job` 与 [3] `build_job_spec` 建议归入后续 Step 001；[4] 观察与事件处理、[5] `_patch_status` 建议归入后续 Step 002。每个编号同时列出要解决的问题、实际源码、对应函数记录名称与返回位置；[5] 被两条路径共用，未来只维护一张函数卡片。

本轮只完善阅读安排，未提前创建后两步，也未填写这些函数的个人认识。已有 `run` 卡片作为启动参考直接链接；[1] 的目标记录写明本步 `02` 中的路径，尚未实际展开，因此先指向源码。完整安排见 [scope 3.4](01-scope.md#reading-navigation)。

新增的后续分组属于助手据本轮需求提出的安排，实际开启下一步时再按当前问题确认范围。编号前的[完整 scope](references/history/2026-11-03-scope-before-reading-numbers.md)保留回查。继续只修改本地 Markdown，没有运行 Hugo 或集群。

<a id="function-notes-out-of-scope"></a>

## 2026-11-03 · 函数内部说明归入短期记忆

用户指出：

> 那么这里的3.3不应该放在这里的scope区域啊
> 这些函数不应该放在short term memory里面吗?

原 3.3 已经展开 `_reconcile_once` 的代码与状态分支、`_create_job` 的内部调用、Job 观察和事件处理，超出了当前 scope 用来展示整体骨架与导航的职责。助手按用户要求将这些已有说明分别迁入 [短期函数记录](02-short-term-memory/overview.md)，补齐场景、输入输出、未知与原始来源；没有将格式反馈写成用户对函数的技术理解。

scope 保留用户认可的 3.1、3.2 和 [1]–[5] 编号，原 3.4 的导航顺移为 3.3，`reading-navigation` 与各编号锚点保持。当前 [1] 以及已有 [2]、[4] 的导航直接链接函数卡；仅定位接口的 [3]、[5] 继续链接源码。

这些卡片保存本步已写出的材料，不表示后续 Step 001、002 已经开始。后续精读按原安排继承并调取记录，保留首次来源、个人表述和未知。原 scope 的[迁移前快照](references/history/2026-11-03-scope-before-function-notes-move.md)保留完整旧文；`03` 未改，仍暂无前序继承。没有运行 Hugo、Gateway 或 Kubernetes。

<a id="reading-order-audit"></a>

## 2026-11-03 · 对照 Slime 与 skill，先恢复周期循环的语境

用户提出：

> 请你看一下之前的slime是怎么阅读的好吗?
> 如果阅读方式和skill 有出入
> 那么请给出提示
> 否则我们当前第一个看的内容应该是这里的periodic reconcile_loop对吗?

### 实际历史与规则

- [Slime Step 001 的形成过程](../../../slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md)：先有整体骨架，用户把问题指定为 Harness 怎样接到 Adapter 请求处理，阅读据此跟随所需交接，而不是机械通读全部上游函数。
- [Slime Step 012 的开始记录](../../../slime/topics/02-rollout-reward/steps/step-012-async-rollout-worker-loop/04-flow.md#step012-start)：入口是负责持续调度的 `_loop`。先给完整正常骨架，再从接回前一步的任务创建处进入，之后回看回收、发布与等待。
- [repo-reading-order](../../../../../.agents/skills/repo-reading-order/SKILL.md)要求“从骨架中找直接回答问题的核心动作”，也明确“不要按列表编号自动从头深读”。它允许按问题先看核心，再补必要前置与返回位置。

**核对结论**：上述 Slime 做法与 skill 的核心原则一致，没有“所有场景必须先读调用树上层”的规则。此前选择 `_reconcile_once` 本身不违反先核心的原则，它回答的是“单轮怎样匹配任务和 Job”；不足之处在于没有充分区分这一问题与用户当前要恢复的“控制器怎样持续运行”的语境。

### 当前采用的入口建议

针对当前问题，先读 **[1] `_periodic_reconcile_loop`** 更合适：确认何时调用一次检查、调用结束后等什么、怎样进入下一轮及退出。`_reconcile_once` 暂作“一次检查”的黑箱；随后进入 **[1.1] `_reconcile_once`**，再回到外层等待位置。两者继续在同一 Step 000，后续 [2]–[5] 不重排。

本轮先核对并修订阅读导航，没有代替用户回答机制问题，也没有开始完整函数讲解或建立外层循环的新卡片。已有 `_reconcile_once` 卡片保留为 [1.1]，初次来源与认识状态不变。

### scope 与短期记忆的边界提示

[repo-reading-scope](../../../../../.agents/skills/repo-reading-scope/SKILL.md)允许 scope 包含必要的裁剪骨架与局部阅读导航；它不等于“scope 里一行函数代码也不能放”。用户上一轮要求迁移的是已经展开的具体函数说明、输入输出和分支解释，放入 `02` 与这一分工兼容。当前按用户认可的整体图与编号组织 scope，未修改 skill 或把本轮选择变成所有仓库的固定顺序。

<a id="reconcile-once-start"></a>

## 2026-11-03 · 纠正入口文字，明确从 _reconcile_once 开始

用户澄清：

> 没有我打错了
> 我也觉得reconcile once 更加合适
> 青葱这个函数开始吧

本轮按其明确意图，从 `_reconcile_once` 开始。上轮关于外层循环的推荐是基于误输入作出的安排，不再作为当前入口；历史讨论保留。阅读编号恢复为 [1]，外层 `_periodic_reconcile_loop` 只说明调用与返回，不增加新的前置课程。

助手给出函数 163–172 行的数据读取部分：先从 Gateway 查询排队与运行中的任务，再通过 Kubernetes 客户端列出当前 namespace 内带管理标签的 Job。区分 `self._api` 与局部 `api`，以及 `Rollout` 对象列表与 Job 字典列表；未展开 helper 的内部机制。

随后给出教学情景：任务名单有 `r1`、`r2`，集群只查到对应 `r1` 的 Job，暂未给出任务状态。当前问题是：**仅凭没有查到对应 Job，能立即把 `r2` 判为失败吗？还需要查看 `r2` 的哪项信息？**

用户尚未回答。下轮按回答进入匹配和状态分支，不把入口确认或已有助手说明写成个人理解。材料保存在 [函数卡的两份数据来源](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#two-data-sources)，scope 仅更新导航。无真实 Gateway、Kubernetes 或训练运行。

<a id="query-rollouts-and-k8s-boundary"></a>

## 2026-11-03 · 先厘清任务查询的返回合同与 Kubernetes 边界

用户原话已完整保存在 [本函数的直接表述](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#my-statements)。用户认为开头在拿 rollout，进一步询问是否需要单独读 `_query_rollouts`、能否先记为返回每项状态，以及哪些调用直接涉及 Kubernetes。

助手核对 `_query_rollouts` 的 GET 请求、`Rollout.model_validate` 与 `Rollout` 类型定义后，给出当前阅读建议：先在父函数中掌握“状态筛选与数量上限 → 任务对象列表”的合同，暂不单开辅助函数步骤。返回对象有 `rollout_id`、`input`、`config` 和 `status` 等字段，不能只理解为状态列表；查询本身也只是 `_reconcile_once` 的第一项动作。

边界进一步明确：`self._api.get("/api/rollouts", ...)` 请求 Gateway；`_get_k8s_api` 获取 Kubernetes 客户端，`Job.async_list` 查询 Kubernetes Job。`.raw`、字典整理与分支判断在 Python 内完成。当前先解决这两份记录与访问边界的区别，再回到后续匹配；此前的 r2 判断题不作为继续阅读的门槛。

上述为助手提供的校准，尚无用户后续理解反馈。未新建 `_query_rollouts` 独立卡片，未进入新步骤或运行服务。

<a id="reconcile-memory-segmentation"></a>

## 2026-11-03 · 函数卡过密，按同一例子与数据阶段重排

用户反馈：

> 作为一个认知学家和资深的程序员
> 你会如何阅读这里的reconcile once
> 并且会考虑如何构建的这里的short term memory呢?
> 我感觉当前reconcile once里面的内容太多了

助手判断：旧卡把整体裁剪代码、当前输入代码、辅助函数实现、字段表、Kubernetes 边界和状态分支连续展开，同一读取关系多次出现，章节又跟着追问不断加深。此前在读者仍确认两份数据的含义时就问“缺少 Job 是否失败”，要求提前使用后面的决策知识。

本次按实际数据依赖重排同一张函数卡：1.1 取得记录，1.2 建立索引并配对，1.3 按状态决定动作。用同一条排队任务 r1、没有对应 Job 的正常创建情景贯穿；默认仅展示总纲、整体输入输出和当前 1.1，后两段折叠。辅助接口先保留调用合同，详细 HTTP/模型转换的旧说明保存在完整快照，后续需要时回查。

原话、未知、固定源码与来源保留；卡片仍使用既有“LLM 四项 → 本场景输入输出与阶段 → 我的直接表述 → 尚不清楚 → 来源”结构。此次修改是本地试读版本，是否有助于理解仍需用户反馈，未标记任何新增机制掌握。原卡片[完整快照](references/history/2026-11-03-reconcile-once-before-segmentation.md)保留。方法依据与取舍另见[本轮评估](../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#reconcile-memory-segmentation)。

当前阅读位置仍是 1.1 的两份记录与访问边界；不继续提前提问终态判断，也未开始 1.2、1.3 的互动阅读。

<a id="breadcrumb-reference-confirmation"></a>

## 2026-11-03 · 核对“骨架 + 一次一个函数”的既有 reference

用户明确：

> 我一直觉得是需要有骨架
> 同时每一次只会像面包屑一样打开一个函数
> 请看一下之前skill中的short term memory中的reference有没有类似的案例

本轮直接查阅短期记忆 skill 的 reference，找到两个互补的现有样例：

- [面包屑链路与通用底层基座](../../../../../.agents/skills/repo-reading-short-term-memory/references/breadcrumb-navigation-and-shared-infra.md)：2026-10-23 已获用户认可，以 `run_agent → exec_and_wait` 为例，规定卡片顶部的调用链面包屑、父函数自身职责与子函数独立实现的分工，以及带返回值和接续位置的跳转表。
- [BaseAdapter._run_turn](../../../../../.agents/skills/repo-reading-short-term-memory/references/base-adapter-run-turn.md)：父函数保留完整的调用组合、当前场景与输入输出；各局部代码后列出需要时进入哪个子函数，以及读完返回后使用什么结果。

也回查了 Slime Step 008 的实际 `run_agent` 和 `exec_and_wait` 卡片，确认这些链接与职责划分不只是模板描述。`run_agent` 保存目录准备、委派与退出码交接，长命令执行机制在 `exec_and_wait`；后者注明多个调用来源，读完可回到原调用点。

用户强调的是阅读焦点与函数间跳转：骨架保持可见，每次只展开当前函数；需要进入子函数时保留来路和返回位置。前一版的三段与折叠只处理父函数内部的组织和显示密度，尚未充分落实这套面包屑结构。后续应沿现有 reference 整理，不再把阶段折叠当作完整替代方案。

本次完成 reference 核对并保存用户的呈现要求，没有新建子函数卡、改写函数技术正文或推进理解状态。当前源码阅读仍在 `_reconcile_once` 的两份数据来源。

<a id="breadcrumb-card-applied"></a>

## 2026-11-03 · 按已确认 reference 修改 _reconcile_once 卡片

用户要求：

> 好的那么按照这个修改一下当前的reconcile once这个short term function的内容吧

本次按 `breadcrumb-navigation-and-shared-infra` 与 `BaseAdapter._run_turn` reference 修改现有卡片：顶部显示 scope、函数索引、上游调用链和当前函数；父函数的完整主干保持可见；每个主要子调用列出入口、输入与返回项，以及回到本卡后的接续位置。

父卡只保留自身读取、索引、循环和状态判断的组合，不展开查询、客户端构造、Job 创建或状态写回的内部实现。已有 `_create_job` 卡补上上游面包屑与反向返回链接；尚未独立阅读的辅助函数链接固定版本源码，不预建新的函数卡。

此前的[分段版完整卡片](references/history/2026-11-03-reconcile-once-before-breadcrumbs.md)保留。用户原话、未知、认识日期与源码版本未改成新的理解结论。当前阅读仍在两份数据的区别，本轮没有实际下钻新函数或运行服务。

<a id="query-rollouts-card-start"></a>

## 2026-11-03 · 独立阅读 _query_rollouts

用户明确要求：

> 好的那么我们目前来看一下这里的这个query rollouts是干什么的吧
> 开一个short term memory的函数卡片吧

本轮沿已建立的父函数骨架下钻，在本步 `02` 中创建 [K8sReconciler._query_rollouts](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._query_rollouts.md)。顶部面包屑指回父卡的查询位置，父卡的原源码入口改为子卡入口，返回表明确接回 163 行再继续 164 行。

阅读聚焦三项：状态和数量上限怎样形成查询参数，怎样向 Gateway 发出 GET 请求，以及 JSON 项怎样变成 `Rollout` 对象。输入保持本次调用的 `QUEUING / RUNNING` 和 `limit=500`；用一条合法任务记录的字段节选说明返回对象，标明静态教学假设。

此前“是否在拿 rollout、是否只返回状态”的原话从父卡引用并保留来源。新增的内部说明尚未得到用户理解反馈；没有进入 Gateway 存储、HTTP 传输、Pydantic 内部或 Kubernetes 执行。

<a id="query-rollouts-first-retelling"></a>

## 2026-11-03 · 用户复述查询链条，校准筛选条件与返回记录

用户的[完整复述](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._query_rollouts.md#first-retelling)保存在当前函数卡。他已描述把两个状态组织成查询条件、向 Gateway 发送 GET、把 JSON 各项转成 Rollout 并返回列表，同时仍将目的与返回结果概括为取得每项状态。

助手再次核对 `_query_rollouts`、Gateway 的 `list_rollouts` 与 `Rollout` 定义：`state_in` 用来筛选任务，服务端返回符合条件的完整任务记录；客户端将这些记录转换成 `list[Rollout]`。因此查询与转换的流程概述符合源码，待校准的是返回值并非只有状态字段。当前调用是在执行一次查询，父函数随后可用返回对象的标识、配置与状态继续协调。

这项说明保存在同一函数卡，未向用户预填已经理解精确区别，也未进入后续 Kubernetes 客户端函数。当前继续围绕查询的输入、返回记录与父调用交接。

<a id="gateway-versus-k8s-client"></a>

## 2026-11-03 · 返回父函数，区分 Gateway 与 Kubernetes 两个客户端

用户表示理解上一段并继续到 `api`，同时指出此前把 `_query_rollouts` 理解为向 Kubernetes 发请求。[完整原话](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._get_k8s_api.md#my-statements)保存在本次函数卡中。

本轮核对 `_run_controller`、`K8sReconciler.__init__`、`_query_rollouts` 与 `_get_k8s_api`：控制器创建时已收到 `AgentLightningAsyncClient` 并保存为 `self._api`；任务查询直接用它访问 Gateway。`self._k8s_api` 初始为 None，由 `_get_k8s_api` 取得并缓存；父函数的局部 `api` 接住这个 Kubernetes 客户端，供下一段 Job 查询使用。

这解释了为何前一行没有先调用 `_get_k8s_api`：前一行的服务目标是 Gateway，并且已有相应客户端。当前区分的是两个对象和两个访问目标，不将用户说“理解了”扩大为已经掌握全部请求链路。

已建立短小的 [_get_k8s_api 函数卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._get_k8s_api.md)，保留三行函数主体、缓存前后变化和返回父调用的位置。当前只静态核对，没有访问真实服务。

<a id="two-services-understood"></a>

## 2026-11-03 · 用户已区分两类服务的 API

用户明确表述“一个是 gateway 的 api，一个是 k8s 服务的 api”，完整原话保存在 [_get_k8s_api 函数卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._get_k8s_api.md#two-services-understood)。这一服务区分与源码一致。

助手确认，并将代码中的对象名称补齐：`self._api` 是 Gateway 客户端；`self._k8s_api` 是缓存的 Kubernetes 客户端，局部 `api` 接住它的返回值。当前记录用户已说清的服务区别，变量映射与缓存机制不据此自动记为已经掌握。

<a id="job-listing-interface"></a>

## 2026-11-03 · 查看 Job 查询、模块来源与两个过滤条件

用户给出父函数的 Job 列表推导式，并提出以下问题（节选）：

> 这里的k8s objects是什么?
> 以及async list反蝴蝶是什么?
> 还有这里的namespace和label slector什么的?
> 是否能够给出这里的解释呢?
>
> 或者说
> 这里的k8s_objects.Job又是哪里来的呢?

本轮先确认本地导入 `from kr8s.asyncio import objects as k8s_objects`、管理标签常量和默认 namespace。项目的 `uv.lock` 锁定 `kr8s==0.20.15`，本地未找到已安装的该库源码，因而读取对应 GitHub 发布标签的 `asyncio/objects.py`、`_objects.py` 和 `_api.py` 核对接口。

确认的来源链为：本地别名 `k8s_objects` → `kr8s.asyncio.objects` 导出的 `Job` → `Job(APIObject)` 继承的 `APIObject.async_list`。本例未传 `raw=True`，异步生成器提供 Job 实例；外层列表推导式取 `.raw` 收入普通列表。核对版本的 `.raw` 是支持字典访问的 `Box`，不能把 `typing.cast` 解释为创建或转换资源对象。

已按用户当前问题建立 [Job 查询场景的库接口卡](02-short-term-memory/functions/kr8s/_objects.py/APIObject.async_list.md)，并接上父卡返回位置。用不同 namespace 和管理标签的三个假设 Job 说明两个过滤条件共同生效；保留 namespace 是资源命名作用域、label 是元数据键值标记的初步说明，不扩展到集群调度或库内 HTTP 分页。

以上是助手的源码核对和教学说明，尚无用户对此接口的理解反馈；未安装依赖、执行集群查询或创建 Job。

<a id="k8s-basics-folder"></a>

## 2026-11-03 · 撤回未读卡片，Kubernetes 基础单独整理

用户说明并要求：

> 之前几份是因为之前更本就没有接触就直接创建我觉得是不合适的
>
> 这一个repo
> 是否能够单独列出一个k8s的folder
> 里面单独放一下所有和k8s基础内容相关的部分呢?

据此确认 `run`、`_create_job`、`_watch_jobs_loop`、`_handle_job_event` 的缺失是用户主动撤回未读卡片，不是需要恢复的意外丢失。本轮从当前函数索引移除这四项，scope 与父卡保留源码入口；历史记录中的旧卡片链接改为固定版本源码，原话与当时处理过程保留。

在项目级建立 [k8s 基础目录](../../../kubernetes/README.md)，先整理实际问到的五类内容：API 与客户端、Job/Pod、Namespace、Labels/Selector、kr8s 资源对象。通用概念集中在这里；`APIObject.async_list` 与 `_get_k8s_api` 的函数卡通过链接回查，保留当前场景的参数、返回值及父函数接续。

目录分工不新增学习进度，也不预生成未接触的课程或函数卡。以后实际进入新函数时再建卡；基础笔记也随真实问题扩充。本轮保持本地 Markdown 方式，没有建立 Hugo 页面或运行集群。

<a id="pure-k8s-hierarchy"></a>

## 2026-11-03 · 通用 Kubernetes 知识与项目映射分开，并按主题分层

用户反馈：

> 有些地方有问题
> 1.api和客户端
> 这里的只有kubernetes的api server是相关的
> 但是agent lightning并不是
> 2.这里的job and pod我觉得还不错
> 但是这里的agent lightning controller也是k8s的内容吗?
> 这个folder需要放的是纯粹k8s的内容
> 3. 我觉得kr8s这里说的还是比较清楚的?
> 这里的是python和k8s库相关的内容?
> 4. label和selector我觉得也是很重要的内容
> 5.也还可以
>
> 请根据有问题的地方做出修改
> 同时希望先构建一个和k8s相关的分层的folder
> 这样子之后再复习k8s相关的内容的时候会比较清晰?
> 否则太混乱了

本轮按此要求将 `k8s/` 改为可独立复习的四层目录：架构、资源组织、工作负载、客户端库。前三层只讲 Kubernetes 自身的概念；`kr8s` 作为 Python 客户端生态单独放在第四层。

基础正文移除了 Gateway、应用 K8sReconciler、项目配置与变量映射，标签例子改为通用的 `app=report-worker`。这些项目材料集中保存到[项目专属对应关系](../../references/kubernetes-integration.md)。其中明确应用控制器与 Kubernetes 内置 Job 控制器的职责不同。

旧平铺文件移至[历史目录](../../references/history/2026-11-03-k8s-before-topic-separation/README.md)，原内容和来源可回查；当前函数卡的基础链接更新到新目录，两个客户端的比较链接到项目参考。没有新增源码阅读步骤或把本轮结构反馈记为新的机制掌握。

<a id="role-aligned-k8s-structure"></a>

## 2026-11-03 · 用户确认按腾讯岗位落实八类 Kubernetes 目录

用户明确要求（开头节选）：

> 重点是需要满足腾讯的这个岗位
> 请看一下这里的job description
> 请结合这里的内容 也就是上面你给出的意见
> 重新划分一下这里的这个folder结构
> 同时更新一下md

随后用户贴出上一轮八类目录与整体模型建议，并确认：

> 就写这个吧

本轮重新读取已保存的完整 JD，按要求 3 的 Kubernetes/容器集群经验，以及职责 2、4 和要求 1、5 的接入、并发、资源、日志与稳定性要求，落实知识目录和阅读深度。具体映射保存于[岗位对应范围](../../references/tencent-k8s-scope.md)，通用 `k8s/` 正文保持项目无关。

目录采用用户确认的 `00-overview`、`01-architecture`、`02-resource-model`、`03-workloads`、`04-runtime-environment`、`05-security-and-isolation`、`06-operations`、`90-clients`。原有资料迁入对应位置，并同步函数卡中的基础链接；补写 Job 生命周期总览、资源对象模型与协调循环三个起步主题。运行环境、安全与运维先提供归属、观察问题和官方入口，细项随真实阅读与实践展开。

此前结构的[完整快照](../../references/history/2026-11-03-k8s-before-role-aligned-structure/README.md)保留。此次完成资料结构与正文建设，没有建立未读函数卡、开展集群实践或改变函数理解状态；当前代码阅读仍停在 Job 列表查询。

<a id="job-filter-purpose-understood"></a>

## 2026-11-03 · 用户说明 Job 筛选用途，返回父函数的数据整理

用户已概括：通过 Kubernetes API 查询现有 Job，并通过 namespace 和标签筛选特定 Job。完整原话保存在 [Job 查询卡](02-short-term-memory/functions/kr8s/_objects.py/APIObject.async_list.md#filter-purpose-understood)。这个用途判断与源码一致。

助手确认，并补充：两个条件共同生效，设置的是查询条件；筛选后逐项取得 Job 对象，父函数再收集 `.raw` 数据。没有将这项用途理解扩展成库实现或对象类型全部已掌握。

随后按用户“继续”的要求返回父函数 173 行，初步说明 `jobs_by_name` 把列表按 `metadata.name` 整理成字典，供后面按 rollout 对应的名称查找。它是父函数中的数据整理，未另建函数卡；这项转换还没有用户理解反馈。没有运行集群。

<a id="missing-job-branch"></a>

## 2026-11-03 · 先在父函数读清缺失 Job 的分流

用户将 `jobs_by_name` 理解为字典构造，接着给出 `if job is None` 的原代码，询问 Job 名、排队时的创建，以及 `_patch_status` 的任务 ID 和状态，并问是否需要立即独立建立两个函数记录。完整表述节选保存在[父卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#missing-job-branch)的原话区。

本轮继续当前父函数：Job 名优先读取 `rollout.status.k8s_job_name`，为空时根据 ID 生成；查找不到 Job 后，排队任务调用创建接口，已运行任务请求将 Gateway 中的任务记录标为失败。上方排队分支的 `continue` 排除了继续落到后方写回语句的情况。

说明创建调用的 await 只等待创建函数返回，状态写回按 rollout ID 定位 Gateway 记录；两个调用的内部实现先保留接口。当前用户卡点是父函数的分流和输入用途，先在父卡内解释，不因出现两个调用就立即建两张卡。后续要独立研究创建或状态更新机制时再进入对应函数。

未预填用户已理解本轮校准，也未创建或修改实际 Job。

<a id="create-job-reading-start"></a>

## 2026-11-03 · 用户选择先读创建，再读状态写回

用户复述 Gateway 保存排队/运行中的任务，Kubernetes 查询现有 Job，再按 rollout 取得名字逐项查看，并明确选择先看 `_create_job`、之后再看 `_patch_status`。[完整表述](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#creation-reading-request)保存在父卡。

助手补准两点：Job 查询只筛 namespace 和标签，可能包括已结束但仍保留的 Job；进入创建分支需要 `job is None` 与 rollout 仍是 `QUEUING` 同时成立。本轮尚未取得对这两点的再次反馈。

现按真实阅读请求建立 [_create_job 函数卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._create_job.md)，从父调用进入，先看 manifest 构造、取得客户端、Python Job 对象与提交请求的区别。限速和失败分支保留在骨架/边界中，`build_job_spec` 暂按配置生成接口使用；`_patch_status` 按用户顺序留作下一处，未提前建卡。

本次沿当前 Step 000 的父函数连续下钻，没有因原先的分组建议自动建立新步骤。创建卡是用户已选入函数后的实际阅读记录，原先未读备稿被删除的事实保留。无集群运行或新增个人掌握判断。

<a id="create-job-purpose-and-depth"></a>

## 2026-11-03 · 创建职责已有初步理解，先不深入旁支

用户将本函数概括为“通过 manifest 创建 Job”，并询问其他内容是否需要深入，完整原话保存于 [创建函数卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._create_job.md#creation-purpose-understood)。

助手确认其职责层理解，并补准：Gateway 中的 rollout 在调用前已存在；本函数据此组织并提交 Kubernetes Job。当前先能连接任务、manifest、Job 创建请求与返回父函数即可。创建限速、失败分类、重试和底层库内部留作按需回查，不要求为此继续下钻。

本次记录的是用途层的初步理解与停止深度，不标记整个实现已经掌握。之后按用户已选顺序返回父函数，再看 `_patch_status`；本轮没有创建它的卡片或展开其实现。

<a id="patch-status-reading-start"></a>

## 2026-11-03 · 独立阅读 _patch_status

用户要求：

> 好的 那么我们继续看一下下一个部分的内容吧
> 也就是这里的这个patch status的内容吧
> 请单独创建一个函数卡片吧

本轮按既定顺序，从创建函数回到父流程，再进入父函数的失败登记分支。创建与失败登记是父函数中的不同分支；当前示例选择 Gateway 中 r1 为 RUNNING、但对应 Job 找不到的情景。

已建立 [_patch_status 函数卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._patch_status.md)，解释任务 ID、`**status`、请求体包装、PATCH 请求与布尔返回。卡片顶部指回父调用，返回表注明该分支未接收布尔值、返回后继续下一条任务。

源码核对确认：`state=FAILED` 是希望写入的任务状态，`True/False` 是更新请求成功与否；更新为失败状态也可以返回 True。示例 JSON 保留外层 `status`，未提供字段由 `exclude_unset` 排除。Gateway 状态转换与字段合并仅核对合同，未扩展成服务端内部学习。

以上是本轮助手说明，尚无用户对函数内部的复述；没有修改真实任务或运行服务。

<a id="why-patch-a-running-rollout"></a>

## 2026-11-03 · 返回父函数，理解为什么 RUNNING 还需要 PATCH

用户追问到达 `_patch_status` 的路径，提出“非排队应为 RUNNING”，不清楚此时为什么需要回写，以及已经完成时怎么办。[完整原话与局部分支](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#why-patch-a-running-rollout)保存在父卡。

本轮把观察点从 PATCH 请求的组织返回到调用条件：本轮先筛选 Gateway 的 QUEUING/RUNNING，再查对应 Job；只有 Job 缺失才进入当前分支。QUEUING 创建后执行 `continue`，不会接着回写失败；剩下的 RUNNING 表示 Gateway 仍记录任务运行中，但本轮没有查到其 Job，源码据此请求登记失败。正常找到且尚无终态的 RUNNING Job 不会在此被标为失败。

对“已经完成”的说明区分三层：创建函数返回不代表任务完成；已成功且仍存在的 Job 从后续分支同步 SUCCEEDED；Gateway 已登记 SUCCEEDED 的任务不会被下一轮的两种状态筛选选中。Job 完成与对象被清理也不同；若对象已清理但 Gateway 仍是 RUNNING，本段仍按缺失处理，无法从缺失本身推断成功。

依据为同一固定版本 `k8s_reconciler.py:163–240` 的筛选、缺失分支、Job 终态解析与回写。仅核对调用条件和后续去向，没有进入新的函数卡或逐项展开终态字段；以上补充尚未被用户确认理解，也没有真实运行。

<a id="missing-job-branch-confirmed"></a>

## 2026-11-03 · 用户确认缺失 Job 时的分流

用户明确表示理解，并复述：本轮取得 QUEUING/RUNNING；QUEUING 没找到 Job 就创建，RUNNING 也没找到则通过 `_patch_status` “报错”。[完整原话](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#missing-job-branch-understood)保存在父卡。

助手确认这条条件与动作关系，补准“报错”为请求将 Gateway 中对应 rollout 登记为 FAILED，并保存 `Job disappeared`；它不是通过抛异常中止整个循环，调用返回后按 `continue` 处理下一条任务。本次只确认缺失 Job 分支的用途理解，未将状态更新内部、布尔返回或已完成 Job 的判断标记为已掌握。

<a id="existing-job-reading-segmentation"></a>

## 2026-11-03 · 已有 Job 的状态逻辑怎样拆分阅读

用户反馈：

> 好的那么我们继续下去看吧
> 下面好像还有很多关于状态修改部分的内容
> 这里的逻辑感觉会比较的绕和烦 以及重复?
> 请考虑一下下面的部分而你应该如何做拆分什么的吧

本次沿用既有完整骨架、单函数卡与面包屑约定，只为 `_reconcile_once` 后半段补[三个阅读段](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#existing-job-reading-map)：①从 Job 字段归纳结果，②尚未判断出终态时处理 Gateway 的排队状态，③已有结果时处理合法转换并写回。执行关系为①之后选择②或③；每段都是本函数的连续语句，不另造函数或新卡。

助手提出先区分 `rollout.status.state`（已查询的 Gateway 状态）与局部 `state`（本轮 Job 结果），避免把读取、局部赋值和远端更新混成一件事。`attempt_id` 先作为回写所需的关联信息，失败消息拼接与计数兜底按①的分支逐渐补充。

重复代码的核对：条件与计数是归纳结果的两种依据；两次写 RUNNING 分别处理未见终态的排队记录、已成功但仍在排队的记录。后者来自项目的合法状态转换限制：允许 QUEUING → RUNNING/FAILED、RUNNING → SUCCEEDED/FAILED，不允许直接 QUEUING → SUCCEEDED。依据为同一固定提交的 `k8s_reconciler.py:187–240`、`schemas.py:87–93` 与 `server/routes/rollouts.py:183–196`。

建议接下来只展开①，先成功条件，再补失败与兜底，读到局部结果准备交给②/③时停。本轮为拆分方案与源码导航；用户尚未反馈各段理解，不将此记录成已读懂，也未更改 Agent Lightning 源码或运行服务。

<a id="status-data-and-branches"></a>

## 2026-11-03 · 从数据格式理清条件、计数与回写分支

用户已定位接下来处理的是存在的 Job，但尝试用“condition 正常就没事，不正常就 FAILED”解释代码；又询问既然 Job status 更新，为什么 209–213 行还判断计数。用户明确要求说明 `RolloutState`、`state`、`job_status` 的形状，以及多个分支的分类。[完整原话](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#status-data-question)保存在函数卡。

本轮先区分两份远端数据与一个局部变量：Gateway 响应转换为 Rollout，其 `status.state` 是已登记状态；Job 的 `status` 是条件列表与计数组成的映射；局部 `state` 初始化为 None，读取 Job 字段后可能取 RolloutState 的 SUCCEEDED/FAILED。`RolloutState` 自身是枚举类型，不随这次赋值改变。

条件校准：`condition.status` 是字符串真假，必须结合 `type`；Complete/True 是成功条件成立，Failed/True 是失败条件成立，False 不是任务失败的通用标记。条件循环里的 continue/break 仅控制条件遍历。209–213 行的两个 `state is None` 保证已有结果不被计数覆盖；读取的是同一个本地 `job_status`，没有再次查询或更新 Kubernetes。

后续回写按“本轮结果（None/SUCCEEDED/FAILED）× Gateway 原状态（QUEUING/RUNNING）”列成六种组合。只有 QUEUING + SUCCEEDED 要先补 RUNNING，补写失败则跳过；依据为项目的 VALID_TRANSITIONS 与服务端检查。最后一个 PATCH 使用局部 `state` 作为请求参数，成功更新的是服务端记录，没有刷新手上的 Rollout 快照。

已将父卡按“完整模型、数据形状与样本、连续骨架与函数面包屑、已读缺失分支、已有 Job 的三段代码与决策表”重排，保留全部旧原话、未知与来源；[重排前快照](references/history/2026-11-03-reconcile-once-before-status-data-model.md)保留此前版面。通用字段说明进入纯 Kubernetes 的 [Job status](../../../kubernetes/03-workloads/job-status.md)，项目特有的计数兜底留在父卡。

证据为固定提交 `0029dbb35c467799d35fee81d15d80264b0d1bd3` 的源码，以及 Kubernetes 官方 JobStatus/JobCondition 与 Job 终态说明。计数是 Pod 级统计，不自动等于 Job 整体结果；本项目显式设置 backoffLimit=0，但计数兜底仍不能推广为任意 Job 的通用判定。实际函数配合内存桩的 14 组本地样例通过，三个连续代码片段与本地源码一致，439 处项目内链接与锚点通过核对；没有查询真实集群。以上解释尚未被用户确认理解。

<a id="inline-data-notes"></a>

## 2026-11-03 · 从两份数据出发，把变量解释写在旁边

用户认可具体 JSON 与 Kubernetes Job 的呈现，但不认可开头的流程图、提前介绍局部判断值和集中变量表；当前心智模型仍从“Gateway 控制的任务状态、Kubernetes 返回的 Job 信息”出发，要求具体说明放在相应数据旁边。[完整原话](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#inline-data-feedback)保存在函数卡。

据此把开头模型收回两边记录的对照；同一 r1 场景的两份数据保持不变，用明确标注的 JSONC 添加字段旁注。`rollout.status.state` 的写法紧接 Gateway 数据解释；局部 `state` 在①的真实赋值语句旁才展开，读写交接的说明移至后面的 PATCH 使用处。完整核心骨架与函数面包屑保留。

此次只调整解释出现的位置和形式，没有新增阅读范围，也不把版面反馈记为已理解状态分支。[调整前快照](references/history/2026-11-03-reconcile-once-before-inline-notes.md)保留全部旧内容，Python 注释注明是教学补充。

<a id="reconcile-purpose-confirmation"></a>

## 2026-11-03 · 用户归纳后半段的整体用途

用户把这些分支收拢为一个问题：Kubernetes Job 是否存在、状态是否改变、是否需要修改 Gateway 的状态。[完整原话](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#reconcile-purpose-understood)保存在函数卡。

助手确认这一职责理解，并补准“状态是否改变”为读取本轮 Job 情况，结合 Gateway 已登记的状态选择动作；本函数没有保存上一轮 Job 状态再计算变化，也不必先发生变化事件才执行协调。保留整体理解的进展，不把条件、计数、六种回写组合或事件观察机制标记为已掌握。

<a id="next-function-watch-proposal"></a>

## 2026-11-03 · 下一处入口建议：_watch_jobs_loop

用户询问：

> 好的那么现在看一下下一个function 需要看什么吧?

依据现有职责骨架与用户对单轮协调用途的复述，助手推荐同一控制器中的 `_watch_jobs_loop:292`：补上与周期协调并行的事件观察路径，先弄清 Job 事件怎样交给处理函数。它与 `_reconcile_once` 是经由 `run()` 启动的两条路径，不是后者返回后顺序调用的下一环。

建议本轮只看三个交接：沿用已接触的 namespace/selector/API 客户端开启 watch；从异步迭代取得 `event_type` 与 Job 对象；对 ADDED/MODIFIED 将 `obj.raw` 交给 `_handle_job_event`。到交给处理函数为止，重连等待与停止控制先保留用途；`_handle_job_event` 是下一处按需下钻入口，后续可接回已有 `_patch_status` 卡片。

预期短期记录聚焦“周期查询与事件接收的区别、每次收到的数据、传给谁及何时返回继续接收”。这是阅读建议，尚未建立这两个未读函数的卡片或自动创建新步骤；`build_job_spec` 继续保留为创建配置的按需回查入口。

<a id="watch-jobs-loop-reading"></a>

## 2026-11-03 · 用户选择 _watch_jobs_loop，开始事件接收阅读

用户明确沿上轮建议进入 `_watch_jobs_loop`，原话保存于[本轮函数卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._watch_jobs_loop.md)。本轮继续 Step 000，建立真实选入函数的记录，未提前建立 `_handle_job_event` 卡片。

先接回 `run()` 的并发启动位置：事件观察与周期协调是两条路径；本函数按 namespace 与管理标签接收 Job 事件，将 ADDED/MODIFIED 携带的 Job 数据交给下游，等待后继续取下一条。以一条 MODIFIED 事件和 `obj.raw` 的 JSONC 节选说明数据交接，变量解释位于代码旁，不使用开头的集中变量表或多层状态图。

本轮重点区分事件类型与 Job 的任务结果：MODIFIED 本身不表示成功，完成信息在 Job 的 status 里，由下游判断。本函数仅把 `obj.raw` 作为参数交出。停止信号的检查点、异常后的 5 秒等待保留用途，库内部的重连与资源版本尚未展开。

固定源码仍为 `0029dbb35c467799d35fee81d15d80264b0d1bd3`；kr8s `0.20.15` 的 `asyncio/_helpers.py:84–102` 与 `_api.py:627–667` 用于核对事件类型/对象二元组合同。事件为教学样本，未连接真实服务；用户尚无对内部行为的个人复述。

<a id="continue-as-step-001"></a>

## 2026-11-03 · 事件接收转入独立 Step 001

用户在开始 watch 阅读后提出为这部分建立步骤。沿用已经明确的函数与交接范围，建立 [Step 001 · 接收 Kubernetes Job 事件](../step-001-watch-job-events/README.md)。本步函数卡与原始对话保留，7 份记录完整继承到新步骤的 `03`，watch 再调入其 `02` 继续；首次接触仍归本步，未知与个人理解状态不变。

具体建步说明与用户原话见 [Step 001 的形成记录](../step-001-watch-job-events/04-flow.md#step-001-created)。这里不重写此前已发生的阅读，也不将本步所有细节标为已掌握。

## 证据

- Agent Lightning 提交 `0029dbb35c467799d35fee81d15d80264b0d1bd3`，工作区干净。
- `_run_controller`：`agentlightning/controller/__main__.py:17–43`；`K8sReconciler.run`：`agentlightning/controller/k8s_reconciler.py:126–139`。
- 默认配置来自 `agentlightning/config/controller.yaml`。本轮只有静态核对，没有 Controller、集群或训练运行。
