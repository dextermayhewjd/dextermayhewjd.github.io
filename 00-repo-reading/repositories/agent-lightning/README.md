# Agent Lightning：阅读入口

[通用方法](../../README.md) · [工作流](../../workflow.md) · [Kubernetes 基础](../kubernetes/README.md) · [当前接续](#current-reading)

> **当前在本地 Markdown 中试读和迭代。** 用户于 2026-11-03 明确暂不建立 Hugo 网页；这一阶段无需启动或核对 Hugo 预览。当前正文：[Step 002 · 进入 build_job_spec](steps/step-002-build-job-spec/README.md)；[范围与面包屑](steps/step-002-build-job-spec/01-scope.md)保留整体定位。

## 目标与范围

2026-11-03，用户确认：**Agent Lightning 要与已读的 Slime 结合，用来理解 Kubernetes 部分。** 阅读承接同一份腾讯混元 Agent 强化学习框架工程师 JD，重点是 Agent 任务怎样在集群中启动、执行、报告状态与回收资源。

- **复用的背景**：Slime 的 Agent 执行、环境操作、模型调用、结果与奖励、生成到训练的交接。实际已读范围和未知继续以 [Slime 唯一进度](../../../slime_photo/code-reading/repo-reading-route.md#当前接续)及函数记录为准。
- **首阶段阅读范围**：Agent Lightning 的 Kubernetes Controller、Job/Pod、任务模板、容器配置、网络连通、状态协调、失败处理与清理；沿一个具体 Agent 任务连接这些关系。
- **当前新增重点**：用户希望优先理解可替换 Agent 执行端背后的 Trainer、API Gateway、Rollout Controller 通用交接；具体见[三组件与数据主线](references/framework-components.md)。SWE-smith 的固定 Agent loop 和脚本挂载降为按需回查的示例。
- **增量原则**：先对照已读 Slime，不将三组件重新作为一套必读课程。Kubernetes 是主要新增；轨迹拼接与跨训练步的协调只按具体差异选读，见[本轮评估](references/slime-incremental-reading.md)。
- **阅读深度**：接下来覆盖 Trainer 接入层、Gateway 模型请求与事件采集、训练样本转换；底层训练算法、模型后端和 Kubernetes 调度器内部按实际问题回查。
- **实践目标**：在理解源码关系后，用具体部署与排障案例验证。源码阅读、用户理解和真实集群运行分别记录，实践何时开始及采用什么环境另行确定。

阅读沿用本仓库的通用方法：从一个真实任务找到组织主流程的函数，先建立整体位置，再围绕当前问题有限下钻。每步的函数范围、核心问题与短期记忆重点确定后，再展开阅读。

## 资料放在哪里

| 内容 | 位置与职责 |
| --- | --- |
| 通用 Kubernetes 知识 | [共享 Kubernetes 专题](../kubernetes/README.md)：按已确认的八类职责组织，由总览连接架构、资源、执行与反馈，便于独立复习 |
| 腾讯岗位对应的学习范围与实践证据 | [Kubernetes 岗位对照](references/tencent-k8s-scope.md)：限定投入深度，并连接部署、排障和验证目标 |
| 本项目怎样接入 Kubernetes | [项目对应关系](references/kubernetes-integration.md)：保存 Gateway、K8sReconciler、两个客户端及项目配置的关系 |
| 框架三组件怎样交接 | [组件与数据主线](references/framework-components.md)：Trainer、Gateway、Controller 的源码入口，以及 Agent 交互怎样成为训练数据 |
| 函数的实际阅读与个人理解 | `steps/.../02-short-term-memory/`：只为已经实际接触、展开的函数建卡，保留输入输出、源码和返回位置 |
| 整体骨架与本步阅读导航 | `steps/.../01-scope.md`：未读调用只做源码定位，不提前生成函数卡 |

2026-11-03，用户说明此前缺失的四份卡片是主动删除的，因为尚未接触就被提前创建。实际读到时再建立记录；本轮用户已明确进入 `_create_job`，据此重新建立当前阅读卡，其他未读调用继续只保留源码入口。Kubernetes 基础随真实问题积累，不预生成完整课程；目录中的内容保持项目无关，`kr8s` 明确归入 Python 客户端层。

八类知识目录已按用户确认落实；依据见[原结构评估](../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#k8s-folder-mental-model-review)与[腾讯岗位对应范围](references/tencent-k8s-scope.md)。起步正文先补总览、资源对象模型和协调循环，其他内容按实际阅读补充。

2026-11-05，经用户确认，原 k8s 的 20 份资料整体迁入共享专题，供 Agent Sandbox 等项目共同引用。本项目的函数记录、岗位范围、来源和阅读进度保留原位。

## 与 Slime 和岗位目标的接续

| 已有资料 | 在本项目中的用途 |
| --- | --- |
| [Slime 项目入口](../slime/README.md) | 回查既有主题、函数记忆与来源；当前本地源码为 `/home/fredkeira/projects/slime` |
| [Slime Step 005：Agent 执行前的准备](../slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/README.md) | 回查 Agent 如何取得执行环境；按需恢复既有背景 |
| [Slime Step 017：生成、训练与权重交接](../slime/topics/04-training-data-updates/steps/step-017-generation-training-loop/README.md) | 定位 Agent 任务在整体训练主线中的位置 |
| [用户提供的完整腾讯混元 JD](../../../slime_photo/code-reading/job-evidence/2026-10-28-user-provided-jd.md) | 确定岗位目标与学习深度；2026-10-29 用户再次确认同一份正文 |
| [岗位对照](../../../slime_photo/code-reading/job-alignment.md#agent-lightning-k8s-20261103) | 保存两仓库的学习分工与 Kubernetes 实践目标 |

JD 岗位要求第 3 条原文：

> 熟悉 Kubernetes 和容器化技术，具备在集群环境下进行开发、部署、排障或性能优化的经验；

本次静态核对：Slime 的 `slime/agent/sandbox.py` 中，`E2BSandbox.__aenter__` 调用 E2B SDK 的 `AsyncSandbox.create`，退出时调用沙箱句柄的 `kill`。这段代码展示调用侧的环境生命周期；实际服务端怎样创建和调度容器，需要额外实现证据。该文件在已有材料的 `18868a79` 与当前本地 `540ea919` 之间没有变化。

Agent Lightning 的 `agentlightning/controller/k8s_reconciler.py` 则直接构造、提交并观察 Kubernetes Job。两者可围绕同一个问题对照：**Agent 需要一个执行环境时，谁把任务变成真实运行，谁观察结果，谁负责清理？** 这里建立的是阅读上的接续与概念对照，尚未设计或运行两个框架的代码集成。

<a id="sandbox-and-k8s"></a>

## 起点理解：五个沙箱接口与 Kubernetes 任务管理

2026-11-03，用户给出当前理解：

> 也就是说
> 其实slime已经给关于进入一个sandbox需要做的事情都通过五个接口写好了
> 但是agent lightning
> 更多的内容是这里的k8s receconciler对吗?
> 这是我的理解

**助手据源码核对的澄清：** 两者的学习分工方向成立，需要区分沙箱的使用接口与集群中的任务管理。Slime 的 `Sandbox` 是 `Protocol`，声明以下五个方法；当前 `E2BSandbox` 借助 E2B SDK 提供具体实现。

| 接口 | 上层使用的能力 |
| --- | --- |
| `__aenter__` | 进入上下文并取得可用沙箱；当前 E2B 实现创建远端沙箱 |
| `__aexit__` | 退出上下文并清理沙箱 |
| `exec` | 在沙箱内执行命令 |
| `write_file` | 向沙箱写文件 |
| `read_file` | 从沙箱读文件 |

五项覆盖环境生命周期、命令与文件操作。准备代码仓库、启动具体 Agent、执行评测等任务逻辑仍由上层调用这些能力来组织，不能把接口约定理解成已经完成全部业务准备。

本轮看 Agent Lightning，重点转到 `K8sReconciler` 所在的任务管理层：取得 rollout，与集群里的 Job 状态对照，需要时构造并提交 Job，再将观察到的运行或完成状态写回 rollout。Pod 的创建、调度与容器运行由 Kubernetes 相应组件承担。`build_job_spec` 设置 Job 的超时和完成后清理配置；自动清理由 Kubernetes 执行。

可用于继续阅读的两句话是：**Slime 的五个接口让上层统一使用执行环境；Agent Lightning 的 Kubernetes Controller 让 Agent 任务在集群中被创建、跟踪和收束。** `K8sReconciler` 不是这五个接口的直接实现，也不是整个 Agent Lightning；它是当前补充 Kubernetes 知识的主要入口。

上述接口与实现、应用控制器与 Kubernetes 的分工是起点讨论时的助手补充，尚未收到用户对这些细分关系的确认；不据此标记机制已掌握。这段讨论发生在 Step 000 开始之前。

<details>
<summary>本轮源码依据与验证边界</summary>

- Slime：[`Sandbox` 的五个方法](https://github.com/THUDM/slime/blob/540ea919e45b8b929198abce008a103be9cfc779/slime/agent/sandbox.py#L33)，[`E2BSandbox` 的进入与退出](https://github.com/THUDM/slime/blob/540ea919e45b8b929198abce008a103be9cfc779/slime/agent/sandbox.py#L298)。与旧记录版本 `18868a79` 的该文件一致。
- Agent Lightning：[`build_job_spec`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L43)、[`K8sReconciler._reconcile_once`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L161)、[`_create_job`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L242) 与 [`_handle_job_event`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L311)。
- 本轮为接口与职责的静态核对，未创建沙箱、Kubernetes Job 或运行训练。

</details>

## 源码与资料

| 项目 | 本次核对结果 |
| --- | --- |
| 本地 Git 根目录 | `/home/fredkeira/projects/agent-lightning` |
| 核心包 | `agentlightning/` |
| 分支 | `main` |
| 固定提交 | `0029dbb35c467799d35fee81d15d80264b0d1bd3` |
| 提交日期与标题 | 2026-11-03 · `fix(verl): classify trajectory prefix mismatch diagnostics (#646)` |
| 工作区 | 登记时干净；仅静态查阅，未运行 Agent 或训练 |
| origin | `git@github.com:dextermayhewjd/agent-lightning.git` |
| 上游项目 | [microsoft/agent-lightning](https://github.com/microsoft/agent-lightning) |
| 版本边界 | README 对应 v1.0 架构；`pyproject.toml` 包版本为 `1.0.2`，要求 Python ≥ 3.12 |

当前版本的 README 将框架分为 **Trainer、API Gateway、Rollout Controller**。这是助手根据项目资料提供的初始定位，具体交接留待源码阅读核对。

- [固定版本 README](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/README.md)：项目目标、三部分架构和示例索引。
- [固定版本 Quick Start](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/docs/01-quick-start.md)：Calc-X 的本地运行流程，文档要求单机单张 A100 及相应 GPU 依赖；本次未执行。
- [固定版本 Basics](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/docs/05-basics.md)：rollout、事件和三个组件的职责。
- [固定版本 Controller 配置](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/docs/30-controller-configuration.md)：Kubernetes Job、Controller 与 Agent 的网络地址、创建限速及完成后清理。
- [官方文档](https://microsoft.github.io/agent-lightning/stable/)：辅助查阅；页面会更新，具体接口以本地固定提交为准。

后续沿用这个 checkout。源码更新时重新记录 HEAD 与差异，只校准受影响的证据，保留旧步骤的版本与来源。

<a id="current-reading"></a>

## 当前接续（唯一进度记录）

- **阶段**：用户明确开始 [Step 002 · build_job_spec](steps/step-002-build-job-spec/README.md) 的函数阅读，已补齐本步记录结构，完整继承 Step 001 的 `03 + 02` 为八份累计函数记录；前两步原始记录与未知保留。
- **当前观察点**：用户要求再次仔细比较两仓库的完成组数、未完成保留、HTTP 接入与轨迹能力。已核对 Slime 的 fully-async 完成队列和消费者、模式差异、推理暂停与轨迹组装，[当前建议收束 Agent Lightning 的默认通读](references/slime-incremental-reading.md#5-当前建议)，保留 Kubernetes Job 管理参考与具体问题触发的对照价值；不再默认把 trajectory 或异步组收集排为下一课。未新增步骤、未改变任何已读或未知状态。[本轮实现核对](steps/step-002-build-job-spec/04-flow.md#slime-capability-overlap-audit)。
- **个人认识**：已有“五个沙箱接口与 K8sReconciler”的初步关系理解，以及对任务查询的首次表述。原话和未确认的校准分别保存在[起点讨论](#sandbox-and-k8s)与当前函数卡；不把助手解释直接记为已掌握。
- **接续方式**：先在本地步骤 README 试读，按回答展开必要的局部代码并保存形成过程。项目内当前进度只更新本节；未运行集群或训练。

## 首步范围：从控制器入口进入 Kubernetes 任务管理

用户在前述范围讨论后表示“好的那么我们开始吧”，随后要求先看整个 Reconciler 的骨架。`run` 保留为启动定位，当前先连接周期协调、Job 创建、事件观察与状态回写；实际范围和调用导航见 [Step 000 scope](steps/step-000-k8s-controller-entry/01-scope.md)。

| 要确定的事 | 候选内容 |
| --- | --- |
| 核心问题 | 一个待执行的 rollout 怎样变成 Kubernetes Job，运行状态又怎样交回 Agent Lightning？ |
| 整体与局部入口 | `run` 与外层周期循环作为背景；当前从 [1] `_reconcile_once` 的数据来源开始 |
| 后续定位点 | [2] `_create_job` → [3] `build_job_spec`；[4] 观察与事件处理 → [5] `_patch_status`。步骤和函数记录映射在 scope 统一维护 |
| 选择理由 | 这个组件直接连接 rollout 状态与 Kubernetes Job，能承接 Slime 中已经接触过的任务执行、环境生命周期和结果交接问题 |
| 短期记忆重点 | `_reconcile_once` 的两份数据来源、匹配和动作选择；内部创建与回写先保留接口，个人解释按实际回答保存 |
| 停止位置 | 本步先看清 [1] 的主流程；[2]–[5] 按后续步骤展开，Job 模板、网络、资源限制、失败与清理继续按具体问题取舍 |

最初目标尚未明确时提出的 `AgentLightningRayPPOTrainer.fit` 候选已撤回。当前从 Kubernetes 任务执行方向确定首步；需要解释任务来路或训练消费时，再回查训练侧。

## 步骤与记录规则

| 步骤 | 本步核心问题 | 本地正文 |
| --- | --- | --- |
| 000 | 整个 Reconciler 怎样连接任务、Job 与状态？ | [README](steps/step-000-k8s-controller-entry/README.md) |
| 001 | Job 事件怎样被接收，并将数据交给后续处理？ | [README](steps/step-001-watch-job-events/README.md) |
| 002 | rollout 与模板怎样成为可提交的 Job 配置？ | [README](steps/step-002-build-job-spec/README.md) · [scope](steps/step-002-build-job-spec/01-scope.md) |

新问题实际展开时再创建后续步骤；本地 README 是当前试读正文，scope 和函数记录提供导航与回查。

- 每步包含 `README.md`、`01-scope.md`、`02-short-term-memory/`、`03-long-term-memory/` 和 `04-flow.md`；阅读后的任务交接总结按需写入 `05-task-flow.md`。
- Step 000 的函数记录进入 `02`，`03` 仅注明暂无前序继承。下一步再将前一步的 `03 + 02` 合并到新的 `03`。
- 函数卡片按源码路径保存，`overview.md` 只作索引；整体位置和跨函数交接放在步骤 README / scope。
- 用户表述、助手解释、静态源码证据与真实运行证据分别记录。目录建立和资料核对不代表已读懂或已运行。

## 建立依据

用户于 2026-11-03 提出：

> 那么现在开始新建立一个要看的repo吧
> 这一个repo 是本地的agent lightning

本次据此登记实际 checkout，并接入现有阅读制度。

同日用户进一步澄清（节选）：

> 这个repo的目的更多的是和我们读的slime结合在一起
> 因为slime 只有和sanbox相关的一小部分
> 但是我需要通过这个项目来理解k8s的部分

据此更新目标、资料关联与首步候选。此时确认的是跨仓库学习目的。

随后用户确认开始，并明确本地 README 试读方式，完整原话见 [Step 000 的开始记录](steps/step-000-k8s-controller-entry/04-flow.md#start-confirmation)。
