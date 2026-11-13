# 01 · Job 事件接收的阅读范围

[本步入口](README.md) · [当前 watch 函数卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._watch_jobs_loop.md) · [前一步完整骨架](../step-000-k8s-controller-entry/01-scope.md#core-skeleton)

## 1. 阅读目标

- **整体目标**：理解 Agent 任务在 Kubernetes 中怎样被创建、观察并向 Gateway 反馈状态。
- **本步问题**：持续的 Job 事件怎样进入控制器，处理函数怎样据此向 Gateway 回写任务结果？
- **停止位置**：从 `_watch_jobs_loop` 进入 `_handle_job_event`，看清任务标识、条件与回写，再返回 watch；`_patch_status` 复用已有接口，完整并发恢复机制暂不展开。

用户先明确选择 watch 并要求建立步骤，随后明确选择独立阅读 `_handle_job_event`；本步据此从“观察范围 → 收到的数据 → 交给谁”继续到标签、条件和状态回写。

## 2. 指挥官函数与已有背景

入口为 [`K8sReconciler._watch_jobs_loop:292`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L292)。它组织创建观察器、接收事件、选择事件并调用处理函数。

来路是 `run()` 的 `asyncio.gather`。另一条周期协调路径属于前一步背景；namespace、管理标签和 Kubernetes 客户端已经接触过，必要时从[累计索引](03-long-term-memory/overview.md)回查。

用户本轮提出两条路径都会回写的职责疑问，先看[同一任务上的职责对照](README.md#polling-and-job-events)。`_reconcile_once` 已按需调入本步短期记忆；本轮重点是它与事件处理的关系，不扩大到新的控制器模块。

## 3. 核心骨架与阅读导航

### 3.1 在整体中的位置

下面是职责定位；Step 000 中的全局编号 [1]–[5] 保持不变，当前进入 [4]。

```text
K8sReconciler.run()
|-- [A] _periodic_reconcile_loop()
|   `-- [1] _reconcile_once()
|       |-- query rollouts + list Jobs
|       |-- [2] _create_job() -> [3] build_job_spec()
|       `-- [5] _patch_status()
`-- [B] [4] _watch_jobs_loop()   <-- Step 001
    `-- _handle_job_event()     <-- current reading
        `-- [5] _patch_status()
```

A/B 并行运行。新建学习步骤不表示程序从 A 顺序切换到 B；[5] 仍是一份可以复用的状态更新记录。

### 3.2 当前函数骨架

教学裁剪：省略日志、异常后的等待与具体参数；保留循环、停止检查、事件选择和等待交接。原代码和就地注释在函数卡中。

```python
while not self._stop.is_set():
    watcher = kr8s.asyncio.watch(...)
    async for event_type, obj in watcher:
        if self._stop.is_set():
            return
        if event_type in ("MODIFIED", "ADDED"):
            await self._handle_job_event(...)
```

<a id="read-4"></a>
<a id="read-handle-job-event"></a>

### 3.3 进入与返回

| 入口 | 本轮看什么 | 读完回到哪里 |
| --- | --- | --- |
| [4 · `_watch_jobs_loop` 函数卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._watch_jobs_loop.md) | 观察范围、单次事件中的两个值、交出的 Job 数据 | 回到 `run()` 的 B 路径；函数内部则持续接收后续事件 |
| [`_handle_job_event` 函数卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._handle_job_event.md) | 从 `obj.raw` 的标签找到任务、从条件读取结果，交给状态更新接口 | 处理完成后返回 watch 的 `async for` |
| [`_patch_status` 本步调取卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._patch_status.md) | 复用任务 ID、状态字段到 Gateway PATCH 的接口 | 返回布尔结果；本次处理函数不保存它，随后返回 watch |

旧卡中的原始来源仍指向 Step 000，首次接触与未知不因调取改变。处理函数按本轮明确选择建卡；状态更新卡仅补本步调用场景，入步时的 `03` 快照保持不变。
