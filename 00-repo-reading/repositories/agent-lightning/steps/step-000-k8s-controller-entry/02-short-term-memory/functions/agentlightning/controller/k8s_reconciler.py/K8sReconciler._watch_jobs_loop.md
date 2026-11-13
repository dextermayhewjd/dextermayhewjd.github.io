# K8sReconciler._watch_jobs_loop

> **调用链面包屑**：[Step 000 范围](../../../../../01-scope.md#read-4) · [短期函数索引](../../../../overview.md) → [run 的并发启动](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L134) → **_watch_jobs_loop** → [_handle_job_event（源码）](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L311)

- 源码：[k8s_reconciler.py:292](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L292)；骨架编号 [4]。
- 首次实际阅读：Step 000，2026-11-03；用户明确选择本函数后建卡。
- 最近认识更新：当前已确认阅读范围，尚无用户对本函数行为的个人复述。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`run()` 同时启动周期协调与事件观察。本函数负责后者，与周期协调并行运行。
2. **具体内容**：通过 Kubernetes 客户端观察指定范围的 Job，逐条接收事件；把 ADDED/MODIFIED 中的 Job 数据交给 `_handle_job_event`，等待处理返回后继续接收。保留停止检查与异常重试。
3. **建议构建的心智模型**：

   > **持续接收 Kubernetes 的 Job 事件 → 选出新增/修改事件 → 把其中的 Job 数据交给处理函数。** 下游负责判断任务结果，当前函数负责接收与交接。

4. **调用代码**（`run:134–137`）：

   ```python
   await asyncio.gather(
       self._periodic_reconcile_loop(),
       self._watch_jobs_loop(),
   )
   ```

## 本场景的输入与输出

本函数只有 `self` 参数，使用已有的 Kubernetes 客户端、namespace、管理标签与停止信号。先沿用之前的理解：**这里接触的是 Kubernetes 返回的 Job 信息。** Gateway 的任务记录在后续处理需要回写时才用到。

<a id="watch-skeleton"></a>

### 完整代码：先圈出接收与交接

以下为 294–309 行，注释为教学添加，原语句与顺序保持不变。

```python
while not self._stop.is_set():
    try:
        watcher = kr8s.asyncio.watch(
            "jobs",                              # 观察 Job 资源
            namespace=self._namespace,           # 与之前查询 Job 使用同一个 namespace
            label_selector=MANAGED_BY_SELECTOR,  # 仍只观察带本项目管理标签的 Job
            api=await self._get_k8s_api(),        # 已读过的 Kubernetes 客户端
        )
        async for event_type, obj in watcher:    # 每次得到事件类型，以及事件携带的 Job 对象
            if self._stop.is_set():
                return
            if event_type in ("MODIFIED", "ADDED"):
                await self._handle_job_event(obj.raw)  # 交出 Job 数据，等处理完再取下一条
    except Exception:
        log.exception("Watch error — restarting watch")
        await asyncio.sleep(5)
```

`MANAGED_BY_SELECTOR` 仍是 `app.kubernetes.io/managed-by=agentlightning`。这里与先前的 `Job.async_list(...)` 使用同一组范围条件；`watcher` 则是逐条提供事件的异步迭代器。`kr8s.asyncio.watch(...)` 本身不写 `await`，后面的 `async for` 推进接收。

<a id="one-job-event"></a>

### 这次拿到什么，再交出什么

教学例子：任务 r1 的 Job 已成功，构造一条携带该 Job 数据的 MODIFIED 事件来阅读本次交接。它不是一次真实集群运行，也不表示每条修改事件都是任务完成。

`async for` 取到的这一项被拆给两个名字：

```python
event_type = "MODIFIED"  # 事件类型：这个 Job 对象发生了修改
# obj 是 kr8s 包装的 Job 对象；通过 obj.raw 取得它携带的资源数据
```

下面是 `obj.raw` 的相关字段，使用 JSONC 放置旁注；注释不属于实际接口数据：

```jsonc
{
  "metadata": {
    "name": "agl-rollout-r1",                  // 这条事件对应的 Job
    "labels": {
      "app.kubernetes.io/managed-by": "agentlightning",
      "agentlightning/rollout-id": "r1",       // 下游可以据此找到 Gateway 中的任务
      "agentlightning/attempt-id": "0"
    }
  },
  "status": {
    "conditions": [
      {"type": "Complete", "status": "True"}  // 成功完成信息在 Job 数据里面
    ],
    "succeeded": 1
  }
}
```

这里拿到的是事件携带的 Job 数据，不只是变更字段的差异。`MODIFIED` 表示对象被修改；是否成功或失败，要继续查看 Job 的内容。

本例命中 `event_type in ("MODIFIED", "ADDED")`，于是执行：

```python
await self._handle_job_event(obj.raw)
```

**本次交出的数据**：上面这份 Job 数据，作为下游的 `job` 参数；没有把 `event_type` 一起传进去。处理函数返回后，本协程继续取下一条事件。本轮读到这次交接为止，下一张函数卡再展开标签与条件怎样用于回写。

### 接收循环里的三个判断

- **范围筛选**：namespace 与 label selector 决定观察哪些 Job。
- **事件筛选**：本函数只处理 ADDED、MODIFIED；例如 DELETED 不会进入 `_handle_job_event`。这两个值都不是 rollout 的成功/失败状态。
- **停止检查**：在外层开始观察前、每次取得事件后检查停止信号。处理单条事件时使用 `await`，没有为每条事件另开并发任务。

本函数不会因为处理完一条事件就返回事件列表。按停止条件正常退出时返回 `None`；持续接收时则一直运行。

<a id="watch-handoffs"></a>

### 下钻与返回

| 从哪里进入 | 读完回到哪里，接着做什么 |
| --- | --- |
| [_get_k8s_api（已有卡）](K8sReconciler._get_k8s_api.md) | 取得 Kubernetes 客户端，交给 `watch(..., api=...)` |
| [_handle_job_event:311（源码，尚未独立展开）](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L311) | 处理 `obj.raw` 后回到本函数，继续接收事件 |
| 本函数整体返回 [run:134](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L134) | 它是 `gather` 中的一条运行路径；另一条是周期协调，并非从本函数顺序进入 `_reconcile_once` |

<details>
<summary>重试与停止：保留边界，暂不展开完整生命周期</summary>

捕获到 `Exception` 时，记录日志、等待 5 秒，再回到外层循环。这 5 秒是异常后的等待，不是每次接收事件的固定间隔。事件流正常结束时也会回到外层重新检查停止信号。

停止信号只在代码所示的位置检查；仅设置这个信号并不会由本函数立即中断一次正在等待的事件接收。库内部的连接恢复、资源版本与完整取消流程留待对应问题再看。

</details>

## 我的直接表述（原话）

用户本轮选择：

> 好的 那么看一下这里的这个k8s reconciler的这个watch jobs loop的部分吧

当前确认的是阅读入口与范围，尚无对内部行为的个人复述。此前关于周期协调的认识保存在 [_reconcile_once 卡片](K8sReconciler._reconcile_once.md#reconcile-purpose-understood)。

## 尚不清楚

- 周期查询与持续事件接收的关系，当前由助手定位，尚待用户反馈。
- `event_type`、Job 对象与 `.raw` 的交接已经给出例子，尚无个人复述。
- `_handle_job_event` 怎样按标签找到任务、判断结果并回写，留作后续单独下钻。
- 停止、异常重试与 watch 库内部机制尚未深入。

<details>
<summary>来源与验证边界</summary>

- Agent Lightning 固定提交 `0029dbb35c467799d35fee81d15d80264b0d1bd3`；本函数 292–309 行，调用方 `run` 在 134–137 行。
- 项目锁定 kr8s `0.20.15`。[asyncio._helpers.watch:84–102](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/asyncio/_helpers.py#L84) 逐项产出事件类型与对象；[Api.async_watch:627–667](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_api.py#L627) 将事件中的 object 包装后产出 `(event["type"], obj)`。这里只核对接口，不建立库内部函数卡。
- `.raw` 的数据形态沿用此前 [Job 查询卡](../../../kr8s/_objects.py/APIObject.async_list.md)中的版本核对。
- [本轮阅读记录](../../../../../../step-000-k8s-controller-entry/04-flow.md#watch-jobs-loop-reading)。事件数据为教学节选，没有连接真实 Kubernetes 或修改 Gateway。

</details>
