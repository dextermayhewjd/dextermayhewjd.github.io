# 01 · Kubernetes Step 000：一次协调怎样连接需求、Pod 和状态

[主题入口](../../README.md) · [项目进度](../../../../README.md#current-reading) · [完整主线](#whole-flow) · [第一处阅读入口](#reading-navigation)

## 1. 阅读目标

**给定一份已经提交的 Sandbox，控制器怎样读取它、协调运行资源，并把观察到的状态写回？**

1. 本步先建立一个 Sandbox 的协调闭环，不继续沿 Python Fleet 的任务调度阅读。
2. 主攻 SandboxReconciler.Reconcile；进入 reconcileChildResources 时，先看它负责哪些资源和状态，再返回主函数。
3. 读到能解释“创建 Pod 对象”和“Pod 真正就绪”的区别就够。WarmPool、Claim、复杂失败恢复和资源调优留到后续。

## 2. 入口、场景与边界

**第一处打开 [SandboxReconciler.Reconcile 函数卡](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.Reconcile.md)，源码位于 [366–501 行](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L366)。** 它是 controller-runtime 处理协调请求的入口，连接读取资源、调用子资源协调、状态回写与重新排队。

本轮选定普通路径：Sandbox 存在、未被删除、未过期，operatingMode 为 Running；先按默认关闭写入合并、未启用失败 Pod 重建的场景理解。第一遍不展开过期、挂起和各类异常恢复。

| 进入时需要知道 | 本步只理解到哪里 |
| --- | --- |
| req.NamespacedName | 指定本次要处理的 Sandbox 的 namespace/name，不是一份创建 Pod 的完整参数 |
| Sandbox.spec | 声明期望的运行配置，核心是 podTemplate；定义见 [Sandbox API](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/api/v1beta1/sandbox_types.go#L338) |
| Sandbox.status | 控制器写出的观察结果，包括 conditions、Pod IP 和节点等；不是把 spec 原样复制过来 |
| Reconcile 的返回值 | ctrl.Result 与 error，用于告诉调度框架是否需要后续协调；不返回 Pod 或沙箱句柄 |

可用仓库的 [hello-world Sandbox 清单](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/hello-world-sandbox/hello-world.yaml)辨认资源外观。它的 IMAGE 是待替换占位符，本步只读清单结构，不部署。该最小例子未请求 Service 或 PVC：本步保留它们的协调位置，但不假定每个 Sandbox 都创建它们。

## 3. 整体位置与阅读导航

<a id="whole-flow"></a>

### 3.1 完整主线：一次返回之后，还可能继续协调

下面表示资源与事件关系，不是一个同步函数从上执行到下的源码。controller-runtime 已在运行；SetupWithManager 事先注册对 Sandbox 及其拥有的 Pod、Service 的观察，不是每次由它直接调用 Reconcile。

```text
[1] caller creates or updates Sandbox.spec
      -> Kubernetes API server
      -- watch event --> controller-runtime queue

[2] SandboxReconciler.Reconcile                 // OUTER: first-pass mainline
      -> r.Get(...): read the target Sandbox
      -> r.reconcileChildResources(...)         // NOW: local skeleton only
           -> r.reconcilePVCs(...)              // if volume templates exist
           -> r.reconcilePod(...)               // create or observe backing Pod
           -> r.reconcileService(...)           // creation requires service=true
           -> r.computeConditions(...)
           -> update sandbox.Status in memory
      -> r.updateStatus(...)                    // persist observed status
      -> return ctrl.Result, error              // scheduling result

[3] Kubernetes scheduler + kubelet + runtime
      -> schedule Pod and run containers
      -> update Pod status
      -- watch event --> queue --> [2] again

[4] caller observes Sandbox.status
      -> uses the environment when usable
      -> later shutdown/deletion                // later scope
```

1. **声明需求**：调用方提交 Sandbox 对象，描述想要的运行环境。
2. **协调资源与记录状态**：当前控制器根据需求和已观察到的对象推进子资源，并反馈状态。
3. **实际运行与再次观察**：Pod 的调度和容器启动由 Kubernetes 原有组件完成；新状态触发后续协调，控制器再据此更新 Sandbox。
4. **使用与后续回收**：调用方读取状态并使用环境。完整删除、过期和资源回收机制后续单独展开。

**本步的位置是 [2]，必须知道它与 [1]、[3]、[4] 的交接。一次 Reconcile 返回不等于环境 Ready，也不是在这个函数里一直阻塞等容器启动。**

<a id="reading-navigation"></a>
<a id="current-excerpt"></a>

### 3.2 面包屑：从 Reconcile 进入子调用，再回到 Reconcile

controller-runtime → [Reconcile：外层主线](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.Reconcile.md) → **[reconcileChildResources：当前展开](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcileChildResources.md)** → 回到 Reconcile → [updateStatus](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L928) → 返回 controller-runtime。

以下摘出普通路径的关键调用位置，用省略号隐藏参数和其余语句；这是导航骨架，不是可编译的 Go 函数。原文件中的过期、错误及重新排队分支仍然存在。

```go
// [1] Reconcile:369-382, read the target object
sandbox := &sandboxv1beta1.Sandbox{}
if err := r.Get(...); err != nil { ... }

// [2] Reconcile:458, enter the resource coordinator
recreateRequeue, err = r.reconcileChildResources(...)

// Reconcile computes the next requeue time from the observed situation.
...

// [3] Reconcile:486-492, persist the observed status
if statusUpdateErr := r.updateStatus(...); statusUpdateErr != nil { ... }

// [1] Reconcile:500, return to controller-runtime
return result, err
```

| 阅读位置与入口 | 本次要弄清什么 | 返回哪里继续 |
| --- | --- | --- |
| 1. [Reconcile](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.Reconcile.md)，外层主线 | 请求定位哪份对象；普通路径怎样串起资源协调、状态回写与返回 | 458 行进入 2；返回后继续到 488 行的 3 |
| 2. [reconcileChildResources](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcileChildResources.md)，当前局部展开 | PVC、Pod、Service 各是什么职责；哪些观察结果写进内存中的 Sandbox.status | 返回 Reconcile:458，保留延迟与错误，再继续主线 |
| 3. [updateStatus](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L928)，先按接口读 | 把已算出的 status 持久化；它与子函数在内存中修改 status 有什么区别 | 返回 Reconcile:488，最终在 500 行结束本次调用 |
| 4. [SetupWithManager](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L2414)，只有事件来路不清楚时回查 | 哪些资源事件会让控制器再次处理这个 Sandbox | 回到 Reconcile 入口；这是阅读回查，不是执行顺序上的第四阶段 |

本步先读第 1 个函数的外层主线，再进入第 2 个函数的职责骨架；两者现均有独立函数卡。reconcilePod、Service/PVC 细节和 computeConditions 的完整条件规则先保留源码定位，不因为出现在图中就预建函数卡。

**停止位置**：能指认请求、期望状态、子资源操作、观察状态、状态回写，以及后续事件／重新排队的去向。尚未读懂的条件和辅助函数保留未知，不要求把控制器一次读完。

<details>
<summary>源码定位、选定分支与后续材料</summary>

- 固定 checkout：/home/fredkeira/projects/agent-sandbox，37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1；本次核对工作区干净。
- 主要入口：Reconcile:366–501；reconcileChildResources:507–594；状态计算入口 computeConditions:607；updateStatus:928；事件注册 SetupWithManager:2414。
- 子资源定位：[reconcilePod](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L1674)、[reconcileService](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L1463)、[reconcilePVCs](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/controllers/sandbox_controller.go#L2202)。本步先看它们被谁调用和交出什么，不深挖全部实现。
- 未请求 volumeClaimTemplates 时，PVC 协调没有需要创建的条目。Service 未设置时不会为新的 Sandbox 自动创建 Service；请求自动创建需 service=true。不要把调用了协调函数等同于必定创建资源。
- 本轮不进入删除、过期处理、Suspended、失败 Pod 重建退避或 write-behind 合并；这些分支在后续问题出现时再读。
- WarmPool/Claim 以及任务侧 Fleet 是其他层次，本步不要求继承旧主题的函数卡。旧背景可从[项目资料](../../../../references/tencent-k8s-learning-scope.md)按需回查。
- 已建立 Reconcile 与 reconcileChildResources 函数卡；更深的辅助函数仍只保留源码导航，没有运行实验或已掌握判断。实时进度以项目入口为准。

</details>
