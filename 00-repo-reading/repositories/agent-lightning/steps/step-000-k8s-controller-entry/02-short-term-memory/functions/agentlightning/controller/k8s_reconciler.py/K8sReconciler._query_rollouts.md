# K8sReconciler._query_rollouts

> **调用链面包屑**：[Step 000 范围](../../../../../01-scope.md) · [短期函数索引](../../../../overview.md) → [_reconcile_once](K8sReconciler._reconcile_once.md#call-query-rollouts) → **_query_rollouts**

- 源码：[k8s_reconciler.py:348](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L348)。
- 首次接触：Step 000 的数据来源讨论；2026-11-03 首次独立建卡并开始阅读。
- 最近认识更新：2026-11-03，用户已表述“组织状态条件 → 向 Gateway 发送 GET → 将 JSON 各项转为 Rollout → 返回列表”的链条；仍需校准“按状态筛选”与“仅返回状态”的区别。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`_reconcile_once` 开始一轮检查时，先从 Gateway 取得需要处理的任务。
2. **具体内容**：把状态筛选与数量上限组织成 HTTP 查询参数，发送 GET 请求，检查响应，并把返回 JSON 中的每项转换成 `Rollout` 对象。
3. **建议构建的心智模型**：

   > 状态与数量条件 → Gateway 查询 → `list[Rollout]`。每个对象是一条任务记录，状态只是其中一个字段。

4. **调用代码**（`_reconcile_once:163`）：

   ```python
   rollouts = await self._query_rollouts(
       state_in=[RolloutState.QUEUING, RolloutState.RUNNING],
       limit=500,
   )
   ```

## 本场景的输入与输出

**输入**是上面的两个关键字参数，以及 `self` 持有的 Gateway HTTP 客户端 `self._api`。函数的 `limit` 默认值为 50，本次调用显式传入 500。

| 传入值 | 形成的查询条件 |
| --- | --- |
| `[RolloutState.QUEUING, RolloutState.RUNNING]` | `state_in=queuing&state_in=running` |
| `500` | `limit=500` |

组合起来相当于请求：

```text
GET /api/rollouts?state_in=queuing&state_in=running&limit=500
```

**`state_in` 决定“选出哪些任务”，返回值包含“选中任务的完整记录”。** 这里执行一次查询，拿回的数据同时带有任务标识、输入、配置和状态；状态是筛选依据，也是返回对象中的字段。

**输出**是 `list[Rollout]`。教学场景：假设 Gateway 成功返回一条符合类型定义的任务记录，字段节选为 `rollout_id="r1"`、`input={"question": "1 + 1 = ?"}`、`status.state="queuing"`。转换后：

| 读取返回值 | 本例结果 |
| --- | --- |
| `len(rollouts)` | `1` |
| `rollouts[0].rollout_id` | `"r1"` |
| `rollouts[0].input` | `{"question": "1 + 1 = ?"}` |
| `rollouts[0].status.state` | `RolloutState.QUEUING` |

这里只节选相关字段；完整响应还包含 `config`、状态时间等定义所需字段。本例是静态推导，没有发出真实请求。服务端没有匹配任务时返回空列表，正常转换结果也为 `[]`。

### 函数自身的完整主体

以下为源码主体，保留实际顺序：

```python
params = httpx.QueryParams()
for state in state_in:
    params = params.add("state_in", state.value)
params = params.add("limit", limit)
response = await self._api.get("/api/rollouts", params=params)
response.raise_for_status()
return [Rollout.model_validate(item) for item in response.json()]
```

- **构造参数**：`state.value` 将枚举变成 `"queuing"`、`"running"`；同名 `state_in` 可出现多次。`add` 返回新的参数对象，所以每次赋回 `params`。
- **查询 Gateway**：`self._api.get` 发出请求，`await` 等待响应。这里读取任务记录；Kubernetes 客户端由调用方的下一行另行取得。
- **检查并转换**：`raise_for_status()` 在响应状态不成功时抛出异常；正常路径解析 JSON，对每项调用 `Rollout.model_validate`，得到任务对象列表。HTTP 与字段校验的内部机制暂按库接口理解。

### 读完返回哪里

| 返回入口 | 接住什么，接着执行什么 |
| --- | --- |
| [_reconcile_once 的任务查询处](K8sReconciler._reconcile_once.md#call-query-rollouts) | 163 行将 `list[Rollout]` 赋给 `rollouts`；随后 164 行调用 `_get_k8s_api()`，准备读取集群中的 Job |

本函数的返回边界到任务列表为止。任务与 Job 的匹配、创建或状态更新继续由父函数组织。

关于“前面为什么不需要获取 api”的后续澄清见 [_get_k8s_api 的两个客户端对照](K8sReconciler._get_k8s_api.md)：本函数直接使用已经保存的 Gateway 客户端 `self._api`，后续取得的局部 `api` 用于 Kubernetes。

## 我的直接表述（原话）

此前在父函数中提出的疑问（节选）：

> 这里是在拿rollout?
> 是否需要单独看一下这里的query rollouts?
> 这个函数?
> 还是说当前先记住返回的是每一个rollout的状态?

完整原话仍保存在 [父函数卡](K8sReconciler._reconcile_once.md#my-statements)。

<a id="first-retelling"></a>

<details>
<summary>2026-11-03：第一次复述查询与返回的过程</summary>

> 我简单的理解为
> 这里在做的事情是询问目前
> 在队伍里的排队的和正在跑的rollout的状态?
> 然后和返回的是每一个rollout的状态?
> 是我目前听你说的理解
> 简单来说是把这里的state in的这两个状态组织为查询函数
> 通过向gateway发送get请求
> 然后json中将每一项转化为rollout 返回列表是我的理解
>
> 这一步在做的内容更多的像是先做一个这样子查询方法?
> 来获得一下状态?

</details>

助手据源码核对：用户已经说出了参数组织、GET 请求与逐项转换后返回列表的过程。还需把“返回每个 rollout 的状态”细化为“按状态筛选，并返回每条符合条件的完整 Rollout 记录”。这里是在执行现有查询函数，实际取得记录；这项措辞校准尚待后续反馈。

## 尚不清楚

- 用户已复述查询与转换链条；“状态用于筛选，返回完整任务记录”的区别刚由助手补充，尚待反馈。
- Gateway 内部怎样维护任务、HTTP 客户端的传输机制及 Pydantic 校验规则，当前未展开。

<details>
<summary>来源与验证边界</summary>

- 固定版本：`0029dbb35c467799d35fee81d15d80264b0d1bd3`。本函数从 348 行开始；调用处 163 行；`Rollout` 和 `RolloutState` 定义位于同版本 `agentlightning/schemas.py`。
- 额外静态核对：`agentlightning/client.py` 中 `AgentLightningAsyncClient` 继承 `httpx.AsyncClient`；服务端 `server/routes/rollouts.py:126` 按状态筛选并截取 `limit`，本轮仅用于核对返回合同。
- [原先的返回合同问题](../../../../../../step-000-k8s-controller-entry/04-flow.md#query-rollouts-and-k8s-boundary) · [本次独立建卡与阅读](../../../../../../step-000-k8s-controller-entry/04-flow.md#query-rollouts-card-start)。
- [首次复述与筛选／返回的校准](../../../../../../step-000-k8s-controller-entry/04-flow.md#query-rollouts-first-retelling)。
- 示例响应是教学假设，只核对代码与类型定义，未运行 Gateway 或 Kubernetes。

</details>
