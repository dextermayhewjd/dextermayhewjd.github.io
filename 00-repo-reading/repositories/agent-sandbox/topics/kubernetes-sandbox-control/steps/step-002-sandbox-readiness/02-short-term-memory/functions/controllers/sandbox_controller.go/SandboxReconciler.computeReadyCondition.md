# SandboxReconciler.computeReadyCondition

[本步 scope](../../../../01-scope.md#reading-navigation) → [computeConditions：620 行调用](SandboxReconciler.computeConditions.md#ready-condition-call) → **computeReadyCondition（本页）** → [返回汇总入口，加入条件列表](SandboxReconciler.computeConditions.md#ready-condition-call)

- 源码定位：[controllers/sandbox_controller.go:729–839](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L729)。
- 首次接触：Step 002 中先按职责定位；2026-11-05，用户明确要求开始独立阅读。
- 最近认识更新：2026-11-05，用户已概括正常路径中的两项要求：Pod 实际 Running、Ready 且有 IP，Service 按需检查存在性；助手补充无协调错误、未要求挂起及非终态的前置边界。原话与补充分别保存。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：computeConditions 已取得当前 Sandbox、Pod、可选 Service 和协调错误，调用本函数生成其中的 Ready 条目。
2. **具体内容**：初始化为未就绪；错误、挂起或终态时提前返回原因；普通路径检查 Pod 与 Service 要求，再决定是否改为就绪。
3. **建议构建的心智模型**：

   > 用本轮已有的观察结果，生成一条“是否就绪，以及为什么”的说明。默认保留 False，满足当前实现的要求才改成 True；函数不调度、不创建资源，也不等待状态变好。

4. **调用代码**：computeConditions:620 接住返回的 Condition 值，将其追加进列表。

   ```go
   conditions = append(conditions, r.computeReadyCondition(sandbox, err, svc, pod))
   ```

## 本场景的输入与输出

沿用父卡的静态教学场景：default/hello-world 要求 Running，未过期，无协调错误；不要求 Service，svc=nil。所属 Pod 已存在，phase=Pending，没有 Ready 条目或 IP。本例进一步明确没有额外容器错误信息；这不是实测运行结果。

| 输入 | 当前含义 |
| --- | --- |
| r | 当前协调器，本函数通过它调用方法 |
| sandbox | 提供 operatingMode、Service 配置及 generation 等信息 |
| err | 前面资源协调中收集的错误，经父函数传入；本例 nil，不是本函数新发起操作产生的错误 |
| svc | 已取得的 Service 对象；本例不需要且不存在 |
| pod | 本轮已取得的 Pod 观察对象；本例为所属 Pending Pod |

**返回一条 metav1.Condition 值**，不是条件列表，也没有单独返回 error。本例结果节选为：

| 字段 | 本例结果 |
| --- | --- |
| Type | Ready |
| Status | False |
| Reason | DependenciesNotReady |
| Message | Pod exists with phase: Pending |
| ObservedGeneration | 当前传入的 sandbox.Generation |

这条新记录先返回给 computeConditions；写进内存 Status 和持久化是外层的后续动作。本函数当前实现会返回 True 或 False，不返回 nil，也没有将 Ready.Status 设为 Unknown 的分支。

### 内部主线：下面五段都属于同一个函数

2.2 是 scope 中的 Ready 判断入口，下面 2.2.1–2.2.5 只是它内部的连续阶段。代码默认展开，长说明按需展开。

| 阶段 | 做什么 |
| --- | --- |
| [2.2.1 初始化](#initial-condition) | 准备一条默认未就绪的记录 |
| [2.2.2 提前返回](#early-results) | 已有错误、要求挂起或 Pod 已终止时，直接说明原因 |
| [2.2.3 Pod 要求](#pod-readiness) | 检查 Running、Pod Ready 与 IP |
| [2.2.4 Service 要求](#service-readiness) | 先决定是否需要 Service，再判断这项要求是否满足 |
| [2.2.5 合并与返回](#ready-return) | 更新说明；两项要求满足时设为 True，再返回 |

以下按源码顺序节选函数主体，未改调用和判断语句；函数声明行及部分注释省略。

<a id="initial-condition"></a>

#### 2.2.1 初始化：默认记录“尚未就绪”（730–736）

```go
readyCondition := metav1.Condition{
	Type:               string(sandboxv1beta1.SandboxConditionReady),
	ObservedGeneration: sandbox.Generation,
	Message:            "",
	Status:             metav1.ConditionFalse,
	Reason:             sandboxv1beta1.SandboxReasonDependenciesNotReady,
}
```

先准备本地的状态说明，后面根据观察改写它。默认 False 不表示函数执行出错。

<details>
<summary>这几个字段分别说明什么</summary>

1. Type=Ready：这是就绪条目。
2. Status=False：尚未确认就绪；后面的普通判断通过后才改为 True。
3. Reason：便于程序识别的原因代码，初始为 DependenciesNotReady。
4. Message：具体说明文字，后面按观察填入。
5. ObservedGeneration：这次判断针对哪一代 Sandbox 配置；不同于前面学过的 resourceVersion。

</details>

<a id="early-results"></a>

#### 2.2.2 提前返回：先处理明确不能报告就绪的情况（738–779）

以下省略源码中的解释性注释，保留实际分支。当前例子没有错误、不要求挂起、Pod 也未进入终态，所以继续下一段。

```go
if err != nil {
	if multiplePodsErr := asMultipleSandboxPodsError(err); multiplePodsErr != nil {
		readyCondition.Reason = sandboxv1beta1.SandboxReasonMultiplePods
		readyCondition.Message = multiplePodsErr.Error()
		return readyCondition
	}
	if k8serrors.IsInvalid(err) {
		readyCondition.Reason = sandboxv1beta1.SandboxReasonInvalidConfiguration
		readyCondition.Message = err.Error()
		return readyCondition
	}
	readyCondition.Reason = sandboxv1beta1.SandboxReasonReconcilerError
	readyCondition.Message = "Error seen: " + err.Error()
	return readyCondition
}

isSuspended := sandbox.Spec.OperatingMode == sandboxv1beta1.SandboxOperatingModeSuspended
if isSuspended {
	readyCondition.Reason = sandboxv1beta1.SandboxReasonSuspended
	if pod != nil {
		readyCondition.Message = "Sandbox is suspending"
	} else {
		readyCondition.Message = "Sandbox is suspended"
	}
	return readyCondition
}

if pod != nil {
	switch pod.Status.Phase {
	case corev1.PodSucceeded:
		readyCondition.Reason = sandboxv1beta1.SandboxReasonPodSucceeded
		readyCondition.Message = "Pod completed successfully"
		return readyCondition
	case corev1.PodFailed:
		readyCondition.Reason = sandboxv1beta1.SandboxReasonPodFailed
		readyCondition.Message = "Pod failed"
		return readyCondition
	}
}
```

<details>
<summary>三类提前返回与判断先后</summary>

1. 有资源协调错误时，先按映射冲突、非法配置或一般错误记录原因，然后返回。
2. 没有前述错误，但要求挂起时，返回挂起中的说明；这里只描述情况，不执行删除 Pod。
3. 前面未返回，且 Pod 已成功或失败退出时，报告该终态。成功退出也不是“可以继续使用的运行环境”。

这些出口都保留初始化的 Status=False，主要改写 Reason 和 Message。代码有先后优先级，并非收集完所有原因才返回。错误分类和完整挂起机制暂不继续下钻。

</details>

<a id="pod-readiness"></a>

#### 2.2.3 Pod 要求：实际 Running、Ready 且已有 IP（781–809）

```go
message := ""
podReady := false
if pod != nil {
	message = "Pod exists with phase: " + string(pod.Status.Phase)
	// Check if pod Ready condition is true
	if pod.Status.Phase == corev1.PodRunning {
		message = "Pod is Running but not Ready"
		for _, condition := range pod.Status.Conditions {
			if condition.Type == corev1.PodReady {
				if condition.Status == corev1.ConditionTrue {
					if len(pod.Status.PodIPs) == 0 {
						message = "Pod is Ready but has no podIPs yet"
					} else {
						message = "Pod is Ready"
						podReady = true
					}
				}
				break
			}
		}
	}
} else {
	message = "Pod does not exist"
}
if pod != nil && !podReady && isOwnedBySandbox(pod, sandbox) {
	if issue := podContainerIssue(pod); issue != "" {
		message += "; " + issue
	}
}
```

本例 Pod 仍为 Pending，因此 podReady 保持 false，说明是 Pod exists with phase: Pending。

<details>
<summary>Pod 的三个判断与诊断文字</summary>

1. Pod 必须存在。不存在时保留 false，并写明 Pod does not exist。
2. Pod 的 phase 必须为 Running；这里读取实际观察，不是 Sandbox.Spec 中“希望运行”的配置。
3. 在 Pod 的 Conditions 中找到 Ready=True，并且 PodIPs 至少有一项，才把局部变量 podReady 设为 true。
4. 已知属于当前 Sandbox 的 Pod 尚未就绪时，podContainerIssue 可补充容器问题文字；它在这里没有把 podReady 改成 true。

这里涉及两个 Ready：Pod.Status.Conditions 中的 Ready 是输入；本函数构造的 Sandbox Ready 是输出。并不是把其他三个 Sandbox 条目做一次 AND。

</details>

<a id="service-readiness"></a>

#### 2.2.4 Service 要求：先判断是否需要，再判断是否存在（813–830）

```go
svcRequired := false
if sandbox.Spec.Service != nil {
	svcRequired = *sandbox.Spec.Service
} else if svc != nil {
	// Backward compatibility: require service readiness
	svcRequired = true
}

svcReady := true
if svcRequired {
	svcReady = false
	if svc != nil {
		message += "; Service Exists"
		svcReady = true
	} else {
		message += "; Service does not exist"
	}
}
```

本例未配置 Service 且 svc=nil，因此 svcRequired=false，svcReady 保持 true，表示“这一项要求已满足，无需额外 Service”。

<details>
<summary>配置与存在性怎样配合</summary>

| Sandbox.Spec.Service | svcRequired 的结果 |
| --- | --- |
| 显式 true | 需要 Service |
| 显式 false | 不需要 Service |
| 未设置 | 已取得 Service 时按兼容规则要求它；没有则不要求 |

需要 Service 时，当前实现只用 svc 是否为 nil 判断这一项。它没有在此进行 DNS 查询、端口连接或业务请求。svcReady=true 不是“已实测网络畅通”的证明。

</details>

<a id="ready-return"></a>

#### 2.2.5 合并与返回：条件满足才把 False 改成 True（832–838）

```go
readyCondition.Message = message
if podReady && svcReady {
	readyCondition.Status = metav1.ConditionTrue
	readyCondition.Reason = sandboxv1beta1.SandboxReasonDependenciesReady
}

return readyCondition
```

本例是 podReady=false、svcReady=true，所以最终仍为 Ready=False，Reason 保留 DependenciesNotReady，Message 描述 Pending 状态。

<details>
<summary>换一种观察输入，返回结果怎样变化</summary>

以下仅比较输入，不是实际运行时间线。均假设没有前面的错误、挂起或终态出口。

| 当前观察 | Ready 结果 |
| --- | --- |
| Pod Pending，未要求 Service | False |
| Pod Running、Pod Ready=True，但还没有 IP | False |
| Pod Running、Pod Ready=True、有 IP，且不需要 Service | True，Reason=DependenciesReady |
| 同上，但明确要求 Service 而 svc=nil | False |

返回的只是一个状态值，不会在此更新集群。computeConditions 在 620 行把它加入条件列表，reconcileChildResources 再更新内存 Status，外层 Reconcile 按需写回。

</details>

读完回到 [computeConditions 的 Ready 调用位置](SandboxReconciler.computeConditions.md#ready-condition-call)。基础就绪不自动包含题目初始化或 Agent 工具调用成功。

## 我的直接表述（原话）

用户本轮要求：

> 好的
> 那么我们来看一下这里的computereadyucondition这里吧

建卡时只是确认进入本函数，不据建卡或源码核对推断已掌握。随后用户对主要判断作出表述：

> 简单的心智模型是
> 这里会需要
> 看清楚conditions?
>
> 条件式两个内容一个是pod 实际running ready 并且有ip
> 然后第二个是service 是判断需要再判断是否存在
> 只要满足这两个条件满足就判断为ready对吗?
>
> 如果是的话这里的这个step是否就算结束和完成了呢?

这准确概括了正常路径中 podReady 与 svcReady 的合并。助手补充：前面如果已有协调错误、要求挂起或 Pod 已终止，会提前返回 False，不能无条件只看最后两个布尔量。这里是本函数内部的两项判断，不是要求其他几个 Sandbox conditions 全部为 True。

## 尚不清楚

1. 用户已说清正常路径的两项要求；提前返回的错误分类与优先级已补说明，未逐项确认掌握。
2. Service 配置未设置、显式 false 等具体分支仍保留回查；对象存在与实际连接成功的边界不因本步收束改变。
3. 额外错误分类、容器诊断、完整客户端等待与业务验证不在本轮深入。

<details>
<summary>来源与验证范围</summary>

- 固定源码：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1；controllers/sandbox_controller.go:729–839。调用方为 computeConditions:620。
- 原因常量与语义：api/v1beta1/sandbox_types.go:25–106。本页普通输入、输出和对照均按静态源码核对，没有查询真实 Pod 或调用网络。
- [Kubernetes Step 002 · 本次进入 Ready 判断](../../../../../step-002-sandbox-readiness/04-flow.md#compute-ready-first-card)。
- [本轮心智模型与收束](../../../../../step-002-sandbox-readiness/04-flow.md#step002-closure)保存用户原话、前置限定及结束范围。
- 代码默认展开，详细说明按需展开；辅助方法只保留当前所需用途，未另建未读卡片。

</details>
