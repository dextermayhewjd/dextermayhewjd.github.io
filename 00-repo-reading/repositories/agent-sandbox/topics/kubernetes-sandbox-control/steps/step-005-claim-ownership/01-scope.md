# 01 · Kubernetes Step 005：Claim 怎样领取环境并确定归属

[主题入口](../../README.md) · [项目唯一进度](../../../../README.md#current-reading) · [前一步 scope](../step-004-warmpool-reconcile/01-scope.md) · [后一步 scope](../step-006-access-and-isolation/01-scope.md)

本页按规划预先准备；只定义本步问题和入口，不表示领取、并发或清理机制已经读懂或运行验证。

## 1. 阅读目标

**跟随一份 SandboxClaim，解释它怎样取得正确池中的一个 Sandbox、保存绑定关系，并在使用结束后按归属回收。**

1. 区分复用已绑定对象、领取池中候选、等待候选网络就绪和冷创建。
2. 看清 Claim 上的分配记录与 Sandbox 的 OwnerReference 分别怎样更新；为什么两个调用方不能简单领取同一个缓存候选。
3. 将 Claim 状态交付和删除/过期后的清理接起来，不假定使用过的环境自动返回干净备用池。

## 2. 指挥官、入口条件与停止位置

上层指挥官是 [SandboxClaimReconciler.Reconcile](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L293)，主要阅读入口为 [reconcileActive](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L580)。

先选同 namespace、明确 warmPoolRef、未删除且未过期的一份新 Claim。以兼容池模板、没有 env/volumeClaimTemplates 覆盖的情况观察热领取，再对比冷创建条件。Step 004 的备用数量和前序 Sandbox Ready 作为背景。

**停止位置**：能从 Claim 请求追到 Sandbox 名称与 Ready 的状态交付，并说明一条删除/过期的资源回收路径。只挑一次分配竞争看保护条件；不要求遍历全部缓存恢复、指标和旧标签迁移分支。

## 3. 整体位置与本步阅读

### 3.1 本步在 Kubernetes 沙箱主线中的位置

下面表示 API/watch 与资源归属关系，不是同步调用栈：

```python
SandboxTemplate + SandboxWarmPool.spec
  -> SandboxWarmPoolReconciler  # 前一步：创建并维持备用 Sandbox。
       -> Kubernetes API: Sandbox

Sandbox.spec
  -- watch --> SandboxReconciler  # 前序范围：协调 Pod / Service / PVC。
       -> Sandbox.status         # Ready 等观察结果。
       -> Kubernetes API: Pod / Service / PVC
            -> scheduler / kubelet / runtime  # 调度和运行 Pod，不是直接调度 Sandbox CR。

caller creates SandboxClaim
  -- watch --> SandboxClaimReconciler  # Step 005：匹配、领取或冷创建。
       -> Claim assignment + Sandbox OwnerReference
       -> Claim.status          # 调用方可读取 Sandbox 名称与 Ready。
       -- member leaves pool --> WarmPool replenishes

SDK uses assigned environment   # 后续：取得连接并执行命令/文件操作。
  -> deletion / expiry          # 本步只接清归属与一种回收路径。
```

### 3.2 本步调用骨架与阅读顺序

以下为正常 active 分支的教学裁剪，省略参数和错误包装，保留真实方法名与返回形状：

```go
// Reconcile 先读取 Claim、保存旧状态，并判断删除/过期。
sandbox, reconcileErr = r.reconcileActive(...)
// 某些未就绪候选以暂态返回，外层延后重试，不进入下面的通常状态计算。
r.computeAndSetStatus(...)
statusAuthoritative, updateErr := r.updateStatus(...)
// 外层结合生命周期与错误决定返回或重新排队。
```

```go
// reconcileActive 的主要分派。
sandbox, err := r.getOrCreateSandbox(...) // 先找既有绑定或尝试热领取。
if err != nil { return nil, err }
if sandbox != nil {
    // 原函数按模板协调附加 metadata 等信息。
    return sandbox, nil
}
// 原函数按条件重新读取 Claim，防止旧缓存导致重复冷创建。
template, templateErr := r.getTemplate(...)
// 省略错误检查。
return r.createSandbox(...)
```

getOrCreateSandbox 的名称不能替代阅读其返回合同：该方法可返回既有/领取结果或 nil；真正按模板冷创建发生在调用方 reconcileActive。

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 1. Reconcile 的 active 入口 | [293 行起](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L293) | 定位未过期分支与后续状态写回，进入 reconcileActive |
| 2. reconcileActive | [580 行起](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L580) | 看 sandbox/error/nil 怎样决定返回、重试或冷创建；从 getOrCreateSandbox 下钻 |
| 3. 已有绑定与热领取条件 | [getOrCreateSandbox:2230](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L2230) | 看 status、annotation、同名对象的查找与归属检查，再到候选领取；env/PVC 覆盖可能直接要求冷创建 |
| 4. 领取一个候选 | [adoptSandboxFromCandidates:1377](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L1377) | 先记录 Claim 的分配，再调用 completeAdoption；只跟一个成功候选和一次冲突分支 |
| 5. 完成归属转移 | [completeAdoption:1478](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L1478) | 移除池标签、设置 Claim 归属、以乐观锁 Patch；冲突不能直接当成功或随意换第二个候选 |
| 6. 返回 active 分支 | reconcileActive 的冷创建分支与 [createSandbox:1936](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L1936) | 有结果时返回；真正无可用对象时按模板创建。网络未就绪候选的暂态等待与空池分开理解 |
| 7. 返回外层并交付状态 | [computeAndSetStatus:1102](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L1102) 与 updateStatus | 确定调用方从哪里取得 Sandbox 名称与 Ready；不把创建请求成功当 Ready |
| 8. 回查结束路径 | Reconcile 中的过期策略与 [reconcileExpired:702](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L702) | 选 Delete 或 Retain 的一条实际路径核对对象归属与删除；保留另一条策略的语义区别 |

本步可以形成“一份 Claim → 一个被领取/创建的 Sandbox → 可观察状态 → 回收责任”的模型。所有异常恢复暂不展开，但不能把冲突后直接重试旧写入、未就绪候选和无候选混成同一种情况。

<details>
<summary>源码与准备状态</summary>

- 固定版本：Agent Sandbox 37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1；方法与分派经本地静态核对。
- Delete/DeleteForeground 由删除 Claim 并利用资源归属回收；Retain 保留 Claim 而显式删除其 Sandbox。具体终态与错误按选定分支读取。
- 只准备 scope，未创建 Claim、修改池、运行并发领取，也未生成函数卡。

</details>
