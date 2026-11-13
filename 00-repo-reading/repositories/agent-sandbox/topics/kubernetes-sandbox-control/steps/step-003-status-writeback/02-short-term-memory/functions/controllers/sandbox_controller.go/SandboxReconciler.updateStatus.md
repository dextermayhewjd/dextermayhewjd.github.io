# SandboxReconciler.updateStatus

[本步 scope](../../../../01-scope.md#reading-navigation) → [Reconcile：488 行调用](SandboxReconciler.Reconcile.md#status-writeback-call) → **updateStatus（本页）** → [回到 Reconcile 接收错误并返回](SandboxReconciler.Reconcile.md#status-writeback-call)

- 源码定位：[controllers/sandbox_controller.go:928–983](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L928)。
- 首次接触：Step 000 按接口解释旧状态和版本用途；2026-11-05，Kubernetes Step 003 开始独立阅读。
- 最近认识更新：用户本轮确认进入写回方法，尚无内部机制的个人复述；旧状态的原话保留在 Reconcile 来源卡。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Reconcile 已保存旧状态和版本，子资源协调也已更新本地 Sandbox.Status；本方法负责决定是否写回这些观察。
2. **具体内容**：跳过部分无需立即写入的变化，准备带版本约束的状态补丁，通过 status 子资源提交；区分正常成功、对象消失、版本冲突与其他错误。
3. **建议构建的心智模型**：

   > 旧状态和旧版本说明“这次观察依据什么”，sandbox.Status 保存“准备写出的新结果”。把二者用于受版本约束的状态写入，避免过期观察覆盖更新后的对象。

4. **调用代码**：Reconcile:488–491，当前对象未被删除，进入此分支。

   ```go
   if statusUpdateErr := r.updateStatus(ctx, oldStatus, oldResourceVersion, sandbox); statusUpdateErr != nil {
       err = errors.Join(err, statusUpdateErr)
   }
   ```

## 本场景的输入与输出

静态教学场景：同一个 default/hello-world，读取时 Ready=False，随后本地观察结果变为 Ready=True。对象仍存在，变化不止 NodeName；主路径假设写入时对象版本仍匹配。版本用 v-read 作示意标记，不代表数字递增或真实集群值。

| 输入 | 当前含义 |
| --- | --- |
| r | 协调器及其 Kubernetes 客户端 |
| ctx | 当前协调调用的上下文 |
| oldStatus | Reconcile:425 保存的独立旧状态，Ready=False |
| oldResourceVersion | Reconcile:426 保存的读取版本，示意为 v-read |
| sandbox | 同一份本地对象，当前 Status 已包含新观察 Ready=True；它是写入目标 |

返回值只有 **error**，不会返回 Sandbox 或 Ready 条目。主路径成功时，API 中的状态得到更新，随后记录事件与指标，返回 nil；跳过、NotFound 或已处理的 Conflict 也会返回 nil，因此要结合经过的分支理解结果。

### 内部骨架：四段都在本函数中

| 阶段 | 核心动作 |
| --- | --- |
| [2.1 是否写入](#should-write) | 比较新旧，过滤无需立即写入的情况 |
| [2.2 补丁依据](#patch-base) | 用旧状态与旧版本准备比较基准 |
| [2.3 实际写回](#status-patch) | 提交 Patch，处理写入结果 |
| [2.4 后续与返回](#return-to-reconcile) | 成功写入后记录事件与指标，交回调用方 |

代码片段默认展开。以下省略日志初始化和源码中的长注释，保留核心操作、分支和返回；不是独立可编译程序。

<a id="should-write"></a>

#### 2.1 是否写入：先比较状态，再看可延后的小变化（931–947）

```go
if apiequality.Semantic.DeepEqual(oldStatus, &sandbox.Status) {
	return nil
}

if nodeNameOnlyChange(oldStatus, &sandbox.Status) &&
	!meta.IsStatusConditionTrue(sandbox.Status.Conditions, string(sandboxv1beta1.SandboxConditionReady)) {
	return nil
}
```

本例 Ready 从 False 变为 True，不满足这两个跳过条件，继续准备写回。

<details>
<summary>两种跳过分别意味着什么</summary>

1. 新旧状态相同：没有需要提交的状态变化，直接返回。
2. 只有 NodeName 改变且当前仍未 Ready：暂不为单独节点名变化产生一次写请求，后续有新的观察再一并反馈。这里没有睡眠或等待循环。
3. nodeNameOnlyChange 只用于判断这类变化，本轮不展开其逐字段比较实现；该规则不是忽略所有尚未 Ready 的状态更新。

</details>

<a id="patch-base"></a>

#### 2.2 补丁依据：base 放旧值，sandbox 保留新值（951–954）

```go
base := sandbox.DeepCopy()
base.Status = *oldStatus
base.ResourceVersion = oldResourceVersion
patch := client.MergeFromWithOptions(base, client.MergeFromWithOptimisticLock{})
```

base 是本地的比较基准；给它设置旧值不会把集群状态改回过去。

| 对象 | 本例状态 | 用途 |
| --- | --- | --- |
| base | Ready=False，版本依据为 v-read | 表示本次观察所依据的旧状态 |
| sandbox | Ready=True | 表示希望写回的新状态 |

<details>
<summary>为什么只给 MergeFrom 旧基准，下一行却能写新状态？</summary>

1. DeepCopy 产生独立基准对象，随后把它的 Status 和 ResourceVersion 换成原始观察对应的旧值；当前 sandbox 不随之退回旧状态。
2. MergeFromWithOptions 准备基于 base 生成差异的补丁策略；新目标 sandbox 在下一条 Patch 调用中传入。这里不应理解为单独把 base 提交出去。
3. WithOptimisticLock 使补丁带上版本约束。如果 API 对象版本已不同，写请求可能被拒绝为 Conflict，而不是无条件覆盖。
4. 中途其他操作可能已经修改过本地 sandbox.ResourceVersion。这里明确使用 oldResourceVersion，是让版本约束仍绑定到 oldStatus 的观察时刻。

resourceVersion 是不透明版本标记，不是镜像版本；具体补丁序列化算法暂不下钻。

</details>

<a id="status-patch"></a>

#### 2.3 实际写回：提交状态补丁，分别处理返回情况（955–973）

```go
if err := r.Status().Patch(ctx, sandbox, patch); err != nil {
	if k8serrors.IsNotFound(err) {
		r.forgetSandboxCreationMetrics(sandbox.UID)
		return nil
	}
	if k8serrors.IsConflict(err) {
		logger.V(4).Info("Dropping sandbox status patch computed from a stale cache view (optimistic-lock conflict); awaiting converged watch event",
			"staleResourceVersion", base.ResourceVersion)
		return nil
	}
	logger.Error(err, "Failed to patch sandbox status")
	return err
}
```

**真正的状态写请求在 r.Status().Patch。** r.Status() 取得客户端用于 status 子资源的写入接口；Patch 将新 sandbox 状态按准备的补丁策略提交。它不是重新计算 Ready。

<details>
<summary>成功、对象消失、版本冲突及其他错误</summary>

1. **成功**：err=nil，跳过错误分支，继续到事件与指标记录。本例 API 中的观察状态更新为 Ready=True。
2. **NotFound**：写入时 Sandbox 已不存在，清理本地追踪记录并返回 nil；这里没有重新创建它。
3. **Conflict**：本次旧版本依据失效，放弃这份过期补丁并返回 nil。当前实现依赖对象更新事件再次入队，下一轮重新读取与计算，不在这里反复提交旧结果。
4. **其他错误**：返回 err，交给 Reconcile 合并处理。

冲突分支没有单独设置 RequeueAfter。源码明确依赖 watch 事件以及更新事件不被过滤；相关 predicate 的 UpdateFunc 返回 true。本轮只知道这一后续来源，完整事件与缓存机制按需回查。

</details>

<a id="return-to-reconcile"></a>

#### 2.4 后续与返回：成功持久化以后再记录观察（977–982）

```go
r.recordReadyTransitionEvent(sandbox, oldStatus)
r.recordLifecycleMetrics(ctx, oldStatus, sandbox)
r.recordSandboxCreationMetrics(ctx, sandbox, oldStatus)

return nil
```

这些调用位于成功 Patch 之后；前面的跳过、NotFound 和 Conflict 已经返回，不会执行本段。事件与指标的内部实现暂不展开。

<details>
<summary>为什么不能只看返回 nil 就断言已写入</summary>

| 返回 nil 的路径 | 这次是否完成新状态写入 |
| --- | --- |
| 新旧相同，或暂缓仅节点名变化 | 没有提交本次状态写请求 |
| API 返回 NotFound | 没有，目标已不存在 |
| API 返回 Conflict | 没有接受这份过期补丁，需要后续重新观察 |
| Patch 成功并经过本段 | 是，之后再记录事件和指标 |

返回外层后，Reconcile 用 statusUpdateErr 接收 error；非 nil 时与先前错误合并。它随后返回本次协调结果，不是把这个 nil 当成 Agent 任务成功。

</details>

返回 [Reconcile 的状态写回段](SandboxReconciler.Reconcile.md#status-writeback-call)。共同基础见[内存对象与 API 写回](../../../../../../../../../kubernetes/02-resource-model/objects-spec-status.md#local-object-and-api)。

## 我的直接表述（原话）

用户本轮确认：

> 好的那么就按照这样子看一下这里的这个update sandbox吧

沿用上一轮已确定的 updateStatus 方法。当前尚无具体写回机制的个人复述；没有把入口确认记为掌握。

## 尚不清楚

1. base、sandbox 和 patch 三者的关系，尚待阅读反馈。
2. 版本冲突与返回 nil 的含义，尚待通过本例确认。
3. 客户端补丁实现、完整事件入队和指标内部仍按需后置。

<details>
<summary>来源与验证范围</summary>

- 固定版本：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1；controllers/sandbox_controller.go:928–983。
- Reconcile 保存快照:425–426，调用和接收:488–491；nodeNameOnlyChange:1202–1208；更新事件 predicate:1000–1007。
- [Kubernetes Step 003 · 本轮入口与说明](../../../../../step-003-status-writeback/04-flow.md#update-status-first-card)。
- 本页只核对静态源码；v-read 与 Ready 变化为教学构造，没有真实 API 请求、并发写入或冲突实验。

</details>
