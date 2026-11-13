> 历史快照：2026-11-03，Kubernetes 基础与项目专属说明分开、按主题分层之前。本目录保留当时内容，不是当前通用基础入口。

# kr8s 与资源对象：模块、类、实例和 raw

[基础入口](README.md) · [Job 与 Pod](job-and-pod.md) · [回到 Job.async_list](../../../steps/step-000-k8s-controller-entry/02-short-term-memory/functions/kr8s/_objects.py/APIObject.async_list.md)

`kr8s` 是第三方 Kubernetes Python 客户端库。当前项目的 `uv.lock` 锁定 `0.20.15`；下面按对应版本源码整理。

## k8s_objects.Job 从哪里来

Agent Lightning 的导入语句是：

```python
from kr8s.asyncio import objects as k8s_objects
```

| 写法 | 对应什么 |
| --- | --- |
| `kr8s.asyncio.objects` | 导出异步资源类的模块，包括 Job、Pod、Service 等 |
| `k8s_objects` | 本文件给上述模块起的别名 |
| `k8s_objects.Job` | 代表 Kubernetes Job 资源的 Python 类 |
| 循环变量 `job` | 当前迭代得到的一个 Job 实例 |
| `job.raw` | 这个实例持有的字典式资源数据 |

源码中，`kr8s.asyncio.objects` 从 `kr8s._objects` 导出 `Job`；`Job` 继承 `APIObject`，`async_list` 方法来自这个父类。

## 类、实例与资源数据

`Job.async_list(...)` 通过类查询资源。当前调用使用默认的对象返回模式，`async for` 每次取得一个 Job 实例；父函数再用 `.raw` 读取它的资源数据。

```text
Job class -> async_list(...) -> Job instance -> .raw
```

核对版本中，`.raw` 返回的具体类型是 `Box`，支持按字典读取 `metadata`、`spec`、`status` 等字段。它不是向集群重新发起一次 Job 查询。

代码中的 `cast(k8s_objects.Job, job)` 来自 Python 的 `typing`，用于向类型检查器表达预期类型；运行时仍返回原对象。后面的 `.raw` 才是在读取该对象的资源数据。

`async_list` 的参数、异步迭代结果和父函数怎样收集 `jobs`，继续在[函数卡](../../../steps/step-000-k8s-controller-entry/02-short-term-memory/functions/kr8s/_objects.py/APIObject.async_list.md)中阅读。

## 来源

- 已核对的发布版源码：[模块导出](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/asyncio/objects.py)、[Job 类](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_objects.py#L1993)、[async_list](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_objects.py#L911)、[raw 属性](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_objects.py#L133)。
- Python 官方接口入口：[typing.cast](https://docs.python.org/3/library/typing.html#typing.cast)。
