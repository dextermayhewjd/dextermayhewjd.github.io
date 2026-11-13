# SandboxReconciler.computeConditions

[本步 scope](../../../../01-scope.md#reading-navigation) → [reconcileChildResources：571 行交入](SandboxReconciler.reconcileChildResources.md#observed-conditions) → **computeConditions（本页）** → [回到父函数更新内存状态](SandboxReconciler.reconcileChildResources.md#observed-conditions)

- 源码定位：[controllers/sandbox_controller.go:607–623](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L607)。
- 首次接触：Step 000 按接口定位；Kubernetes Step 002，2026-11-05 开始独立阅读。
- 最近认识更新：2026-11-05，用户明确“这里只是计算状态，不涉及任何调度内容”；此前四类语义与可选条目的说明保留，未据此推断全部细节已掌握。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：父函数已经取得 Pod、可选 Service 与资源协调错误，准备形成 Sandbox 的观察状态。
2. **具体内容**：分别调用四类状态计算方法，把适用的条件条目加入列表，返回给父函数。
3. **建议构建的心智模型**：

   > 这是状态的汇总入口。它收集“是否挂起、是否结束、是否已调度到节点、是否就绪”等不同方面的描述，不负责创建资源，也不要求所有描述都为 True。

4. **调用代码**：来自 reconcileChildResources:571。

   ```go
   conditions := r.computeConditions(sandbox, conditionErrors, svc, pod, podErr)
   ```

## 本场景的输入与输出

**教学观察时刻**：default/hello-world 要求 Running、无需 Service，Pod 已存在且属于它；假设 Pod phase 为 Pending，尚无 PodScheduled 条目或 IP，协调无错误。不是实际部署或前一步 API 返回值的实测结果。

| 输入 | 含义 |
| --- | --- |
| r | 当前协调器，用来调用状态计算方法 |
| sandbox | 已有 Sandbox 的需求与状态；本例要求 Running |
| err | 调用方传来的 conditionErrors，即资源协调中收集的错误；本例 nil |
| svc | 已取得的 Service；本例不需要且不存在，为 nil |
| pod | 属于当前 Sandbox 的 Pod 观察对象，状态如上 |
| podErr | Pod 协调这一步的错误；本例 nil。它单独传入部分条件函数 |

返回值是 **[]metav1.Condition，一个条件列表**，没有第二个 error 返回值。每条可描述 Type、Status、Reason、Message 等信息。

本例的输出节选，只展示条目种类与状态：

| 列表条目 | Status | 当前含义 |
| --- | --- | --- |
| Suspended | False | 当前没有要求挂起 |
| PodScheduled | Unknown | 这个 Pod 尚未报告调度条件 |
| Ready | False | 当前观察到的 Pod 尚未就绪 |

Finished 在本例不产生条目，因为 Pod 不在终态。上述结果来自静态核对；具体判断算法在子函数中，本轮先看怎样把结果收集起来。

<a id="condition-meanings"></a>

### 四类 condition 分别回答什么

这是同一观察时刻的四个判断，不是 Sandbox 必须依次经过的四个状态，也不要求它们全部为 True。computeConditions 负责汇总描述，具体的暂停、删除、调度和容器启动由其他代码或 Kubernetes 组件执行。

| 条件类型 | 回答的问题 | 当前实现中需要区分的含义 |
| --- | --- | --- |
| Suspended | 请求的挂起是否已经落实？ | 要求 Suspended 且确认 Pod 已不存在时为 True。请求挂起但 Pod 仍在退出时仍为 False；无法确认 Pod 状态时可能为 Unknown |
| Finished | 所属 Pod 是否进入终态？ | 正常运行模式下，所属 Pod 的 phase 为 Succeeded 或 Failed 都会形成 True 条目，用 Reason 区分成功或失败；不是 Agent 某道题已完成的通知 |
| PodScheduled | 所属 Pod 是否已被调度到节点？ | 主要镜像 Pod 的 PodScheduled condition。表示调度结果，不是未来计划执行；成功分配节点后仍可能拉取镜像或等待容器启动 |
| Ready | 当前依赖是否满足控制器的可用判断？ | 正常路径需要 Pod Running、Pod Ready=True、有 Pod IP；按配置/兼容规则需要 Service 时还要求 Service 存在，并且没有相关协调错误 |

1. **请求与观察分开。** spec.operatingMode=Suspended 是期望；Suspended=True 是当前观察到挂起已落实。这里的挂起通过终止 Pod 实现，不是冻结容器进程后原地保存运行状态。
2. **已调度与就绪分开。** PodScheduled=True 可以和 Ready=False 同时出现，例如已选好节点但仍在拉镜像。Pod phase=Running 也不单独保证 Sandbox Ready=True。
3. **结束与成功分开。** Finished=True 可能因为 PodSucceeded，也可能因为 PodFailed。Agent 在一个持续运行的服务 Pod 中完成一次任务，并不自动让 Pod 进入终态。
4. **挂起删除与工作负载结束分开。** computeFinishedCondition 在挂起模式中避免把主动删除 Pod 造成的终态当作新的完成事件；有已记录的 Finished 时可保留它，否则不新报完成。
5. **类型与状态分开。** Suspended 等是 Condition.Type，True/False/Unknown 是条目的 Status。Finished 和 PodScheduled 在不适用时可能没有条目；缺项不等于返回了一个 False。
6. **基础就绪与任务可用分开。** Ready 是本控制器依据 Pod 与 Service 作出的判断，不是一次完整的业务请求或任务初始化验收；本实现的 Service 检查是对象存在性，不是连通性探测。

本例原有 Pending 且未报告调度条件的观察对应 PodScheduled=Unknown、Ready=False。若随后 Pod 报告调度成功但尚未就绪，则可以是 PodScheduled=True、Ready=False；到了 Pod Running、Pod Ready=True、已有 IP 且所需 Service 存在的正常时刻，Ready 才可能为 True。

四个计算方法读取相关资源和状态各自作出判断；Ready 不是将另外三个 Condition.Status 做一次布尔 AND。

源码对应：[PodScheduled](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L639)、[Suspended](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L689)、[Ready](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L729)、[Finished](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L877)。本次只为解释语义核对这些分支，不表示已独立精读四个子函数。

<a id="ready-condition-call"></a>

### 2.1 汇总入口：完整短函数

下面是原函数完整源码，默认展开。if 判断的是是否有条目，而不是条目的 Status 是否为 True。

```go
func (r *SandboxReconciler) computeConditions(sandbox *sandboxv1beta1.Sandbox, err error, svc *corev1.Service, pod *corev1.Pod, podErr error) []metav1.Condition {
	var conditions []metav1.Condition

	conditions = append(conditions, r.computeSuspendedCondition(sandbox, pod, podErr))

	if finished := r.computeFinishedCondition(sandbox, pod); finished != nil {
		conditions = append(conditions, *finished)
	}

	if podScheduled := r.computePodScheduledCondition(sandbox, pod, podErr); podScheduled != nil {
		conditions = append(conditions, *podScheduled)
	}

	conditions = append(conditions, r.computeReadyCondition(sandbox, err, svc, pod))

	return conditions
}
```

1. **准备列表**：conditions 用来收集当前这次计算的条目，初始还没有条目。
2. **加入挂起状态**：computeSuspendedCondition 直接返回一条 Condition，因此直接追加；本例即使为 False 也会保留。
3. **按需加入结束状态**：computeFinishedCondition 返回可空指针。非 nil 表示有适用条目，取出该条目加入列表；本例为 nil，所以不加入。
4. **按需加入调度状态**：computePodScheduledCondition 也返回可空指针，判断方式相同。本例有一条状态为 Unknown 的条目，仍然加入。
5. **加入就绪状态**：computeReadyCondition 直接返回一条 Condition；它收到汇总错误、Service 和 Pod。本例 Ready=False，也加入列表。
6. **返回列表**：return conditions 将这些结果交给父函数。函数自身没有调用 Kubernetes API 写入状态。

**nil 表示没有条目，False 表示条目存在但条件不成立，Unknown 表示条目存在但当前无法确认。** 这里不能把“追加到列表”理解成“检查通过”。

<details>
<summary>两个语法点：append 与指针解引用</summary>

1. append 返回追加条目后的切片，所以结果再次赋给 conditions。
2. finished 与 podScheduled 是指针；通过非 nil 检查后，*finished、*podScheduled 取出所指向的 Condition 值，再放入值类型的列表。这里不是乘法。

</details>

### 2.2 子调用与返回位置

| 需要展开时进入 | 当前深度 | 读完返回哪里 |
| --- | --- | --- |
| [computeReadyCondition 函数卡](SandboxReconciler.computeReadyCondition.md) | 本轮已进入，沿普通路径看 Ready 与原因怎样形成 | 本函数 620 行，接住 Ready 条目并加入列表 |
| [computeSuspendedCondition:689](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L689) | 本轮按职责理解 | 610 行 |
| [computeFinishedCondition:877](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L877) | 本轮按职责理解 | 612–614 行 |
| [computePodScheduledCondition:639](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L639) | 本轮按职责理解 | 616–618 行 |

### 2.3 回到父函数：列表随后怎样使用

父函数在 571 行接收 conditions，再调用 SetStatusCondition 更新内存里的 Sandbox.Status.Conditions，并移除部分不再适用的旧条目。外层 Reconcile 的 updateStatus 才负责按需持久化。

因此有三个动作：本函数**计算列表**，父函数**更新内存状态**，外层**写回 API**。具体父函数代码见[状态更新段](SandboxReconciler.reconcileChildResources.md#observed-conditions)。

## 我的直接表述（原话）

确认继续下一函数：

> 好的那么我们现在在看下一个函数吗?

随后用户按四项概括，并询问区别：

> 好的
> 那么我们来看一下这里的computeconditions吧
> 我比较想要知道这里具体在做什么
> 首先看一下这里的conditions?
> 也就是这里的conditions?
> 1. 是否是暂停的
> 2. 是否结束了
> 3. 是否被计划要进行
> 4 这里是否已经ready了 就绪了?
>
> 具体这里的几种状态有特别需要区分和理解的吗?

这是对四类含义的初步表述。助手对“已调度”、挂起落实、终态和就绪的校准见上文；用户尚未反馈这些精确区别，也尚未复述可选条目的汇总规则。

随后对整体职责作出明确区分：

> 那么下一个需要看的函数了呢?
> 我知道这里只是计算状态
> 不涉及任何调度内容

这条认识对应本函数的计算与汇总边界：它描述调度等观察结果，不执行调度。未把该表述扩大为已经掌握所有条件判断或汇总语法。

## 尚不清楚

1. 条目为 nil 与 Status 为 False/Unknown 的区别，尚待阅读反馈。
2. computeReadyCondition 的具体判断已开始在独立卡中展开，理解反馈继续记录在那里。
3. 四类条件的主要语义已作比较，但完整边界与状态写回算法仍按需后置；解释提供不等于用户已掌握。

<details>
<summary>来源与验证范围</summary>

- 固定版本：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1，controllers/sandbox_controller.go:607–623。
- 调用与内存更新：571、577–591；外层写回调用：488。
- [Kubernetes Step 002 · 四类 condition 的区别](../../../../../step-002-sandbox-readiness/04-flow.md#condition-meanings)。
- 输出节选根据各子函数对 Running、所属 Pending Pod、无 PodScheduled 条目的路径静态核对；没有实际集群或运行输出。
- [Kubernetes Step 002 · 本轮阅读过程](../../../../../step-002-sandbox-readiness/04-flow.md#compute-conditions-first-card)。

</details>
