# K8sReconciler._patch_status

> **调用链面包屑**：[Step 001 范围](../../../../../../step-001-watch-job-events/01-scope.md) · [累计函数索引](../../../../overview.md) → [_watch_jobs_loop](K8sReconciler._watch_jobs_loop.md) → [_handle_job_event](K8sReconciler._handle_job_event.md#call-patch-status) → **_patch_status**

- 源码：[k8s_reconciler.py:362](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L362)。
- 首次接触：Step 000 中先按接口定位；2026-11-03 用户明确要求独立建卡并阅读。
- 最近认识更新：2026-11-03，用户已将 RUNNING 任务找不到对应 Job 与调用 `_patch_status` “报错”联系起来；用途已有初步复述，内部实现尚未复述。

- 继承来源：[Step 000 的完整原记录](../../../../../../step-000-k8s-controller-entry/02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._patch_status.md)。本次完整继承到 Step 001；首次接触、最近认识更新、原话与未知保持原值。

- 本步调取：[Step 001 的累计快照](../../../../../../step-001-watch-job-events/03-long-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._patch_status.md)。沿用状态更新接口，并补充本步成功事件场景；此前原话、未知与认识时间保留。

- 本次继承（Step 002）：[Step 001 的完整来源记录](../../../../../../step-001-watch-job-events/02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._patch_status.md)。此前继承和调取说明保留历史语境；原话、未知、首次接触与最近认识更新保持原值。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：本步 `_handle_job_event` 从 Job 读到成功完成后，用本方法请求更新 Gateway。此前 Step 000 的示例是父函数的另一条分支：任务记录是 `RUNNING`，但找不到对应 Job，需要将这条任务标为失败。同一方法也用于其他运行状态更新。这里同时满足“缺少 Job”和“Gateway 仍记为 RUNNING”；[完整调用条件与已完成路径](K8sReconciler._reconcile_once.md#why-patch-a-running-rollout)留在父卡。
2. **具体内容**：校验传入的状态字段，组织 `status` 更新体，对目标任务发送 PATCH 请求；成功返回 `True`，捕获异常后记录日志并返回 `False`。
3. **建议构建的心智模型**：

   > 用任务 ID 找到 Gateway 中的记录，提交本次要改的状态字段；返回值报告更新请求是否成功。

4. **调用代码**（本步 `_handle_job_event:331`）：

   ```python
   await self._patch_status(rollout_id, state=RolloutState.SUCCEEDED, last_attempt_id=attempt_id)
   ```

## 本场景的输入与输出

### 本步场景：把 Job 成功回写为 rollout 成功

沿用 r1 例子：Gateway 原来为 RUNNING，调用方从 Job 标签取得 `rollout_id="r1"`、`attempt_id="0"`，读到 Complete/True 后调用本方法。这里假定 Gateway 接受更新，没有发送真实请求。

输入是任务 ID，以及 `state=RolloutState.SUCCEEDED`、`last_attempt_id="0"`。它们组织成对 `/api/rollouts/r1` 的 PATCH 请求体：

```json
{
  "status": {
    "state": "succeeded",
    "last_attempt_id": "0"
  }
}
```

成功返回 `True`，捕获异常返回 `False`。本步调用方不接收这个布尔值，调用结束后便从 `_handle_job_event` 返回 `None`，回到 watch 继续接收。输入 Job 数据在调用方只被读取。

### 此前场景：Job 缺失时登记失败（Step 000）


教学场景：Gateway 中任务 r1 原本处于 `RUNNING`，本轮找不到对应 Job，父函数决定登记失败。假定 Gateway 接受这次更新；没有发送真实请求。

| 输入 | 本例值与用途 |
| --- | --- |
| `rollout_id` | `"r1"`，定位要更新的 Gateway 任务记录 |
| `**status` | 收集 `state=FAILED` 与 `error_message="Job disappeared"` 两个关键字参数 |
| `self._api` | 已配置的 Gateway HTTP 客户端 |

本例会组织成以下请求：

```text
PATCH /api/rollouts/r1
```

```json
{
  "status": {
    "state": "failed",
    "error_message": "Job disappeared"
  }
}
```

**返回值**：请求成功时为 `True`；校验、请求或响应检查等环节抛出异常时，被捕获后返回 `False`。这里的布尔值描述更新操作，和任务状态 `FAILED` 是两个概念。

<details>
<summary>此前缺失 Job 场景的调用代码</summary>

4. **调用代码**（`_reconcile_once:184`）：

   ```python
   await self._patch_status(
       rollout.rollout_id,
       state=RolloutState.FAILED,
       error_message="Job disappeared",
   )
   ```

</details>

### 完整函数主体

```python
try:
    patch = RolloutPatch(status=RolloutStatusPatch.model_validate(status))
    response = await self._api.patch(
        f"/api/rollouts/{rollout_id}",
        json=patch.model_dump(mode="json", exclude_unset=True),
    )
    response.raise_for_status()
    return True
except Exception as exc:
    log.warning("Failed to patch rollout", rollout_id=rollout_id, error=str(exc))
    return False
```

按当前调用读这段代码：

- `RolloutStatusPatch.model_validate(status)`：检查本次状态更新的字段，并转换为相应的模型对象。
- `RolloutPatch(status=...)`：外面加一层 `status`，对应 Gateway 接口需要的请求结构。
- `model_dump(mode="json", exclude_unset=True)`：转换为 JSON 可表示的数据，只发送本次明确提供的字段；例如 `FAILED` 枚举变成 `"failed"`。
- `self._api.patch(...)`：向 Gateway 发出更新请求，路径中的任务 ID 决定更新哪条记录。
- `raise_for_status()`：检查 HTTP 响应，正常后返回 `True`；异常统一进入下方日志与 `False` 返回。

Gateway 会检查状态转换是否合法，并合并提供的字段；本例 `RUNNING → FAILED` 是允许的转换。本函数没有把服务端响应再解析为一个返回的 Rollout 对象。

回写成功改变的是 Gateway 中的记录；本函数不刷新调用方之前取得的 `rollout` 对象。调用方的局部 `state`、原有 Rollout 快照与服务端记录需要分开看，具体对照见[父卡的数据模型](K8sReconciler._reconcile_once.md#status-data-model)。

服务端用 `body.status` 的字段更新 `rollout.status`，并保存到 `_rollouts[rollout_id]`。所以从两处调用传入的 `state` 最终都落在 Gateway 这条任务的 `status.state`；它不是写入 Kubernetes Job 的 `status.conditions`。完整取值路径与两种请求体见[读写 key 对照](../../../../../../step-001-watch-job-events/README.md#read-write-keys)。

### 读完返回哪里

| 返回位置 | 接住什么，接着执行什么 |
| --- | --- |
| [本步 `_handle_job_event`](K8sReconciler._handle_job_event.md#call-patch-status) | 没有接住布尔结果；调用结束后直接 return，回到 watch |
| [父函数的缺失 Job 分支](K8sReconciler._reconcile_once.md#missing-job-branch) | 本次调用没有保存布尔结果；函数返回后执行 `continue`，进入下一条 rollout |
| [父函数的其他状态更新位置](K8sReconciler._reconcile_once.md#call-patch-status) | 某些调用也会接住 `patched`，据此决定是否继续提交后续状态；这些分支按需回查 |

## 我的直接表述（原话）

用户已将 RUNNING 任务找不到对应 Job 与通过 `_patch_status` “报错”联系起来，[本次完整原话](K8sReconciler._reconcile_once.md#missing-job-branch-understood)保存在父卡。助手补准为向 Gateway 请求登记 FAILED 与失败原因；尚无对函数内部实现的个人复述。此前的[调用动机疑问](K8sReconciler._reconcile_once.md#running-patch-question)和[任务 ID、状态参数疑问](K8sReconciler._reconcile_once.md#my-statements)继续保留。

## 尚不清楚

- 用途已有初步理解；“报错”具体体现为 Gateway 状态更新，而不是向上抛出异常终止循环，刚由助手补准。
- 状态值与更新成功布尔值的区别，刚由助手说明，尚待用户反馈。
- `**status`、模型校验和 `exclude_unset` 的细节，先理解本例的数据变化即可。
- Gateway 内部存储和并发状态更新的约束，当前仅核对接口行为，未深入实现。

<details>
<summary>来源与验证边界</summary>

- [Step 001 本次调取与调用场景](../../../../../../step-001-watch-job-events/04-flow.md#handle-job-event-reading)。

- 固定提交：`0029dbb35c467799d35fee81d15d80264b0d1bd3`；本函数从 362 行开始，Step 000 的调用在 184 行，本步成功事件的调用在 331 行。
- 更新类型：`agentlightning/schemas.py` 中的 `RolloutStatusPatch`、`RolloutPatch` 与 `VALID_TRANSITIONS`。
- 服务端合同：[`server/routes/rollouts.py:183`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/server/routes/rollouts.py#L183)。本方法被协调循环、事件处理和无效 Job 配置处理复用；最初从缺失 Job 分支进入，本步从事件处理进入。
- [本次建卡与阅读范围](../../../../../../step-000-k8s-controller-entry/04-flow.md#patch-status-reading-start)。
- 请求体是本例的静态推导，没有运行 Gateway、修改真实任务或操作 Kubernetes。

</details>
