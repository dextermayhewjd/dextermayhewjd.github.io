# K8sReconciler._reconcile_once

> **调用链面包屑**：[Step 000 范围](../../01-scope.md) · [短期函数索引](../../02-short-term-memory/overview.md) → [run](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L126) → [_periodic_reconcile_loop（源码）](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L147) → **_reconcile_once**

- 源码：[k8s_reconciler.py:161](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L161)；本步编号 [1]。
- 首次接触：Step 000，2026-11-03。
- 最近认识更新：2026-11-03，用户已理解缺失 Job 时的创建与失败登记；本轮尝试把 conditions 理解为正常/异常检查，并明确对状态数据、计数兜底和后续分支感到混淆。下文为助手核对后的解释，尚待理解反馈。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：外层周期循环调用本函数，核对 Gateway 的待执行/执行中任务与 Kubernetes Job 是否对应，并选择创建或更新状态。
2. **具体内容**：查询两边的记录，按名称匹配；缺少 Job 时区分排队与运行中任务；已有 Job 时先得出本轮结果，再按 Gateway 的旧状态决定回写。
3. **建议构建的心智模型**：

   > **读取两份数据 → 匹配 → 本地判断 → 必要时向 Gateway 回写。** `state` 是中间判断值，远端更新发生在 `_patch_status` 调用中。
   >
   > ```mermaid
   > flowchart TD
   >     A["取得 rollout 与 Job"] --> B{"找到对应 Job？"}
   >     B -- "否" --> C["QUEUING：尝试创建<br/>RUNNING：登记 FAILED"]
   >     B -- "是" --> D["① 从同一 job_status 推断局部 state"]
   >     D --> E{"state is None？"}
   >     E -- "是" --> F["② 未判断出终态<br/>按 Gateway 旧状态决定是否补 RUNNING"]
   >     E -- "否" --> G["③ 已判断出结果<br/>按转换规则写 SUCCEEDED 或 FAILED"]
   > ```
   >
   > 第一层按 **Job 是否存在** 分；已有 Job 后按 **本轮是否判断出终态** 分；具体怎样回写，再看 **Gateway 原来登记的状态**。这是代码处理层次，不是 Kubernetes 的组件分层。

4. **调用代码**（`_periodic_reconcile_loop:151`）：

   ```python
   await self._reconcile_once()
   ```

## 本场景的输入与输出

