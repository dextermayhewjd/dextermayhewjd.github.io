# 05 · 从 Sandbox 需求到已提交的 Pod

> reconcilePod 接住 Sandbox 的运行需求，先确认已有 Pod，再在选定的缺失路径中组装 Pod、设置归属并提交创建，最后把对象与处理结果交回父函数。

[本步 scope](01-scope.md) · [reconcilePod 函数卡](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcilePod.md) · [实际讨论](04-flow.md) · [下一步](../step-002-sandbox-readiness/01-scope.md)

## 1. 本步在整体中的位置

Reconcile 已经读取 Sandbox，reconcileChildResources 在 538 行调用本函数。本步选定 Running、没有对应 Pod、没有旧名称注解、无 PVC 模板、未启用失败重建的正常创建路径。

这里延续总图 [2] 的资源协调，终点是创建 API 对象并返回。选择 Node、运行容器及后续就绪变化仍由 Kubernetes 其他组件继续推进。

## 2. 已读部分怎样完成交接

```text
reconcileChildResources:538
  -> reconcilePod
       -> List candidates + sandboxOwnedPods        # 1686-1695
       -> resolvePodName + Get named Pod             # 1698-1718
       -> merge ownership views / select branch     # 1723-1951
       -> copy PodTemplate and build Pod             # 1953-2027
       -> SetControllerReference                     # 2028
       -> Create                                     # 2031
       -> return pod, 0, nil                         # 2059
  <- pod, recreateRequeue, podErr
  -> copy observed Pod information
  -> reconcileService
  -> computeConditions                              # next reading unit
```

1. **确认现状**：List 以 namespace 和跟踪标记共同筛选候选；本地归属筛选确认控制者 UID。按名称 Get 是另一条查询，两路结果随后合并。本例确实无 Pod，进入创建分支。
2. **组装对象**：模板里的运行配置进入 Pod.Spec，名称、namespace、标签与注解进入元数据。此时只有本地对象。
3. **归属与提交**：SetControllerReference 将控制归属写入 Pod 元数据；Create 再将对象提交到 Kubernetes。这不是选择运行节点的动作。
4. **交回调用者**：正常返回的三个值由父函数依次接住；父函数继续整理 Pod 信息、处理 Service 并计算状态。

已有 Pod、挂起、失败重建、复杂元数据传播与并发创建冲突只保留分支定位，不属于本次完整展开范围。

## 3. 本步结果的含义与去向

| 返回项 | 本例 | 父函数怎样接收 |
| --- | --- | --- |
| Pod 指针 | 已提交创建的 Pod 对象 | 赋给 pod，继续读取节点、地址与状态 |
| 重建等待时长 | 0 | 赋给 recreateRequeue，交给外层调度逻辑 |
| 错误 | nil | 赋给 podErr，与其他资源错误一起形成状态和返回结果 |

创建正常返回不代表 Pod 已经 Ready，也不代表 Agent 任务完成。这里没有直接返回 reward、轨迹或业务结果。

## 4. 收束与后续衔接

用户明确说清了查询条件的 AND 关系，并能概括字段组装和创建归属引用；两路查询及具体分支的后续解释仍按原卡保留来源和未知，不因进入下一步改为全部掌握。

本步按正常创建路径收束。用户确认继续下一函数后，建立 Step 002：先看 computeConditions 的汇总，再以 computeReadyCondition 为下一处重点，回答创建以后怎样表达 Sandbox 是否就绪。

<details>
<summary>源码与验证边界</summary>

- 固定版本：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1，controllers/sandbox_controller.go:1674–2060。
- 讨论与修正见本步 04，完整输入输出和源码节选见函数卡。
- 本次只有静态源码阅读与文档核对，没有创建 Pod、连接集群或运行容器的实践结果。

</details>
