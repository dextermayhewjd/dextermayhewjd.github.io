# 05 · 从资源观察形成 Sandbox 的状态与 Ready 判断

> computeConditions 接住当前资源与错误，汇总多种状态；其中 computeReadyCondition 根据 Pod 与 Service 要求形成 Ready 条目。列表返回父函数后更新内存 Status，再由外层按需写回 API。

[本步 scope](01-scope.md) · [函数索引](02-short-term-memory/overview.md) · [本轮复述与收束](04-flow.md#step002-closure)

## 1. 本步在任务中的位置

前一步处理 Pod 的正常创建。本步读取已有 Pod 等资源的当前情况，研究它们怎样变成 Sandbox 的观察状态；仍位于总图 [2]，没有进入 Scheduler、kubelet 或执行任务的内部。

沿用要求 Running、未过期、无协调错误、无需 Service 的教学场景。主例是所属 Pod 仍处于 Pending，正常就绪输入作为对照；这些均为静态构造，没有实际运行集群。

## 2. 已读部分怎样完成交接

```text
reconcileChildResources:571
  -> computeConditions                         # 607-623
       -> computeSuspendedCondition             # add returned condition
       -> computeFinishedCondition              # add only if non-nil
       -> computePodScheduledCondition          # add only if non-nil
       -> computeReadyCondition                 # 620 -> 729
            -> initialize Ready=False
            -> error / suspended / terminal?    # early False result
            -> evaluate Pod requirements
            -> evaluate Service requirements
            -> set True only if both pass
            -> return one Condition             # 838
       -> return conditions                     # 622
  -> update in-memory Sandbox.Status.Conditions # 577-591
  -> return to Reconcile
       -> updateStatus                          # persistence boundary
```

1. [computeConditions](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.computeConditions.md)负责汇总列表，不执行调度。四类状态描述同一时刻的不同方面，不是依次发生的四个生命周期阶段。
2. [computeReadyCondition](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.computeReadyCondition.md)生成一条 Ready 记录。初始化为 False；错误、挂起或终态可直接返回未就绪原因。
3. 普通路径中，Pod 需要存在、phase=Running、Pod 自身 Ready=True，并且已有 IP。Service 先按配置与兼容规则判断是否需要，需要时检查对象是否存在。
4. podReady 与 svcReady 同时为 true，才将最终记录改成 Ready=True。返回后由汇总入口追加到列表，而不是在本函数直接写 API。
5. [父函数](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcileChildResources.md#observed-conditions)使用条件列表更新内存状态，持久化仍交给 Reconcile 中的 updateStatus。

## 3. 结果的含义与去向

| 结果 | 含义 |
| --- | --- |
| 单条 Ready Condition | 描述 Status、Reason、Message 等，不是调用成功或任务奖励 |
| 条件列表 | 可以包含 False 或 Unknown；可选条目为 nil 时不加入列表，缺项不是 False |
| 内存中的 Sandbox.status | 由父函数设置或移除相应条目；外层按需写回后才成为持久化观察状态 |

主例 Pod 为 Pending 时，podReady=false、svcReady=true，返回 Ready=False，Reason=DependenciesNotReady，消息描述 Pending。若换成 Pod Running、Pod Ready=True 且有 IP、其他前置也满足的观察，则可返回 Ready=True。需要 Service 却没有该对象时仍为 False。

Ready 反映此控制器定义的依赖就绪，不是业务初始化或端到端调用验收；本实现对 Service 的判断为对象存在性。

## 4. 本步收束与保留边界

用户已经明确状态计算不执行调度，并用自己的话概括了 Pod 与按需 Service 两项主判断。助手补充提前返回的前提，并将一条状态、列表、内存更新和持久化的交接收拢在本页。本步按状态汇总与 Ready 普通路径的既定范围完成阅读收束。

完整错误分类、其他三个条件函数的全部边界、具体 Service 配置兼容分支和状态写回算法继续按需回查；原卡中未得到个人反馈的内容保留为未知，不要求为本步结束把所有辅助函数读完。尚未开启下一 Step。

<details>
<summary>来源与验证范围</summary>

- 固定版本：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1，controllers/sandbox_controller.go。
- 本步重点：computeConditions:607–623、computeReadyCondition:729–839；父函数调用:571，内存更新:577–591，外层写回调用:488。
- 用户原话、解释与修正见 04 和两张当前函数卡；没有把助手解释全部改写为个人理解。
- 静态源码核对与教学对照，没有集群部署、实际调用或运行验证。

</details>
