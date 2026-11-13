# K8sReconciler._reconcile_once

> **调用链面包屑**：[Step 000 范围](../../01-scope.md) · [短期函数索引](../../02-short-term-memory/overview.md) → [run](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L126) → [_periodic_reconcile_loop（源码）](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L147) → **_reconcile_once**

- 源码：[k8s_reconciler.py:161](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L161)；本步编号 [1]。
- 首次接触：Step 000，2026-11-03。
- 最近认识更新：2026-11-03，用户已复述本轮只查询 QUEUING/RUNNING；找不到对应 Job 时，QUEUING 创建，RUNNING 通过 `_patch_status` 报告异常。助手将“报错”补准为向 Gateway 请求登记 FAILED 与原因；已有 Job 的处理仍待继续。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：外层周期循环等待本函数完成一轮检查，结束后继续其等待与下一轮安排。
2. **具体内容**：取得任务与 Job，为每条任务找到对应 Job，再选择创建 Job 或同步任务状态。
3. **建议构建的心智模型**：

   > 本函数组织“取两份记录 → 逐条配对 → 按状态选择动作”。子函数负责兑现查询、创建或写回；读清一次子调用后，回到本函数继续使用其结果。

4. **调用代码**（`_periodic_reconcile_loop:151`）：

   ```python
   await self._reconcile_once()
   ```

## 本场景的输入与输出

显式输入只有 `self`；任务和 Job 由本函数查询。沿用一个教学场景：**Gateway 返回一条排队任务 r1，集群中没有对应 Job**。假定查询成功、模板有效且创建额度允许，没有实际运行集群。

- **输入到本次检查的数据**：`rollouts` 含 r1，`jobs=[]`；r1 的 `status.state` 为 `QUEUING`。
- **本例动作**：给 r1 找不到 Job，委派 `_create_job(rollout)`；正常完成后继续处理其余任务。
- **本函数返回值**：整轮正常结束返回 `None`；创建 Job 或更新任务状态是过程中产生的副作用。

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

### 从 Job 查询返回：按名称建立索引（173 行）

现在已经取得 `jobs`，接着执行本函数自己的数据整理：

```python
jobs_by_name = {job.get("metadata", {}).get("name", ""): job for job in jobs}
```

它把列表整理为“Job 名称 → 对应 Job 数据”的字典。比如 `jobs` 中有 `metadata.name` 分别为 `job-a`、`job-b` 的两项，整理后就是两个键分别指向原来的两份数据；没有重新查询集群，也没有复制出新的 Kubernetes Job。

后面的循环先算出某条 rollout 对应的 `job_name`，再用 `jobs_by_name.get(job_name)` 找 Job。本段属于 `_reconcile_once` 自身，继续在父卡中读，不另建函数卡；具体匹配行为尚待用户反馈。

<a id="missing-job-branch"></a>

### 当前段落：没找到 Job 时，为什么有两种处理

先接回这一条任务的查找位置：

```python
job_name = rollout.status.k8s_job_name or build_job_name(rollout.rollout_id)
job = jobs_by_name.get(job_name)
```

Job 名优先使用 Gateway 任务记录中已有的 `status.k8s_job_name`；该字段没有值时，`build_job_name` 根据任务 ID 生成名字，例如 `r1` 对应 `agl-rollout-r1`。因此名字不一定直接由查询返回。

`job is None` 表示这次取得的 Job 索引中没有对应项。任务 `rollout` 本身仍在手上，接下来按它原先的状态决定动作：

| 当前 rollout 状态 | 对缺少 Job 的解释 | 代码做什么 |
| --- | --- | --- |
| `QUEUING` | 还在排队，没有对应 Job 可以是尚未创建 | 调用 `await self._create_job(rollout)`，等创建函数返回，随后处理下一条任务 |
| `RUNNING` | 任务记录已是运行中，但对应 Job 没找到 | 请求把 Gateway 中这条任务更新为 `FAILED`，原因记为 `Job disappeared` |

本轮查询只选择 `QUEUING / RUNNING`。排队分支里的 `continue` 已经跳到下一次 `for rollout in rollouts`，所以能到达后面的警告和状态写回的，在本场景中就是 `RUNNING`。代码虽没写 `else`，控制流已作出这个分流。

`await self._create_job(rollout)` 等待的是这个创建函数返回，不是在这里等待 Agent 把整个任务执行完。

状态写回调用中的三个输入分别是：

- `rollout.rollout_id`：定位 Gateway 中要更新的那条任务。
- `state=RolloutState.FAILED`：请求写入的新状态。
- `error_message="Job disappeared"`：保存失败原因。

