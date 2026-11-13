# SandboxReconciler.reconcileChildResources

[本步 scope](../../../../01-scope.md#reading-navigation) → [Reconcile：458 行进入](SandboxReconciler.Reconcile.md#child-resource-call) → **reconcileChildResources（本页）** → [回到 Reconcile：安排后续协调与状态写回](SandboxReconciler.Reconcile.md#after-child-resources)

基础回查：[所有者关系](../../../../../../../../../kubernetes/02-resource-model/ownership-and-identity.md) · [Pod 与就绪](../../../../../../../../../kubernetes/03-workloads/pod-node-and-readiness.md) · [PVC 与挂载](../../../../../../../../../kubernetes/04-runtime-environment/volumes-and-pvc.md) · [Service](../../../../../../../../../kubernetes/04-runtime-environment/service-and-pod-address.md)。本函数的代码、解释、原话和未知继续保留在下文。

- 源码定位：[controllers/sandbox_controller.go:507–594](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L507)。
- 首次接触：Kubernetes 主题 Step 000，2026-11-05；此前在父函数中按接口认识，本轮开始单独阅读。
- 最近认识更新：2026-11-05，用户已尝试串联 PVC、Pod、Service 和条件计算，但将整体理解为容量、节点、网络检查；本次校准为按需求协调资源、摘取观察信息并形成状态，仍待确认。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Reconcile 已经读出一份 Sandbox，并保存旧状态。本页沿未删除、未过期、要求 Running 的普通路径，进入它的子资源协调。
2. **具体内容**：依次调用 PVC、Pod、Service 的协调方法，整理 Pod 的地址和节点信息，计算状态条目，最后交回重排延迟与错误。具体资源操作由各自的子函数完成。
3. **建议构建的心智模型**：

   > **根据 Sandbox 的需求维护所需资源，记录观察到的状态，再将延迟和错误交回 Reconcile。**
   >
   > 根据这份 Sandbox 的需求，检查现有子资源并执行必要的创建或调整，再把本次观察到的情况整理进同一个 Sandbox 的内存状态。返回外层后，由 updateStatus 按需写回 Kubernetes。
   >
   > 协调包含实际资源操作；状态既能记录就绪，也能记录未就绪或失败。不是等容量、节点、网络全部检查通过后才写状态。

4. **调用代码**：来自 Reconcile:457–458，当前 wd 为 nil。

   ```go
   var recreateRequeue time.Duration
   recreateRequeue, err = r.reconcileChildResources(ctx, sandbox, wd)
   ```

## 本场景的输入与输出

### 1. 进入时有什么

沿用父卡的教学场景：default/hello-world 已提交，要求 Running，没有 shutdownTime，未启用失败 Pod 重建，WriteBehindWindow=0；没有 volumeClaimTemplates，也未请求自动创建 Service。本例另假设没有遗留 Service。这里只静态阅读，没有运行集群。

| 输入 | 本次含义 |
| --- | --- |
| r | 同一个 SandboxReconciler，持有 Kubernetes 客户端等依赖 |
| ctx | 当前操作的上下文，继续传给资源协调方法 |
| sandbox | 父函数已读出的 Sandbox 指针，带 Spec、Status 和身份信息；不是重新创建的空对象 |
| wd | 可选的写入延迟记录，本场景为 nil；其机制不在本轮展开 |

父函数保存的 oldStatus 和 oldResourceVersion 没有传入这里；它们留在父函数中，供稍后写回状态使用。

### 2. 离开时留下什么

| 结果 | 在哪里 | 交给谁 |
| --- | --- | --- |
| 子资源操作 | 协调方法按需向 Kubernetes 操作 Pod 等对象；已有符合要求的对象可以继续使用 | Kubernetes 后续调度、启动或维护这些资源 |
| 本次观察状态 | 同一个 sandbox.Status：包括 PodIPs、NodeName、LabelSelector、Conditions 等；Service 方法也会维护相关状态字段 | 父函数后续调用 updateStatus 持久化 |
| recreateRequeue | 第一个返回值，类型为 time.Duration，来自 Pod 协调 | 父函数用于计算下次协调时间 |
| allErrors | 第二个返回值，类型为 error，汇总需要交回的协调错误 | 父函数合并处理，最终交给 controller-runtime |

**pod 和 svc 是本函数内部使用的资源对象；本函数并不返回它们，也不返回新的 Sandbox。** 若本次无错误且没有重建等待，返回值可以是 0、nil，Pod 仍可能尚未 Ready。

<a id="stage-framework"></a>

### 3. 按执行顺序看这六段

先用这张表定位每段的动作和结果，再按同名标题进入下面的源码。原来合在一起的 Pod 协调与信息摘取，现在分别放在 3.2 和 3.3；代码仍按原执行顺序阅读。

| 编号与标题 | 这一段留下什么 | 源码位置 |
| --- | --- | --- |
| [3.1 存储申请：按配置协调 PVC](#storage-preparation) | 需要的 PVC 申请对象，以及处理错误 | 509–535 |
| [3.2 运行对象：协调 Pod，处理对应关系冲突](#pod-and-observation) | pod、recreateRequeue、podErr，以及冲突标记 | 538–545 |
| [3.3 运行信息：记录 Pod 地址与节点名称](#pod-observed-fields) | 更新内存中的 PodIPs、NodeName、LabelSelector | 547–559 |
| [3.4 访问入口：按配置协调 Service](#service-reconciliation) | svc、处理错误与相关状态字段 | 563–568 |
| [3.5 观察状态：计算并更新 Conditions](#observed-conditions) | 更新内存中的状态条目，包括未就绪或失败说明 | 571–591 |
| [3.6 返回外层：交回延迟与错误](#return-to-reconcile) | 返回 Reconcile，随后由外层安排重排与状态写回 | 593 |

**先从 3.1 接住输入，再按需展开后续段落。** 每段只说明当前函数怎样交接，不要求同时读完所有子函数。

<a id="storage-preparation"></a>

#### 3.1 存储申请：按配置协调 PVC

源码：509–535。根据 Sandbox 声明的存储需求，查找或创建对应的存储申请对象，并记录处理错误；当前无存储模板时，没有需要创建的 PVC。

**这一段要解决的是：如果沙箱需要一份独立保存数据的存储，先把对应的存储申请在 Kubernetes 中准备好。** nameHash 是为后面的资源标记做准备，真正处理存储申请的是 reconcilePVCs。

先补上 PVC 的含义：容器中运行的程序可能需要保存工作文件，希望替换 Pod 后还能继续使用这些数据。可以在 Sandbox 配置里声明存储需求，例如容量，再让容器把对应存储挂载到一个目录使用。这里的 PVC，全称 PersistentVolumeClaim，就是 Kubernetes 管理的这份**持久化存储申请对象**。

PVC 记录需求，实际存储由集群的存储机制提供或匹配；后续 Pod 引用它，容器才通过挂载目录读写数据。因此，这一段准备申请对象，后面的 Pod 阶段配置如何使用；提交 PVC 不等于已经分配好存储或完成挂载。

这里没有检查节点磁盘剩余容量或读取 PVC 的绑定容量来验收。它管理的是存储申请对象；容量能否得到满足，还需要集群存储机制继续处理。

下面为源码节选；省略的 recordChildErr 定义在本页末尾折叠保存。这段不是独立可编译的程序。

```go
nameHash := NameHash(sandbox.Name)

var allErrors error
var conditionErrors error

// ... recordChildErr definition omitted; see below ...

recordChildErr(r.reconcilePVCs(ctx, sandbox, nameHash))
```

按实际执行顺序拆开看：

1. **从名称算一个标记。** NameHash 把 sandbox.Name 转成固定 8 位的十六进制字符串，保存在 nameHash。后面创建 PVC 等资源时，会把它写进标签，帮助查找与关联。这一行只计算字符串，不访问集群，也没有创建 PVC；标签不是全局唯一身份，资源归属还有单独检查。
2. **准备两份错误记录。** allErrors 和 conditionErrors 初始都是 nil，表示目前没有记录到错误。一份供最后返回，一份供后面形成状态说明；为什么分两份可先留在[错误处理折叠项](#child-errors)中。
3. **执行存储申请的协调。** reconcilePVCs 从已经传入的 sandbox.Spec.VolumeClaimTemplates 读取需求。没有条目就不需要创建；有条目时查找对应 PVC，已存在则检查归属、按规则接纳或继续使用，不存在才提交创建。它向 Kubernetes 产生操作，返回值则只说明处理有没有出错。
4. **接住并记录错误。** 内层 reconcilePVCs 执行完，返回的 error 才传给外层 recordChildErr。nil 表示本次处理没有错误，记录函数直接返回；非 nil 才按规则加入错误记录。recordChildErr 本身不创建 PVC，也不执行重试。

原文最后一行是**先执行内层，再调用外层**。为了看清顺序，可以这样展开理解；pvcErr 是教学时加的临时变量，原源码没有这一行赋值：

```go
// Teaching expansion of the nested call; not a source excerpt.
pvcErr := r.reconcilePVCs(ctx, sandbox, nameHash)
recordChildErr(pvcErr)
```

**回到当前例子**：hello-world 没有配置 volumeClaimTemplates，所以 reconcilePVCs 的处理列表为空，返回 nil；recordChildErr 不添加错误，然后继续第 3.2 段的 Pod 协调。这里不会为了“每个沙箱都要有存储”而自动创建一个 PVC，也没有等待存储就绪的循环。

<details>
<summary>需要具体例子时展开：声明 1Gi 存储之后，会产生什么、怎样使用？</summary>

这是仓库中另一个[已有存储配置的例子](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/sandbox-ksa/sandbox.yaml)，用于解释用途，不替换本页无 PVC 的 hello-world 主场景。

1. Sandbox 名为 sandbox-example，其 volumeClaimTemplates 声明一个名为 my-pvc、容量为 1Gi 的存储申请模板。
2. reconcilePVCs 据此查找或创建名为 my-pvc-sandbox-example 的 PVC。名称由“模板名 + Sandbox 名”组成；nameHash 写入的是跟踪标签，并不充当这个 PVC 的名称。
3. 后面的 Pod 创建代码把该 PVC 配置成可引用的 volume；容器配置通过 volumeMounts 将它挂到 /my-data。
4. 存储就绪且挂载成功后，程序向 /my-data 写文件，就是在使用这份存储。数据能否跨 Pod 替换保留，取决于这份 PVC 及背后存储是否仍保留。

本轮只理解这条交接，存储分配、绑定及挂载的具体机制继续留白。源码依据：reconcilePVCs:2209–2279、Pod 卷构建:2004–2017，以及该例子的 volumeMounts。

</details>

| 需要实现细节时进入 | 读完回到这里 |
| --- | --- |
| [reconcilePVCs:2202](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L2202)，本轮只按职责理解 | 535 行记录错误，然后进入 Pod 协调 |

<a id="pod-and-observation"></a>

#### 3.2 运行对象：协调 Pod，处理对应关系冲突

源码：538–545。根据 Sandbox 的需求和已有 Pod 执行必要操作，接住 Pod、延迟和错误，再辨认是否出现多个所属 Pod 的冲突。

Pod 是承载沙箱容器的运行单元。前半段由 reconcilePod 按需求处理 Pod；后半段从返回的 Pod 摘取地址与节点名称，更新本地 Sandbox 的观察字段。这里没有读取 Node 对象来诊断节点，也没有重新获取 Sandbox。

前半段在本节展开，后半段接着看 [3.3 运行信息](#pod-observed-fields)。

<details>
<summary>展开 Pod 协调、三个返回值与对应关系冲突</summary>

```go
pod, recreateRequeue, podErr := r.reconcilePod(ctx, sandbox, nameHash, wd)
podMappingConflict := isMultipleSandboxPodsError(podErr)
if podMappingConflict {
	conditionErrors = errors.Join(conditionErrors, podErr)
	r.recordMultiplePodsEvent(sandbox, podErr)
} else {
	recordChildErr(podErr)
}
```

1. **交给 Pod 协调并接住结果**：reconcilePod 根据需求和现状执行必要操作。例如当前要求 Running，普通路径上 Pod 不存在时会创建 Pod 对象；有可用的所属 Pod 时继续协调它。返回 pod、recreateRequeue、podErr，分别是本次取得的 Pod、重建等待时长和错误；创建对象不表示容器已启动。
2. **辨认一种特定冲突**：podMappingConflict 判断的是是否发现多个属于同一 Sandbox 的 Pod，无法确定唯一对应关系。这不是 CPU、内存或节点网络冲突，也不是所有错误的统一判断。遇到这一特定冲突会记录状态错误与事件，并跳过第 3.4 段的 Service 操作。

| 需要实现细节时进入 | 读完回到这里 |
| --- | --- |
| [reconcilePod:1674](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L1674)，本轮只按接口理解 | 538 行接住 Pod、延迟、错误，再摘取观察字段 |

</details>

<a id="pod-observed-fields"></a>

#### 3.3 运行信息：记录 Pod 地址与节点名称

源码：547–559。从刚取得的 Pod 中摘取信息，更新同一个 Sandbox 的内存状态；没有可用的所属 Pod 时清空地址与节点字段。

<details>
<summary>展开归属检查、地址与节点字段的状态记录</summary>

```go
if pod == nil {
	sandbox.Status.PodIPs = nil
	sandbox.Status.NodeName = ""
} else {
	sandbox.Status.LabelSelector = sandboxv1beta1.SandboxNameHashLabel + "=" + nameHash
	if isOwnedBySandbox(pod, sandbox) {
		sandbox.Status.PodIPs = podIPsFromStatus(pod.Status.PodIPs)
		sandbox.Status.NodeName = pod.Spec.NodeName
	} else {
		sandbox.Status.PodIPs = nil
		sandbox.Status.NodeName = ""
	}
}
```

1. **没有 Pod 时清空旧信息**：pod 为 nil 时，清空内存中的 PodIPs 和 NodeName，避免保留过时的地址或节点；本段不会因此去另一个节点寻找 Sandbox。
2. **有 Pod 时先确认归属**：isOwnedBySandbox(pod, sandbox) 检查这个 Pod 是否属于当前 Sandbox。它没有检查节点健康。确认归属后才把这个 Pod 的信息记录到当前 Sandbox；未确认归属则清空地址与节点字段。
3. **摘取字段，不再查询节点**：PodIPs 来自 pod.Status.PodIPs，NodeName 来自 pod.Spec.NodeName。例如后者已有 worker-1，就把 worker-1 记入 sandbox.Status.NodeName；节点尚未分配时它可以为空。LabelSelector 保存基于跟踪标签的选择表达式，供查找使用，不是地址。

</details>

<a id="service-reconciliation"></a>

#### 3.4 访问入口：按配置协调 Service

源码：563–568。按配置和已有资源维护访问入口对象；当前未请求 Service 且没有已有对象时，不创建新 Service。

Service 提供面向 Pod 的网络访问入口。这里按配置与现状创建或调整 Service 对象，并检查资源归属；不通过发起网络连接来验证“网络是否畅通”。本例没有请求自动创建，也没有已有 Service，因此正常返回的 svc 为 nil。

<details>
<summary>展开 Service 调用与后续去向</summary>

```go
var svc *corev1.Service
if !podMappingConflict {
	var svcErr error
	svc, svcErr = r.reconcileService(ctx, sandbox, nameHash)
	recordChildErr(svcErr)
}
```

1. **确认可以继续**：正常路径没有 Pod 对应关系冲突，进入 Service 协调；冲突时跳过，避免修改指向不明确的访问入口。
2. **按配置和现状处理**：新建 Service 需要 spec.service=true。未设置该字段不代表一律删除旧 Service；已有资源还有自己的处理分支。
3. **留下计算状态所需的数据**：svc 和累计错误将交给后面的 computeConditions；reconcileService 也会维护 Sandbox 内存中的 Service 状态字段。本例没有 Service，会清理对应字段。

| 需要实现细节时进入 | 读完回到这里 |
| --- | --- |
| [reconcileService:1463](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L1463)，本轮只按职责理解 | 566 行接住 svc 与错误，然后计算整体状态 |

</details>

<a id="observed-conditions"></a>

#### 3.5 观察状态：计算并更新 Conditions

源码：571–591。根据 Pod、Service 和错误计算当前状态，把结果写进内存中的 Conditions；有错误时也要形成状态说明。

Conditions 是描述“是否 Ready、是否已调度”等情况的状态条目。computeConditions 是计算这些条目的函数；它根据本次资源与错误算出结果，随后放回同一个 sandbox.Status。有错误或资源尚未就绪时也会生成状态，不要求前面全部成功。

<details>
<summary>展开状态计算、写入与旧条目移除</summary>

以下节选保留实际语句，只省略源码注释。

```go
conditions := r.computeConditions(sandbox, conditionErrors, svc, pod, podErr)
presentWhileApplicable := map[string]bool{
	string(sandboxv1beta1.SandboxConditionFinished):     false,
	string(sandboxv1beta1.SandboxConditionPodScheduled): false,
}
for _, condition := range conditions {
	meta.SetStatusCondition(&sandbox.Status.Conditions, condition)
	if _, ok := presentWhileApplicable[condition.Type]; ok {
		presentWhileApplicable[condition.Type] = true
	}
}
for condType, present := range presentWhileApplicable {
	if !present {
		meta.RemoveStatusCondition(&sandbox.Status.Conditions, condType)
	}
}
```

1. **计算**：computeConditions 使用 Sandbox 需求、Pod、Service 和错误，计算本轮适用的状态条目；本轮先不逐项展开判定规则。
2. **更新**：SetStatusCondition 更新内存切片中的对应条目。函数名带 Status，但这一步没有把 Sandbox 状态提交给 API Server。
3. **移除不再适用的旧条目**：Finished 和 PodScheduled 如果本轮没有算出，就从已有状态中移除；不清空整份 Conditions。
4. **保留观察的含义**：计算出 Ready=False 也可以是一次正常协调的结果，例如 Pod 还在启动。这里不会把“子函数已返回”当成“环境已就绪”。

| 需要规则细节时进入 | 读完回到这里 |
| --- | --- |
| [computeConditions:607](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L607)，本轮只按接口理解 | 571 行接住条件列表，随后更新内存中的 Conditions |

</details>

<a id="return-to-reconcile"></a>

#### 3.6 返回外层：交回延迟与错误

源码：593。返回 recreateRequeue 和 allErrors；修改后的 Sandbox 仍是调用方持有的同一个对象，状态持久化由外层继续完成。

```go
return recreateRequeue, allErrors
```

1. **返回值交接**：父函数在 458 行接住延迟与错误，随后计算后续协调时间。
2. **状态交接**：前面修改的是传入指针所指向的同一个 Sandbox，父函数可以直接读取新 Status；不需要另行返回这个对象。
3. **写回交接**：父函数在 488 行调用 updateStatus，利用先前保存的旧状态与版本，按需持久化本次观察结果。

读完回到 [Reconcile 的第 3.3 段](SandboxReconciler.Reconcile.md#after-child-resources)，继续“后续协调时间 → 状态写回 → 返回框架”。

<a id="child-errors"></a>

<details>
<summary>按需回查：开头的 recordChildErr 为什么分两份错误（523–532）</summary>

```go
recordChildErr := func(err error) {
	if err == nil {
		return
	}
	conditionErrors = errors.Join(conditionErrors, err)
	if k8serrors.IsInvalid(err) {
		return
	}
	allErrors = errors.Join(allErrors, err)
}
```

1. nil 表示没有错误，直接结束本次记录。
2. 非空错误先进入 conditionErrors，让状态能反映失败原因。
3. API 校验拒绝的 Invalid 错误不进入 allErrors，避免把无法靠重试修复的配置反复交回框架重试；其他错误也进入返回用的集合。

这是 reconcileChildResources 内部定义的局部辅助函数；此处的 return 只结束一次错误记录，不退出 reconcileChildResources。当前无错误场景先记住两份记录的去向即可。

</details>

## 我的直接表述（原话）

本轮确认单独打开函数卡：

> 好的 那么我们看一下这个controller当中的这个下一个函数吧
> 单独开一个关于这个函数的short term memroy吧

建卡时只是阅读请求，尚无对本函数内部机制的独立复述。此前对外层交接的表述保留在 [Reconcile 卡](SandboxReconciler.Reconcile.md)及过程记录中，不据此推断已理解各子资源实现。后续实际复述保存在下方。

随后对第 3.1 段提出疑问：

> 这里我其实就没有特别能够理解了?
> 这里在干吗?
> 主要我不是特别熟悉pvc和k8s的相关的内容
> 先把这个namehash一下
>
> 但是这里的3.1在干吗我其实没有明白
> 就给了一个namehash还有对应的一个record child err
> 我其实不是特别理解

本次说明补在第 3.1 段：先交代存储需求，再区分名称标记、处理 PVC 和记录错误；尚未收到用户对这三者关系的确认。

<details>
<summary>本轮对整条子资源主线的复述与待校准理解</summary>

> 好的 我可以简单理解为pvc的部分是检查一下是否存在请求volume会出现问题这件事情
>
> 然后这里的协调pod的部分
> 在做的事情是
> 看一下这个pod是否是否被需要被操作?
> 然后下面的一步是查看是否有冲突?
>
> 如果都没有的话
> 就通过这里的一系列内容来检查和查询这里的node
> 是否是有问题的
> 如果没有问题的话
> 就考虑一下获取 一下这个sandbox?
> 这里在做的内容更多的是在干吗?
> 简单的获取地址和节点?
> 是我简陋的理解?
>
> 然后在考虑这里的reconcileservice
> 查看service部分是否有问题?
>
> 最后是更具这里的的svc pod 还有看一下这里是否都没有问题了?
>
> 总的来说这个reconcilechildresources
> 是否可以理解为
> 看一下pcv (容量是否足够)
> 看一下这里的pod 节点是否正确
> 以及最后看一下这里的service网络是否正确
> 最后再更新这里的compute condition是否完备?
> 是我的理解

助手核对：用户已经串起三类资源与状态汇总，也辨认出 Pod 操作、冲突和信息摘取的先后；需要校准整体职责。PVC 是申请对象的协调，不是磁盘容量验收；Pod 协调会执行必要操作，后续归属检查与字段赋值不诊断 Node，也不重新获取 Sandbox；Service 是访问入口对象的协调，不是连接测试；computeConditions 根据观察和错误形成状态，不以全部成功为前提。校准尚待反馈。

</details>

## 尚不清楚

1. 本函数的“返回值”与“修改同一个 Sandbox 的状态”两条交接，尚待阅读反馈。
2. reconcilePod 怎样判断已有资源可用、何时创建 Pod，本轮仍按接口理解。
3. Ready 等状态的完整计算规则、资源归属检查和错误恢复机制尚未展开。
4. 当前明确卡点：PVC 表达什么需求，内层 reconcilePVCs 实际做什么，以及它与外层 recordChildErr 的执行顺序。说明已补，不能据此记为已理解。
5. 本轮复述暴露的关键区别：资源协调与容量/节点/网络检查、Pod 归属与节点健康、摘取字段与重新获取对象，以及失败状态同样需要记录。

<details>
<summary>来源、验证与阅读边界</summary>

- 固定源码：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1，本地 /home/fredkeira/projects/agent-sandbox。
- 当前函数：controllers/sandbox_controller.go:507–594；调用处 458；父函数状态写回 488。
- 职责核对：reconcilePVCs:2202、reconcilePod:1674、reconcileService:1463、computeConditions:607。助手核对接口与相关分支不表示用户已读完这些函数。
- 第 3.1 段补充依据：NameHash:1220–1233；reconcilePVCs:2202–2279；api/v1beta1/sandbox_types.go:294–309 的存储模板定义；examples/sandbox-ksa/sandbox.yaml 的 1Gi 存储及 /my-data 挂载配置。
- 本轮主线校准依据：reconcilePod 中 ownedPods 数量检查（1726 起）、本函数 Pod 信息赋值（547–559）、reconcileService 的资源创建/修正（1463 起）、computeConditions（607 起）与 computeReadyCondition 的错误及就绪分支（729 起）。这些为静态核对，不是节点或网络探测实验。
- [Kubernetes Step 000 · 本次函数阅读与记录](../../../../04-flow.md#child-resources-first-card)。
- 展示沿用短期 memory 的四项概括、场景输入输出、分段源码和返回导航；首段可见，后续详细代码与辅助错误处理按需展开。
- 本页示例由静态源码推导；没有运行控制器、创建资源或取得实际 Pod IP、节点、Ready 状态。

</details>
