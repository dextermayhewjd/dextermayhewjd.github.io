> 历史快照：2026-11-03，将通用 Kubernetes 基础说明集中到项目 k8s/ 目录之前。当前函数卡保留接口场景与返回导航。

# APIObject.async_list（Job 查询场景）

> **调用链面包屑**：[Step 000 范围](../../01-scope.md) · [短期函数索引](../../02-short-term-memory/overview.md) → [_reconcile_once](../../02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#call-list-jobs) → **Job.async_list（继承自 APIObject）**

- 实现来源：[`kr8s/_objects.py:911`](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_objects.py#L911)，`APIObject.async_list`；`Job` 定义在同文件 1993 行，继承此方法。
- 版本：Agent Lightning 固定提交 `0029dbb3` 的 `uv.lock` 锁定 `kr8s==0.20.15`；本次按对应发布标签核对，未安装或运行库。
- 首次接触：Step 000，2026-11-03，父函数的 Job 查询语句。
- 最近认识更新：用户提出模块来源、返回内容、namespace 和 label selector 的疑问；下面为助手核对的接口说明，尚待反馈。

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

### 先找到 k8s_objects 和 Job 的来路

当前文件第 26 行导入：

```python
from kr8s.asyncio import objects as k8s_objects
```

- `kr8s`：第三方 Kubernetes Python 客户端库。
- `kr8s.asyncio.objects`：它提供异步资源接口的模块，导出 `Job`、`Pod`、`Service` 等资源类。
- `as k8s_objects`：本文件给模块取的别名；所以 `k8s_objects.Job` 就是这里导出的 `Job` 类。

`Job` 类对应 Kubernetes 的 Job 资源，用于组织在 Pod 中运行到完成的工作。Python 中的 `Job` 对象是库对集群资源的封装。这个类声明资源类型为 `Job`、API 版本为 `batch/v1`，本例通过类方法查询已有资源。

### 三个实参各做什么

| 实参 | 本例来源与含义 |
| --- | --- |
| `namespace=self._namespace` | 来自 `config.k8s_runner.namespace`，仓库默认 `"default"`。namespace 是 Kubernetes 资源的命名作用域；本次只查指定作用域内的 Job |
| `label_selector=MANAGED_BY_SELECTOR` | 常量为 `"app.kubernetes.io/managed-by=agentlightning"`。要求 Job 的 `metadata.labels` 中，这个键的值等于 `agentlightning` |
| `api=api` | 使用前一步 `_get_k8s_api()` 返回的 Kubernetes 客户端；左侧是参数名，右侧是父函数的局部变量 |

namespace 与标签条件同时生效。下面是假设集群已有三份 Job 的教学例子：

| Job | namespace | `app.kubernetes.io/managed-by` | 本次是否选中 |
| --- | --- | --- | --- |
| job-a | default | agentlightning | 是 |
| job-b | default | other | 否：标签不同 |
| job-c | experiments | agentlightning | 否：namespace 不同 |

Job 上的标签形状可理解为以下 `metadata` 节选：

```yaml
metadata:
  name: job-a
  namespace: default
  labels:
    app.kubernetes.io/managed-by: agentlightning
```

### async_list 给出什么，jobs 最后装什么

本方法是异步生成器。`async for` 每次取得一个符合条件的对象；列表推导式把所有取到的数据收集完，才赋给 `jobs`。

本例调用没有开启库的 `raw=True` 模式，流程是：

```text
Job.async_list(...) -> async iteration -> Job instance -> .raw -> jobs list
```

`cast(k8s_objects.Job, job)` 是类型提示，运行时返回原对象；它不创建或转换 Job。`.raw` 才取出这个 Job 的字典式资源数据。核对的库版本中，具体类型是 `Box`，可按字典读取 `metadata`、`spec`、`status`。

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
| [_reconcile_once 的 Job 列表查询处](../../02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#call-list-jobs) | 列表推导式得到 `jobs` 后，173 行按 `metadata.name` 建立 `jobs_by_name`，用于给每条 rollout 找对应的 Job |

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

## 尚不清楚

- 模块别名、资源类、逐项得到的对象和最终 `jobs` 列表之间的区别，刚由助手说明，尚待反馈。
- Kubernetes 中实际 Job 与 Pod 的生命周期、库的 HTTP 分页与请求实现，本轮不展开。

<details>
<summary>源码依据与验证边界</summary>

- 本地导入、常量、配置与调用：Agent Lightning `k8s_reconciler.py:26、34、116、165–172`，`config/controller.yaml` 的默认 namespace；依赖版本来自 `uv.lock`。
- 对应版本的模块导出：[`kr8s/asyncio/objects.py`](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/asyncio/objects.py)。它从 `kr8s._objects` 导入并导出 Job。
- 类与接口：[`Job:1993`](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_objects.py#L1993)、[`APIObject.async_list:911`](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_objects.py#L911)、[`.raw:133`](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_objects.py#L133)。
- 默认对象返回：[`Api.async_get:509`](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_api.py#L509) 的 `raw=False`，后续按资源类构造实例；通用接口也支持原始字典模式，本例未使用。
- [本次阅读与原始问题](../../04-flow.md#job-listing-interface)。本轮只读本地与发布版库源码，未安装依赖、查询集群或创建 Job。

</details>
