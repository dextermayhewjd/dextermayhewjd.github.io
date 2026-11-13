> 链接维护说明：用户已撤回尚未接触就提前创建的函数卡；本文指向这些卡片的旧链接现改为固定版本源码。历史叙述保留。

> 历史快照：2026-11-03，用户反馈函数记录过密后，重排为三段阅读之前。原有说明、原话、未知与来源完整保留；当前使用同名短期函数卡。

# K8sReconciler._reconcile_once

- 源码定位：[`agentlightning/controller/k8s_reconciler.py:161`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L161)。
- 首次接触：Step 000，2026-11-03；阅读编号 [1]。用户已明确从本函数开始，外层周期循环先作调用背景。
- 最近认识更新：2026-11-03，用户提出对 `_query_rollouts` 的初步理解，并追问返回结构与 Kubernetes 边界；本轮校准尚未取得确认。此前迁移不计为新增理解。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`_periodic_reconcile_loop` 每次检查时调用，核对 Gateway 中的任务与 Kubernetes 中的 Job。
2. **具体内容**：查询排队和运行中的 rollout，列出当前管理范围内的 Job，按名字逐条匹配，再选择创建 Job 或更新任务状态。
3. **建议构建的心智模型**：

   > 对照“框架记录的任务”与“集群里的 Job”，处理两边需要协调的地方；一次调用检查一批任务，完成后回到周期循环。

4. **调用代码**（`_periodic_reconcile_loop:151`）：

   ```python
   await self._reconcile_once()
   ```

## 本场景的输入与输出

没有除 `self` 外的显式入参，任务与 Job 由本函数查询。下面是正常创建路径的教学场景节选，未实际运行：

| 输入条件 | 本函数的对应行为与返回 |
| --- | --- |
| Gateway 返回一条 `rollout_id="r1"`、状态为 `RolloutState.QUEUING` 的任务；集群查询结果中没有对应 Job | 调用 `await self._create_job(rollout)`，再继续检查其他任务；本轮正常结束返回 `None` |

这不是把 Job 作为返回值交给调用方。实际提交由 `_create_job` 完成；任务模板、创建额度与集群请求是否成功属于该子调用的条件。

### 1. 读取、匹配与选择动作

以下保留原 scope 的职责级教学裁剪，参数通常省略，类型转换和日志折叠；已有 Job 的状态分支由下表承接。

```python
# [1] _reconcile_once
rollouts = await self._query_rollouts(...)  # 查询 QUEUING / RUNNING 的任务
api = await self._get_k8s_api()
jobs = [job.raw async for job in k8s_objects.Job.async_list(...)]
jobs_by_name = {job.get("metadata", {}).get("name", ""): job for job in jobs}

for rollout in rollouts:
    job_name = rollout.status.k8s_job_name or build_job_name(...)
    job = jobs_by_name.get(job_name)

    if job is None:
        if rollout.status.state == RolloutState.QUEUING:
            await self._create_job(...)  # [2] 创建路径
            continue
        await self._patch_status(..., state=RolloutState.FAILED)  # [5] 共用出口
        continue

    ...  # 已有 Job：根据下面的状态分支，按需调用 [5] _patch_status
```

<a id="two-data-sources"></a>

#### 1.1 当前先看：从两边读取记录

本轮从 `k8s_reconciler.py:163–172` 开始。我们已经进入一次检查；外层的 `_periodic_reconcile_loop` 正在等待它完成。先只读取得 `rollouts` 和 `jobs` 的部分，后面的匹配与分支暂不展开。

下面按源码保留实参，分行展示；仅省去 `cast(k8s_objects.Job, job)` 的类型提示写法，仍取同一个对象的 `.raw`：

```python
rollouts = await self._query_rollouts(
    state_in=[RolloutState.QUEUING, RolloutState.RUNNING],
    limit=500,
)

api = await self._get_k8s_api()
jobs = [
    job.raw
    async for job in k8s_objects.Job.async_list(
        namespace=self._namespace,
        label_selector=MANAGED_BY_SELECTOR,
        api=api,
    )
]
```

| 变量 | 从哪里取得 | 本次装的是什么 |
| --- | --- | --- |
| `rollouts` | `_query_rollouts` 使用 Gateway 客户端 `self._api` 查询 | 最多 500 条状态为排队或运行中的 `Rollout` 对象，包含任务标识、配置与状态 |
| `api` | `_get_k8s_api` 取得 Kubernetes 客户端 | 访问集群的客户端；不是上一行查询 Gateway 所用的 `self._api` |
| `jobs` | Kubernetes 的 `Job.async_list` | 当前 namespace 中带 `app.kubernetes.io/managed-by=agentlightning` 标签的 Job；`.raw` 使列表保存 Job 字典 |

这里先后取得两份数据，没有创建 Job，也没有开始执行 Agent。第一份是框架记录的任务，第二份是集群中查到的 Job；`limit=500` 只出现在任务查询中。

##### 1.1.1 当前追问：是否先单独读 _query_rollouts

当前先核对这个辅助函数的调用合同，继续留在 `_reconcile_once` 主线。`_query_rollouts` 是本函数的第一项读取动作；`_reconcile_once` 的完整职责还包括读取 Job、匹配任务和 Job、创建或更新状态。

`_query_rollouts` 的核心实现是：

```python
response = await self._api.get("/api/rollouts", params=params)
response.raise_for_status()
return [Rollout.model_validate(item) for item in response.json()]
```

前面几行把传入的状态和数量上限整理成 `params`。这里请求的是 Agent Lightning Gateway 的业务接口，成功后把每项 JSON 转成 `Rollout` 对象。HTTP 参数编码与模型校验暂按现有库接口理解，需要研究查询失败或字段转换时再深入。

