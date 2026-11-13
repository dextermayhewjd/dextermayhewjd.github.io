# kr8s：用 Python 访问 Kubernetes 资源

[客户端层入口](../README.md) · [资料总入口](../../README.md)

`kr8s` 是第三方 Kubernetes Python 客户端库。本页以 `0.20.15` 的已核对源码说明模块、类与异步查询的关系；Kubernetes 资源本身见 [Pod 与 Job](../../03-workloads/pods-and-jobs.md)。

## 模块别名与资源类

```python
from kr8s.asyncio import objects as k8s_objects
```

| 写法 | 含义 |
| --- | --- |
| `kr8s.asyncio.objects` | 导出异步资源类的模块，包括 Job、Pod、Service 等 |
| `k8s_objects` | 为这个模块取的本地别名 |
| `k8s_objects.Job` | 表示 Kubernetes Job 资源的 Python 类 |
| 一个 `Job` 实例 | 资源数据及其操作方法的封装 |
| 实例的 `.raw` | 它持有的字典式资源数据 |

该版本中，`kr8s.asyncio.objects` 从 `kr8s._objects` 导出 `Job`；`Job` 继承 `APIObject`，`async_list` 方法来自这个父类。

## 异步查询怎样得到对象

假设 `api` 已经是可用的 Kubernetes 客户端，在协程中可以按 [namespace](../../02-resource-model/namespaces.md) 和 [label selector](../../02-resource-model/labels-and-selectors.md) 查询 Job：

```python
async for job in k8s_objects.Job.async_list(
    namespace="default",
    label_selector="app=report-worker",
    api=api,
):
    print(job.name)
```

`async_list` 提供异步生成器；在默认的对象返回模式下，每次迭代取得一个 Job 实例。是否把结果收集成普通列表，由调用者决定。

```text
Job class -> async_list(...) -> async iteration -> Job instance
```

## 对象与 raw 数据

`.raw` 在本页版本中返回 `Box`，支持按字典读取 `metadata`、`spec`、`status` 等字段。读取 `.raw` 使用的是对象持有的数据。

若代码出现 `cast(k8s_objects.Job, job)`，其中的 `cast` 属于 Python 的 `typing`：它向类型检查器表达预期类型，运行时返回原对象。它与资源查询、资源创建是不同的操作。

## 来源

- kr8s `v0.20.15`：[模块导出](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/asyncio/objects.py)、[Job 类](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_objects.py#L1993)、[async_list](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_objects.py#L911)、[raw 属性](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_objects.py#L133)。
- [kr8s 文档](https://docs.kr8s.org/en/stable/)
- [Python typing.cast](https://docs.python.org/3/library/typing.html#typing.cast)
