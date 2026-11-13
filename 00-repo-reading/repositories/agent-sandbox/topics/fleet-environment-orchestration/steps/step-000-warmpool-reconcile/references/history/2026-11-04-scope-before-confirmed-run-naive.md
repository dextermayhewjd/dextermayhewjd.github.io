> 2026-11-04：用户确认从 run_naive 开始前的 scope 快照。相对链接已按归档位置调整。

# 01 · 预热池补充备用环境：阅读范围与核心骨架

[本步入口](../../README.md) · [项目当前接续](../../../../../../README.md#current-reading) · [函数记录](../../02-short-term-memory/overview.md) · [本次过程](../../04-flow.md)

## 1. 阅读目标

整体沿用已经确定的四项：**预热与环境供给、不同任务与环境的抽象、不同 Agent 的接入与隔离、大规模 rollout 的运行保障**。此前 12 组 examples 是这些目标的[材料索引](../../../../../../references/rl-environments-and-jd.md#learning-scope)，按问题选用。

**Step 000 从预热供给开始：目标备用 3 个、当前只有 1 个时，谁发现差额，创建什么对象，又把观察到的数量写到哪里？** 先看完整协调骨架，再一次打开一个函数。

本轮采用正常补池场景：Template 已存在，WarmPool 未删除；池中有 1 个有效且 Ready 的 Sandbox，没有正在删除的成员；创建预算允许补足差额，之前的创建和删除也已被缓存观察到。批量限速、旧缓存、异常与资源不足的处理保留为后续观察点。

## 2. 找到指挥官函数

首读 **[1] `SandboxWarmPoolReconciler.Reconcile`**。它负责取出一个 WarmPool，交给 `reconcilePool` 协调，再写回状态，适合先看清一轮工作的边界。

| 定位 | 内容 |
| --- | --- |
| 本地仓库 | `/home/fredkeira/projects/agent-sandbox` |
| 固定版本 | `37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1`，2026-11-04 核对时工作区干净 |
| 源文件 | `extensions/controllers/sandboxwarmpool_controller.go` |
| 首读入口 | [Reconcile，第 435 行](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L435) |
| 数量协调入口 | [reconcilePool，第 491 行](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L491) |

进入前只需区分三个对象：`SandboxTemplate` 保存环境蓝图，`SandboxWarmPool` 保存备用目标及观察状态，`Sandbox` 表示一个受管理的环境。字段定义可按需回查 [SandboxWarmPool API](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/api/v1beta1/sandboxwarmpool_types.go#L43)。

调用背景是 controller-runtime：它把相关资源变化排入队列，再用 namespace/name 请求协调一个 WarmPool。`Reconcile` 处理一轮，并非内部一直运行的循环。观察注册在 [SetupWithManager](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L1418)，本轮先知道来路即可。

## 3. 给出真正干活的核心骨架

### 3.1 放回强化学习的环境供给主线

下图是职责与资源交接示意，`# Step 000` 标出本步位置。这里跟随从预热池领取环境的路径；跨控制器的箭头由 Kubernetes 资源变化连接，不表示一串同步函数调用，也不是可执行代码。

```python
RL batch demand
  -> SandboxFleet / LookaheadWarmer
  -> SandboxTemplate + SandboxWarmPool
  -> WarmPool controller  # Step 000: current focus
  -> Sandbox CR -> core Sandbox controller -> Pod

rollout -> SandboxClaim -> available Sandbox -> task / tool calls -> result -> release
              |
              +-> claimed Sandbox leaves pool -> WarmPool reconciles again
```

这条主线跟随一批训练任务所需环境的供给与使用过程。上半段准备环境，下半段使用这些环境；领取后的补池流程单独列出。

#### 3.1.1 上半段负责准备环境

1. 提出环境需求。训练侧确定需要哪类环境、备用多少。
2. 准备环境模板。编排层通过 SandboxTemplate 描述所需环境；图中的 SandboxFleet / LookaheadWarmer 承接训练侧需求。
3. 设置备用目标。编排层在 SandboxWarmPool 中指定备用数量，并关联对应模板。
4. 补充 Sandbox 对象。WarmPool controller 根据目标与现有数量，在允许创建时补充缺少的 Sandbox CR。
5. 协调 Pod。核心 Sandbox controller 为 Sandbox 管理对应的 Pod 等子资源。
6. 调度 Pod。Kubernetes 调度器为 Pod 选择运行节点。
7. 启动环境。节点上的 kubelet 和容器运行时负责启动容器。

#### 3.1.2 下半段使用上半段准备的环境

1. 领取环境。rollout 通过 SandboxClaim 取得一个准备好的 Sandbox。
2. 完成题目初始化。任务执行逻辑把本题需要的数据、文件或初始状态准备到领取的环境中。
3. 进行工具交互。Agent 在任务过程中使用环境提供的命令、文件等接口。
4. 取回所需结果。任务执行逻辑收集后续评分或处理需要的输出、文件等产物。
5. 释放环境。使用结束后，调用方释放本次申请的环境资源。

#### 3.1.3 领取后的补池流程

这条分支从 3.1.2 的第 1 步接出，可以与第 2–5 步并行推进。

1. 移出备用池。成功领取的 Sandbox 转归 Claim 管理，不再作为池内备用成员。
2. 观察备用缺口。WarmPool controller 在后续协调中比较当前成员数量与备用目标。
3. 补充备用环境。满足创建条件时，WarmPool controller 按缺口发起补充。

因此，备用目标 3 个指向池内尚未领取的环境数量；已领取、正在执行任务的环境另计。补池无需等到这些任务完成并释放资源后才开始。

#### 3.1.4 Step 000 当前位于哪里

本步位于 3.1.1 的第 4 步：WarmPool controller 对池内 Sandbox 做数量协调。先跟随“目标 3 个、当前 1 个”的正常补池场景。

1. 看清输入。已有的环境模板和备用目标怎样进入本轮协调。
2. 看清观察。控制器怎样统计现有成员和 Ready 数量。
3. 看清补充。控制器怎样根据数量差额组织 Sandbox CR 的创建。
4. 看清状态交付。本轮观察到的数量怎样写回 WarmPool。

上面四项是本步的阅读问题；实际代码中，观察状态先在内存中计算，外层在数量协调后写回。Pod 管理以及下半段的环境使用流程继续保留为后续交接位置。

### 3.2 一轮协调的外层骨架

下面是 [Reconcile:435](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L435) 的**正常路径教学裁剪**。参数用 `...` 省略；删除/不存在检查、日志与错误合并暂时折叠，不是可直接编译的完整代码。

```go
// [1] Reconcile
warmPool := &extensionsv1beta1.SandboxWarmPool{}
r.Get(...)
oldStatus := warmPool.Status.DeepCopy()

// [2] Reconcile members and update the in-memory status.
requeueAfter, err := r.reconcilePool(...)

// [3] Persist observed status when it changed.
r.updateStatus(...)

return ctrl.Result{RequeueAfter: requeueAfter}, nil
```

先认出“**读取对象 → 协调成员 → 回写状态 → 返回**”。即使补池出现部分错误，原实现仍会尝试更新状态；上面只展示各调用都成功的路径。返回也不表示新建 Pod 已经 Ready。

### 3.3 从 [2] 下钻时的职责导航

下图保留 `reconcilePool` 内的主要交接和数量分支；它是阅读地图，具体语句、输入输出例子与机制解释待进入相应函数时再记录。

```text
[2] reconcilePool(...)
  |
  +-- r.List(...)
  +-- r.fetchTemplateAndHash(...)
  +-- r.filterActiveSandboxes(...)
  +-- readiness / health filtering
  |
  +-- desiredReplicas / currentReplicas / totalReplicas / readyReplicas
  +-- warmPool.Status.Replicas / ReadyReplicas / ObservedGeneration
  |
  +-- deficit + creation gates allow
  |     +-- [2a] r.buildSandboxCR(...)
  |     +-- slowStartBatch(..., callback)
  |           +-- [2b] r.createPoolSandbox(...)
  |
  +-- surplus + deletion gate allows
  |     +-- slowStartBatch(..., callback)
  |           +-- r.Delete(...)
  |
  +-- progress signals / next requeue delay
  +-- return requeueAfter, allErrors
          |
          v
      Reconcile -> [3] updateStatus(...) -> return
```

`r.List` 找池成员，模板提供环境配置，过滤后再统计数量。状态数量来自本轮观察，并在创建动作之前写入内存；`updateStatus` 随后把这些观察结果写回 API。因此不能把“这轮成功提交了 2 次创建”直接当成“这轮已经观察到 3 个 Ready”。新增成员及其就绪状态要通过后续观察反映出来。

创建预算还会计入正在删除但尚未消失的成员，并受批量上限、延迟、速率和缓存观察约束。第一遍只走第 1 节选定的补池场景；缩池分支保留位置，内部算法暂不展开。`slowStartBatch` 只需先知道它会调用创建回调，暂不追其并发实现。

<a id="reading-navigation"></a>

### 3.4 一次打开一个函数

编号与上面的骨架一致。**现在先打开 [1]，看清外层交接后再进入 [2]**；[2a]、[2b] 是回答“创建什么、何时提交”时的局部回查。源码定位不表示这些函数已读或已建卡。

| 编号与源码入口 | 本次要看清什么 | 看完回到哪里 |
| --- | --- | --- |
| **[1] [SandboxWarmPoolReconciler.Reconcile:435](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L435)** | 输入怎样定位一个 WarmPool；如何组织协调、状态回写与返回 | 到第 461 行的 [2] |
| **[2] [SandboxWarmPoolReconciler.reconcilePool:491](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L491)** | 怎样把已有成员、备用目标、创建动作和观察数量连起来 | 需看创建时进入 [2a]/[2b]；整体返回后到 `Reconcile:466` 的 [3] |
| [2a] [SandboxWarmPoolReconciler.buildSandboxCR:1135](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L1135) | Template 怎样成为待创建的 Sandbox CR，归属如何设置；先不追默认策略内部 | 回到 `reconcilePool:693`，继续缓存观察门槛及批量创建 |
| [2b] [SandboxWarmPoolReconciler.createPoolSandbox:1201](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L1201) | 构造对象与向 Kubernetes 提交创建分别发生在哪一步 | 返回 `reconcilePool:714` 的批量回调，批量结束后继续本轮收尾 |
| **[3] [SandboxWarmPoolReconciler.updateStatus:1214](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L1214)** | 观察数量怎样通过状态 Patch 写回 WarmPool | 返回 `Reconcile:466`，再向 controller-runtime 返回结果 |

后续实际打开哪个函数，才在本步 `02-short-term-memory/functions/extensions/controllers/sandboxwarmpool_controller.go/` 下建立相应的 `SandboxWarmPoolReconciler.<方法名>.md`。当前[函数索引](../../02-short-term-memory/overview.md)为空；`03` 暂无前序继承。

**本步停止位置**：能沿骨架说明谁读取目标和成员、谁创建 Sandbox CR、谁回写观察状态，并区分“创建请求成功”与“环境 Ready”。核心 Sandbox controller 如何管理 Pod、Claim 如何领取、训练侧如何计算下一批需求，继续作为后续交接点，不在此步一起展开。
