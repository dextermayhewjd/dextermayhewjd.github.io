# 01 · Kubernetes Step 003：状态写回与版本冲突

[本步入口](README.md) · [前一步总结](../step-002-sandbox-readiness/05-task-flow.md) · [共享基础](../../../../../kubernetes/README.md) · [唯一进度](../../../../README.md#current-reading)

## 1. 阅读目标

**内存里已经得到 Ready=True，怎样让这份观察状态可靠地更新到 Kubernetes？**

1. 主攻 SandboxReconciler.updateStatus，接回 Step 000 的旧状态与版本快照，以及 Step 002 的新状态结果。
2. 分清跳过写入、正常写入、放弃版本冲突补丁与返回其他错误。
3. 读到能说明比较基准、实际写请求和后续协调的关系就停，不展开全部客户端或指标实现。

## 2. 入口与场景

当前入口：[updateStatus 函数卡](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.updateStatus.md)，对应 [controllers/sandbox_controller.go:928–983](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L928)。外层 Reconcile 在 488 行调用。

选同一个 default/hello-world 的后来一次协调：

1. Reconcile 读取时保存了旧状态 Ready=False，以及对应的 oldResourceVersion。
2. 子资源协调观察到依赖满足要求，将同一个本地 Sandbox 的 Ready 更新为 True。
3. 对象未删除，Ready 本身发生变化，因此不是仅 NodeName 改变的情况；先假设 API 正常接受写入。
4. 再对照一种情况：写入前其他操作已改变对象版本，本次依据过期，API 返回 Conflict。

这是静态教学场景，不是已运行的集群结果。updateStatus 返回的是 error，外部状态变化是 API 写入的副作用；nil 不必然说明本次执行了写请求。

## 3. 整体位置与本轮展开

<a id="whole-flow"></a>

### 3.1 完整主线：从已计算的状态进入写回

read 标记已讲过的范围，role only 表示只按职责定位，NOW 表示当前入口；它们不等于所有细节已掌握。

```text
[1] caller submits Sandbox.spec                 # context only
      -> Kubernetes API server
      -- watch event --> controller-runtime queue

[2] SandboxReconciler.Reconcile                  # Step 000: read
      -> r.Get(...): read Sandbox                # Step 000: read
      -> save oldStatus / oldResourceVersion    # Step 000: read; reused here
      -> r.reconcileChildResources(...)          # Step 000: read
           -> r.reconcilePVCs(...)               # role only
           -> r.reconcilePod(...)                # Step 001: normal creation read
           -> copy Pod IPs / node name           # Step 000: read
           -> r.reconcileService(...)            # role only
           -> r.computeConditions(...)           # Step 002: aggregation read
                -> computeSuspendedCondition     # role only
                -> computeFinishedCondition      # role only
                -> computePodScheduledCondition  # role only
                -> computeReadyCondition         # Step 002: readiness path read
           -> update sandbox.Status in memory   # Step 000 / 002: read
      -> determine next requeue time            # Step 000: read
      -> r.updateStatus(...)                    # Step 003: NOW
      -> return ctrl.Result, error               # Step 000: read

[3] scheduler + kubelet + runtime                # context only
      -> schedule Pod and run containers
      -> report Pod status
      -- watch event --> queue --> [2] again

[4] caller observes Sandbox.status              # context only
      -> uses the environment when usable
      -> shutdown / deletion                    # later scope
```

本轮位于 [2] 的外层写回，不在 computeReadyCondition 内部，也不重新创建 Pod。完整调用方已调入 [Reconcile 卡](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.Reconcile.md#status-writeback-call)。

<a id="reading-navigation"></a>

### 3.2 本轮骨架：判断要不要写，再准备和提交补丁

以下四段都在 updateStatus 内部。是教学裁剪，省略实参、日志和部分辅助处理，不是可编译函数；关键分支与返回含义保留。

```go
// [2.1] 931-947：不需要写入时提前返回
if apiequality.Semantic.DeepEqual(...) { return nil }
if nodeNameOnlyChange(...) && !meta.IsStatusConditionTrue(...) { return nil }

// [2.2] 951-954：准备旧状态与旧版本作为比较基准
base := sandbox.DeepCopy()
base.Status = *oldStatus
base.ResourceVersion = oldResourceVersion
patch := client.MergeFromWithOptions(...)

// [2.3] 955-973：提交状态补丁，区分资源消失、版本冲突和其他错误
if err := r.Status().Patch(...); err != nil {
    if k8serrors.IsNotFound(err) { ...; return nil }
    if k8serrors.IsConflict(err) { ...; return nil }
    ... // 记录其他写入错误
    return err
}

// [2.4] 977-982：成功写入后记录事件与指标，再返回
r.recordReadyTransitionEvent(...)
r.recordLifecycleMetrics(...)
r.recordSandboxCreationMetrics(...)
return nil
```

| 入口 | 本轮要弄清什么 | 下一次交接 |
| --- | --- | --- |
| [2.1 是否写入](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.updateStatus.md#should-write) | 相同状态与仅节点名变化为什么可跳过；本例 Ready 变化则继续 | 比较基准 |
| [2.2 补丁依据](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.updateStatus.md#patch-base) | 为什么 base 放旧状态，而 sandbox 仍带新状态；旧版本保护什么 | API 状态写请求 |
| [2.3 提交与冲突](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.updateStatus.md#status-patch) | 哪一行实际写 API；冲突时为什么不覆盖、不在这里重试旧结果 | 成功进入 2.4，其他分支提前返回 |
| [2.4 返回调用方](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.updateStatus.md#return-to-reconcile) | 为什么事件在写入成功后记录；nil 与持久化成功不能简单等同 | Reconcile:488 接收 error，随后结束本次协调 |

下面是调用方 Reconcile 中的接收位置，不属于 updateStatus 内部：

```go
if statusUpdateErr := r.updateStatus(...); statusUpdateErr != nil {
    err = errors.Join(err, statusUpdateErr)
}
```

**停止位置**：能区分新状态的计算、状态写请求、旧版本冲突和后续重新协调。nodeNameOnlyChange、事件与指标方法先按职责理解；若对冲突后的事件来路有疑问，只回查最小的 watch/事件过滤依据，不通读框架。

通用背景继续复用[对象与 API 写回](../../../../../kubernetes/02-resource-model/objects-spec-status.md#local-object-and-api)。本步不追加新的 Kubernetes 基础课程，也不进入 WarmPool 的实现。

<details>
<summary>源码版本与已确认边界</summary>

- 本地 /home/fredkeira/projects/agent-sandbox，37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1；本轮核对工作区干净。
- updateStatus:928–983；调用方旧状态/版本:425–426，写回调用:488；nodeNameOnlyChange:1202–1208。
- Conflict 分支依赖的事件说明位于 961–969；sandboxCreationMetricsPredicate 的 UpdateFunc 返回 true，见 1000–1007。当前只确认这一联系，不另建辅助函数卡。
- 用户确认与实际阅读见 [04](04-flow.md)，没有集群写入实验。

</details>
