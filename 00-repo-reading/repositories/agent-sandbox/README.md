# Agent Sandbox：阅读入口

[通用方法](../../README.md) · [工作流](../../workflow.md) · [Kubernetes 共享基础](../kubernetes/README.md) · [当前接续](#current-reading)

## 目标与范围

当前进入独立主题 [Kubernetes 沙箱资源与生命周期](topics/kubernetes-sandbox-control/README.md)，从[本主题 Step 000](topics/kubernetes-sandbox-control/steps/step-000-sandbox-reconcile/01-scope.md)开始。旧 Fleet 步骤已归入 [Fleet 主题](topics/fleet-environment-orchestration/README.md)；本项目采用[主题内编号、按需跨主题引用](AGENTS.md)，不再默认跨主题继承全部记忆。

**当前目标已确认**：补足腾讯混元 Agent 强化学习框架岗位所需的 Kubernetes 沙箱工程能力，重点理解并验证环境的创建、就绪、领取、使用、失败处理和回收。核心阅读与实践边界见[五项学习主线](references/tencent-k8s-learning-scope.md)；任务级前瞻和训练调度另以 Slime/Dressage 对照，原步骤与学习历史保留。


本目录保存 Agent Sandbox 的源码阅读记录。此前在 2026-11-03，用户明确希望围绕大规模强化学习中的 Kubernetes 预热、不同环境与题目的抽象、Agent/安全示例与腾讯岗位的对应关系来读。具体核对见[RL 环境供给与岗位对照](references/rl-environments-and-jd.md)；2026-11-04 经完整批次流程核对，用户确认 [Step 000](topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/01-scope.md) 从 run_naive 开始。继续在本地 Markdown 中试读。

最新范围澄清见[目标、12 组材料与观察问题的对应](references/rl-environments-and-jd.md#learning-scope)：12 组是材料索引，后续 rollout/Ready/取消/回收问题是读这些材料时的观察点，不另加一套必读课程。当前做岗位相关的源码学习选题，尚未要求实施与 Slime 的代码集成。

根据项目 README，Agent Sandbox 通过 Kubernetes 的 `Sandbox` CRD 与 controller 管理具有稳定身份的有状态单 Pod 工作负载，适用于 Agent 运行环境等场景。它负责沙箱编排，底层隔离取决于实际配置的容器运行时；gVisor、Kata Containers 是可选方案，创建 Sandbox 本身不等于启用了这些隔离机制。以下是助手核对源码后的定位，不代表用户已经掌握。

## 1. 接回此前的学习主线

此前 Agent Lightning 的 K8s Controller 将 Gateway 中登记的 rollout 对应到 Kubernetes Job，由 Kubernetes 的 Job controller 管理 Pod，再将执行状态写回 Gateway。此前比较见 [Slime 与 Agent Lightning 的学习增量](../agent-lightning/references/slime-incremental-reading.md)。

这里新增的核心关系是：**用 Kubernetes 自定义资源 `Sandbox` 表达所需环境，由 Sandbox controller 协调 Pod、按配置需要的存储和 Service，并将观察结果写回 Kubernetes 中的 `Sandbox.status`。** CRD 是向 Kubernetes 注册这种自定义资源类型的定义；一份具体 Sandbox 对象才表示一个需要管理的环境。

此前通过 Fleet 认识训练侧怎样使用环境；现在按已确认目标，将单个 Sandbox 的资源与状态协调作为下一处核心入口，再接 WarmPool 与 Claim。原有 Python 预热细节保留为按需回查。

## 2. 当前核对到的核心骨架

以下序号只是职责定位，不是已确认的 Step 编号，也不是五次同步函数调用：

1. 用户通过 Kubernetes API 提交 `Sandbox` 对象，`spec.podTemplate` 描述要运行的 Pod。
2. `SetupWithManager` 注册对 Sandbox 及其所拥有的 Pod、Service 的观察；controller-runtime 将相关对象变化转换为协调请求。
3. `SandboxReconciler.Reconcile` 按请求中的 namespace/name 读取一个 Sandbox；正常且未过期时调用 `reconcileChildResources`。
4. `reconcileChildResources` 依次协调 PVC、Pod、Service，并根据观察到的资源计算 Sandbox 的 conditions。真正把 Pod 调度到节点并运行容器，仍由 Kubernetes 的调度器、kubelet 和运行时负责。
5. `Reconcile` 通过 `updateStatus` 按需写回 `Sandbox.status`，向 controller-runtime 返回结果与错误；后续事件或重新排队继续推动协调。一次返回不代表 Pod 已经就绪。

源码依据固定在下方登记的提交：

- [Sandbox API 类型](https://github.com/dextermayhewjd/agent-sandbox/blob/400df364753adb9e36a61f93c506166856998590/api/v1beta1/sandbox_types.go#L338)。
- [Reconcile](https://github.com/dextermayhewjd/agent-sandbox/blob/400df364753adb9e36a61f93c506166856998590/controllers/sandbox_controller.go#L366) → [reconcileChildResources](https://github.com/dextermayhewjd/agent-sandbox/blob/400df364753adb9e36a61f93c506166856998590/controllers/sandbox_controller.go#L507)。
- [reconcilePod](https://github.com/dextermayhewjd/agent-sandbox/blob/400df364753adb9e36a61f93c506166856998590/controllers/sandbox_controller.go#L1674)：直接管理 Pod；创建分支通过 `SetControllerReference` 设置归属并调用 `Create`。
- [updateStatus](https://github.com/dextermayhewjd/agent-sandbox/blob/400df364753adb9e36a61f93c506166856998590/controllers/sandbox_controller.go#L928)：通过 `r.Status().Patch` 更新 Sandbox 状态。
- [SetupWithManager](https://github.com/dextermayhewjd/agent-sandbox/blob/400df364753adb9e36a61f93c506166856998590/controllers/sandbox_controller.go#L2414)：注册观察与 reconciler。

## 3. Step 000 已建立的整体调用骨架

前一阶段沿用现有目录结构，从 [main](topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/02-short-term-memory/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md) 进入 [SandboxFleet.run](topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.run.md)，再接 [run_naive](topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md)。对象模型由 [SandboxFleet 类卡](topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/02-short-term-memory/classes/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.md)说明；构造与任务加载各有已读方法记录，其余材料在[备用区](topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/references/reserve/README.md)，当前范围见 [scope](topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/01-scope.md)。

- 输入：已配置并登记任务的 Fleet、任务处理函数、并发度、清理开关及执行器。
- 本步问题：调用方怎样提供任务与处理函数，整批运行怎样安排准备、执行和清理？
- 停止位置：看清当前编排入口之间的交接及各自的主要调用；子函数先按接口理解。
- Step 000 记录：五张函数/方法卡和一张 SandboxFleet 类卡，已随前一步的 03 + 02 继承到 Step 001 的 03。

完整流程和历史判断见[批次流程核对](references/rl-batch-flow-and-entry.md)。此前已经发生的讨论、原话和未知保留，当前范围收窄不清零已有认识。

## 源码与资料

| 项目 | 2026-11-03 核对结果 |
| --- | --- |
| 本地 Git 根目录 | `/home/fredkeira/projects/agent-sandbox` |
| 分支 | `main` |
| 固定提交 | `400df364753adb9e36a61f93c506166856998590` |
| 提交日期与标题 | 2026-11-03 · `docs: document Kubernetes version requirements (#1892)` |
| 工作区 | 登记时干净；本次仅核对仓库信息与 README |
| origin | `git@github.com:dextermayhewjd/agent-sandbox.git` |
| 上游项目 | [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox) |

- [固定版本 README](https://github.com/dextermayhewjd/agent-sandbox/blob/400df364753adb9e36a61f93c506166856998590/README.md)：项目定位、核心资源、扩展能力与安装说明。
- [官方文档](https://agent-sandbox.sigs.k8s.io/docs/)：辅助查阅；页面会更新，后续源码证据以记录的固定提交为准。
- [记忆格式规范](../../memory-format.md)：后续函数记录与跨步骤继承沿用通用格式。

后续沿用这个 checkout。源码更新时重新核对 HEAD 与工作区差异，保留旧步骤的版本和来源。

同日复核已更新到 `37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1`（`feat(go-sdk): add mkdir, move and copy to files (#2156)`），工作区干净。本次 RL/examples 分析绑定新版本；上表和第 2 节保留初次登记的版本。两版的核心 controllers/extensions 无差异。

<a id="current-reading"></a>

## 当前接续（唯一进度记录）

- **当前主题**：[Kubernetes 沙箱资源与生命周期](topics/kubernetes-sandbox-control/README.md)。按用户 2026-11-05 授权独立组织，旧 Fleet 方向保留为回查资料。
- **当前步骤**：[Kubernetes Step 003 · 状态写回与版本冲突](topics/kubernetes-sandbox-control/steps/step-003-status-writeback/01-scope.md)。用户已确认进入 updateStatus，本步仍在总图 [2]，从内存观察接到 API 持久化。
- **当前函数与问题**：[SandboxReconciler.updateStatus](topics/kubernetes-sandbox-control/steps/step-003-status-writeback/02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.updateStatus.md)。围绕旧 Ready=False、新 Ready=True，看是否需要写、补丁依据、Patch、冲突与返回；当前是首轮讲解，尚无内部机制的个人复述。
- **前一步认识**：Step 002 已按状态汇总与 Ready 普通路径[收束](topics/kubernetes-sandbox-control/steps/step-002-sandbox-readiness/05-task-flow.md)。用户已概括 Pod 和按需 Service 两项主判断，前置限定与未确认细节分别保留。
- **后续方向**：完成本步后再接既定 WarmPool 主线。按本次范围整理，已准备 [Step 004 预热池](topics/kubernetes-sandbox-control/steps/step-004-warmpool-reconcile/01-scope.md)、[Step 005 Claim](topics/kubernetes-sandbox-control/steps/step-005-claim-ownership/01-scope.md)、[Step 006 访问与隔离](topics/kubernetes-sandbox-control/steps/step-006-access-and-isolation/01-scope.md) 的 scope；尚未展开阅读或建立这些步骤的函数卡。
- **已有背景与边界**：computeConditions 已讲汇总，用户明确状态计算不执行调度；其卡与未知保留。其他三个条件函数和辅助诊断方法仍按职责理解，没有提前建卡。
- **累计背景与共享基础**：本步 03 按前一步 03 + 02 合并继承五张完整函数卡，原话、来源与未知保留；通用概念继续引用[共享专题](../kubernetes/README.md)。
- **目标与边界**：沿用[岗位导向的五项范围](references/tencent-k8s-learning-scope.md)。本步不进入 WarmPool/Claim、完整调度器、过期/挂起和复杂失败恢复。
- **记录规则**：主题独立编号；本步 02 新增 updateStatus，并从 03 调取直接调用方 Reconcile。其他背景保存在 03，不跨主题整套复制，不预建辅助函数卡。
- **此前学习与证据**：旧 Fleet Step 000 已按整体骨架范围收束；旧 Step 001 保留其已读内容与未完成机制。Dressage 比较与局部假环境实验继续保留；尚无本主题真实集群运行证据。

## 主题与步骤入口

| 入口 | 内容 |
| --- | --- |
| [Kubernetes 主题](topics/kubernetes-sandbox-control/README.md) | 当前主题；实时入口见上方“当前接续”，各步索引保存在主题入口 |
| [Fleet 主题](topics/fleet-environment-orchestration/README.md) | 原 Step 000、001：应用侧调用骨架、预热入口和任务匹配；原进度与未知保留 |

主题内继续使用 scope、02 短期记忆、03 本主题前序记忆和 04 过程记录；需要时形成 05 任务总结。新主题的编号不改变旧步骤编号，引用 Step 000 时需同时注明主题。

## 建立依据

用户于 2026-11-03 提出：

> 创建一个关于agent sandbox的repo folder吧

据此建立项目入口，并登记本机同名源码仓库。

同日用户继续提出：

> 好的 那么我们再看一下这里的这个agent sandbox吧?

本次据此补充源码定位与首步建议；没有把建议记为已确认范围或已掌握内容，也没有执行集群实验。
