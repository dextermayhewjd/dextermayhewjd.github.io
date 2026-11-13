# SandboxReconciler.reconcilePod

> Step 003 继承：完整承接 [前一步记录](../../../../../step-002-sandbox-readiness/03-long-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcilePod.md)；保留原话、认识时间、来源与未知，原步骤说明属于历史语境。

> Step 002 继承：完整承接 [前一步记录](../../../../../step-001-pod-creation/02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcilePod.md)。以下认识时间、原话和未知保持来源；旧步骤说明属于历史语境。

[本步 scope](../../../../../step-001-pod-creation/01-scope.md#reading-navigation) → [reconcileChildResources：538 行交入](SandboxReconciler.reconcileChildResources.md#pod-and-observation) → **reconcilePod（本页）** → [回到父函数记录 Pod 信息](SandboxReconciler.reconcileChildResources.md#pod-observed-fields)

- 源码定位：[controllers/sandbox_controller.go:1674–2060](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L1674)。
- 首次接触：Kubernetes Step 000 中按职责定位；Step 001，2026-11-05 开始独立阅读正常创建路径。
- 最近认识更新：2026-11-05，用户已明确 namespace 与 nameHash 是 AND 关系，并能概括组装字段和记录归属；当前仍不清楚归属筛选的必要性、resolvePodName 的返回内容，以及 List 与按名 Get 的关系。引用记录的位置与提交边界继续校准。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：父函数已经持有 Sandbox，处理 Pod 时调用本方法。传入的是沙箱需求；对应的 Pod 此时可能存在，也可能不存在。
2. **具体内容**：确认哪些 Pod 对应当前 Sandbox，再按运行模式和现状处理。当前只读 Running 且没有 Pod 的路径：组装 Pod、设置归属、提交创建、返回对象。其他路径仍保留源码位置。
3. **建议构建的心智模型**：

   > 先确认“该使用哪个 Pod、现在有没有”，再决定如何处理。当前例子确实没有，所以把 Sandbox 中的 Pod 模板变成一份新的 Pod 对象，提交给 Kubernetes。
   >
   > 本函数负责这次资源协调；节点选择和容器启动由 Kubernetes 其他组件继续完成。

4. **调用代码**：父函数 538 行接住三个返回值：

   ```go
   pod, recreateRequeue, podErr := r.reconcilePod(ctx, sandbox, nameHash, wd)
   ```

## 本场景的输入与输出

**输入**：沿用本步 default/hello-world 的教学场景。Sandbox 已存在且要求 Running，没有所属 Pod、同名占用或旧 Pod 名称注解；无 PVC 模板，未启用失败重建，wd=nil。podTemplate 中的容器镜像、命令等已经由调用方配置。本页没有实际部署。

| 输入 | 来源与用途 |
| --- | --- |
| r | 同一个协调器，持有 Kubernetes 客户端、Scheme 等依赖 |
| ctx | 父函数传来的操作上下文 |
| sandbox | 已读取的资源对象，提供名称、namespace、UID、运行模式和 podTemplate |
| nameHash | 父函数已从名称生成的标记，用于查询索引和新 Pod 的跟踪标签 |
| wd | 可选写入延迟记录，本例为 nil；主要在已有 Pod 的元数据更新路径使用 |

**本例正常出口**：返回 pod、0、nil。这里的 0 是未请求重建等待，nil 是没有返回错误；不是 Agent 的奖励或完成信号。

| 结果 | 当前含义 |
| --- | --- |
| Pod 对象 | 名称 hello-world、namespace default，运行配置来自 Sandbox 的 PodTemplate，所有者指向这个 Sandbox |
| 集群副作用 | Create 正常返回，已提交创建 Pod；不是只有本地结构体 |
| 暂不能推出 | 容器已经启动、Pod 已有节点/IP、Pod Ready 或业务任务已完成 |
| 回到父函数后 | 使用返回的 Pod 摘取地址和节点信息，再形成 Sandbox 的观察状态 |

### 内部骨架：四段编号沿用 scope 的 2.1–2.4

| 位置 | 本轮动作 | 交出什么 |
| --- | --- | --- |
| [2.1 查询与分支](#find-pod) | 找候选、确认归属、按名读取，确定当前走哪条路径 | 本例 pod=nil，进入创建分支 |
| [2.2 组装对象](#build-pod) | 从 PodTemplate 组装 Pod 的配置与元数据 | 本地的 Pod 结构体 |
| [2.3 归属与提交](#create-pod) | 设置所有者，再调用 Kubernetes Create | API 中的 Pod 对象 |
| [2.4 返回](#return-pod) | 将 Pod、等待时长与错误交回父函数 | 父函数继续观察与状态计算 |

**本页代码片段全部默认展开；详细解释、补充例子和原始讨论按需打开。** 保留当前正常路径的源码节选与省略标记，不扩展成全部失败恢复分支。

<a id="find-pod"></a>

#### 2.1 查询与分支：先确认有没有应当使用的 Pod

本段首先处理的是 **Pod 对象的查找与归属**。它没有开始查询哪台 Node 更适合运行容器。

这里有两次先后执行的查询，中间夹着本地数据处理：

| 顺序 | 实际动作 | 得到什么 |
| --- | --- | --- |
| 1. r.List | 同时用 namespace 和跟踪标签值查候选 | 结果填入 podList；调用返回 error |
| 2. sandboxOwnedPods | 在刚取得的候选中按控制者 UID 筛选 | ownedPods：属于当前 Sandbox 的 Pod 列表 |
| 3. resolvePodName | 从已有 Sandbox 字段决定预期 Pod 名称 | podName：一个字符串 |
| 4. r.Get | 按 namespace + podName 读取那个 Pod | 结果填入 pod，或返回 NotFound / 其他错误 |

**第 4 项不是第 1 项的内部实现。** 两次查询可能找到同一个对象，但第一项能发现一组带标记的候选，第四项定位一个特定名称的对象。

通用概念可回查 [List 与 Get](../../../../../../../../../kubernetes/01-architecture/api-server.md#list-and-get)；本页继续解释这个控制器为何组合两路结果。

入口的日志和 Trace 先省略。1686–1695 行先按 namespace 和跟踪标记找候选：

```go
podList := &corev1.PodList{}
if err := r.List(ctx, podList,
	client.InNamespace(sandbox.Namespace),
	client.MatchingFields{podSandboxNameHashIndex: nameHash},
); err != nil {
	logger.Error(err, "Failed to list pods")
	return nil, 0, fmt.Errorf("pod list failed: %w", err)
}

ownedPods := sandboxOwnedPods(podList.Items, sandbox)
```

**为什么还要筛归属：标签帮助查找，控制者 UID 才确认这里的资源归属。** 例如同名 Sandbox 被删除后重建，名称产生的 nameHash 可以相同，新旧 Sandbox 的 UID 却不同；带旧标签的 Pod 不能因此直接算作新 Sandbox 的所属 Pod。

<details>
<summary>展开列表查询与归属筛选的逐项说明</summary>

1. **准备接收列表**：PodList 是本地对象，用来装查询结果；不是创建一批 Pod。
2. **查询候选 Pod**：InNamespace 与 MatchingFields 是同一次 List 的两个条件：同时要求 namespace 匹配、Pod 的跟踪标签值匹配 nameHash。后者通过预先注册的缓存索引查询。不是先取出整个 namespace 再单独查询 nameHash，也不是检查 Namespace 对象自身有没有这个哈希；nameHash 关联的是 Pod 上的标签。
3. **再确认归属**：sandboxOwnedPods 从候选中筛出确实由当前 Sandbox 控制的 Pod。实际依据是 Pod 的控制者引用中的 UID 是否等于当前 sandbox.UID；相同标签只说明它是候选，不能代替这项检查。这里筛选已有数据，不再发起一次 Pod 查询。
4. **本例的结果**：查询成功，但列表为空，ownedPods 也为空。若查询本身失败，函数直接返回错误，不会把“查询失败”当成“可以创建”。

</details>

随后确实继续执行原文件 **1698–1718 行**。这段先确定预期 Pod 名称，再单独读取该对象；它与上面 List 的代码处于同一个 reconcilePod 函数内：

```go
podName := resolvePodName(sandbox)
_, podNameAnnotationExists := sandbox.Annotations[sandboxv1beta1.SandboxPodNameAnnotation]
if podName != sandbox.Name {
	logger.Info("Using tracked pod name from sandbox annotation", "podName", podName)
}

pod := &corev1.Pod{}
err := r.Get(ctx, types.NamespacedName{Name: podName, Namespace: sandbox.Namespace}, pod)
if err != nil {
	if !k8serrors.IsNotFound(err) {
		logger.Error(err, "Failed to get Pod")
		return nil, 0, fmt.Errorf("pod get failed: %w", err)
	}
	if podNameAnnotationExists {
		logger.Info("Pod referenced by annotation not found, clearing annotation to recover state", "podName", podName)
		if err := r.clearPodNameAnnotation(ctx, sandbox); err != nil {
			return nil, 0, err
		}
	}
	pod = nil
}
```

**resolvePodName 是一个真实的辅助函数，返回“应该查的 Pod 名字”，不是去集群寻找 Sandbox。** 它在 1698 行被调用，定义在同文件 198–203 行：

```go
func resolvePodName(sandbox *sandboxv1beta1.Sandbox) string {
	if name, ok := sandbox.Annotations[sandboxv1beta1.SandboxPodNameAnnotation]; ok && name != "" {
		return name
	}
	return sandbox.Name
}
```

1. 如果已有 Sandbox 注解记录了 Pod 名称，就返回那个名称。
2. 否则使用 sandbox.Name。本例恰好 Pod 和 Sandbox 都叫 hello-world，但返回值在这里用作 Pod 的名字。

读完这个短定义，回到上面的 `podName := resolvePodName(sandbox)`；接下来的 r.Get 才实际读取 Pod。

<details>
<summary>展开按名读取、NotFound 与后续分支的说明</summary>

1. **确定名称**：源码注释 Determine the pod name to look up 表示“确定要查哪个名字的 Pod”。resolvePodName 只从已有 Sandbox 数据计算名称，优先使用 Pod 名称注解；本例没有，因此名称是 hello-world。这个方法本身尚未读取 Pod。
2. **按名读取**：Get 读取 default/hello-world 这个 Pod。它与上面的列表查询互相补充，后面还会综合归属判断；不是只要列表为空就马上创建。
3. **区分不存在和读取失败**：本例返回 NotFound，于是 pod=nil；其他错误直接返回。没有旧注解，所以本例不会执行清除注解。
4. **确定正常创建路径**：后续 1723–1742 行合并查询信息、拒绝多个所属 Pod，并在必要时优先使用唯一所属 Pod。本例两路都没有，仍为 nil；运行模式为 Running，也不进入挂起路径。
5. **越过已有 Pod 的处理**：1777–1936 行定义了一个局部函数 reconcileExistingPod，定义本身不执行它；1939 行仅在 pod 非 nil 时调用。本例跳过，再越过未启用的重建退避，进入 1953 行的创建分支。

</details>

| 当前跟踪的数据 | 本例查询后的值 |
| --- | --- |
| podList.Items | 空列表 |
| ownedPods | 空列表 |
| podName | hello-world |
| pod | nil |
| 下一站 | 2.2：根据模板组装新 Pod |

<details>
<summary>按需回查：为什么既查列表，又按名称读取？</summary>

先区分列表内部的“候选”和“所属”。下面只是说明筛选规则的教学对照，不替换本页两路都为空的创建场景；A、B、H 都是示意值：

| 当前 Sandbox UID 为 A，查询标记为 H | 是否进入 podList.Items | 是否进入 ownedPods |
| --- | --- | --- |
| 当前 namespace 中，Pod 标签为 H，控制者 UID 为 A | 可以 | 是 |
| 当前 namespace 中，Pod 标签为 H，控制者 UID 为 B | 可以 | 否 |

归属检查的实现在 checkOwnership 中读取控制者引用，再比较 UID。第二种候选未进入 ownedPods，也不代表调用方就一定能创建：后面还要按名称读取，处理名称占用与整体分支。

两次查询各自补充的场景：按名称可能读到一个尚未出现在标签索引里的对象；按标签则可能发现一个名字与旧记录不同、但确实属于当前 Sandbox 的 Pod，或者发现多个所属 Pod。代码需要综合两路结果，不能将其中一种“没查到”直接等同于完全不存在。

按跟踪标记查列表，可以发现一个或多个所属 Pod；按名称读取，可以取得预期对象，包括标签索引暂时没有反映的对象。后面综合两路信息：若有多个所属 Pod，报映射冲突；若有一个所属 Pod，则优先使用它，避免因名称注解过旧等原因误建另一份。

这仍不使“查询→创建”成为原子操作。提交时的 AlreadyExists 分支另外处理查询之后出现同名对象的情况；当前正常路径先保留该边界，不展开并发兜底。

源码入口：[sandboxOwnedPods:176](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L176)、[resolvePodName:198](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L198)、[归属合并与冲突判断:1723](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L1723)。本轮不另建辅助函数卡。

</details>

<a id="build-pod"></a>

#### 2.2 组装对象：把模板变成本地 Pod 结构体

确认走创建路径后，1953–2027 行准备元数据和 Pod.Spec；此时仍在组装要提交的对象。

1955–2000 行准备 podLabels 和 annotations：合并模板允许的标记，并写入控制器的跟踪信息。下面从 2002 行接着看；PVC 模板循环在本例为空，节选略去循环体。

```go
mutatedSpec := sandbox.Spec.PodTemplate.Spec.DeepCopy()

var pvcVolumes []corev1.Volume
// ... loop over VolumeClaimTemplates; empty in this scenario ...
mutatedSpec.Volumes = MergeVolumeClaimVolumes(mutatedSpec.Volumes, pvcVolumes)
pod = &corev1.Pod{
	ObjectMeta: metav1.ObjectMeta{
		Name:        sandbox.Name,
		Namespace:   sandbox.Namespace,
		Labels:      podLabels,
		Annotations: annotations,
	},
	Spec: *mutatedSpec,
}
pod.SetGroupVersionKind(corev1.SchemeGroupVersion.WithKind("Pod"))
```

这里把 metadata 和 spec 装进同一个本地 Pod；调用 Create 之前，还没有提交集群创建。

<details>
<summary>展开模板、元数据与 Pod 对象的交接说明</summary>

1. **复制运行配置**：容器 image、command、资源请求等来自 PodTemplate.Spec。DeepCopy 产生独立配置副本，避免直接修改 Sandbox 持有的模板。
2. **接入存储引用**：有 PVC 模板时会把引用合并进 Pod 的 volumes；本例没有，保留模板本身的卷配置。这里不创建 PVC。
3. **组装 Pod**：名称和 namespace 沿用 Sandbox，Labels 与 Annotations 使用前面准备的数据，Spec 放入复制后的运行配置。这里同时填写 metadata 与 spec 两个不同部分，并不是把运行配置都塞进 metadata。
4. **写明类型**：设置为核心 API 的 Pod。到这里仍是程序内的对象，下一段才提交创建。

| 新 Pod 的部分 | 本例怎样填写 |
| --- | --- |
| metadata | 名称、namespace、标签与注解；下一段还会加入所有者引用 |
| spec | 复制 PodTemplate.Spec 中的容器镜像、命令、资源请求等运行配置，按需合并卷引用 |

标签与注解的过滤细节、存储合并实现按问题回查；本轮重点是输入模板怎样进入输出 Pod。

</details>

<a id="create-pod"></a>

#### 2.3 归属与提交：先设置所有者，再创建集群资源

2028 行修改本地 Pod 的所有者信息，2031 行才调用客户端提交创建。

**这里的 reference 是资源之间的归属记录：这个 Pod 由哪一份 Sandbox 控制。** 它保存在 Pod 的 metadata.ownerReferences 中。前面的 sandboxOwnedPods 读取这种关系来筛选已有 Pod；这里为新 Pod 写入这种关系，使下一轮也能认出它。

共同机制见[归属引用的写入与读取](../../../../../../../../../kubernetes/02-resource-model/ownership-and-identity.md#write-and-read-owner-reference)，当前代码及个人表述仍保留在本页。

```go
if err := ctrl.SetControllerReference(sandbox, pod, r.Scheme); err != nil {
	return nil, 0, fmt.Errorf("SetControllerReference for Pod failed: %w", err)
}
if err := r.Create(ctx, pod, client.FieldOwner(sandboxControllerFieldOwner)); err != nil {
	// ... AlreadyExists recovery, logging and event recording omitted ...
	return nil, 0, err
}
```

上段对 Create 错误体做了裁剪：原代码遇到 AlreadyExists 会先读取已有 Pod 并交给已有对象处理路径；本例没有错误，不经过该分支。

你概括的“记录这个 Pod 归哪个 Sandbox”对应第一条调用。记录写在 **Pod 自己的 metadata.ownerReferences** 中，第二条 Create 把这份记录连同 Pod 一起保存到 Kubernetes；并非只记在控制器进程自己的私有表里。

<details>
<summary>展开归属、事件关联与创建边界的说明</summary>

1. **设置归属**：SetControllerReference 把当前 Sandbox 的控制者引用写到 pod 的元数据。它不是向集群创建资源的调用。
2. **提交创建**：r.Create 使用客户端向 Kubernetes API 提交这个 Pod。正常返回后，已创建对应 API 对象。
3. **区分两种 owner**：SetControllerReference 记录资源之间的控制归属；FieldOwner 参数用于字段管理身份，不能把二者当作同一件事。
4. **保留运行边界**：创建成功后，Scheduler、kubelet 和运行时继续推进；这里没有等待 Pod Ready 的循环。

例如，本页的 Sandbox 名为 hello-world，假设它的 UID 为 A。SetControllerReference 会让新 Pod 的控制者引用指向这份 Sandbox，包含其类型、名称、UID 和控制者标记；A 仅为教学示意。它是 API 对象的关联信息，不是 Go 的内存地址，也不是另建一个 Sandbox。

这条关系有三处用途：

1. 后续查询时，控制器可以通过控制者 UID 判断该 Pod 是否属于当前 Sandbox；这与本页 2.1 的归属筛选相接。
2. 控制器注册了 Owns(Pod) 的观察后，可借助归属把 Pod 变化关联回相应 Sandbox；不是这行设置引用就立即触发一次同步调用。
3. 所有者引用也供 Kubernetes 垃圾回收处理依赖关系；实际删除仍受传播方式等条件影响，不在这里承诺立即回收。

因此，前面的模板回答“这个 Pod 怎样运行”，这里的引用回答“这个 Pod 属于谁”；二者一起随下一条 Create 提交。

通用解释：[对象与 API 写回](../../../../../../../../../kubernetes/02-resource-model/objects-spec-status.md)、[资源所有者](../../../../../../../../../kubernetes/02-resource-model/ownership-and-identity.md)。

</details>

<a id="return-pod"></a>

#### 2.4 返回：把这次协调的结果交回父函数

正常创建后的事件记录和 Trace 先省略；2059 行是本例出口：

```go
return pod, 0, nil
```

本例把已提交创建的 Pod 对象交回父函数，容器调度与启动仍由 Kubernetes 后续推进。

<details>
<summary>展开三个返回值及父函数的后续处理</summary>

1. pod 交给父函数用于摘取地址、节点等信息，刚创建时这些字段仍可能为空。
2. 0 表示本次没有返回重建等待时长；nil 表示本例创建没有返回错误。
3. 父函数继续计算观察状态，再由外层 Reconcile 按需写回 Sandbox.status。

返回 [reconcileChildResources 的运行信息段](SandboxReconciler.reconcileChildResources.md#pod-observed-fields)。运行与就绪的区别可回查 [Pod、节点与就绪](../../../../../../../../../kubernetes/03-workloads/pod-node-and-readiness.md)。

</details>

## 我的直接表述（原话）

本轮确认进入该函数，以下节选用户第二项要求：

> 2.好的那么我们现在看一下这里第二step001的部分吧
> 看一下这里的reconcilepod具体在做什么吧

建卡时尚无对本函数内部机制的独立复述；后续实际表述保留在下方。不将读卡、源码核对或开始阅读记为已经掌握。

<details>
<summary>对查询、组装及 reference 的当前理解与疑问</summary>

> 好的
> 我简单地理解一下
> 1.先通过这里第一步在namespace里面查询
> 然后再看在这个namespace是否有这个namehash?
>
> 2.然后查看第二个代码注释是在做什么呢?
>
> 看看是否能够拿到这个pod?
>
> 3. 如果要创造的话就通过template和spec来具体
> 写下meta data 需要的内容?
>
> 后面我其实就不是特别理解
> 这里在做什么为什么还需要一个reference?

助手校准：namespace 与标签值在同一次 List 中共同限定候选，随后在内存中筛归属；resolvePodName 确定名称，Get 才读取 Pod。组装分别填写 metadata 与 spec，SetControllerReference 再记录新 Pod 对 Sandbox 的控制归属。前面的归属读取与后面的归属写入相接，说明尚待用户反馈。

</details>

<details>
<summary>代码默认展开，以及两路查询为何同时存在的追问</summary>

> 展开式这里所有的代码的部分吧
> 缩进别的部分比较好?
>
> 我来理解一下
> 1.首先这里的rlist通过两个条件
> 一个是namespace另一个是跟踪值是namehash
> 好的我理解了
> 是and的关系
>
> 2.为什么这里的sandboxownedpods?
> 会需要考虑pod是否属于这个sandbox
> 为什么会这么操作?
>
> 3.这里在1698–1718 行 真的有出现吗? 我没理解
> 这个resolvedpodname是一个特定的function对吗?
> 是转梦通过sandbox的数据来找到sandbox的名字?
>
> 4. 最后这里在做什么呢?
> 我其实有点没有理解
> 这里的这个reconcilepod内容还是蛮多的
>
>
> 我最后再看一遍吧
> 这里的首先通过pod来查询这里的这个pod中pod是否都存在
> 然后在查看是否是sandbox控制的pod
>
> 然后1698开始的内容是
> sandbox相关的部分
> 寻找这里的pod by podname
> 但是这里的不就是和上面的内容一样了吗?
> 还是下面是上面的部分代码的具体实现?
>
> 后续组装对象其实比较好理解
> 吧这个pod需要的星系
> 类似于namespace和label和annotation什么的都写清楚包括这里的数据也放在这里都写清楚
>
> 最后在让这里的controleer记录一下这个pod归那个sandbox
> 是我的理解
> 创建一个reference

用户已经明确说清组合查询的 AND 关系，并概括了字段组装和归属记录。助手继续澄清：列表筛选、归属过滤与按名读取不是嵌套实现；resolvePodName 返回 Pod 名称；引用记录在 Pod 元数据中，随后随 Create 持久化。后续区分尚待反馈。

</details>

## 尚不清楚

1. 用户已说清 namespace 与跟踪标签是 AND 条件；仍不清楚为什么筛归属后还要按名称查询，以及两路结果怎样接到 pod=nil。
2. 用户已能概括 Pod 字段组装；PodTemplate、Pod 本地结构体、Create 和真正容器运行之间的界线继续保留核对。
3. 已有 Pod 接纳、挂起、失败重建和并发 AlreadyExists 的细节暂未展开。
4. 用户已将 reference 概括为记录 Pod 所属 Sandbox；记录在 Pod 元数据中、随 Create 持久化及后续归属筛选的关系仍需校准。

<details>
<summary>来源、验证与当前阅读边界</summary>

- 固定源码：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1；本地 /home/fredkeira/projects/agent-sandbox；工作区核对干净。
- 主要范围：查询与分支 1686–1742；已有对象路径 1777–1941；创建准备 1953–2027；归属与提交 2028–2046；正常返回 2059。
- 缓存索引由 SetupWithManager 预先注册；本轮按用途理解 MatchingFields，不展开客户端缓存实现。
- 归属判断的核对位置：checkOwnership:132–141、isOwnedBySandbox:144–149、sandboxOwnedPods:176–183。教学对照只展示筛选结果，没有调用集群或改变本例创建场景。
- resolvePodName 的完整短定义来自同文件 198–203 行，调用处为 1698 行；作为当前入口的辅助说明保存在本卡，没有新建独立函数卡。
- [代码默认展开前的历史版本](../../../../../step-001-pod-creation/references/history/2026-11-05-reconcile-pod-before-code-visible.md)保留此前正文；本次将代码移出折叠，长解释与例子保留。
- [Kubernetes Step 001 · 本轮问题与阅读过程](../../../../../step-001-pod-creation/04-flow.md#reconcile-pod-first-card)。
- [岗位目标与辅助函数的阅读深度](../../../../../../../../references/tencent-k8s-learning-scope.md#helper-reading-depth)。
- 本页为静态源码核对与教学场景，没有查询真实 Pod、调用 Create 或运行容器。错误分支的省略不等于原实现不存在。

</details>
