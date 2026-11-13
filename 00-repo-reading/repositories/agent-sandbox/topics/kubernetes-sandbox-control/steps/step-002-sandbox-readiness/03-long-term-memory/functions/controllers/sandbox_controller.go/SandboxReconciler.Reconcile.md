# SandboxReconciler.Reconcile

> Step 002 继承：完整承接 [前一步记录](../../../../../step-001-pod-creation/03-long-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.Reconcile.md)。以下认识时间、原话和未知保持来源；旧步骤说明属于历史语境。

> 本页完整继承自 [Kubernetes Step 000 的原卡](../../../../../step-000-sandbox-reconcile/02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.Reconcile.md)，供 Step 001 回查。原话、认识时间与未知保留；文中的原步骤 scope 和过程链接仍指向来源，继承不表示新增理解。

[本步 scope](../../../../../step-000-sandbox-reconcile/01-scope.md#reading-navigation) → **Reconcile（本页）** → [reconcileChildResources（子函数卡）](SandboxReconciler.reconcileChildResources.md) → [回到 Reconcile](#after-child-resources)

基础回查：[对象、内存与 API 写回](../../../../../../../../../kubernetes/02-resource-model/objects-spec-status.md) · [协调循环](../../../../../../../../../kubernetes/01-architecture/reconciliation.md)。下文保留本函数的具体场景和解释。

- 源码定位：[controllers/sandbox_controller.go:366–501](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L366)。
- 首次接触：Kubernetes 主题 Step 000，2026-11-05；此前只在结构图中定位，本轮开始函数级阅读。
- 最近认识更新：2026-11-05，用户开始串联读取、子资源协调、时间检查和状态写回；仍需区分 Ready 判断、重新协调时间及更新函数/错误变量。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：controller-runtime 从工作队列取得一个 Sandbox 的 namespace/name，调用本方法处理当前资源状态。触发原因可以是资源事件或之前请求的重新排队。
2. **具体内容**：读取 Sandbox，判断是否需要停止或走过期处理；普通路径委托子资源协调，再按观察结果写回 status，最后返回调度信息与错误。
3. **建议构建的心智模型**：

   > Reconcile 每次为一个 Sandbox 做一次“读取现状、推进必要操作、反馈结果”。它不持有整条任务直到运行结束，也不在这里阻塞等到 Pod Ready；后续事件可以再次触发它。

4. **入口与注册**：这是框架调用的接口，签名来自实际源码：

   ```go
   func (r *SandboxReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
       // body discussed below
   }
   ```

   [SetupWithManager](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L2414) 注册 Sandbox 和它拥有的 Pod、Service 的观察，并用 Complete(r) 注册协调器。它不是每次请求的普通直接调用方，当前先不展开框架内部。

## 本场景的输入与输出

### 1. 先分清这几个对象

| 名称 | 在本次调用中是什么 |
| --- | --- |
| r | 长驻的 SandboxReconciler 协调器实例，带 Kubernetes 客户端和管理状态 |
| ctx | 本次调用的上下文 |
| req.NamespacedName | 指向某个 Sandbox 的 namespace/name；不是整份 Sandbox，也不是原始事件变化内容 |
| sandbox | 读出资源后保存在本地内存中的 Sandbox 对象，包含 Spec、Status 等字段 |
| result、err | 返回 controller-runtime 的后续调度信息和错误，不是返回给 Agent 的任务结果 |

读取的资源是什么、与本地变量和镜像有什么区别，紧接代码写在[第 3.1 段](#sandbox-object-vs-image)。

贯穿本页的静态场景：假设 namespace 为 default，名称为 hello-world 的 Sandbox 已提交，未删除、未过期，要求 Running；没有 shutdownTime，WriteBehindWindow=0，未启用失败 Pod 重建。它没有配置 PVC，也未开启自动创建 Service。本页只跟踪这个对象，不在各段切换场景，没有运行真实集群。

### 2. 先确定哪些路径本轮不展开

```text
Reconcile(req)
  target absent / deleting -> clear local tracking, stop
  target expired           -> expiry handling
  normal target            -> child resources -> status -> scheduling result
                               ^ current path
```

这是按业务结果归纳的分支图，日志、Trace 写入失败等提前返回仍存在于原实现。过期路径和删除中的记录清理先知道职责；不要从看到的第一个辅助函数开始逐个向下追。

<a id="reconcile-normal-flow"></a>

### 3. 普通路径：四段源码与交接

本页只沿未过期的普通路径，先抓住这一条主线：

1. 读出 Sandbox 的需求和已有状态，并保留更新前的状态/版本。
2. 将同一个 Sandbox 交给子资源协调，操作所需资源，并形成新的观察状态。
3. 根据关闭时间、重建延迟等信息，决定何时需要再次协调。
4. 调用 updateStatus，将本次观察状态按需写回 Kubernetes。
5. 返回 result 和 err，控制权交回 controller-runtime；后续事件或重排再触发下一轮。

下面按原执行顺序节选实际语句，行号用于回查；不是完整函数。详细解释按需展开，始终跟踪同一个 sandbox，不把 ctx 当作被管理的环境。

#### 3.1 读出对象，保存修改前的状态（369–380、425–429）

<a id="sandbox-object-vs-image"></a>

**当前读取的是 Kubernetes 中的 Sandbox 需求记录，不是镜像或运行中的容器。** 假设目标为 default/hello-world：记录已提交，但对应 Pod 仍可能尚未创建。

```go
sandbox := &sandboxv1beta1.Sandbox{}
if err := r.Get(ctx, req.NamespacedName, sandbox); err != nil {
	if k8serrors.IsNotFound(err) {
		logger.Info("sandbox resource not found. Ignoring since object must be deleted")
		r.suspendStartTimes.Delete(req.NamespacedName)
		r.resumeStartTimes.Delete(req.NamespacedName)
		r.deferralClock.clear(req.NamespacedName)
		r.recreateBackoff.clear(req.NamespacedName)
		return ctrl.Result{}, nil
	}
	return ctrl.Result{}, err
}
```

1. **本地接收对象**：&Sandbox{} 只在控制器内存里准备一个空对象，不向集群创建资源。
2. **读取并填入内容**：r.Get 按 Sandbox 类型和 namespace/name 读取记录，填入 sandbox，后续才依据它协调资源。
3. **是否继续**：读取成功继续；NotFound 结束本次协调；其他读取错误交回框架。

<details>
<summary>需要时展开：具体对象、读取分支，以及集群与镜像位置的区别</summary>

**这段开始前，集群里已经有一份“沙箱需求记录”。** 用户、SDK 或上游控制器先提交 Sandbox 对象，例如声明“需要一个叫 hello-world、按某个 podTemplate 运行的沙箱”。控制器现在接到通知，要检查这份需求如何落实。

这里的 Kubernetes 资源，是由 Kubernetes API 管理的对象记录，包含名称、配置和观察状态；不是本地 YAML 文件、镜像文件或已经运行的容器。**Sandbox 记录可以已经存在，而对应的 Pod 还没有创建。**

沿用本页的示意对象：

| 读代码前已有的信息 | 当前含义 |
| --- | --- |
| 资源类型 | Sandbox，由接收对象的 Go 类型确定 |
| req.NamespacedName | namespace=default、name=hello-world，指定要读取哪一份记录 |
| 记录的内容 | metadata 保存身份信息，spec 保存期望配置，status 保存已观察到的状态 |
| 此时尚不能推出 | Pod 已存在、镜像已拉取或环境已就绪 |

下面的两项核心动作是：先准备本地接收对象，再按类型和名称读取这份记录。其余语句处理读取失败。




1. **先建立本地接收对象**：sandbox := &sandboxv1beta1.Sandbox{} 在控制器进程内存中建立空的 Go 结构体，变量 sandbox 指向它。这行没有向 Kubernetes 提交创建请求。
2. **再读取集群中的 Sandbox 记录**：r.Get 使用 Sandbox 类型和 req.NamespacedName 定位目标，把读到的 metadata、spec、status 等填入这个本地对象。因此它不只是问“有没有”，还要取回后续协调需要的数据；r.Get 本身交回的是 error，资源内容通过传入的对象获得。
3. **读取成功就继续**：err 为 nil，跳过整个错误处理块。此时 sandbox 已携带这份资源的配置和观察状态，后面才据此检查或创建 Pod 等子资源。
4. **记录不存在就结束这次协调**：IsNotFound 表示指定的 Sandbox API 对象没找到，不表示某个镜像不存在。这时只清理控制器自己的跟踪记录并返回；例如通知排队期间，用户可能已把对象删除。
5. **其他读取错误也不继续**：例如读取请求失败，直接返回错误交给框架处理；不会带着空对象继续创建环境。

控制器连接的 Kubernetes 集群可以运行在本机，也可以在远程服务器。读取实现可能使用本地缓存，但缓存的是集群资源记录；这里既不搜索本机镜像，也不访问镜像仓库下载镜像。后续 Pod 创建之后，才由节点侧处理镜像和容器启动。

**读完这里，拿到的是“一份已有沙箱需求及其状态的本地表示”，不是“已经创建好的运行环境”。** 接下来保存修改前状态，再交给子资源协调。

</details>

中间的 Trace、删除中检查和重建退避维护先不展开。它们之后，源码记录状态快照并建立返回变量：

```go
oldStatus := sandbox.Status.DeepCopy()
oldResourceVersion := sandbox.ResourceVersion
var err error
sandboxDeleted := false
result := ctrl.Result{}
```

<a id="old-status-and-resource-version"></a>

**当前只需分清这两个变量：**

1. **oldStatus**：独立保存修改前的状态，供后续比较新旧变化。
2. **oldResourceVersion**：保存这份旧状态对应的版本标记，防止过期写入覆盖新修改。它来自 metadata.resourceVersion。
3. **共同用途**：给后面的 updateStatus 提供更新依据，不用于回滚 Pod 或恢复容器。

<details>
<summary>需要时展开：Sandbox 的完整字段层次、差异补丁与版本冲突</summary>

这里先留下一份“本次修改所依据的数据”，不是为了将来回滚容器。先看这两行读的属性在对象里属于哪里：

| Kubernetes API 对象的字段 | 表示什么 | Go 中的对应访问 |
| --- | --- | --- |
| apiVersion、kind | 资源的接口版本和类型；本例类型是 Sandbox | 来自嵌入的 TypeMeta |
| metadata.name、metadata.namespace | 对象身份 | sandbox.Name、sandbox.Namespace |
| metadata.resourceVersion | API Server 给这份对象状态提供的版本标记，用于并发控制等；按不透明字符串使用 | sandbox.ResourceVersion |
| spec | 期望的运行配置，例如 podTemplate、运行模式 | sandbox.Spec |
| status | 控制器观察到的情况，例如 conditions、podIPs、nodeName | sandbox.Status |

Sandbox 在 Go 中嵌入了 metav1.ObjectMeta，因此代码可以直接写 sandbox.ResourceVersion。它在 API 对象中仍属于 metadata.resourceVersion，不是单独一个 resource 配置块，也不是镜像标签或 apiVersion。

1. **oldStatus = 独立保留修改前的观察状态。** 后面的 reconcileChildResources 会修改 sandbox.Status，所以用 DeepCopy 保留不随之变化的旧状态。updateStatus 先比较新旧是否相同；相同可跳过写入，不同则用旧状态作为生成差异补丁的基准。成功写入后也用它判断状态转换、记录事件和指标。
2. **oldResourceVersion = 保留旧状态对应的版本标记。** updateStatus 使用 MergeFromWithOptimisticLock 构造补丁。如果在此期间该对象又被修改，旧版本可能已失效，API Server 会拒绝冲突的写入。这防止旧观察结果覆盖更新后的内容；不是把服务器恢复到旧版本。
3. **局部基准不等于回滚目标。** updateStatus 中把 base.Status 设为 oldStatus、把 base.ResourceVersion 设为旧版本，是构造比较基准；要写入的仍是新 sandbox.Status。当前实现遇到 Conflict 会放弃这次过期补丁，等待后续 watch 事件再次协调。

一个简化例子：本次读取时 Ready=False，随后观察到 Pod 已就绪，内存里的 sandbox.Status 被改成 Ready=True。oldStatus 仍保存 False，用来识别变化。如果对象版本在期间改变，旧版本的状态补丁可能被拒绝；下一轮再重新读取并判断，而不是将 Pod 或容器恢复成过去状态。

其余三项局部变量只为组织本次返回：err 汇总错误，sandboxDeleted 跟踪本轮是否删除了对象，result 保存重新排队等调度结果。本次对象未过期，继续进入普通协调分支。

</details>

<a id="child-resource-call"></a>

#### 3.2 把同一个对象交给子资源协调（449、457–458）

这里把同一个 sandbox 交给子资源协调，推进资源操作并更新本地 Status；ctx 只携带本次操作的上下文。

进入 [reconcileChildResources 函数卡](SandboxReconciler.reconcileChildResources.md)，读完回到下方第 3.3 段。

<details>
<summary>展开本段源码、返回值与状态变化</summary>

当前 WriteBehindWindow=0，故 450–456 的可选配置分支跳过，wd 保持 nil：

```go
var wd *writeDeferral
var recreateRequeue time.Duration
recreateRequeue, err = r.reconcileChildResources(ctx, sandbox, wd)
```

1. 传入 sandbox 指针，子函数可以更新这份内存对象的 Status；这里没有用返回值接收一个新 Sandbox。
2. reconcileChildResources 组织 PVC、Pod、Service 的协调，并根据观察到的 Pod 等对象计算状态。没有相应配置时，不表示一定创建 PVC 或 Service。
3. 返回的是 recreateRequeue 和 err：前者提供相关重建路径希望再次协调的延迟，后者承接可返回的协调错误。本轮先记住返回含义，不追重建算法。
4. 下一次下钻优先进入这个子函数，读完回到 Reconcile:458；不会自动转入整个文件的所有方法。

</details>

<a id="after-child-resources"></a>

#### 3.3 确定后续协调时间（459–468）

这一段根据到期时间、重建延迟等决定何时再协调；它不负责判断 Pod 是否 Ready，Ready 的观察状态来自前一段。

<details>
<summary>展开重排时间的源码与条件</summary>

```go
expiredAfterReconcile, requeueAfter := checkSandboxExpiry(sandbox, time.Now())
result.RequeueAfter = requeueAfter
if expiredAfterReconcile {
	r.recreateBackoff.clear(req.NamespacedName)
	setSandboxExpiredCondition(sandbox)
	result.RequeueAfter = immediateRequeueDelay
}
if recreateRequeue > 0 && (result.RequeueAfter == 0 || recreateRequeue < result.RequeueAfter) {
	result.RequeueAfter = recreateRequeue
}
```

1. 这里再次检查过期，是因为子资源操作花费时间后，资源可能已跨过 shutdownTime。本页没有配置 shutdownTime，过期分支不生效。
2. result.RequeueAfter 保存希望框架稍后再次调用的延迟；有多个时间要求时保留更早的一个。
3. 给 RequeueAfter 赋值不会在函数内部等待，也不会直接递归调用 Reconcile。

之后 469–483 是 wd 非 nil 时的延迟写入处理，当前关闭该功能，先跳过其内部。

</details>

#### 3.4 写回观察状态，然后返回（486–492、500）

updateStatus 把观察状态按需写回 Kubernetes 中的 Sandbox.status；statusUpdateErr 只是记录写回错误的局部变量。最后返回调度结果与错误。

<details>
<summary>展开状态写回、错误合并与返回代码</summary>

```go
if !sandboxDeleted {
	// Update status
	if statusUpdateErr := r.updateStatus(ctx, oldStatus, oldResourceVersion, sandbox); statusUpdateErr != nil {
		// Surface update error
		err = errors.Join(err, statusUpdateErr)
	}
}
```

1. 当前普通路径没有删除 Sandbox，因此进入状态更新。
2. 子函数在内存中修改 Status；updateStatus 负责按需将其写回 Kubernetes。状态未变等情况可以不写，不能把“调用了它”理解为每次必然产生一次写请求。
3. 即使前面的子资源协调出现错误，这里仍可能更新相应状态；状态写入错误与已有错误合并，避免只保留其中一个。

命名空间终止时另有 30 秒重排的特殊出口（495–496），当前先不展开。普通路径最终是：

```go
return result, err
```

</details>

### 4. 本次返回和环境就绪是两件事

| 观察项 | 在本页选定场景中的含义 |
| --- | --- |
| Kubernetes 子资源 | 子函数按需求创建或观察 Pod；Pod 真正启动仍由调度器、kubelet 和运行时推进 |
| sandbox.Status | 本次根据观察结果计算的状态；Pod 尚未就绪时，可以报告尚未 Ready |
| err 为 nil | 本次没有需要返回给框架的错误，不代表 Pod Ready |
| result.RequeueAfter 为 0 | 本次未安排定时重排；不表示以后不会再收到事件 |

例如，没有过期时间、没有重建延迟、也没有返回错误时，可以返回空的 ctrl.Result 和 nil，同时 Pod 仍在启动。后续 Pod 状态事件进入工作队列，再次调用 Reconcile；新的观察才可能使 Sandbox Ready。

### 5. 当前怎样读这个大文件

1. 第一遍只读本页四段，沿“请求编号 → sandbox → 子资源和 Status → result/err”建立关系。
2. 下一处只进入 [reconcileChildResources 函数卡](SandboxReconciler.reconcileChildResources.md)，先看它组织什么操作；其内部方法仍按接口理解，随后返回本页第 3.3 段。
3. 只有状态如何写入不清楚时，再看 [updateStatus](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L928)。事件从哪里来不清楚时，回查 [SetupWithManager](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L2414)。
4. 日志/Trace、过期、暂停恢复、写入合并、失败重建与重试细节不作为第一遍的前置知识；原源码和下表保留回查位置。

<details>
<summary>本轮折叠的源码位置</summary>

| 位置 | 作用与后续展开条件 |
| --- | --- |
| 382–391、411–423 | Trace 与追踪注解；研究链路观测时进入 |
| 393–409 | 删除中及重建退避状态维护；研究资源结束/重建时进入 |
| 431–443 | 过期后的状态与清理；研究生命周期结束时进入 |
| 450–456、469–483 | 可恢复元数据写入的延迟合并；研究写入压力时进入 |
| 495–496 | namespace 终止时延后重排；研究删除期间的请求风暴时进入 |

这些代码并未从仓库删除；本页仅固定普通路径作为第一遍的阅读对象。

</details>

## 我的直接表述（原话）

当前明确的问题是资源含义、旧状态与版本的用途，以及如何控制一次展开的内容量。以下原话完整保留，不作为已掌握结论。

<details>
<summary>展开本函数阅读中的原始提问与反馈</summary>

用户本次要求：

> 好的那么我们看一下这里的这个sandbox controller是怎么做的吧
> 是否考虑一下生成一下这里的reconcile的部分吧
> 这里应该考虑怎么读呢?
> 毕竟这里的这个sandbox controller代码量非常的多?

当前保存的是阅读需求，尚无用户对本函数机制的独立复述。不把函数卡建好或代码核对通过当作已掌握。

用户阅读开头两行时提出：

> 我不是很理解
> 这里应该怎么读
> 我的理解是
> 这里先建立本地的sandbox? 不是集群就只是一个?
> 然后从rget里面读取指定资源??? 先看看这个资源是否存在? 我是否可以理解为
>
> 如果如果存在才继续?
> 这里读取资源是外部的资源?
> 公网上的资源?
> 还是说本地也可以有类似的镜像资源需要确定存在才能够读取?

本轮澄清聚焦 Sandbox API 对象、本地结构体与镜像的区别；尚未收到用户对该区分的确认。

用户进一步要求将读取对象的前置说明放到第 3.1 段：

> 这个部分写清楚吧
> 这一部分是否更加适合写在这里的3.1当中呢?
> 否则我在本身不是非常熟悉k8s的情况下 并不是很清楚这里到底是在做什么

本次按此反馈调整说明位置，保留读取前提、真实源码、返回分支与后续交接；不视为已经掌握这些概念。

用户继续对状态快照与版本提出疑问：

> 好的那么鞋面的odlstatus的部分而女士在做什么呢?
> 用于记录一下这里的这个旧的sandbox的状态?
> 以及resource的版本?
> 后续是用来恢复的或者复原的吗?
> 我不是特别理解
> 以及一个sandbox在k8s中有很多attribute吗
> 类似于这里的status还有这里的resource吗?
> 还是什么?

本次校准 oldStatus 的差异比较用途、metadata.resourceVersion 的并发控制用途；没有把用户提问改写成已经理解。


本次展示方式反馈：

> 这里是否需要考虑一下哪些内容是可以隐藏或者缩进的呢?
> 全部在这里的展开是否不是特别合适?

用户随后尝试整理整条主线：

> 好的 我感觉这里整体还是比较复杂的
> 我需要理成一条主线
> 也就是这里的controller在做的事情是
> 首先看一下这里的对应的sandbox具体是怎么样的
> 也就是3.1 需要记录一系列的状态是我的理解
>
> 然后是第二个
> 这里具体的记录了
> 这里的sandbox的一系列的星系
>
> 后续吧这里的ctx还是这里的sandbox交给这里的reconcilechildresources这里统一管理
> 是我的理解
>
> 然后下面的是检查这里的协调时间
> 是用来接安插请求是否真的被实现吗?
> 也就是这里的sanbbox是否真的开启了?
> 或者是否到了关闭的时间?
>
> 然后把这里的状态写回给这里的statusUpdate?

助手校准：3.1 先读取已有需求，快照只是更新依据；reconcileChildResources 接收 sandbox 并推进资源与状态，ctx 是调用上下文；时间检查用于到期与后续协调，不是 Ready 检查；updateStatus 写回对象状态，statusUpdateErr 接收错误。以上区分尚待用户反馈。

</details>

## 尚不清楚

1. 用户明确不清楚 r.Get 读取的对象性质；Sandbox API 记录、本地 Go 结构体、Pod 和镜像的区别是当前重点。
2. 子资源协调怎样具体创建或更新 Pod，以及状态如何计算，下一层再展开。
3. result、err、Ready 与后续事件的关系已给出说明，尚未确认理解。
4. oldStatus 与旧版本不是回滚机制；API 对象的 metadata/spec/status 层次和乐观并发检查仍需巩固。
5. 重新协调时间与 Ready 观察状态的区别、updateStatus 与 statusUpdateErr 的区别，是当前主线校准重点。

<details>
<summary>来源、参考与验证范围</summary>

- 固定源码：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1；原函数 366–501，子资源协调 507–594。
- updateStatus:928 起；checkSandboxExpiry:2364 起；SetupWithManager:2414 起。
- 使用场景沿用本主题 scope 中的最小 Sandbox 定位。namespace=default 是本页的教学假设，未查询真实集群。
- 组织方式沿用短期记忆 skill：一个明确调用场景、连续源码片段、紧邻的数据交接和局部返回导航；全局路线保留在 scope。
- [本次阅读开始与记录](../../../../../step-000-sandbox-reconcile/04-flow.md#reconcile-first-card)。
- 本次只核对静态源码，没有创建 Pod、执行控制器测试或观察真实 Ready 状态。

- 快照用途依据：updateStatus:928 起的新旧比较、旧基准构造、MergeFromWithOptimisticLock、Conflict 分支与写入后事件记录。
- 客户端来源：SandboxReconciler 内嵌 client.Client；cmd/agent-sandbox-controller/main.go:503–510 注入 mgr.GetClient()。资源结构：api/v1beta1/sandbox_types.go:449–463。
- [第 3.1 段调整前的完整卡片](../../../../../step-000-sandbox-reconcile/references/history/2026-11-05-reconcile-before-read-context.md)保留原说明位置。

- [折叠调整前的完整卡片](../../../../../step-000-sandbox-reconcile/references/history/2026-11-05-reconcile-before-progressive-disclosure.md)保留此前默认展开的全部说明；本次只调整展示层次，源码与原话保留。

</details>