Job 已找不到，仍然可以按任务 ID 更新 Gateway 的记录。这里的 `_patch_status` 使用 Gateway 客户端；它不要求先找到一个可操作的 Kubernetes Job。

**当前记录方式**：父卡保留“缺少 Job + 原状态 → 选择动作”。用户已先进入 [_create_job](../../02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._create_job.md)，随后独立阅读 [_patch_status](../../02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._patch_status.md)；现在回到本段核对为什么会调用它。

Kubernetes 的这次 Job 查询只按 namespace 和标签筛选，并没有限定 Job 必须正在运行。符合条件、已经完成或失败但尚未清理的 Job 也可能被查到。

<a id="why-patch-a-running-rollout"></a>

### 回到调用条件：已经是 RUNNING，为什么还要 PATCH？

进入当前这次失败回写，需要两个条件同时成立：**本轮查不到对应 Job，且 Gateway 的任务记录是 RUNNING**。`RUNNING` 来自 Gateway 保存的状态，不是这次向 Kubernetes 查询后确认的运行事实。

下面节选真实分支，仅省略警告日志；注意外层条件与两个 `continue`：

```python
if job is None:
    if rollout.status.state == RolloutState.QUEUING:
        await self._create_job(rollout)
        continue
    await self._patch_status(rollout.rollout_id, state=RolloutState.FAILED, error_message="Job disappeared")
    continue
```

- 缺少 Job 且任务为 `QUEUING`：尝试创建 Job，随后处理下一条 rollout。同一轮不会再落到这里的失败回写。
- 缺少 Job 且任务为 `RUNNING`：两边记录不一致。源码选择向 Gateway 登记 `FAILED`，避免任务一直保留为 RUNNING；写入失败时不能视为已经改成功。
- 找得到 Job：跳过整个 `if job is None`，继续读取这个 Job 的状态。

“已经完成”需要说明完成的是哪一层：

| 完成的对象 | 本函数怎样处理 |
| --- | --- |
| `_create_job` 调用已返回 | 表示创建函数返回；不表示 Agent 任务已完成，接着执行上面的 `continue` |
| Kubernetes Job 已成功，且对象仍能查到 | 走下方已有 Job 的分支，读到成功状态后用 `_patch_status` 向 Gateway 同步 `SUCCEEDED` |
| Gateway 的 rollout 已记录为 `SUCCEEDED` | 下一轮的 `QUEUING / RUNNING` 查询不会选中它 |

完成的 Job 对象可以继续保留供查询，完成并不自动等于 `job is None`。如果 Job 实际已完成但对象已被清理，而 Gateway 仍记为 RUNNING，这段缺失分支仍会请求标记失败；它无法仅凭“查不到 Job”还原此前是否成功。

