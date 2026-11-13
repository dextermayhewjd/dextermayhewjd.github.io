# APIObject.async_list（Job 查询场景）

> **调用链面包屑**：[Step 000 范围](../../../../../step-000-k8s-controller-entry/01-scope.md) · [累计函数索引](../../../overview.md) → [_reconcile_once](../../agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#call-list-jobs) → **Job.async_list（继承自 APIObject）**

- 实现来源：[`kr8s/_objects.py:911`](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_objects.py#L911)，`APIObject.async_list`；`Job` 定义在同文件 1993 行，继承此方法。
- 版本：Agent Lightning 固定提交 `0029dbb3` 的 `uv.lock` 锁定 `kr8s==0.20.15`；本次按对应发布标签核对，未安装或运行库。
- 首次接触：Step 000，2026-11-03，父函数的 Job 查询语句。
- 最近认识更新：2026-11-03，用户已概括通过 Kubernetes API 查询已有 Job，并按 namespace 和标签筛选；异步迭代、对象与 `.raw` 的具体关系尚未单独复述。

- 继承来源：[Step 000 的完整原记录](../../../../../step-000-k8s-controller-entry/02-short-term-memory/functions/kr8s/_objects.py/APIObject.async_list.md)。本次完整继承到 Step 001；首次接触、最近认识更新、原话与未知保持原值。

- 本次继承（Step 002）：[Step 001 的完整来源记录](../../../../../step-001-watch-job-events/03-long-term-memory/functions/kr8s/_objects.py/APIObject.async_list.md)。此前继承和调取说明保留历史语境；原话、未知、首次接触与最近认识更新保持原值。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`_reconcile_once` 已取得 Kubernetes 客户端，现在要查询集群中由 Agent Lightning 管理的 Job。
2. **具体内容**：通过 `Job` 类调用继承的方法，按 namespace 和标签条件查询，提供可异步迭代的资源对象；当前未传 `raw=True`，逐项得到 `Job` 对象。
3. **建议构建的心智模型**：

   > `Job.async_list(...)` 提供符合条件的 Job 对象；父函数用 `async for` 逐项取得它们，把每个对象的 `.raw` 收集到普通 Python 列表 `jobs`。

4. **调用代码**（Agent Lightning `k8s_reconciler.py:165–172`）：

   ```python
   jobs = [
       cast(k8s_objects.Job, job).raw
       async for job in k8s_objects.Job.async_list(
           namespace=self._namespace,
           label_selector=MANAGED_BY_SELECTOR,
           api=api,
       )
   ]
   ```

## 本场景的输入与输出

### 本次传入什么

基础概念分别见 [kr8s 与资源对象](../../../../../../../kubernetes/90-clients/python/kr8s.md)、[Job 与 Pod](../../../../../../../kubernetes/03-workloads/pods-and-jobs.md)、[Namespace](../../../../../../../kubernetes/02-resource-model/namespaces.md)、[Labels 与 Selector](../../../../../../../kubernetes/02-resource-model/labels-and-selectors.md)。看清当前需要的概念后，回到下面的调用合同。

| 实参 | 本次取值与作用 |
| --- | --- |
| `namespace=self._namespace` | 仓库默认 `"default"`，限定查询范围 |
| `label_selector=MANAGED_BY_SELECTOR` | `"app.kubernetes.io/managed-by=agentlightning"`，筛选管理标签 |
| `api=api` | 使用前一步取得的 Kubernetes 客户端 |

这里传入的是查询条件：Job 必须位于指定 namespace，且标签匹配，才会被选中。该查询不会修改 Job 的 namespace 或标签。

贯穿本卡的教学情景：假设集群中只有一个 Job `job-a` 同时满足上述 namespace 和标签条件。它会被本次调用返回；不同范围与标签的对照例子放在 Labels 基础说明中。

这组查询条件没有限制 Job 必须正在运行；已经完成或失败但尚未清理的匹配 Job 也可能被列出。

### async_list 给出什么，jobs 最后装什么

本方法是异步生成器。`async for` 每次取得一个符合条件的对象；列表推导式把所有取到的数据收集完，才赋给 `jobs`。

本例调用没有开启库的 `raw=True` 模式，流程是：

```text
Job.async_list(...) -> async iteration -> Job instance -> .raw -> jobs list
```

本次收集每个 Job 的 `.raw` 字典式资源数据。`cast` 的作用、Job 实例与 `.raw` 的区别集中在 [kr8s 基础说明](../../../../../../../kubernetes/90-clients/python/kr8s.md)中；当前返回合同仍是逐项得到 Job，再由父函数收集数据。

因此，父调用在值的处理上可以写成下面的等价形式：

```python
jobs = []
async for job in k8s_objects.Job.async_list(
    namespace=self._namespace,
    label_selector=MANAGED_BY_SELECTOR,
    api=api,
):
    jobs.append(job.raw)
```

教学例子最终只有 `job-a` 被选中，因此 `jobs` 长度为 1，第一项是它的 `.raw` 数据；没有符合条件的 Job 时得到 `[]`。这是构造情景下的静态说明，没有向集群发请求。

### 读完返回哪里

| 返回位置 | 接住什么，接下来做什么 |
| --- | --- |
| [_reconcile_once 的名称索引处](../../agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#index-jobs-by-name) | 列表推导式得到 `jobs` 后，173 行按 `metadata.name` 建立 `jobs_by_name`，用于给每条 rollout 找对应的 Job |

## 我的直接表述（原话）

本次问题节选：

> 这里的k8s objects是什么?
> 以及async list反蝴蝶是什么?
> 还有这里的namespace和label slector什么的?
> 是否能够给出这里的解释呢?
>
> 或者说
> 这里的k8s_objects.Job又是哪里来的呢?

本轮据上下文将第二行理解为询问 `async_list` 的返回内容。以上是问题原话，不视为已经掌握库接口。

<a id="filter-purpose-understood"></a>

随后用户复述：

> 那么我们继续吧
> 也就是说这里通过k8s的api
> 来查询现有的job
>
> 然后通过设置这里的namespace还有label来返回 通过山选之后特定的jobs对吗?

这项查询用途的概括与源码一致。助手进一步明确两个条件共同生效，设置的是查询条件；循环取得 Job 对象后，父函数收集其 `.raw` 数据。后一句关于具体返回形态仍是助手补充。

## 尚不清楚

- 用户已说明按 namespace 和标签查询已有 Job 的用途；模块别名、资源类、逐项对象与最终 `.raw` 列表的具体关系尚未单独复述。
- Kubernetes 中实际 Job 与 Pod 的生命周期、库的 HTTP 分页与请求实现，本轮不展开。

<details>
<summary>源码依据与验证边界</summary>

- 本地导入、常量、配置与调用：Agent Lightning `k8s_reconciler.py:26、34、116、165–172`，`config/controller.yaml` 的默认 namespace；依赖版本来自 `uv.lock`。
- 对应版本的模块导出：[`kr8s/asyncio/objects.py`](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/asyncio/objects.py)。它从 `kr8s._objects` 导入并导出 Job。
- 类与接口：[`Job:1993`](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_objects.py#L1993)、[`APIObject.async_list:911`](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_objects.py#L911)、[`.raw:133`](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_objects.py#L133)。
- 默认对象返回：[`Api.async_get:509`](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_api.py#L509) 的 `raw=False`，后续按资源类构造实例；通用接口也支持原始字典模式，本例未使用。
- [本次阅读与原始问题](../../../../../step-000-k8s-controller-entry/04-flow.md#job-listing-interface)。本轮只读本地与发布版库源码，未安装依赖、查询集群或创建 Job。
- [查询用途的理解反馈与返回父函数](../../../../../step-000-k8s-controller-entry/04-flow.md#job-filter-purpose-understood)。
- [基础内容集中前的完整卡片](../../../../../step-000-k8s-controller-entry/references/history/2026-11-03-job-listing-before-k8s-basics.md)保留原有说明；[本轮资料分工](../../../../../step-000-k8s-controller-entry/04-flow.md#k8s-basics-folder)记录迁移原因与未读卡片的撤回。

</details>
