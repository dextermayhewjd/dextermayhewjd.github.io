# 01 · Kubernetes Step 001：从 Sandbox 需求创建 Pod

[步骤入口](README.md) · [前一步总结](../step-000-sandbox-reconcile/05-task-flow.md) · [共享 Kubernetes 基础](../../../../../kubernetes/README.md) · [唯一进度](../../../../README.md#current-reading)

## 1. 阅读目标

**Sandbox 已经存在、要求 Running，但没有对应 Pod 时，控制器在哪里把这份需求变成真正提交给 Kubernetes 的 Pod 对象？**

1. 主攻 SandboxReconciler.reconcilePod 的普通创建路径。
2. 看清“查询现状 → 组装 Pod → 设置归属 → 提交 → 返回”的交接。
3. 读到能区分本地 Pod 结构体、API 中的 Pod 对象和真正运行的容器就停。

## 2. 入口、场景与边界

入口：[reconcilePod 函数卡](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcilePod.md)，对应[源码 1674 行](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L1674)。调用来自 reconcileChildResources:538，接收已有 Sandbox、nameHash 和 wd。

沿用 default/hello-world 的教学对象，固定在以下情况：

1. Sandbox 未删除、未过期，要求 Running；没有所属 Pod，也没有同名占用的 Pod。
2. 没有需要修复的旧 Pod 名称注解；未启用失败 Pod 重建，wd=nil。
3. 无 PVC 模板；镜像来自用户事先填写的 podTemplate。本步不部署仓库中尚带 IMAGE 占位符的示例。
4. API 读取与创建正常返回，不进入并发创建冲突等失败路径。

输入输出先按接口定位：输入是父函数持有的对象；返回是 Pod 指针、time.Duration 和 error。创建成功的正常出口为 pod、0、nil，不能据此断言 Pod Ready。

## 3. 整体位置与本轮展开

<a id="whole-flow"></a>

### 3.1 完整主线：Step 000 与 Step 001 的阅读位置

以下包含 API 事件与组件协作，不是一个同步函数从头执行到底。

图中直接标出两步已经覆盖的阅读范围：

1. **Step 000: read**：已读所在函数的正常路径或字段交接，不代表其调用的底层实现都已读完。
2. **Step 000: role only**：已解释这处调用的职责与结果，内部细节尚未展开。
3. **Step 000: context only**：已作为整体流程的背景说明，没有进入这些组件的源码。
4. **Step 001: read (normal creation)**：本步已讲查询与分支、组装对象、归属与提交、返回四段；仅覆盖正常创建路径，已有 Pod、挂起、失败重建等其他路径未完整展开。以上标记表示阅读历史，不表示已经掌握全部机制。

```text
[1] caller submits Sandbox.spec                # Step 000: context only
      -> Kubernetes API server
      -- watch event --> controller-runtime queue

[2] SandboxReconciler.Reconcile                 # Step 000: read
      -> r.Get(...): read Sandbox               # Step 000: read
      -> save oldStatus / oldResourceVersion   # Step 000: read
      -> r.reconcileChildResources(...)         # Step 000: read
           -> r.reconcilePVCs(...)              # Step 000: role only
           -> r.reconcilePod(...)               # Step 001: read (normal creation)
           -> copy Pod IPs / node name          # Step 000: read
           -> r.reconcileService(...)           # Step 000: role only
           -> r.computeConditions(...)          # Step 000: role only
           -> update sandbox.Status in memory  # Step 000: read
      -> determine next requeue time           # Step 000: read
      -> r.updateStatus(...)                   # Step 000: role only
      -> return ctrl.Result, error              # Step 000: read

[3] scheduler + kubelet + runtime               # Step 000: context only
      -> schedule Pod and run containers
      -> report Pod status
      -- watch event --> queue --> [2] again

[4] caller observes Sandbox.status             # Step 000: context only
      -> uses the environment when usable
      -> shutdown / deletion                   # later scope
```

1. Step 000 已读 [Reconcile](03-long-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.Reconcile.md) 与 [reconcileChildResources](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcileChildResources.md) 的外层关系，当时对 reconcilePod 只看接口职责。Step 001 从父函数 538 行进入，已讲 [reconcilePod 的正常创建路径](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcilePod.md)；直接调用方已调入本步 02。
2. Step 001 对应第 [2] 部分中的 Pod 对象创建；第 [3] 部分负责实际启动容器，本步没有深入其组件源码。
3. 子函数返回后，回到父函数摘取观察字段和计算状态，继续原主线。

**总图的 [1]–[4] 是四个职责区域，不是四个必须依次通读的 Step。** Step 000 读了 [2] 的外层骨架，Step 001 已讲其中 reconcilePod 的正常创建路径；不表示 [2] 的所有内部实现已经读完。

| 总图位置 | 当前需要理解到哪里 | 源码安排 |
| --- | --- | --- |
| [1] 提交 Sandbox | 已有需求通过 API 提交，随后才有协调请求 | 先作为输入边界；SDK/Claim 等具体提交入口后续按使用场景再读 |
| [2] 控制器协调 | Step 000 已讲外层骨架；Step 001 已讲 Pod 正常创建，其他辅助调用仍按原深度标记 | 本主题当前主攻区域；下面 2.1–2.4 全部在这里 |
| [3] 调度与运行 | 创建 Pod 对象之后，Scheduler、kubelet 和运行时继续完成实际启动 | 必须知道职责交接；本轮不读这些组件的内部源码 |
| [4] 调用方使用 | 调用方观察状态，在环境可用后使用，之后释放资源 | 保留最终去向；具体访问、领取和回收在后续范围展开 |

共享基础中的[整体运行流程](../../../../../kubernetes/00-overview/job-lifecycle.md)可用于理解 [1] 与 [3] 的边界，但不要求先把这些区域变成新的源码阅读任务。

<a id="reading-navigation"></a>

### 3.2 本轮骨架：确认缺少 Pod，组装并提交

下面的 **2.1–2.4 都属于总图的 [2]**，是 reconcilePod 内部的局部阅读编号。当前第一处看 2.1，接着沿本函数走到实际创建和返回。

**这四段表示本步范围，不是四项已经完成的记录。** 本步需要沿同一个例子把查询、组装、Create 和返回串起来，再接回父函数；有完整函数卡不代表已经完成这个收束。实际阅读反馈仍以[项目进度](../../../../README.md#current-reading)为准。

这是教学裁剪；省略实参和辅助语句，不是可编译函数。正常路径的前提见第 2 节，不能把省略的分支理解为原代码不存在。

**骨架保留改变数据去向或决定是否创建的调用与分支。** 下列方法是定位入口，不是一份要求全部独立精读的函数清单；实现细节继续看对应函数卡。

```go
// [2.1] 1686-1742：查询候选，确定当前应使用的 Pod
podList := &corev1.PodList{}
if err := r.List(...); err != nil { ... }
ownedPods := sandboxOwnedPods(...)
podName := resolvePodName(...)
pod := &corev1.Pod{}
err := r.Get(...)
if err != nil {
    if !k8serrors.IsNotFound(err) { ... } // 其他读取错误直接返回
    ... // 按需清理过期的 Pod 名称注解
    pod = nil
}

// 将按名称查到的所属 Pod 补入列表，再检查是否有多个所属 Pod。
if pod != nil && isOwnedBySandbox(...) && !containsPod(...) {
    ownedPods = append(...)
}
if len(ownedPods) > 1 { ... } // 返回多个所属 Pod 的冲突错误
if len(ownedPods) == 1 && (pod == nil || pod.Name != ownedPods[0].Name) {
    ... // 按需修复名称对应关系
    pod = ownedPods[0].DeepCopy()
}

// 1744-1936：省略挂起分支和局部函数 reconcileExistingPod 的定义。
if pod != nil {
    return reconcileExistingPod(...) // 1939-1940：已有 Pod，转入相应处理并返回
}
... // 可选的重建退避等待；本例未启用
// 本例 pod=nil，且没有所属 Pod，因此继续创建。

// [2.2] 1953-2027：在内存中组装要创建的 Pod
... // 合并允许使用的标签与注解
mutatedSpec := sandbox.Spec.PodTemplate.Spec.DeepCopy()
var pvcVolumes []corev1.Volume
... // 根据 PVC 模板生成卷引用；本例没有这类模板
mutatedSpec.Volumes = MergeVolumeClaimVolumes(...)
pod = &corev1.Pod{...}
pod.SetGroupVersionKind(...)

// [2.3] 2028-2045：设置归属，再提交给 Kubernetes
if err := ctrl.SetControllerReference(...); err != nil { ... }
if err := r.Create(...); err != nil { ... }

// [2.4] 2059：将 Pod 对象交回调用方
return pod, 0, nil
```

| 位置 | 本轮要弄清什么 | 接下来去哪 |
| --- | --- | --- |
| [2.1 查询与分支](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcilePod.md#find-pod)：1686–1742、1939–1951 | List → sandboxOwnedPods → resolvePodName → Get；合并归属结果后，已有 Pod 交给 reconcileExistingPod，当前无 Pod 才继续创建 | 正常创建分支 1953 |
| [2.2 组装对象](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcilePod.md#build-pod)：1953–2027 | DeepCopy 复制运行配置；MergeVolumeClaimVolumes 合并卷引用；构造 Pod，并用 SetGroupVersionKind 标明类型 | 设置归属 2028 |
| [2.3 归属与提交](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcilePod.md#create-pod)：2028–2046 | SetControllerReference 写入本地归属；Create 提交给 Kubernetes；这两个动作不能合并成“写入归属引用就启动了” | 正常返回 2059 |
| [2.4 返回](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcilePod.md#return-pod)：2059 → 父函数 538 | 返回 pod、0、nil；父函数依次接为 pod、recreateRequeue、podErr | 父函数 547–591 的观察与状态计算 |

2.4 的返回位置在调用方 reconcileChildResources:538，下面这一行**不在 reconcilePod 内部**：

```go
pod, recreateRequeue, podErr := r.reconcilePod(...)
```

1. **归属辅助函数只补当前所需含义。** isOwnedBySandbox 和 containsPod 在这里参与两路结果合并；checkOwnership 位于归属辅助函数内部，不能再画成 reconcilePod 的下一项直接调用。
2. **已有 Pod 分支保留出口，暂不展开内部。** reconcileExistingPod 是本函数内定义的局部函数。本例没有 Pod，不执行它；保留名字和 return 是为了说明为何已有对象不会继续进入创建代码。
3. **元数据准备保留位置，细节按需回查。** 标签/注解过滤、扩展标记传播、排序与日志等仍在源码中。本轮不把每个辅助调用都塞进主骨架；需要回查的清单见下方折叠项。

<details>
<summary>本轮不展开的辅助调用与分支</summary>

| 位置或调用 | 当前处理 |
| --- | --- |
| checkOwnership、sandboxOwnedPods、resolvePodName 的内部 | 所有者判断与名称选择已在当前函数卡就近说明，不再拆新卡 |
| clearPodNameAnnotation、Suspended、sandboxRecreatesFailedPods 与 recreateBackoff | 保留分支位置；本例无旧注解、要求 Running、未启用失败重建 |
| isSystemLabel、isSystemAnnotation | 元数据准备中的保留字段过滤，本轮不展开规则表 |
| computeExtensionPodLabels、computeExtensionPodAnnotations、NormalizeCreatedBy、排序与拼接 | 标签/注解准备，后续遇到扩展归属或传播问题再进入 |
| Create 的 AlreadyExists 处理 | 查询与创建之间可能发生变化；当前读创建成功，冲突兜底后续按问题展开 |
| 日志、追踪与事件记录 | 保留原源码和函数卡的省略说明，当前不深入观测实现 |

</details>

**第一处仍从 reconcilePod 的 2.1 查询和分支骨架定位，重点读到 2.3 的实际创建，再沿 2.4 返回。** 只按接口回查相关辅助函数；当前不预建它们的函数卡。

基础卡点可按需回看 [对象与 API 写回](../../../../../kubernetes/02-resource-model/objects-spec-status.md)、[所有者关系](../../../../../kubernetes/02-resource-model/ownership-and-identity.md)和 [Pod 与就绪](../../../../../kubernetes/03-workloads/pod-node-and-readiness.md)。无需先通读共享专题。

**停止位置**：能指认“对象在哪里组装、归属在哪里设置、哪行提交创建、返回给谁”；既有 Pod 接纳、挂起、失败重建、退避、复杂元数据修复和 kubelet 内部留待具体问题出现。

后续候选 computeConditions 目前只有调用职责说明，位置在父卡的 [3.5 观察状态](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcileChildResources.md#observed-conditions)。它在 reconcilePod 返回后才由父函数调用，不属于当前函数的内部阶段；当前没有独立的 computeConditions 或 computeReadyCondition 函数卡。

<details>
<summary>源码版本与记录范围</summary>

- 本地 /home/fredkeira/projects/agent-sandbox，37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1；本轮核对工作区干净。
- reconcilePod:1674–2060；父函数调用:538；对象组装:2002–2027；归属:2028；Create:2031；返回:2059。
- 用户确认及本轮展开见 [本步过程](04-flow.md#reconcile-pod-first-card)。当前已开始函数级阅读，不表示内部实现已掌握或有真实集群验证。
- [补齐关键分支前的 scope](references/history/2026-11-05-scope-before-branch-navigation.md)保留原骨架；本轮只修正 3.2 导航，3.1 总图与已有函数卡保持。

</details>
