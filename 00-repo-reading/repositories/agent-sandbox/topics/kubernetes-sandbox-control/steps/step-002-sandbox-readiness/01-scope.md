# 01 · Kubernetes Step 002：状态汇总与就绪判断

[步骤入口](README.md) · [前一步总结](../step-001-pod-creation/05-task-flow.md) · [共享基础](../../../../../kubernetes/README.md) · [唯一进度](../../../../README.md#current-reading)

## 1. 阅读目标

**Pod 已经被创建或观察到，控制器怎样据此形成 Sandbox 状态，并判断是否就绪？**

1. 先看 computeConditions，理解状态条目怎样汇总。
2. 再重点进入 computeReadyCondition，理解 Ready 和未就绪原因从哪里来。
3. 返回父函数，接清内存 Conditions 的更新与外层状态写回；不在本步展开所有条件函数和完整持久化算法。

当前优先深入 Ready，是为了接通前一步“Pod 已创建”与调用方“可以开始使用环境”之间的判断。PodScheduled 更适合解释调度等待，Finished 更适合工作负载结束与回收，Suspended 更适合主动挂起；它们已按职责定位，后续遇到相应问题再深入。Ready 提供控制器的就绪信号，具体等待与调用由 SDK/上层决定，不保证任意一次工具调用成功或题目初始化已经完成。

## 2. 入口与场景

当前入口为 [computeConditions 函数卡](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.computeConditions.md)，对应源码 [607–623 行](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L607)。父函数 reconcileChildResources 在 571 行调用它。

汇总入口已展开，本轮从其中的 620 行进入 [computeReadyCondition 函数卡](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.computeReadyCondition.md)，现已按普通路径完成讲解与收束。它返回单条 Condition，再回到上面的汇总入口；仍属于同一个 Step 002，其他分支的未知保留。

沿用 default/hello-world，要求 Running、未删除、未过期、无需 Service。选取一个明确的教学观察时刻：Pod 已存在且属于该 Sandbox，phase 为 Pending，尚无 PodScheduled 条目及 Pod IP，资源协调没有报错。这是用于理解状态的静态假设，不是前一步真实部署结果。

输入为已有 Sandbox、Pod、可选 Service 与错误；返回一个条件列表。创建成功、状态条目存在、状态为 True 是不同事实。本步不负责再次创建 Pod，也不等待容器在函数内启动完成。

## 3. 整体位置与局部骨架

<a id="whole-flow"></a>

### 3.1 完整主线：本轮移到状态计算

图中 read 表示对应范围已讲过；role only 表示只按职责定位。Step 002 已覆盖状态汇总与 Ready 普通路径，不表示已掌握全部机制。

```text
[1] caller submits Sandbox.spec                 # context only
      -> Kubernetes API server
      -- watch event --> controller-runtime queue

[2] SandboxReconciler.Reconcile                  # Step 000: read
      -> r.Get(...): read Sandbox                # Step 000: read
      -> save oldStatus / oldResourceVersion    # Step 000: read
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
           -> update sandbox.Status in memory   # Step 000: read
      -> determine next requeue time            # Step 000: read
      -> r.updateStatus(...)                    # role only
      -> return ctrl.Result, error               # Step 000: read

[3] scheduler + kubelet + runtime                # context only
      -> schedule Pod and run containers
      -> report Pod status
      -- watch event --> queue --> [2] again

[4] caller observes Sandbox.status              # context only
      -> uses the environment when usable
      -> shutdown / deletion                    # later scope
```

本步仍在总图 [2]。四种状态计算都由 computeConditions 组织，但函数内部调用次序不代表 Pod 先挂起、再完成、再调度；它们是在描述同一个观察时刻的不同方面。

<a id="reading-navigation"></a>

### 3.2 本轮导航：汇总入口、Ready 判断与返回

下面是 computeConditions 内部的教学裁剪，省略实参，保留追加条件的分支。完整短函数默认展开在函数卡中。

```go
// [2.1] 汇总不同方面的状态；指针非 nil 才追加可选条目
var conditions []metav1.Condition
conditions = append(conditions, r.computeSuspendedCondition(...))
if finished := r.computeFinishedCondition(...); finished != nil {
    conditions = append(conditions, *finished)
}
if podScheduled := r.computePodScheduledCondition(...); podScheduled != nil {
    conditions = append(conditions, *podScheduled)
}

// [2.2] Ready 的具体判断交给这个子函数，本轮已讲普通路径
conditions = append(conditions, r.computeReadyCondition(...))
return conditions
```

返回后，由另一个函数 reconcileChildResources 继续；以下是调用方节选，不属于 computeConditions 内部：

```go
// [2.3] 接住列表，再更新内存中的 Conditions
conditions := r.computeConditions(...)
// ... 设置当前条目，移除不再适用的部分旧条目 ...
```

| 局部入口 | 当前阅读深度 | 返回位置 |
| --- | --- | --- |
| 2.1 [computeConditions](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.computeConditions.md) | 已讲汇总流程；用户明确只计算状态、不执行调度 | 返回父函数 571 行 |
| 2.2 [computeReadyCondition](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.computeReadyCondition.md) | 本轮已讲普通路径；用户已概括 Pod 与按需 Service 两项主判断，提前返回前提已补充 | 返回汇总入口 620 行 |
| 2.3 [父函数的状态更新](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcileChildResources.md#observed-conditions) | 复用前序模型，确认列表怎样进入内存状态，外层再写回 | 回到 Reconcile 的 updateStatus 调用 |

<a id="condition-reading-questions"></a>

**四种条件分别在什么问题下深入：** 本轮重点是 Ready，接通“Pod 已创建”与“环境可供使用”的判断；其余条件按对应问题回查。下表不是四步执行顺序，也不要求现在同时精读四个函数。

| 条件 | 更适合在哪个问题下深入 |
| --- | --- |
| PodScheduled | 为什么还没分配到节点、卡在调度哪里？ |
| Finished | Pod 是否已经成功或失败退出，之后怎样收尾？ |
| Suspended | 主动挂起是否已经落实？ |
| **Ready（本轮重点）** | 当前是否达到控制器定义的可用条件？ |

**停止位置**：能说清 Ready 条目根据什么产生、False/Unknown/nil 的区别，以及列表返回与写回的边界。不是要求所有条件为 True，也不是研究所有 Kubernetes 就绪机制。

本步已按上述范围整理[收束总结](05-task-flow.md)。用户已表达的主判断与助手补充的边界分别保留；未确认的细节继续见函数卡的未知项。

其他三个条件函数先保留职责与源码定位，完整挂起、终态、失败恢复和写回冲突处理按需后置。共同概念见 [Pod 与就绪](../../../../../kubernetes/03-workloads/pod-node-and-readiness.md)。

<details>
<summary>源码版本和已确认范围</summary>

- 本地 /home/fredkeira/projects/agent-sandbox；固定版本 37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1，本轮核对工作区干净。
- computeConditions:607–623，computeReadyCondition:729；父函数调用:571，内存条目更新:577–591，外层写回调用:488。
- 用户确认与实际阅读记录见 [04](04-flow.md)。本步没有运行集群实验，源码定位与建卡不代表已理解所有实现。

</details>
