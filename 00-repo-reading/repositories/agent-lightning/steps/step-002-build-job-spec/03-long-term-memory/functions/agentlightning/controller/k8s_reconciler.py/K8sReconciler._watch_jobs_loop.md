# K8sReconciler._watch_jobs_loop

> **调用链面包屑**：[Step 001 范围](../../../../../../step-001-watch-job-events/01-scope.md#read-4) · [累计函数索引](../../../../overview.md) → [run 的并发启动](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L134) → **_watch_jobs_loop** → [_handle_job_event](K8sReconciler._handle_job_event.md)

- 源码：[k8s_reconciler.py:292](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L292)；骨架编号 [4]。
- 首次实际阅读：Step 000，2026-11-03；用户明确选择本函数后建卡。
- 最近认识更新：Step 001，2026-11-03。用户已联系 namespace/标签筛选与此前列表查询，明确不理解 watcher、事件与对象以及更新目标；助手校准尚待反馈。随后用户选择独立进入处理函数。

- 继承来源：[Step 000 的完整原记录](../../../../../../step-000-k8s-controller-entry/02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._watch_jobs_loop.md)。本次完整继承到 Step 001；首次接触、最近认识更新、原话与未知保持原值。

- 本步调取：[Step 001 入步时的累计快照](../../../../../../step-001-watch-job-events/03-long-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._watch_jobs_loop.md)。继续同一事件接收场景；本次调取不增加个人理解或改写首次接触。

- 本次继承（Step 002）：[Step 001 的完整来源记录](../../../../../../step-001-watch-job-events/02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._watch_jobs_loop.md)。此前继承和调取说明保留历史语境；原话、未知、首次接触与最近认识更新保持原值。

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

`kr8s` 是 Python 访问 Kubernetes 的客户端库，`kr8s.asyncio` 是它的异步接口。观察的是指定 namespace 内、满足 `app.kubernetes.io/managed-by=agentlightning` 标签的 Job，并非整个集群的所有 Job。

之前用列表推导式把 `Job.async_list(...)` 提供的 Job 收集成列表。这里的 `watcher` 是可持续逐条读取 Job 通知的异步迭代器；没有下一条通知时，`async for` 会等待，流结束或异常则按外围循环处理。`kr8s.asyncio.watch(...)` 本身不写 `await`，接收由后面的 `async for` 推进。

<a id="one-job-event"></a>

### 这次拿到什么，再交出什么

教学例子：任务 r1 的 Job 已成功，Gateway 仍登记为 RUNNING。构造一条携带该 Job 数据的 MODIFIED 事件，并假定后面的更新请求成功。它不是一次真实集群运行，也不表示每条修改事件都是任务完成。

`async for` 取到的这一项被拆给两个名字：

```python
# 本次迭代给出的一对值，形状是：("MODIFIED", obj)
event_type = "MODIFIED"  # 事件类型：这个 Job 对象发生了修改
# obj 是被修改的 Job 的 kr8s 对象；obj.raw 只是取出它的数据，不执行或修改 Job
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

**本次交出的数据**：上面这份 Job 数据，作为下游的 `job` 参数；没有把 `event_type` 一起传进去。处理函数返回后，本协程继续取下一条事件。

<a id="handler-update-target"></a>

### 更新目标与子函数入口

下游从 Job 标签取任务编号 r1，从 Complete/True 得到成功结果，再通过 `_patch_status` 请求更新 Gateway 中对应 rollout 的状态。这里的 `.raw` 是数据属性；这条路径没有修改容器状态或磁盘目录。如果将“目录”理解为任务登记表，接近这里的用途，但准确对象是一条任务记录。

用户现已选择独立进入 [_handle_job_event](K8sReconciler._handle_job_event.md)，具体标签、条件和回写放在该子卡；本卡保留接收与交接。更新接口的旧卡也已[调入本步](K8sReconciler._patch_status.md)。

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
| [_handle_job_event（函数卡）](K8sReconciler._handle_job_event.md) | 处理 `obj.raw` 后回到本函数，继续接收事件 |
| 本函数整体返回 [run:134](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L134) | 它是 `gather` 中的一条运行路径；另一条是周期协调，并非从本函数顺序进入 `_reconcile_once` |

<details>
<summary>重试与停止：保留边界，暂不展开完整生命周期</summary>

捕获到 `Exception` 时，记录日志、等待 5 秒，再回到外层循环。这 5 秒是异常后的等待，不是每次接收事件的固定间隔。事件流正常结束时也会回到外层重新检查停止信号。

停止信号只在代码所示的位置检查；仅设置这个信号并不会由本函数立即中断一次正在等待的事件接收。库内部的连接恢复、资源版本与完整取消流程留待对应问题再看。

</details>

## 我的直接表述（原话）

首次选入时的原话（Step 000）：

> 好的 那么看一下这里的这个k8s reconciler的这个watch jobs loop的部分吧

当时确认的是阅读入口与范围，尚无内部复述。此前关于周期协调的认识保存在 [_reconcile_once 卡片](K8sReconciler._reconcile_once.md#reconcile-purpose-understood)。

<a id="watcher-and-update-question"></a>

Step 001 中的理解与疑问：

> 好的 那么我们来继续看一下这里的这个部分的内容吧
> 我的理解是
> kr8s的asyncio是k8s的包
> 功能哈斯是一样的观察这里的namespace
> 然后通过labelselector来筛选
> 和reconcile once的reconcile的 async list一样的
> 只不过那个是遍历当前的job
> 拿到一个list
>
> 这次是观察所有的job资源?
> 但是这个watcher是干嘛的我没有理解
> 同样的返回的event type还有这里的obj 我也没有理解
> 包括handlle job 的部分
>
> 但是在short term memory中这里有这个obj.raw 也就是处理job的数据
> 我在想应该是在更新这里容器本身的状态?
> 但是这里的self._handle_job_event(obj.raw)
> 内容应该是更新本地关于job状态的目录?

筛选条件与此前列表查询的联系已有个人表述；客户端角色、逐条通知、对象数据与 Gateway 更新目标是助手补充，尚待确认。

## 尚不清楚

- 用户已联系相同筛选条件；watcher 如何持续给出通知，仍待反馈。
- `event_type`、Job 对象与 `.raw` 的交接，以及更新 Gateway 而非容器或目录的区别，刚由助手补充。
- `_handle_job_event` 已独立建卡，其标签、条件与回写分支尚无个人理解确认。
- 停止、异常重试与 watch 库内部机制尚未深入。

<details>
<summary>来源与验证边界</summary>

- [Step 001 的 watcher 与更新目标澄清](../../../../../../step-001-watch-job-events/04-flow.md#watcher-event-and-target)。
- Agent Lightning 固定提交 `0029dbb35c467799d35fee81d15d80264b0d1bd3`；本函数 292–309 行，调用方 `run` 在 134–137 行。
- 项目锁定 kr8s `0.20.15`。[asyncio._helpers.watch:84–102](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/asyncio/_helpers.py#L84) 逐项产出事件类型与对象；[Api.async_watch:627–667](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_api.py#L627) 将事件中的 object 包装后产出 `(event["type"], obj)`。这里只核对接口，不建立库内部函数卡。
- `.raw` 的数据形态沿用此前 [Job 查询卡](../../../kr8s/_objects.py/APIObject.async_list.md)中的版本核对。
- [本轮阅读记录](../../../../../../step-000-k8s-controller-entry/04-flow.md#watch-jobs-loop-reading)。事件数据为教学节选，没有连接真实 Kubernetes 或修改 Gateway。

</details>
