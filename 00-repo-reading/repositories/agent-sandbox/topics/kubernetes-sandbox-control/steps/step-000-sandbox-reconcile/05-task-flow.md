# 05 · 一次协调怎样连接需求、子资源与观察状态

> Reconcile 读出一份 Sandbox，把它交给子资源协调；子函数按需求操作资源并更新内存状态，外层按需写回状态，再把调度信息与错误交还 controller-runtime。

[本步 scope](01-scope.md) · [函数记录](02-short-term-memory/overview.md) · [讨论过程](04-flow.md) · [下一步](../step-001-pod-creation/01-scope.md)

## 1. 本步在任务中的位置

调用方已经提交 Sandbox 对象，控制器接到含 namespace/name 的协调请求。本步跟踪 Running、未删除、未过期的普通路径；没有 PVC 或自动创建 Service 的需求，关闭写入合并与失败重建。

读出的 Sandbox 是 Kubernetes 需求与状态记录在本地内存中的表示。Pod 是否存在、是否启动，需要后续协调观察，不能从读到 Sandbox 直接推出。

## 2. 已读部分怎样交接

以下为本步的职责骨架，子资源的完整创建算法仍按接口理解。

```text
controller-runtime
  -> Reconcile(req)                         # sandbox_controller.go:366
       -> Get Sandbox                       # 369-380
       -> save old status and version       # 425-426
       -> reconcileChildResources           # 458 -> 507
            -> reconcilePVCs                # 535
            -> reconcilePod                 # 538
            -> copy Pod IPs / node name     # 547-559
            -> reconcileService             # 566, unless mapping conflict
            -> compute and set conditions   # 571-591, in memory
            -> return delay, error          # 593
       -> compute next requeue time         # 459-483
       -> updateStatus                      # 488, persist if needed
       -> return result, error              # 500

Pod status changes -> watch event -> controller-runtime -> Reconcile again
```

1. **读取与快照**：[Reconcile](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.Reconcile.md)取得对象，旧状态与版本保留为写回依据；不是用于回滚环境。
2. **资源协调与观察**：[reconcileChildResources](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcileChildResources.md)接收同一个 Sandbox 指针，按配置协调资源，形成观察状态。PVC 与 Service 的调用不代表本例一定创建它们。
3. **字段摘取**：从所属 Pod 中读取 IP 和节点名，写入 Sandbox 状态；这里没有诊断 Node 健康，也没有重新获取 Sandbox。
4. **状态与返回**：内层返回延迟和错误；外层仍持有已经改变的 Sandbox，按需调用 updateStatus，最后返回调度结果。

时间检查决定后续何时再协调；Ready 等状态由资源观察计算。不能把这两个作用合并为“等待环境全部完成”。

## 3. 本步结果的含义与去向

| 结果 | 含义与后续 |
| --- | --- |
| 子资源操作 | 按需创建或维护 API 对象，实际调度与启动由 Kubernetes 的其他组件继续推进 |
| Sandbox.status | 反馈本轮观察，也可以记录未就绪或错误；在内存中改变后，还需要外层持久化 |
| ctrl.Result 和 error | 交给 controller-runtime 组织后续协调，不是 Agent 的执行结果 |

例如本次返回没有错误，但 Pod 仍在启动，Sandbox 可以仍然未 Ready。后续状态事件触发新一轮观察，不需要在这次函数调用里等到容器启动完成。

## 4. 本步收束与下一处

用户已尝试串联三类资源与状态，并在校准和展示调整后反馈“问题差不多了”。本步按外层闭环与子资源职责的深度收束，保留函数卡中的原话、疑问和未确认细节，不表示所有实现已掌握。

用户随后确认下一处看 reconcilePod 的正常创建路径：[Step 001 scope](../step-001-pod-creation/01-scope.md)。具体的既有 Pod 接纳、失败重建、存储驱动、网络实现和完整状态规则不作为本步结束条件。

共同基础独立保存在 [Kubernetes 专题](../../../../../kubernetes/README.md)；项目函数卡继续保留当前调用和版本证据。

<details>
<summary>来源与验证范围</summary>

- 源码固定为 37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1，controllers/sandbox_controller.go；主要范围 Reconcile:366–501、reconcileChildResources:507–594。
- [本步原始问题与修正](04-flow.md)；本页由助手整理实际讨论，不代填新的个人理解。
- 仅静态核对，没有真实集群创建、网络连接或存储挂载实验。

</details>
