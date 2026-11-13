# SandboxReconciler.Reconcile

[本步 scope](../../01-scope.md#reading-navigation) → **Reconcile（当前）** → [reconcileChildResources（下一处）](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L507) → 回到 Reconcile

- 源码定位：[controllers/sandbox_controller.go:366–501](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L366)。
- 首次接触：Kubernetes 主题 Step 000，2026-11-05；此前只在结构图中定位，本轮开始函数级阅读。
- 最近认识更新：2026-11-05，用户开始解释本地构造与 r.Get，明确不清楚读取的是集群对象还是镜像/公网资源；当前停在这一关系。

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

<a id="sandbox-object-vs-image"></a>

**这里的资源是 Kubernetes 的 Sandbox API 对象，不是镜像文件。**

1. 在 Reconcile 被触发之前，用户、SDK 或上游控制器已经向 Kubernetes 提交了 Sandbox 对象，例如声明“需要一个运行某镜像的沙箱”。它可以已经存在，而实际 Pod 尚未创建。
2. &sandboxv1beta1.Sandbox{} 只是在控制器进程内存中建立一个空 Go 结构体；sandbox 变量指向它。这个表达式没有调用 Kubernetes Create。
3. r.Get 使用对象类型 Sandbox 和 req.NamespacedName，读取对应的 Kubernetes API 对象，并将取得的 metadata、spec、status 等填入这份本地结构体。因此它不只是检查是否存在，还要取得后续协调所需的数据。
4. 控制器连接的是配置指定的 Kubernetes 集群；该集群可以是本机测试集群，也可以是远程集群。读取实现可以经过本地缓存，这与镜像在本机缓存或镜像仓库中的位置无关。
5. 读取成功才沿当前正常路径继续；NotFound 则结束本次协调，其他读取错误向上返回。后续创建 Pod 后，镜像拉取与容器启动由节点上的 kubelet/运行时处理，不发生在这里的 r.Get。

客户端来源依据：SandboxReconciler 内嵌 client.Client；cmd/agent-sandbox-controller/main.go:503–510 用 mgr.GetClient() 构造它。Sandbox 类型的 Spec/Status 定义位于 api/v1beta1/sandbox_types.go:449–463。

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

下面按原执行顺序节选实际语句，行号是回查入口。不是完整函数，省略位置会单独说明；没有用新包装函数替代源码。第一遍只跟踪同一个 sandbox，以及 result/err 两个返回值。

#### 3.1 读出对象，保存修改前的状态（369–380、425–429）

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

1. &sandboxv1beta1.Sandbox{} 建立的是本地空对象，供客户端填入内容，不是在集群里创建 Sandbox。
2. r.Get 根据 req.NamespacedName 读取指定资源，成功后 sandbox 才带有实际 Spec、Status 等内容。
3. NotFound 时清理的是控制器的本地跟踪记录，然后正常结束；其他读取错误交回框架。本场景沿读取成功分支继续。

中间的 Trace、删除中检查和重建退避维护先不展开。它们之后，源码记录状态快照并建立返回变量：

```go
oldStatus := sandbox.Status.DeepCopy()
oldResourceVersion := sandbox.ResourceVersion
var err error
sandboxDeleted := false
result := ctrl.Result{}
```

oldStatus 保存更新前的状态；oldResourceVersion 保留读取时的版本，供状态写入处理使用。本次对象未过期，因此进入后面的普通分支。

#### 3.2 把同一个对象交给子资源协调（449、457–458）

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

#### 3.3 确定后续协调时间（459–468）

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

#### 3.4 写回观察状态，然后返回（486–492、500）

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
2. 下一处只进入 [reconcileChildResources](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L507)，先看它组织什么操作；其内部方法仍按接口理解，随后返回本页第 3.3 段。
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

## 尚不清楚

1. 用户明确不清楚 r.Get 读取的对象性质；Sandbox API 记录、本地 Go 结构体、Pod 和镜像的区别是当前重点。
2. 子资源协调怎样具体创建或更新 Pod，以及状态如何计算，下一层再展开。
3. result、err、Ready 与后续事件的关系已给出说明，尚未确认理解。

<details>
<summary>来源、参考与验证范围</summary>

- 固定源码：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1；原函数 366–501，子资源协调 507–594。
- updateStatus:928 起；checkSandboxExpiry:2364 起；SetupWithManager:2414 起。
- 使用场景沿用本主题 scope 中的最小 Sandbox 定位。namespace=default 是本页的教学假设，未查询真实集群。
- 组织方式沿用短期记忆 skill：一个明确调用场景、连续源码片段、紧邻的数据交接和局部返回导航；全局路线保留在 scope。
- [本次阅读开始与记录](../../04-flow.md#reconcile-first-card)。
- 本次只核对静态源码，没有创建 Pod、执行控制器测试或观察真实 Ready 状态。

</details>
