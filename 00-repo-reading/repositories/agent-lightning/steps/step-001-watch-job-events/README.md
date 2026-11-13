# Step 001 · 接收 Kubernetes Job 事件

[项目与唯一进度](../../README.md#current-reading) · [前一步：单轮协调与初步 watch 阅读](../step-000-k8s-controller-entry/README.md) · [Kubernetes 基础](../../../kubernetes/README.md)

> 继续在本地 Markdown 中阅读。本步沿用已确认的 `_watch_jobs_loop` 范围，把正在展开的事件接收问题独立保存。

- 日期与源码：2026-11-03；Agent Lightning `0029dbb35c467799d35fee81d15d80264b0d1bd3`。
- 前一步模型：用户已把单轮协调概括为查看 Job 是否存在、当前状况如何，以及是否需要修改 Gateway 的任务记录。变量、条件和回写细节仍有未知。
- 本步问题：Kubernetes Job 的事件怎样被接收，处理函数怎样识别任务和结果并向 Gateway 回写？
- 当前入口：从 `K8sReconciler._watch_jobs_loop` 的交接进入用户已选择的 `_handle_job_event`，再复用 `_patch_status` 接回状态更新。
- 记录重点：`event_type` 与 Job 对象的关系、`obj.raw` 的内容和去向、标签与条件怎样决定回写，处理返回后继续接收。说明仍放在具体代码与数据旁边。

## 本步入口

1. [阅读范围与骨架](01-scope.md)：把事件接收放回控制器的两条运行路径。
2. [本步短期记忆](02-short-term-memory/overview.md)：watch、事件处理、状态更新，以及本轮调取作对照的单轮协调卡。
3. [进入本步时的累计记忆](03-long-term-memory/overview.md)：完整继承前一步的 7 份函数记录。
4. [理解形成过程](04-flow.md)：保存建步依据与后续实际问答。

## 为什么从这里分成新步骤

前一处主要问题是“这一轮怎样核对两边并选择动作”；这里转为“怎样持续接收事件并交出去”。两者在 `run()` 中并行运行，适合分别保留阅读过程。

watch 的首次阅读已经发生在 Step 000，因此原卡片和对话留在那里。本步继承整份记录后，再将 watch 调入 `02` 继续；不把先前发生的阅读改写成未发生，也不因新增目录而把它标为已理解。

<a id="polling-and-job-events"></a>

## 为什么 _reconcile_once 和 _handle_job_event 都会回写状态

<a id="read-write-keys"></a>

### 先对照实际读取的对象与 key

两者取得 Job 数据的路径不同：周期路径从 `Job.async_list` 取 `.raw`，再按名字选出 `job`；事件路径接收 `obj.raw`，参数名也叫 `job`。它们是**同一种 Kubernetes Job 数据结构**，不表示两次读取一定是同一个 Python 对象或同一时刻的快照。

`_reconcile_once` 在 191–200 行分两次取字段：

```python
job_status = job.get("status", {})
for condition in job_status.get("conditions", []):
    if condition.get("status") != "True":
        continue
    if condition.get("type") == "Complete":
        state = RolloutState.SUCCEEDED
```

`_handle_job_event` 在 319–329 行把前两次取值连在一起：

```python
conditions = job.get("status", {}).get("conditions", [])
for condition in conditions:
    cond_type = condition.get("type", "")
    cond_status = condition.get("status", "")
    if cond_status != "True":
        continue
```

这两段都是摘录；共同读取的是下面这些位置：

```jsonc
{
  "status": {                              // Kubernetes Job 的 status 对象
    "conditions": [
      {
        "type": "Complete",                // 两者都读取：条件名称
        "status": "True",                  // 两者都读取：该条件是否成立
        "reason": "...",                   // 失败分支中，两者都可能读取
        "message": "..."                   // 失败分支中，两者都可能读取
      }
    ],
    "succeeded": 1,                        // 只有周期路径额外读这个计数作兜底
    "failed": 0                            // 只有周期路径额外读这个计数作兜底
  }
}
```

该 JSONC 仅展示字段位置；reason/message 的示意值不是一次实际响应。两者都只读取 `job["status"]["conditions"][i]["status"]`，不会把这里的 `"True"` 改成 `"succeeded"`。

### 周期路径还多读了 Gateway 的另一份状态

`_reconcile_once` 从 `_query_rollouts` 取得 Gateway 的 Rollout 模型，使用 `rollout.status.state` 判断其原先是 QUEUING 还是 RUNNING；`rollout.status.k8s_job_name` 用来定位对应 Job。

`_handle_job_event` 不先查询这份 Gateway 记录。它从 `job["metadata"]["labels"]["agentlightning/rollout-id"]` 得到要更新的任务 ID。两者都从 Job 的 `agentlightning/attempt-id` 标签取得执行编号，缺少时使用默认值。

所以**读取集合不同**：周期路径同时看 Gateway 状态和 Job 状态；事件处理直接从 Job 数据出发。`state = RolloutState.SUCCEEDED` 只是周期路径暂存结果，真正写入发生在下面的公共接口。

### 追到实际写入位置：两者调用同一个 Gateway 接口

两者都调用 `self._patch_status(rollout_id, state=..., ...)`。这个方法将字段包进 `RolloutPatch.status`，使用 `self._api` 发出：

```text
PATCH /api/rollouts/{rollout_id}
```

`self._api` 来自以 `config.agl_server.url` 为地址的 `AgentLightningAsyncClient`，与查询 Job 使用的 Kubernetes 客户端不同。服务端 `patch_rollout` 读取 `body.status`，合并进 `rollout.status`，最后保存：

```python
_rollouts[rollout_id] = updated
```

因此，当两条路径定位到同一个任务 ID，例如 r1，**共同写入的目标是 Gateway 中 `_rollouts["r1"].status.state`**。两条终态回写分支都不修改 Kubernetes Job 的 `status.conditions`。

### 成功场景：同一目标字段，附带字段不完全相同

假设两条路径都对 r1 写入成功，周期路径末尾的请求体是：

```json
{
  "status": {
    "state": "succeeded",
    "k8s_job_name": "agl-rollout-r1",
    "last_attempt_id": "0",
    "error_message": null
  }
}
```

事件处理成功分支的请求体是：

```json
{
  "status": {
    "state": "succeeded",
    "last_attempt_id": "0"
  }
}
```

两者都改同一条任务的 `status.state` 与 `status.last_attempt_id`；周期终态分支还写 `status.k8s_job_name`、`status.error_message`。事件成功分支未提供后两项，`exclude_unset=True` 使它们不出现在请求中，含义是保留旧值；明确发送 null 则会写入空值。事件失败分支也会提供 `error_message`。

服务端接受更新后，两条路径都还会使 `status.version` 增加、`status.updated_at` 刷新。这些是服务端附加的更新，不是两种不同的状态存储。

本轮只据具体字段得出：**读到的状态来源不完全一样；终态回写的核心目标是同一类 Gateway 字段。是否同一条记录由 rollout_id 决定。** 不把 Job 的 condition.status、周期路径的临时 state 和 Gateway 的 status.state 混成一处。

依据：`k8s_reconciler.py:163–240,313–344,362–369`、`controller/__main__.py:17–28`、`schemas.py:146–174`、`server/routes/rollouts.py:183–213`，均为固定提交 `0029dbb35c467799d35fee81d15d80264b0d1bd3`。请求体按源码静态推导，未访问真实服务。[本轮字段核对](04-flow.md#status-read-write-keys)。

<details>
<summary>此前关于覆盖、重复与配合的讨论：先读清字段，再按需回看</summary>

**复核后的结论：两者覆盖不同，有业务交集，交集中的部分判断规则被分别实现。** 这三个判断同时成立，不能把“有共同作用”直接等同于“整个函数重复、多余”。

- **共同作用**：在任务已经 RUNNING、Job 的 Complete/Failed 条件成立等场景下，两者都可能向 Gateway 回写同一个终态。
- **覆盖不同**：它们的启动方式、选取对象、前置检查、状态转换和附带更新字段不同，不能直接互相替代。
- **局部规则重复**：两处各自检查条件是否为 True、把 Complete/Failed 映射为 SUCCEEDED/FAILED，并组织失败原因。HTTP 请求则已经共用 `_patch_status`，并非全部重复实现。

### 从哪里开始工作

| 对照点 | `_reconcile_once` | `_handle_job_event` |
| --- | --- | --- |
| 谁让它运行 | `_periodic_reconcile_loop` 定期调用 | watch 收到 ADDED/MODIFIED 后调用 |
| 工作起点 | 本轮查询到的 QUEUING/RUNNING 任务与 Kubernetes Jobs | 已收到的一份 Job 数据，不先查询 Gateway 任务列表 |
| 怎么建立对应 | 从 rollout 记录或 ID 得到 Job 名，再找 Job | 从 Job 标签取得 rollout ID |
| 覆盖的动作 | 缺少 Job 时创建或登记失败；已有 Job 时补 RUNNING 或同步结果 | 对这份 Job 中成立的 Complete/Failed 条件直接请求回写终态 |

`run()` 并行启动两条路径；`_reconcile_once` 不调用 `_handle_job_event`。它们是不同入口上的协作，不是同一条调用链的前后两步。

### 用相同的起始情况检验，不能只看函数名字

下表中的“被拒绝”依据实际 Gateway 状态转换规则；任务、Job 与网络边界用内存数据代替，未运行真实服务。

| 起始情况 | 周期协调的行为 | 事件处理的行为 |
| --- | --- | --- |
| Gateway 为 RUNNING，Job 为 Complete/True | 请求 SUCCEEDED，可被接受 | 请求 SUCCEEDED，可被接受 |
| Gateway 为 QUEUING，Job 为 Complete/True | 先请求 RUNNING，再请求 SUCCEEDED，两次可被接受 | 直接请求 SUCCEEDED，被拒绝，任务仍为 QUEUING |
| Gateway 为 QUEUING，Job 存在但无终态条件、无成功/失败计数 | 请求 RUNNING | 不发更新请求 |
| Gateway 为 RUNNING，Job 没有条件，只有 `succeeded=1` | 用计数兜底，请求 SUCCEEDED | 无条件则返回，不发更新请求 |
| QUEUING 任务还没有对应 Job | 调用创建函数 | 没有对应 Job 事件可交给本函数；它也没有创建逻辑 |

**第二行就是两个函数不等价的直接反例。** Gateway 只允许 QUEUING → RUNNING/FAILED，不允许直接 QUEUING → SUCCEEDED。不能把事件处理简单描述成“更快执行一遍完全相同的协调逻辑”。

### 那么，重复究竟指哪一部分？

范围仅限于部分规则：两处都要识别“Complete 且 True”与“Failed 且 True”，都将它们翻译为项目的终态；失败原因也各自按 `Job failed: reason` 加可选 message 组织。两段语句并非逐行完全相同：一个先记录到局部变量，再处理转换；另一个直接调用更新接口。

即使第一行的终态相同，更新内容也并非完全相同：周期协调额外发送 Job 名，成功时还发送 `error_message=None`；事件成功分支只发送状态和执行编号。因此本轮把“重复”严格限定为**局部业务规则分别实现**，不据此认定某一个函数可以删除。

### 两条路径一起运行有什么作用

从现有行为可以归纳：事件路径在收到通知后即可尝试反馈结果，周期路径会继续核对任务并处理创建、缺失 Job、状态补齐等情况。若事件没有成功处理，而任务仍被查询选中、Job 尚在，周期核对有机会补上。

这是根据代码归纳出的配合作用，不是从作者说明中确认的设计动机，也不是所有失败场景均可恢复的证明。当前更合适的模型是：**两种入口协作，覆盖各有不同，终态判断存在共同部分。**

<details>
<summary>更细的边界与本轮核对方法</summary>

- 选取对象的范围也不完全相同：周期查询排除已结束的 rollout；watch 仍可能收到这些 Job 的后续事件，处理函数会尝试回写，而服务端拒绝终态再转到同一终态。因此也不把事件处理简单称为周期处理的严格子集。
- 周期路径按名称对应 Job，不要求该 Job 有 rollout-id 标签；事件路径缺少该标签时直接返回。本轮也用同一 Job 名、缺少标签的样本核对了这种差别。
- watch 外层忽略 DELETED，运行中任务失去 Job 的检查由周期路径承担。
- 事件成功回写后，正常的下一次任务查询会排除该终态 rollout；但已持有旧快照的周期路径仍可能重复尝试，不保证只尝试一次。
- 本轮抽取原始 `_reconcile_once`、`_handle_job_event`，并执行 `patch_rollout` 中的状态转换校验片段，配合原始 `VALID_TRANSITIONS`；对六组共有 Job 的输入比较请求、是否接受及最终模拟状态，另核对无 Job 时的创建。输入、HTTP 边界和持久化使用内存桩，未验证网络、实际 watch 投递或并发时序。
- 源码固定为 `0029dbb35c467799d35fee81d15d80264b0d1bd3`；依据 `run:134–137`、`_reconcile_once:161–240`、`_handle_job_event:311–346`、`schemas.py:87–93` 与 `server/routes/rollouts.py:183–197`。

</details>

源码入口：[_reconcile_once 本步对照卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md)、[_handle_job_event 当前卡](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._handle_job_event.md)。[严格复核的讨论](04-flow.md#overlap-scope-audit)。

</details>

## 当前形成的认识与下一问

用户已将 namespace/标签筛选与前面的 Job 列表查询联系起来，明确不理解 watcher、event_type、obj，并猜测下游更新容器状态或本地目录。当前沿[一条事件的例子](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._watch_jobs_loop.md#one-job-event)说明两个返回值及 `.raw`，再把交接连到 Gateway 中的 rollout 记录；校准尚待反馈。

用户要求先核对两处具体读取和修改哪个对象的哪个 key，再讨论覆盖或重复。本轮已把共同读取的 Job conditions、周期路径额外读取的 Gateway 状态，以及共同写入的 Gateway status.state 分开定位；理解尚待反馈。停止、重连、库内部资源版本及真实集群行为按问题取舍；本步尚未开展集群实验。

在主流程讲解收束后，用户倾向先不深挖 watch 外层控制。下一选题建议转向“Job 如何实际启动 Agent”：从已读 `_create_job` 回查 [`build_job_spec:43`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L43)，配合 [`swe_smith/job-template-openai.yaml`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/examples/swe_smith/job-template-openai.yaml)。[取舍与候选范围](04-flow.md#next-topic-job-runtime)保留于本步过程，实际接续仍以项目入口为准。