本次调用合同：**筛选 `QUEUING` / `RUNNING`，传入 `limit=500` → 返回 `list[Rollout]`**。返回列表中的每个对象包含：

| 本轮先需要的字段 | 含义 |
| --- | --- |
| `rollout.rollout_id` | 任务标识，后面用来关联 Job |
| `rollout.input` | Agent 任务输入 |
| `rollout.config` | 执行配置，例如 Job 模板和超时配置 |
| `rollout.status.state` | 当前状态，是对象中的一项字段 |

完整对象还包括 `is_train`、`metadata`，`status` 也有其他字段，本轮不逐项展开。不能将其简记为“返回每个 rollout 的状态列表”，因为后面的创建和匹配还需要标识与配置。

##### 1.1.2 当前代码中哪些直接关联 Kubernetes

| 当前操作 | 所属边界 |
| --- | --- |
| `_query_rollouts(...)` | 访问 Agent Lightning Gateway，取业务任务记录 |
| `_get_k8s_api()` | 通过 `kr8s.asyncio.api()` 获取并缓存 Kubernetes 客户端 |
| `k8s_objects.Job.async_list(...)` | 通过该客户端列出当前 namespace、指定管理标签的 Kubernetes Job |
| `.raw`、`jobs_by_name`、后面的匹配与条件判断 | Python 中读取和组织数据，不是额外的 Kubernetes 请求 |

后面的 `job.async_create()` 才会提交 Job 创建请求，届时从编号 [2] 进入。现在先建立 Gateway 任务记录与 Kubernetes Job 两份数据的区别。

**观察情景（教学构造，仅显示标识）**：Gateway 返回 `r1`、`r2` 两条任务；集群只查到与 `r1` 对应的 Job。暂未给出两条任务的具体状态。

**本轮问题：仅凭没有查到对应 Job，能立即把 `r2` 判为失败吗？还需要查看 `r2` 的哪项信息？**

这项观察问题尚未回答；用户先追问 `_query_rollouts` 的职责、返回结构和 Kubernetes 边界，本轮优先澄清这些问题。后续再进入 `jobs_by_name` 与逐条匹配，不把下方已准备的分支表视为用户已经理解。

### 2. 匹配后的四类情况

| 匹配后的情况 | 原实现的去向 |
| --- | --- |
| 找不到 Job，rollout 仍在排队 | `_create_job` 提交 Job；成功创建本身不立即改写 rollout 状态 |
| 找不到 Job，rollout 已登记为运行中 | `_patch_status` 标为失败，原因是 Job 消失 |
| Job 已存在且尚无终态 | 排队中的 rollout 更新为 `RUNNING`；原本已运行的任务继续等待 |
| Job 已完成或失败 | 按观测结果更新 rollout 的终态；排队中的任务若直接被观测为成功，会先尝试更新为 `RUNNING`，成功后再更新为 `SUCCEEDED` |

这里的 `RUNNING` 是 Agent Lightning 的任务状态；上述判断不等于逐一确认 Pod 内进程已开始执行。终态条件、计数回退及写入失败的细则尚未逐段阅读。

需要查看创建的已有说明时进入 [编号 2：_create_job](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L242)，读完返回上面的无 Job 分支。[5] `_patch_status` 目前仍按写回接口使用，后续阅读入口见 [scope](../../01-scope.md#read-5)。

<a id="my-statements"></a>

## 我的直接表述（原话）

2026-11-03，用户在首次查看开头两份数据后表示：

> 好的我来尝试理解一下吧
> 首先reconcile 的内容是这里的query rollouts?
> 这里是在拿rollout?
> 是否需要单独看一下这里的query rollouts?
> 这个函数?
> 还是说当前先记住返回的是每一个rollout的状态?
> 这里哪些内容是k8s直接有关的呢?

这是初步理解与疑问，不将问句改写成已经确认的结论。助手补充：查询任务是第一步，返回的是任务对象列表；状态只是其中字段，直接的 Kubernetes 访问从客户端获取与 Job 列表查询开始。用户对这项补充的理解尚未确认。

## 尚不清楚

- rollout 与 Job 的完整字段，以及 Job 命名和管理范围如何保证对应。
- 已有 Job 的终态判断、更新顺序及写入失败时的具体行为。
- 创建、状态回写与并发事件观察之间的协调细节。
- `_query_rollouts` 返回对象及 Gateway / Kubernetes 两条查询边界已提供助手解释，尚待用户反馈；HTTP 参数编码和模型转换内部未展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本：`0029dbb35c467799d35fee81d15d80264b0d1bd3`；调用处 `k8s_reconciler.py:151`，本函数从 `161` 开始。
- 原材料：scope 3.3 的 [迁移前快照](2026-11-03-scope-before-function-notes-move.md)。
- [原始讨论与迁移依据](../../04-flow.md#function-notes-out-of-scope)。
- [本次明确入口与两份数据的观察问题](../../04-flow.md#reconcile-once-start)。`_query_rollouts:348`、`_get_k8s_api:121` 与 `MANAGED_BY_SELECTOR:34` 仅作数据来源核对，尚未逐个展开内部机制。
- [本轮返回合同与 Kubernetes 边界的追问](../../04-flow.md#query-rollouts-and-k8s-boundary)。返回类型和字段依据 `k8s_reconciler.py:348–360`、`schemas.py` 中的 `Rollout` 与 `RolloutLifecycleStatus`，均为静态核对。
- 输入是教学构造的查询结果节选；行为来自静态源码核对，没有连接 Gateway、创建 Job 或运行训练。

</details>