显式输入只有 `self`；正常返回 `None`。查询、Job 创建与 Gateway 状态更新是过程中的交互。本页先看[数据形状](#status-data-model)，再对照[完整骨架](#parent-skeleton)；当前重点为[① 读取 Job 结果](#job-result-inference)和[②/③ 回写分支](#gateway-update-decisions)。

<a id="status-data-model"></a>

### 0. 两份远端记录，一个本地判断值

| 名称 | 数据形状与来源 | 当前应怎样读 |
| --- | --- | --- |
| `RolloutState` | 项目定义的字符串枚举类型；成员为 QUEUING、RUNNING、SUCCEEDED、FAILED | 这是可选值的定义；`state = RolloutState.FAILED` 是把一个值交给局部变量，没有修改枚举类型 |
| `rollout` | Gateway 响应转换成的 `Rollout` 模型对象 | 用 `.rollout_id`、`.status` 访问字段 |
| `rollout.status.state` | `RolloutLifecycleStatus` 中的一个 `RolloutState` 值 | 查询时 Gateway 已登记的状态；本轮筛选后只有 QUEUING/RUNNING |
| `job` | Kubernetes Job 的 `.raw`，是字典式 `Box` 数据；找不到时为 `None` | 有 `metadata`、`spec`、`status` 等字段，本页只保留有关字段 |
| `job_status` | `job.get("status", {})` 取得的嵌套映射 | 一组观测字段，不是一个状态枚举；缺少整个 status 时用空字典 |
| `condition` | `job_status["conditions"]` 列表中的一项映射 | `type` 表示哪条条件，`status` 用字符串 `"True"/"False"/"Unknown"` 表示它是否成立 |
| 局部 `state` | 本轮处理当前 rollout 时新建的变量；初始为 `None` | 191–213 行根据 Job 信息将它归纳为 `None`、SUCCEEDED 或 FAILED |

下面是**同一教学场景的字段节选**：任务 r1 的 Gateway 记录仍为 RUNNING，Kubernetes Job 已成功。不含所有必填字段，不是完整构造参数或真实请求响应。

Gateway JSON 节选（解析成 `Rollout` 后，代码用属性访问）：

```json
{
  "rollout_id": "r1",
  "status": {
    "state": "running",
    "k8s_job_name": "agl-rollout-r1"
  }
}
```

Kubernetes Job 数据节选（这里以 JSON 展示 `.raw` 中的字段）：

```json
{
  "metadata": {
    "name": "agl-rollout-r1",
    "labels": {"agentlightning/attempt-id": "0"}
  },
  "status": {
    "conditions": [{"type": "Complete", "status": "True"}],
    "active": 0,
    "succeeded": 1,
    "failed": 0
  }
}
```

**`job_status` 就是第二份数据的 `status` 子对象。** `conditions` 与 `succeeded/failed` 同属这个子对象：前者是 Job 条件列表，后者是成功/失败的 Pod 计数。不是先读一份状态，再向 Kubernetes 请求另一份状态。通用字段含义集中在 [Kubernetes Job status](../../../../../kubernetes/03-workloads/job-status.md)。

本例的数据交接：

| 时机 | 局部 `state` | Gateway 中的状态 |
| --- | --- | --- |
| 开始分析这条 Job | `None` | RUNNING |
| 读到 `Complete` 且 `"True"` | SUCCEEDED | 仍为 RUNNING |
| `_patch_status(..., state=state)` 被服务端接受 | 仍为 SUCCEEDED | 更新为 SUCCEEDED |

`job_status` 在这段分析中只被读取。给 `state` 赋值既不修改 Job，也不修改 Gateway；调用 `_patch_status` 后，本地这份 `rollout` 快照也没有被代码重新赋值或刷新。

<a id="parent-skeleton"></a>
<a id="two-data-sources"></a>

### 完整骨架：当前始终站在 _reconcile_once 中

下面保留本函数的读取、循环和业务分支。教学裁剪省略参数、日志、类型提示和状态字段提取细节；`...` 表示省略的真实语句，不是独立可运行代码。子函数实现从下一张表打开，不在这里展开。

```python
rollouts = await self._query_rollouts(...)  # 163：取得任务记录
api = await self._get_k8s_api()  # 164：取得 Kubernetes 客户端
jobs = [job.raw async for job in k8s_objects.Job.async_list(...)]
jobs_by_name = {job.get("metadata", {}).get("name", ""): job for job in jobs}

for rollout in rollouts:
    job_name = rollout.status.k8s_job_name or build_job_name(...)
    job = jobs_by_name.get(job_name)

    if job is None:
        if rollout.status.state == RolloutState.QUEUING:
            await self._create_job(...)  # 181：创建后返回这里
            continue
        await self._patch_status(..., state=RolloutState.FAILED)
        continue

    # ① 从已有 Job 归纳本轮结果（191–213）
    job_status = job.get("status", {})
    state = None
    ...  # 本函数从 conditions 和成功/失败计数中确定 state

    if state is None:  # ② 本轮尚未判断出终态（215–223）
        if rollout.status.state == RolloutState.QUEUING:
            await self._patch_status(..., state=RolloutState.RUNNING)
        continue

    # ③ 已判断出终态，准备回写（225–240）
    if rollout.status.state == RolloutState.QUEUING and state == RolloutState.SUCCEEDED:
        patched = await self._patch_status(..., state=RolloutState.RUNNING)
        if not patched:
            continue
    await self._patch_status(..., state=state)
```

`state=None` 表示本次还没有从 Job 中得到终态；其余结果为 `SUCCEEDED` 或 `FAILED`。读取这些字段、建立字典、分支判断与 `continue` 都是本函数自身的逻辑，留在这张卡片内理解。
### 从一个调用下钻，再返回原处

先在上面的骨架找到调用位置；需要弄清某个子函数时，一次打开一个入口，带着返回项回到同一位置。已有卡片直接打开；尚未独立阅读的函数先给固定版本源码入口。

| 需要展开时打开 | 本次交入、带回什么 | 读完回到本卡，接着执行什么 |
| --- | --- | --- |
| <a id="call-query-rollouts"></a>[_query_rollouts（函数卡）](../../02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._query_rollouts.md) | 筛选 `QUEUING / RUNNING`、上限 500 → `list[Rollout]`，每项带标识、输入、配置与状态 | 回到 163 行 `rollouts = await ...`，接住任务列表，再取得 Kubernetes 客户端 |
| <a id="call-get-k8s-api"></a>[_get_k8s_api（函数卡）](../../02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._get_k8s_api.md) | 无额外参数；取得或复用 Kubernetes 客户端 | 回到 164 行 `api = await ...`，把它交给后面的 `Job.async_list` |
| <a id="call-list-jobs"></a>[Job.async_list（库接口卡）](../../02-short-term-memory/functions/kr8s/_objects.py/APIObject.async_list.md) | namespace、管理标签与客户端 → 可异步迭代的 Job | 回到列表推导式，取各项 `.raw` 得到 `jobs`；然后建立 `jobs_by_name` |
| <a id="call-create-job"></a>[_create_job（函数卡）](../../02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._create_job.md) | 当前排队任务 `rollout` → 委派创建；正常返回 `None` | 回到 181 行 `await self._create_job(...)`，随后 `continue`，检查下一条任务 |
| <a id="call-patch-status"></a>[_patch_status（函数卡）](../../02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._patch_status.md) | 任务编号、状态字段 → 写回是否成功的 `bool` | 返回刚才的分支；补写 `RUNNING` 的分支检查 `patched`，失败则跳过本条，否则继续写终态 |

`build_job_name` 提供缺省 Job 名；需要核对命名时可看其[源码](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L38)，返回后接着执行 `jobs_by_name.get(job_name)`。

当前的查询边界只需在父卡保留：`self._api` 查询 Gateway 的任务；局部 `api` 查询 Kubernetes 的 Job。`rollouts` 是任务对象列表，`jobs` 是各 Job 的字典式 `.raw` 数据列表。
<a id="index-jobs-by-name"></a>

### 匹配：把已查到的 Job 按名称索引（173–177 行）

```python
jobs_by_name = {job.get("metadata", {}).get("name", ""): job for job in jobs}
```

例如名称为 `job-a`、`job-b` 的两份 Job 数据，成为两个同名键对应的值。这里没有重新查询或创建 Job。逐条处理 rollout 时，名称优先取 `rollout.status.k8s_job_name`，没有时用 `build_job_name(rollout.rollout_id)`；再通过 `jobs_by_name.get(job_name)` 得到 Job 或 `None`。

<a id="missing-job-branch"></a>
<a id="why-patch-a-running-rollout"></a>

### 已读分支：找不到 Job（178–185 行）

下面仅省略原分支中的警告日志：

```python
if job is None:
    if rollout.status.state == RolloutState.QUEUING:
        await self._create_job(rollout)
        continue
    await self._patch_status(rollout.rollout_id, state=RolloutState.FAILED, error_message="Job disappeared")
    continue
```

| Gateway 记录 | 为什么这样处理 | 动作与返回 |
| --- | --- | --- |
| QUEUING | 没有 Job，可能尚未创建 | 尝试 `_create_job(rollout)`，返回后 `continue` 到下一条任务 |
| RUNNING | 已登记运行中，但本轮找不到 Job | 按任务 ID 请求登记 FAILED，原因 `Job disappeared`，再 `continue` |

进入这段必须先满足 `job is None`，不能只凭 QUEUING 就创建。`await _create_job` 等待创建函数返回，不是等待整个 Agent 任务结束；创建后也不会落到本段的失败回写。用户已[复述这两个分支](#missing-job-branch-understood)。

<details>
<summary>此前追问：如果任务已经完成了？</summary>

Job 已成功且对象仍在时，走下方已有 Job 的处理；完成并不等于对象消失。Gateway 已登记 SUCCEEDED 的任务，下一轮不在 QUEUING/RUNNING 查询范围内。如果 Job 对象已被清理但 Gateway 仍为 RUNNING，本段仍按缺失请求登记失败，不能凭对象消失推断此前成功。写入若失败，也不能视为远端已经变更。

[此前问题与校准](../../04-flow.md#why-patch-a-running-rollout)。

</details>

<a id="existing-job-reading-map"></a>

### 已有 Job：先归纳，再选择回写路径

当前从 `job is not None` 进入。局部①②③是本函数内部阅读段，与 scope 中的全局 [1]–[5] 不同。

| 阅读段 | 源码 | 交出什么、接着去哪里 |
| --- | --- | --- |
| [① 读取 Job 结果](#job-result-inference) | 191–213 行 | `job_status` → 局部 `state` 与 `error_message`；再选择②或③ |
| [② 没判断出终态](#nonterminal-job) | 215–223 行 | 必要时向 Gateway 补 RUNNING；`continue` 到下一条 rollout |
| [③ 已判断出结果](#terminal-job) | 225–240 行 | 按 Gateway 转换规则回写 SUCCEEDED/FAILED；必要时先补 RUNNING |

187–189 行先从 Job 标签取得 `attempt_id`，没有时取 `DEFAULT_ATTEMPT_ID`。它随回写成为 `last_attempt_id`，不参与本轮成功/失败的判断。

<a id="job-result-inference"></a>

### ① 同一份 job_status：先看条件，没有结论再看计数

这一段只做本地判断。以下是 191–213 行的完整连续代码：

```python
job_status = job.get("status", {})
state = None
error_message = None
for condition in job_status.get("conditions", []):
    if condition.get("status") != "True":
        continue
    if condition.get("type") == "Complete":
        state = RolloutState.SUCCEEDED
        break
    if condition.get("type") == "Failed":
        reason = condition.get("reason", "Unknown")
        message = condition.get("message", "")
        error_message = f"Job failed: {reason}"
        if message:
            error_message += f" — {message}"
        state = RolloutState.FAILED
        break

if state is None and job_status.get("succeeded", 0) > 0:
    state = RolloutState.SUCCEEDED
elif state is None and job_status.get("failed", 0) > 0:
    state = RolloutState.FAILED
    error_message = "Job failed"
```

**第一层：`conditions` 说哪条条件成立。** `status="True"` 不表示“一切正常”，必须和 `type` 合起来读：

| 一项 condition | 当前代码怎样处理 |
| --- | --- |
| `{"type": "Complete", "status": "True"}` | 成功完成条件成立，局部 `state = SUCCEEDED`，退出条件循环 |
| `{"type": "Failed", "status": "True"}` | 失败条件成立，局部 `state = FAILED`，组织原因，退出条件循环 |
| `{"type": "Failed", "status": "False"}` | 这条失败条件不成立，跳过本项；并不能据此判定成功 |
| 其他 `type`，或 `status` 不是 `"True"` | 本段不据此设置结果；列表中也可能没有本段认识的终态条件 |

195–196 行的 `continue` 跳过的是**当前 condition**；199/207 行的 `break` 退出的是**这个条件列表循环**，还没退出当前 rollout 的处理。

**第二层：209–213 行只在 `state is None` 时尝试看计数。** 前面已经得到 SUCCEEDED 或 FAILED 时，后面的两条条件都不成立，不会覆盖先前的结果。`job_status.get(...)` 仍读取同一个本地映射，没有重新查询，也没有更新 `job_status`。

| 教学输入节选 | 条件循环结束后 | 209–213 行之后 |
| --- | --- | --- |
| `Complete/True`，`succeeded=1` | SUCCEEDED | SUCCEEDED；计数判断被 `state is None` 挡住 |
| `Failed/True`，`failed=1` | FAILED | FAILED；计数判断被挡住 |
| 没有可用终态条件，`succeeded=1` | `None` | SUCCEEDED，来自计数兜底 |
| 没有可用终态条件，`succeeded=0, failed=1` | `None` | FAILED，原因 `Job failed` |
| 没有可用终态条件，两项计数都为 0 或缺少 | `None` | 仍为 `None`，进入② |

两个计数都大于 0、又没有可用条件时，这段 `if/elif` 优先取 succeeded。`None` 只表示本段没判断出结果，不等于“Job 正常运行”，也不是 Kubernetes 的状态值。

<details>
<summary>计数兜底的含义与边界</summary>

`conditions` 是对 Job 的条件描述；`succeeded/failed` 是 Pod 计数，两者并非完全等价。当前代码选择在缺少可用终态条件时用“大于 0”推断结果，能确认的是这个兜底行为；不能据此说 Kubernetes 对所有 Job 都规定一个 Pod 成功就整项成功。

通用 Kubernetes Job 可能要求多个 Pod 成功，也可能容许失败后重试。当前项目 `build_job_spec:72–77` 设置了 `backoffLimit=0` 与 `restartPolicy="Never"`，这是失败兜底的项目上下文；该函数内部仍未独立阅读。模板中的完成数量及其他策略不在这里被统一改写，不能把兜底推广到任意模板。

Kubernetes 文档也区分完成计数与终态条件的发布时机；例如 v1.31 及以后，终态条件等待该 Job 的所有 Pod 终止。这里只核对字段语义，没有复现一次真实集群时序。见 [Job 状态基础](../../../../../kubernetes/03-workloads/job-status.md)。

</details>

<a id="gateway-update-decisions"></a>

### ②/③ 用“Gateway 旧状态 + 本轮结果”决定回写

以下表格覆盖 **Job 已找到** 后的六种组合。所有“写入”都表示发起请求，只有服务端接受才算远端更新。

| 局部 `state` | Gateway 原状态 | 路径与请求 |
| --- | --- | --- |
| `None` | QUEUING | ②：补写 RUNNING，然后 `continue` |
| `None` | RUNNING | ②：本轮不更新，直接 `continue` |
| SUCCEEDED | QUEUING | ③：先补 RUNNING，成功后再写 SUCCEEDED；补写失败则 `continue` |
| SUCCEEDED | RUNNING | ③：直接写 SUCCEEDED |
| FAILED | QUEUING | ③：直接写 FAILED |
| FAILED | RUNNING | ③：直接写 FAILED |

<a id="nonterminal-job"></a>

#### ② state is None：已有 Job，但本段还没判断出终态

```python
if state is None:
    if rollout.status.state == RolloutState.QUEUING:
        await self._patch_status(
            rollout.rollout_id,
            state=RolloutState.RUNNING,
            k8s_job_name=job_name,
            last_attempt_id=attempt_id,
        )
    continue
```

这里把“已有 Job、未判断出终态”的 QUEUING 任务登记为 RUNNING；并没有进一步检查 Pod 是否已开始运行。Gateway 本来就是 RUNNING 时，不需要重复写这个值。223 行的 `continue` 属于外层 rollout 循环，保证本条不会继续执行③。

<a id="terminal-job"></a>

#### ③ state 已有值：写回结果，必要时先补一个转换

```python
if rollout.status.state == RolloutState.QUEUING and state == RolloutState.SUCCEEDED:
    patched = await self._patch_status(
        rollout.rollout_id,
        state=RolloutState.RUNNING,
        k8s_job_name=job_name,
        last_attempt_id=attempt_id,
    )
    if not patched:
        continue
await self._patch_status(
    rollout.rollout_id,
    state=state,
    k8s_job_name=job_name,
    last_attempt_id=attempt_id,
    error_message=error_message,
)
```

Gateway 的规则允许 QUEUING → RUNNING/FAILED、RUNNING → SUCCEEDED/FAILED。因此只有 **Gateway 仍为 QUEUING，而本轮已判断为 SUCCEEDED** 时，要先补 RUNNING 再写 SUCCEEDED。`patched` 是这次补写是否成功的布尔值；失败就不继续发成功请求。它与任务成功/失败是不同概念。

其余终态分支共用末尾的 `_patch_status`。`state=state` 左边是调用参数名，右边是①得出的局部变量；`k8s_job_name` 和 `last_attempt_id` 保存关联，`error_message` 保存失败原因，成功例子中为 `None`。更新接口内部复用[已有函数卡](../../02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._patch_status.md)，读完回到当前调用继续。

<a id="return-to-caller"></a>

### 返回主线

| 返回位置 | 交出什么、接着做什么 |
| --- | --- |
| 当前 `for rollout in rollouts` | 一条任务处理结束或命中外层 `continue` 后，检查下一条任务 |
| [_periodic_reconcile_loop:151](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L151) | 整轮正常结束返回 `None`，外层等待下一次协调 |

本次给出了数据与分支的完整关系；用户尚未确认理解，事件观察与并发更新仍留待后续问题。

<a id="my-statements"></a>

## 我的直接表述（原话）

<details>
<summary>2026-11-03：任务查询、返回内容与 K8s 边界的疑问</summary>

> 好的我来尝试理解一下吧
> 首先reconcile 的内容是这里的query rollouts?
> 这里是在拿rollout?
> 是否需要单独看一下这里的query rollouts?
> 这个函数?
> 还是说当前先记住返回的是每一个rollout的状态?
> 这里哪些内容是k8s直接有关的呢?

这是初步理解与疑问。助手已补充“查询是第一步，返回任务对象列表，状态是其中字段”及两类 API 的区别；尚未收到用户对这些细分关系的确认。

</details>

<details>
<summary>2026-11-03：名称索引与缺失 Job 分支的理解和疑问</summary>

用户同时贴出 `if job is None` 分支，下方节选其代码块前后的表述：

> 这里就是字典构造方法
> 那么我们来看一下下一个部分吧
> 也就是这里的rollouts
> 之前我们就知道这里的rollout是gateway获得的
> 那么继续看一下吧
> 这里的这里通过在一开始query rollouts部分拿到他们的job name
> 如果是还在queuing的话那么就会等待创造job
> 西面的patch status 的rollout rolloutid 什么
>
> 这里的内容我不是特别明白需要单独开两个short term memory的function吗
> 感觉好像只有这里需要稍微了解一下?

字典构造的判断与源码一致。Job 名存在读取和生成两种来源，等待创建函数返回也不同于等待任务完成；这两处及状态写回目标是本轮助手校准，未改写成用户已确认的认识。

</details>

<a id="creation-reading-request"></a>

<details>
<summary>2026-11-03：复述任务与 Job 的对应，选择进入创建函数</summary>

> 我大概理解了
> 这里的gateway里更多的是登记一共有哪些?
> 哪些是queue的哪些是已经running的是我的理解
>
> 那么后面这儿里是通过询问一边k8s的job
> 这样能得到到目前有哪些job已经登记了在运行
> 下面的就是
> 通过这里的queueing和running的
> rollout
> 来那一下job name
> 能够逐条查看这里的rollout
> 然后看一下这里的job
> 如果目前还是queuing的话
> 就创造一个job?
> 所以我觉得我需要看一下这里的这个create job?
> 然后我们再来看一下这里的patch status吧?

用户已描述登记的任务与查询到的 Job 逐条对应的主线。助手补充两项条件：Kubernetes 查询结果不限于运行中的 Job；只有找不到对应 Job 且 rollout 为 `QUEUING` 时才进入创建。具体创建机制尚未获得个人复述。

</details>

<a id="running-patch-question"></a>

<details>
<summary>2026-11-03：为什么 RUNNING 还需要回写，以及已完成时的路径</summary>

> 再怎样的路径下会走到这一层呢?
> 如果只是这里已经完成了呢?
> 至少我目前的理解是queue的任务创建job
> 如果不是queue那么说明应该是running的状态
> 那么为什么会需要这里的patch 我其实有一点`没有理解?

用户对本轮查询结果中“非 QUEUING 则为 RUNNING”的判断与筛选条件一致。创建还需满足外层 `job is None`；RUNNING 是 Gateway 记录，当前缺失分支的 PATCH 用于纠正它与 Job 查询结果的不一致。这些补充尚未获得理解确认。

</details>

<a id="missing-job-branch-understood"></a>

<details>
<summary>2026-11-03：确认缺失 Job 时，排队与运行中任务的不同处理</summary>

> 好的我理解了
> 也就是说
> 这里一开始本来就应该只是有queuing和running的
> queuing没有在现在的job里面找到就创建很合理
> 但是如果这里的running的部分
> 也没有的话 那就应该通过patch status来报错?
> 是否可以这么理解?

这次表述已连接查询范围、缺失 Job 条件和两个处理分支。助手确认该关系，并补准“报错”的含义：请求将 Gateway 中这条 rollout 更新为 `FAILED`，原因是 `Job disappeared`；本次调用不是向上抛出异常来终止整个协调循环，返回后继续下一条任务。补充语义不代记为用户已经复述。

</details>

<a id="status-data-question"></a>

<details>
<summary>2026-11-03：conditions、计数与几种状态变量的混淆</summary>

> 我的可以简单理解为 之前是考虑的内容是还在queueing的就创建job
> 下面的是这个job存在的
> 如果存在的情况下如果condition一切正常就没事
> 如果不正常rolloutstate变成failed
>
> 以及如果这里的job status更新了
> 为什么这里的209-213  还会有更具job status直接来更新的呢?
> 这里的job status为什么感觉有两个分层的部分?
> 我没有特别理解
>
> 包括后面的一系列情况
> 我觉得这里肯定是分层处理的
>
> 能否具体的讲一下呢?
> 以及这里的reconcile once的函数卡片应该怎么做?
> 1.我感觉这里需要讲清楚一下这里的数据格式到底是怎么样的 rolloutstate或者这里的state或者job status
> 有点晕乎乎的
>
> 2.其次我觉得这里需要搞清楚这里的这么多个分支到底是哪些内容

用户已定位接下来是 Job 存在的路径；“条件正常/异常”及“job status 更新”仍是待校准的理解。助手说明：条件是否成立要结合 type；条件和计数读取同一份 Job status，只改局部 state；后续 PATCH 才请求更新 Gateway。上述校准与六种回写组合尚待反馈。

</details>

## 尚不清楚

- 用户明确对 `RolloutState`、Gateway 状态、Job status、condition 和局部 `state` 的数据形状与关系感到混淆；本轮已给字段样本与对照，尚待反馈。
- `conditions` 的 type/status 组合、计数兜底与 `state is None` 的作用，已由助手校准，尚无确认后的个人复述。
- 已有 Job 的六种回写组合、中间 RUNNING 转换与请求成功布尔值，尚未确认理解。
- 缺失 Job 时的两条处理路径已有个人复述；创建函数返回、状态登记和真实任务完成的边界继续保留此前说明。
- 事件观察、并发更新冲突、HTTP 与模型转换内部、任意 Job 模板下计数兜底的适用范围，未展开为实践验证。

<details>
<summary>来源、历史与验证边界</summary>

- [本次数据与分支澄清](../../04-flow.md#status-data-and-branches)。
- [按数据模型重排前的完整卡片](2026-11-03-reconcile-once-before-status-data-model.md)保留原结构与全部表述；重排不表示个人理解已更新。
- 数据模型依据 `schemas.py:77–93,145–183`，Gateway 状态检查依据 `server/routes/rollouts.py:183–216`；本页连续源码直接取自本地固定提交。
- JSON 与计数示例为教学节选。将实际 `_reconcile_once` 的远端边界替换为内存桩后，14 组本地样例核对通过：缺失 Job、六种已有 Job 组合、计数兜底、条件优先、False 条件、双计数以及补写失败。未访问真实 Gateway 或 Kubernetes；这些结果只验证给定输入下的控制流。
- 固定版本：`0029dbb35c467799d35fee81d15d80264b0d1bd3`。骨架覆盖 `_reconcile_once` 的全部主要业务分支；Job 状态提取细节见原函数，未编造额外辅助函数。
- 返回字段依据 [`_query_rollouts`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L348) 和同版本 [`schemas.py`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/schemas.py)。
- [修改前完整卡片](2026-11-03-reconcile-once-before-breadcrumbs.md)保留此前分段、例子与来源；更早的[详细说明](2026-11-03-reconcile-once-before-segmentation.md)继续保留。
- [原始技术讨论](../../04-flow.md#query-rollouts-and-k8s-boundary) · [面包屑 reference 核对](../../04-flow.md#breadcrumb-reference-confirmation) · [本次按 reference 修改](../../04-flow.md#breadcrumb-card-applied)。
- 骨架与跳转的整理不计为新增理解；当前已按用户要求独立进入 `_query_rollouts`，见[本轮记录](../../04-flow.md#query-rollouts-card-start)，仍无真实服务运行。
- [名称索引与缺失 Job 分支的本轮讨论](../../04-flow.md#missing-job-branch)：依据同版本 175–186 行；`build_job_name` 从 38 行开始，`_patch_status` 从 362 行开始。

</details>
