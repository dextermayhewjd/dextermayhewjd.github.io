# K8sReconciler._get_k8s_api

> **调用链面包屑**：[Step 000 范围](../../../../../../step-000-k8s-controller-entry/01-scope.md) · [累计函数索引](../../../../overview.md) → [_reconcile_once](K8sReconciler._reconcile_once.md#call-get-k8s-api) → **_get_k8s_api**

- 源码：[k8s_reconciler.py:121](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L121)。
- 首次接触：Step 000，2026-11-03；本轮独立查看两个客户端的区别。
- 最近认识更新：2026-11-03，用户已明确区分 Gateway 的 API 与 Kubernetes 服务的 API；具体变量对应和缓存机制尚未单独复述。

- 继承来源：[Step 000 的完整原记录](../../../../../../step-000-k8s-controller-entry/02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._get_k8s_api.md)。本次完整继承到 Step 001；首次接触、最近认识更新、原话与未知保持原值。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：父函数已经取得 Gateway 中的任务记录，现在需要访问 Kubernetes，先取得相应客户端。
2. **具体内容**：检查 `self._k8s_api`；首次正常调用时通过 `kr8s.asyncio.api()` 取得客户端并缓存，以后返回已缓存的对象。
3. **建议构建的心智模型**：

   > 取到并复用“访问 Kubernetes 的客户端”。拿到它之后，父函数再通过这个客户端查询 Job。

4. **调用代码**（`_reconcile_once:164`）：

   ```python
   api = await self._get_k8s_api()
   ```

## 本场景的输入与输出

显式输入只有 `self`。把正常创建出的 Kubernetes 客户端记为 `K`，这是教学代号，未实际创建客户端。

| 调用前 | 本函数行为 | 返回值及保存结果 |
| --- | --- | --- |
| `self._k8s_api is None` | 等待 `kr8s.asyncio.api()` | 保存 `self._k8s_api = K`，返回 `K` |
| `self._k8s_api` 已是 `K` | 直接复用 | 返回同一个 `K` |

完整函数主体：

```python
if self._k8s_api is None:
    self._k8s_api = await kr8s.asyncio.api()
return self._k8s_api
```

### 与前一次查询的关系

`_query_rollouts` 直接使用已保存的 Gateway 客户端 `self._api`；本函数返回的是 Kubernetes 客户端 `self._k8s_api`。两类服务与变量对应见 [本项目的客户端对照](../../../../../../../references/kubernetes-integration.md#two-clients)；通用概念见 [Kubernetes API Server](../../../../../../../../kubernetes/01-architecture/api-server.md)。

### 读完返回哪里

| 返回入口 | 接住什么，接着执行什么 |
| --- | --- |
| [_reconcile_once 的客户端获取处](K8sReconciler._reconcile_once.md#call-get-k8s-api) | 164 行把返回对象赋给局部变量 `api`；随后 `Job.async_list(..., api=api)` 使用它列出 Kubernetes 中的 Job |

<a id="my-statements"></a>

## 我的直接表述（原话）

> 好的 我理解了
> 那么继续吧
>
> 看一下这里的api
> 为什么这里的api 在刚才哪里并不需要呢?
> 我之前的理解是这里的query是通过向k8s发送请求的?
>
> 也挺奇怪的
> 刚才就在询问k8s看情况吧?
> 还是说刚才其实并不需要呢?

这段保留此前对查询目标的疑问：用户曾把 Gateway 查询理解为访问 Kubernetes。

<a id="two-services-understood"></a>

随后用户表述：

> 我大概的理解是
> 这里首先是两个api
> 一个是gateway的api
> 一个是k8s服务的api
> 我可以这么理解吗？！

这项服务区分与源码一致。助手补充精确叫法：代码中保存的是分别访问这两类服务的客户端；`self._api` 对应 Gateway，`self._k8s_api` 及接住它的局部 `api` 对应 Kubernetes。变量映射是本轮补充，未记为用户已单独复述。

## 尚不清楚

- 两类服务的区分已有用户表述；具体变量对应、首次创建与后续复用的机制尚未单独复述。
- `kr8s` 从哪里读取集群连接配置、内部如何建立请求，以及配置失败的处理，尚未展开。

<details>
<summary>来源与验证边界</summary>

- 固定版本：`0029dbb35c467799d35fee81d15d80264b0d1bd3`；函数 121–124 行，父调用 164 行，构造器从 112 行开始。
- Gateway 客户端来源：[controller/__main__.py:17](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/__main__.py#L17)；`AgentLightningAsyncClient` 继承 `httpx.AsyncClient`。
- [本轮客户端区别与理解记录](../../../../../../step-000-k8s-controller-entry/04-flow.md#gateway-versus-k8s-client)。
- [用户对两类服务的理解反馈](../../../../../../step-000-k8s-controller-entry/04-flow.md#two-services-understood)。
- 表格按源码静态推导，没有创建客户端、访问集群或发送真实请求。

</details>
