> 链接维护说明：用户已撤回尚未接触就提前创建的函数卡；本文指向这些卡片的旧链接现改为固定版本源码。历史叙述保留。

> 历史快照：2026-11-03，按用户确认的“完整骨架 + 函数间面包屑”修改前保存。此版以阶段折叠为主，现行卡片改为父函数骨架与下钻／返回导航。

# K8sReconciler._reconcile_once

- 源码：[k8s_reconciler.py:161](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L161)；本步编号 [1]。
- 首次接触：Step 000，2026-11-03。
- 最近认识更新：2026-11-03，用户提出任务查询、返回结构与 K8s 边界的疑问；助手校准尚待反馈。本次排版调整不改变认识状态。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：外层周期循环调用它，进行一轮任务检查。
2. **具体内容**：取得任务与 Job，为每条任务找到对应 Job，按两边的状态选择动作。
3. **建议构建的心智模型**：

   > 两份记录 → 逐项配对 → 决定创建 Job 或更新任务状态。

4. **调用代码**：

   ```python
   await self._reconcile_once()
   ```

## 本场景的输入与输出

显式输入只有 `self`；任务和 Job 由本函数查询。贯穿下面三段的教学例子是：**一条排队任务 r1，集群里还没有对应 Job**。假设查询成功，任务模板有效且创建额度允许；这是静态例子，没有运行集群。

| 本函数内的阶段 | 这一例子发生什么 | 源码位置 |
| --- | --- | --- |
| **1.1 取得两份记录（当前）** | 取得含 r1 的 `rollouts`，以及空的 `jobs` | 163–172 |
| **1.2 建立索引并配对** | `jobs_by_name` 为空，查找 r1 的 Job 得到 `None` | 173–177 |
| **1.3 按状态决定动作** | r1 排队且没有 Job，调用 `_create_job(rollout)` | 179–240 |

本函数会依次检查查回的任务；正常结束返回 `None`。Job 创建、任务状态写回是调用过程中产生的副作用。

<a id="two-data-sources"></a>

### 1.1 取得两份记录：当前只看这一段

教学裁剪：省略调用参数与 `cast` 类型提示，保留实际调用和返回结构。

```python
rollouts = await self._query_rollouts(...)
api = await self._get_k8s_api()
jobs = [job.raw async for job in k8s_objects.Job.async_list(...)]
```

- **`rollouts`**：Gateway 返回的任务对象列表。本次筛选 `QUEUING / RUNNING`，请求上限 500 条；每项带有 `rollout_id`、`status`，需要创建 Job 时还会用到 `input`、`config`。
- **`jobs`**：Kubernetes 中查到的 Job 字典列表，只取当前 namespace、带 Agent Lightning 管理标签的对象。

`self._api` 访问 Gateway；这里取得的局部 `api` 访问 Kubernetes。先保留这条边界。`_query_rollouts` 的 HTTP 参数编码和模型转换可以通过下方来源回查，当前不必同时展开。

**这一段的阅读目标**：分清“框架记录的任务”和“集群中查到的 Job”。随后才进入两者怎样配对。

<details>
<summary>1.2 建立索引并配对：读到这里时展开</summary>

以下是源码节选；最后的省略号代表对当前任务继续作状态判断。

```python
jobs_by_name = {job.get("metadata", {}).get("name", ""): job for job in jobs}
for rollout in rollouts:
    job_name = rollout.status.k8s_job_name or build_job_name(rollout.rollout_id)
    job = jobs_by_name.get(job_name)
    ...
```

沿用 r1：`jobs=[]` 得到 `jobs_by_name={}`。假设任务还没有记录 Job 名，`build_job_name("r1")` 得到 `agl-rollout-r1`，字典查询得到 `job=None`。

本段把两份集合缩小到**当前这一条 rollout 与它找到的 Job**。带着这对数据进入 1.3；还未创建或更新资源。

</details>

<details>
<summary>1.3 按状态决定动作：先走 r1 的创建路径，再逐个比较其他情况</summary>

r1 是排队任务且 `job=None`，走到：

```python
if job is None:
    if rollout.status.state == RolloutState.QUEUING:
        await self._create_job(rollout)
        continue
    ...
```

调用完成后，`continue` 进入下一条任务。`_create_job` 内部先当接口，需查看时打开[已有卡片](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L242)，看完回到本行。

后续每次只改变一个条件，用下表核对新的去向：

| 是否找到 Job | 还需要看什么 | 动作 |
| --- | --- | --- |
| 没找到 | rollout 为 `QUEUING` | 尝试创建 Job |
| 没找到 | rollout 为 `RUNNING` | 请求将任务标为失败，原因是 Job 消失 |
| 找到，尚无终态 | rollout 是否还在排队 | 排队任务请求更新为 `RUNNING`；已运行的继续等待 |
| 找到，已完成或失败 | Job 的观测结果 | 请求更新相应终态 |

排队任务若直接被观测为成功，源码先尝试补写 `RUNNING`，成功后再写 `SUCCEEDED`。这是后续状态转换细节，不要求第一遍同时记住。

这里的 `RUNNING` 是 Agent Lightning 的任务状态；源码这项判断并没有逐一检查 Pod 内进程是否已开始。写回通过 `_patch_status` 完成，内部暂按[编号 5 的接口](../../01-scope.md#read-5)使用。

</details>

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

## 尚不清楚

- 任务对象与 Job 的字段、关联方式，以及 Gateway / Kubernetes 两条查询边界的理解仍待反馈。
- 已有 Job 的终态判断、状态转换、写入失败与并发事件观察怎样协调，尚未展开。
- HTTP 参数编码、模型转换、创建与写回的内部机制按需回查。

<details>
<summary>来源、完整旧说明与验证边界</summary>

- 固定版本：`0029dbb35c467799d35fee81d15d80264b0d1bd3`；本函数从 161 行开始，调用方位于 151 行。
- 返回合同：[`_query_rollouts:348`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L348)；对象字段见同版本 [`schemas.py`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/schemas.py)。Kubernetes 客户端见 [`_get_k8s_api:121`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L121)。
- [完整旧说明](2026-11-03-reconcile-once-before-segmentation.md)：保留原始代码、字段表、K8s 边界说明和来源。本卡减少默认展开内容，不删除历史。
- [最初的函数记录迁移](../../04-flow.md#function-notes-out-of-scope) · [实际开始阅读](../../04-flow.md#reconcile-once-start) · [返回合同的追问](../../04-flow.md#query-rollouts-and-k8s-boundary)。
- [本次分段调整](../../04-flow.md#reconcile-memory-segmentation)：没有新增用户机制理解。原先的“缺少 Job 是否失败”问题延后至 1.3，不作当前阅读门槛。
- 示例由助手构造并按源码静态核对，没有连接 Gateway、Kubernetes 或运行训练。

</details>
