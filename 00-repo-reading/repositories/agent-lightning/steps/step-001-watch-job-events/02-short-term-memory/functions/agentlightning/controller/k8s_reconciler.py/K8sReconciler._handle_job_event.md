# K8sReconciler._handle_job_event

> **调用链面包屑**：[Step 001 范围](../../../../../01-scope.md#read-handle-job-event) · [短期函数索引](../../../../overview.md) → [_watch_jobs_loop](K8sReconciler._watch_jobs_loop.md#handler-update-target) → **_handle_job_event** → [_patch_status](K8sReconciler._patch_status.md)

- 源码：[k8s_reconciler.py:311](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L311)。
- 首次接触：Step 000 先定位调用边界，Step 001 先解释更新目标；2026-11-03 用户明确选择独立阅读并建卡。
- 最近认识更新：2026-11-03，用户要求先定位两处读取和修改的具体对象与 key，再讨论职责；当前核对共同读取的 Job conditions 与写入的 Gateway status.state，尚待理解反馈。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：父函数接到 ADDED/MODIFIED 事件，把对应 Job 对象的 `.raw` 数据交进来；本函数处理这一份已收到的数据，不主动遍历 Gateway 的任务列表。
2. **具体内容**：从 Job 标签中找 rollout ID，读取已成立的成功/失败条件，调用状态更新接口；无可处理信息时返回。
3. **建议构建的心智模型**：

   > **用 Job 的标签找到 Gateway 中的任务，用 Job 的条件判断结果，再请求更新这条任务记录。** 当前函数读取 Job 数据，状态回写交给 `_patch_status`。

   当前先核对[读取与写入的具体 key](../../../../../README.md#read-write-keys)：本函数读取 `job["status"]["conditions"]`，经 `_patch_status` 请求写入 Gateway 任务记录的 `status.state`。两处叫 status，但分别属于 Job 条件与 rollout 记录。

4. **调用代码**（`_watch_jobs_loop:305–306`）：

   ```python
   if event_type in ("MODIFIED", "ADDED"):
       await self._handle_job_event(obj.raw)
   ```

## 本场景的输入与输出

### 从父函数带进来的 Job 数据

继续父卡的 r1 成功事件。上层已筛选 MODIFIED 事件；本函数只收到它携带的 Job 数据，没有收到 `event_type`。下面是 `job` 的字段节选，JSONC 注释是教学说明。

```jsonc
{
  "metadata": {
    "name": "agl-rollout-r1",
    "labels": {
      "agentlightning/rollout-id": "r1",  // 找到要更新的 Gateway 任务
      "agentlightning/attempt-id": "0"    // 这次执行的关联编号
    }
  },
  "status": {
    "conditions": [
      {
        "type": "Complete",             // Job 的成功完成条件
        "status": "True"                // 这个条件成立，值是字符串
      }
    ]
  }
}
```

这里的 `job` 就是父函数交来的 `obj.raw`，以字典式字段读取；本函数不再查询 Kubernetes。JSON 内的 `Complete` 是 Job 条件名称，上层的 `MODIFIED` 是事件类型，两者在不同位置回答不同问题。

**本例结果**：假设 Gateway 中 r1 仍为 RUNNING，且更新请求成功，本函数通过 `_patch_status` 把它登记为 SUCCEEDED，并记录 `last_attempt_id="0"`。本函数自身返回 `None`，父函数继续接收下一条事件。Job 数据本身没有被修改。

<a id="handler-source"></a>

### 完整代码：取任务编号、看条件、交给回写接口

以下是 313–346 行，保留全部处理分支，只添加就地注释。

```python
labels = job.get("metadata", {}).get("labels", {})  # ① 取这份 Job 的标签
rollout_id = labels.get("agentlightning/rollout-id")  # 标签告诉我们对应哪条 Gateway 任务
if not rollout_id:
    return
attempt_id = labels.get("agentlightning/attempt-id") or DEFAULT_ATTEMPT_ID

conditions = job.get("status", {}).get("conditions", [])  # ② 取 Job 的条件列表
if not conditions:
    return

for condition in conditions:
    cond_type = condition.get("type", "")
    cond_status = condition.get("status", "")
    if cond_status != "True":  # 只处理已经成立的条件
        continue

    if cond_type == "Complete":  # ③ 成功完成时，请求向 Gateway 回写 SUCCEEDED
        log.info("Job completed", rollout_id=rollout_id, last_attempt_id=attempt_id)
        await self._patch_status(rollout_id, state=RolloutState.SUCCEEDED, last_attempt_id=attempt_id)
        return
    elif cond_type == "Failed":  # 失败时，附上原因再回写 FAILED
        reason = condition.get("reason", "Unknown")
        message = condition.get("message", "")
        error_msg = f"Job failed: {reason}"
        if message:
            error_msg += f" — {message}"
        log.info("Job failed", rollout_id=rollout_id, last_attempt_id=attempt_id, reason=reason)
        await self._patch_status(
            rollout_id,
            state=RolloutState.FAILED,
            last_attempt_id=attempt_id,
            error_message=error_msg,
        )
        return
```

沿上面的 r1 数据，只跟这条成功路径：

1. `labels` 取出标签，得到 `rollout_id="r1"`、`attempt_id="0"`。没有 rollout ID 时直接返回，因为无法确定要更新哪条任务。
2. `conditions` 取到那一项 `Complete/True`；`cond_type` 与 `cond_status` 分别保存这两个字符串。没有条件时返回，不成立的条件用 `continue` 跳过。
3. 命中 Complete，把任务编号、SUCCEEDED 和执行编号交给 `_patch_status`，然后 `return` 回到 watch。Failed 分支则改为发送 FAILED，并带上失败原因。

<a id="call-patch-status"></a>

### 回写与返回的交接

| 进入哪里 | 本例交入什么 | 返回后在哪里继续 |
| --- | --- | --- |
| [_patch_status（本步复用的旧卡）](K8sReconciler._patch_status.md) | `"r1"`、`state=SUCCEEDED`、`last_attempt_id="0"` | 本函数不保存其布尔结果，调用结束后执行 `return` |
| [返回 _watch_jobs_loop](K8sReconciler._watch_jobs_loop.md#watch-skeleton) | 本函数返回 `None` | 父函数的 `await` 结束，`async for` 继续接收下一条事件 |

<details>
<summary>其他分支与当前实现边界</summary>

- 无 rollout ID、无条件、或没有成立的 Complete/Failed 条件时，不发送状态更新，返回 `None`。
- 一个条件的 `status` 不是 `"True"` 时，只跳过这条条件；其他类型的条件也不触发本函数的成功/失败回写。
- Failed 分支从 `reason`、`message` 组织 `error_msg`，缺少 reason 时用 `Unknown`。成功与失败都是发出一次回写后就返回，不继续遍历其余条件。
- 本函数只看 conditions，没有 `_reconcile_once` 中的 succeeded/failed 计数兜底。
- 本函数不读取 Gateway 当前状态，也不先补写 RUNNING。本例假定 Gateway 原来为 RUNNING，故允许写 SUCCEEDED；实际是否接受仍由服务端校验。`_patch_status` 返回 False 时，本函数也不检查或在这里重试，不能仅凭本函数返回就断言更新成功。
- 这些边界由源码核对，尚未作为真实集群时序验证；当前先读清正常成功路径。

</details>

## 我的直接表述（原话）

用户本轮选择：

> 那么我们是否需要看一下这里的handle job event 的内容了呢?

这是对阅读入口的选择，尚无对函数内部的个人复述。此前对 watcher、obj/raw 与更新目标的疑问保留在[父卡的本轮原话](K8sReconciler._watch_jobs_loop.md#watcher-and-update-question)。

<a id="overlap-question"></a>

用户随后追问职责与重叠：

> 我其实比较想要知道这里在做什么这件事情
> 我觉得很重要
> 我还是不是很理解
> 这个handle job event
> 我怎么感觉他做的事情和_reconcile_once
> 里面对于每一个rollout去查看这里的已经登记的rollout 对这kubernetes返回的job更新gateway有什么区别吗?
> 我觉得这个很重要?
> 这里的功能是否是混合的?
> 还是我的理解有问题?

用户识别的共同作用与源码一致。助手确认终态反馈确有重叠，并对照“按任务列表定期核对”与“处理收到的一份 Job 数据”、独有分支和并行关系；对分工的解释尚未得到用户确认。

<a id="strict-overlap-question"></a>

用户要求再次核对判断：

> 请仔细考虑一下 到底是我的判断是对的
> 还是说两者两者覆盖不一样
> 请仔细考虑
> 还说这里的真的重复了
> 还是只是我的误判和不理解

助手按相同输入重新核对，并区分三个判断：共同效果存在、覆盖不同、部分规则分别实现。采用 QUEUING + Complete/True 这一反例说明整体不等价，避免把“看起来都回写”直接概括为两个多余函数。用户尚未确认本轮结论。

<a id="read-write-key-question"></a>

用户要求先核对数据位置：

> 你先看一下这两个到底在查询的status或者具体的哪一个数据结构的哪一个key再做讨论?
> 他们修改的是否不是一个东西?

助手据取值表达式、共同回写接口与服务端保存位置核对：两者都读取 Kubernetes Job 的 conditions；周期路径还读 Gateway 的原状态及 Job 的计数。相同 rollout ID 下，两者终态回写都落到 Gateway 该任务的 status.state，但附带字段集合不同。以上是源码校准，尚无用户确认。

<a id="first-pass-closeout"></a>

用户询问本函数是否已读到收束位置：

> 好的 那么我们继续往下看吧
> 这里算是我们对于handle job event的内容看完了吗?
> 还是说我们还没有看完呢?

按本轮约定，主流程的讲解已覆盖：接收 `obj.raw`、从标签定位 rollout、从 conditions 判断结果、通过 `_patch_status` 请求更新 Gateway、返回 watch。可以先在这里收束单函数阅读，接回父调用；这项阅读位置判断不代表用户已掌握全部字段或分支。并发、重复事件、更新被拒绝等仍保留为后续深入问题。

## 尚不清楚

- 当前首要疑问是两处具体读写哪份数据、哪个 key；Job 条件的 status 与 Gateway 记录的 status.state 已按源码分开定位，尚待反馈。
- Job 标签怎样连接到 Gateway 任务，和 conditions 怎样触发状态回写，当前由助手沿样本说明，尚待反馈。
- 事件类型、Job 条件、本地变量与 Gateway 状态的关系仍需按实际理解继续核对。
- 写入失败、重复事件及与周期协调并发时的配合，尚未展开。

<details>
<summary>来源与验证边界</summary>

- [本轮收束位置与返回主线](../../../../../../step-001-watch-job-events/04-flow.md#handler-first-pass-closeout)。
- [读取与写入 key 的本轮核对](../../../../../../step-001-watch-job-events/04-flow.md#status-read-write-keys)。
- [覆盖范围与重复的严格复核](../../../../../../step-001-watch-job-events/04-flow.md#overlap-scope-audit)。
- [本次职责对照与重复逻辑讨论](../../../../../../step-001-watch-job-events/04-flow.md#polling-versus-event-feedback)。
- 固定提交 `0029dbb35c467799d35fee81d15d80264b0d1bd3`；本函数从 311 行开始，调用方在 305–306 行。
- 类型与转换约束见同版本 `schemas.py:77–93`；状态更新接口为 `_patch_status:362–373`。
- [Step 001 本次阅读与卡片建立](../../../../../../step-001-watch-job-events/04-flow.md#handle-job-event-reading)。
- 输入来自父卡的同一教学事件，仍为字段节选；未发送真实请求或修改集群。

</details>
