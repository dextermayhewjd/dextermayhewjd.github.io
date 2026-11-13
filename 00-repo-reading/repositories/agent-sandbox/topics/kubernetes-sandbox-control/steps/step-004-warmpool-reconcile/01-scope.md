# 01 · Kubernetes Step 004：WarmPool 怎样维持备用环境

[主题入口](../../README.md) · [项目唯一进度](../../../../README.md#current-reading) · [前一步 scope](../step-003-status-writeback/01-scope.md) · [后一步 scope](../step-005-claim-ownership/01-scope.md)

本页按已确认规划预先准备，只定义阅读范围。尚未展开本步阅读，不代表相关函数已经掌握或完成集群验证。

## 1. 阅读目标

**理解 WarmPool 怎样把期望备用数量与观察到的 Sandbox 数量对齐。**

1. 区分活跃成员、Ready 成员、正在删除的成员与本轮尚未被缓存观察到的写入。
2. 沿“期望 3、观察到 1”的例子看补池，再用缩容分支核对相同的数量与写入保护。
3. 解释一次协调结束后为何还需要 watch 或重新排队，而不是把创建请求成功当作环境全部 Ready。

## 2. 指挥官、入口条件与停止位置

指挥官是 [SandboxWarmPoolReconciler.Reconcile](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L435)，主要展开 [reconcilePool](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L491)。

入口已有 SandboxTemplate 与引用它的 SandboxWarmPool，池未删除、模板可读。先假定容量足够、正常成员没有过期；单个 Sandbox 的 Pod 创建、Ready 计算和状态写回复用前序步骤。

**停止位置**：reconcilePool 交回 requeueAfter/error，外层尝试写回池状态并返回；能说明“发出资源写入”“缓存观察到写入”“Sandbox Ready”是不同节点。expectations 的作用需要看清，完整队列、限速、哈希和指标实现先不展开。

## 3. 整体位置与本步阅读

### 3.1 本步在 Kubernetes 沙箱主线中的位置

以下是跨控制器关系示意，使用 Python 高亮显示注释，不是可执行代码。各 controller 经 API/watch 协作，不是普通嵌套调用。

```python
SandboxTemplate + SandboxWarmPool.spec
  -> SandboxWarmPoolReconciler  # Step 004：维持池中备用 Sandbox 的数量。
       -> Kubernetes API: Sandbox

Sandbox.spec
  -- watch --> SandboxReconciler
       -> PVC / Pod / Service  # 前序范围：创建与协调单个环境。
       -> Sandbox.status      # 前序范围：Ready 观察与状态写回。
       -> Kubernetes API: Pod / Service / PVC
            -> scheduler / kubelet / runtime  # 调度和运行 Pod，不是直接调度 Sandbox CR。  # 实际调度和运行容器。

caller creates SandboxClaim
  -- watch --> SandboxClaimReconciler  # 后续：领取并改变资源归属。
       -> Claim.status / assigned Sandbox
       -- API event --> WarmPool observes fewer members and replenishes

SDK uses assigned environment  # 后续：命令、文件、连接与权限。
  -> claim deletion / expiry   # 后续：按归属和生命周期回收资源。
```

### 3.2 本步调用骨架与阅读顺序

外层正常路径的教学裁剪，省略参数、日志和具体错误包装：

```go
// SandboxWarmPoolReconciler.Reconcile
r.Get(...)                              // 读取本次池对象。
oldStatus := warmPool.Status.DeepCopy()
requeueAfter, err := r.reconcilePool(...) // 观察成员并按条件增减。
statusErr := r.updateStatus(...)         // 部分创建失败时也尝试写回已观察状态。
// 原函数合并错误；无错误时返回 RequeueAfter。
return ctrl.Result{RequeueAfter: requeueAfter}, nil
```

reconcilePool 内部按下面的真实动作定位；条件说明为教学摘要，不是完整可编译函数：

```go
r.List(...)                                      // 找池标签对应的 Sandbox。
template, currentPodTemplateHash, currentSandboxBlueprintHash, tmplErr := r.fetchTemplateAndHash(...)
activeSandboxes, terminatingReplicas, allErrors := r.filterActiveSandboxes(...)
// 原函数先处理成员健康与宽限期，再统计 active、terminating 和 Ready。
currentReplicas := int32(len(activeSandboxes))
totalReplicas := currentReplicas + terminatingReplicas
// 缺少成员：先考虑补池等待/速率，再用 expectations 防止基于过期缓存重复创建。
// 多出成员：等待既有写入被观察，再选择超额成员删除。
return requeueAfter, allErrors
```

编号只表示阅读顺序，不表示调用深度。每次从下层返回后继续表格的下一项。

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 1. Reconcile 外层 | [435 行](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L435) | 确定读取对象、旧状态快照与主要委派；进入 reconcilePool |
| 2. 观察与筛选成员 | [491 行起](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L491) | 看 List、模板和归属筛选各交出什么；哈希算法按接口理解 |
| 3. 数量与 Ready 分开统计 | [596 行起](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L596) | 分清 current、total、ready 的比较用途；不把“未 Ready”全当成需要补一份 |
| 4. 补足缺额 | [创建分支](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L651) | 跟到 TryExpectCreations、slowStartBatch 与 createPoolSandbox 的交接；关注未成功发出的写入怎样降低预期计数 |
| 5. 删除超额成员 | [缩容分支](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L731) | 看 SatisfiedExpectations、删除选择和 DeletionObserved；回到 requeueAfter/error |
| 6. 返回外层 | Reconcile 的 updateStatus 与返回 | 确定池状态是观察值；部分失败、容量等待与缓存滞后都保留再次协调的入口 |

必要边界只保留三类：正在删除仍占容量、写入未被缓存观察、Pod 因容量不足不能调度。补池延迟、令牌桶和宽限期先看如何影响本轮是否创建与何时重试，不通读全部调优实现。

<details>
<summary>源码与准备状态</summary>

- 固定版本：Agent Sandbox 37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1；本地源码已静态核对。
- 本步只准备 scope，不生成函数卡、长期记忆或学习完成记录。
- 后续的领取与归属交给 Step 005；不在本步重新分析 Python Fleet 的批次调度。

</details>