本轮先理解上述条件与交接，Job 的具体终态字段仍留在下方骨架，尚未逐项阅读。[本次问题与说明](../../04-flow.md#why-patch-a-running-rollout)。

<a id="existing-job-reading-map"></a>

### 找到 Job 后：按三个阅读段接续

用户已理解缺失 Job 时的分流，接着反馈后半段的状态修改绕、重复，要求考虑怎样拆分。下面是助手据源码整理的阅读导航，尚不表示用户已理解各段；完整连续代码仍见[上方骨架](#parent-skeleton)。三段均属于本函数，只有实际调用的 [_patch_status](../../02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._patch_status.md) 使用已有子卡。

**入口条件：`job is not None`。** 可以继续用任务 r1 作教学场景：某次后续协调已查到它的 Job，Gateway 此时仍可能登记为 QUEUING。这是接续例子，不是先前那轮创建调用会直接执行到这里。

先区分两个名字相近的数据：

| 数据 | 来自哪里、在这里表示什么 |
| --- | --- |
| `rollout.status.state` | 前面从 Gateway 取得的任务状态；本轮是 QUEUING 或 RUNNING |
| 局部变量 `state` | 由本轮 Job 信息判断出的结果；在这段代码里是 `None`、SUCCEEDED 或 FAILED |

给局部 `state` 赋值还没有更新 Gateway。这里的 `None` 表示本段未判断出终态，不是 Kubernetes 的一个状态值，也不保证 Pod 已经运行。

| 局部编号与源码入口 | 只解决的问题 | 交接与停止位置 |
| --- | --- | --- |
| **① 归纳 Job 的结果**：[191–213 行](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L191) | 从 `job_status` 得到 `state`，必要时附上 `error_message` | 先看条件判断，再看计数兜底；到 `state` 的三种可能值为止，尚不展开 PATCH |
| **② 尚未判断出终态**：[215–223 行](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L215) | `state is None` 时，Gateway 是否还停在 QUEUING？ | 若是则请求写 RUNNING；若已是 RUNNING 则不写。随后 `continue`，不会进入③ |
| **③ 已判断出终态**：[225–240 行](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L225) | 怎样把 SUCCEEDED/FAILED 写回 Gateway？ | 先处理 QUEUING → SUCCEEDED 所需的中间转换，再共用末尾 PATCH 写结果；补写失败则 `continue` |

执行关系是 **① → 按 `state` 选择②或③**。编号仅用于本函数内部阅读，与 scope 中的全局 [1]–[5] 不同。

187–189 行的 `attempt_id` 是随状态一起回写的关联标识。先保留它的来处与去向，读取标签和默认值不单独拆卡。`error_message` 的字符串拼接也留到①的失败情况再看。

<details>
<summary>为什么看起来重复：两种结果依据与两次 RUNNING 的区别</summary>

- ①先看 `conditions`；若仍未得出 `state`，再用 `succeeded/failed` 计数兜底。这是在不同字段中寻找依据，最后归纳到同一个局部变量。这里记录当前实现的判定方式，不把失败 Pod 计数与 Kubernetes Job 的 Failed 条件视为完全等价。
- ②写 RUNNING：已找到 Job，本轮尚未判断出终态，但 Gateway 还登记为 QUEUING。
- ③也可能先写 RUNNING：已经观察到成功，但 Gateway 还登记为 QUEUING。Gateway 的规则不允许直接 QUEUING → SUCCEEDED，因此先补 QUEUING → RUNNING，成功后才写 SUCCEEDED。QUEUING → FAILED 则被允许直接发生。
- 多处 `_patch_status` 复用相同的更新机制；各处的条件和目标状态不同，阅读时重点看“何时调用、写成什么、返回后去哪”，不重复展开 HTTP 与模型校验。

转换约束来自 Agent Lightning 的 [`schemas.py:87`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/schemas.py#L87)，由 [`patch_rollout:183`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/server/routes/rollouts.py#L183)检查；这是项目的任务状态规则。

</details>

**推荐下一处只读①。** 先选成功条件这一条简单路径，看 `job_status` 怎样使局部 `state` 变成 SUCCEEDED，再补失败和计数兜底；到准备进入②/③时停。三段的完整逐项讲解随实际问题补充，本次只建立关系与入口。[拆分讨论](../../04-flow.md#existing-job-reading-segmentation)。

<a id="return-to-caller"></a>

### 本函数读完，返回调用方

| 返回哪里 | 已完成什么，接下来是什么 |
| --- | --- |
| [_periodic_reconcile_loop:151](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L151) | 本轮逐项检查正常结束，返回 `None`；外层继续等待下一周期或停止信号 |

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

## 尚不清楚

- 用户已区分 Gateway 与 Kubernetes 两类服务，见 [_get_k8s_api 的反馈](../../02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._get_k8s_api.md#two-services-understood)；任务对象与 Job 的字段、关联方式和具体客户端变量仍需继续连接。
- 已有 Job 的终态判断、状态转换、写入失败与并发事件观察怎样协调，尚未展开。
- HTTP 参数编码、模型转换、创建与写回的内部机制按需回查。
- 缺失 Job 时的两个处理分支已有个人复述；“报错”具体指状态登记、调用返回后继续循环，以及已完成任务的几种路径，仍只由助手说明。

<details>
<summary>来源、历史与验证边界</summary>

- 固定版本：`0029dbb35c467799d35fee81d15d80264b0d1bd3`。骨架覆盖 `_reconcile_once` 的全部主要业务分支；Job 状态提取细节见原函数，未编造额外辅助函数。
- 返回字段依据 [`_query_rollouts`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L348) 和同版本 [`schemas.py`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/schemas.py)。
- [修改前完整卡片](2026-11-03-reconcile-once-before-breadcrumbs.md)保留此前分段、例子与来源；更早的[详细说明](2026-11-03-reconcile-once-before-segmentation.md)继续保留。
- [原始技术讨论](../../04-flow.md#query-rollouts-and-k8s-boundary) · [面包屑 reference 核对](../../04-flow.md#breadcrumb-reference-confirmation) · [本次按 reference 修改](../../04-flow.md#breadcrumb-card-applied)。
- 骨架与跳转的整理不计为新增理解；当前已按用户要求独立进入 `_query_rollouts`，见[本轮记录](../../04-flow.md#query-rollouts-card-start)，仍无真实服务运行。
- [名称索引与缺失 Job 分支的本轮讨论](../../04-flow.md#missing-job-branch)：依据同版本 175–186 行；`build_job_name` 从 38 行开始，`_patch_status` 从 362 行开始。

</details>
