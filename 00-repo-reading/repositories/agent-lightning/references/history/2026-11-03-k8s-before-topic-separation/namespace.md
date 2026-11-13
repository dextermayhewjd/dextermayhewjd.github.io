> 历史快照：2026-11-03，Kubernetes 基础与项目专属说明分开、按主题分层之前。本目录保留当时内容，不是当前通用基础入口。

# Namespace：指定在哪个资源作用域中查询

[基础入口](README.md) · [回到 Job 查询](../../../steps/step-000-k8s-controller-entry/02-short-term-memory/functions/kr8s/_objects.py/APIObject.async_list.md)

**Namespace 为集群中的一部分资源提供命名作用域。** 对 Job 这类属于 namespace 的资源，可以先把它理解为查询和管理资源时指定的分组。

同一种资源在同一个 namespace 内名称必须唯一；不同 namespace 可以存在同名 Job。因此查找资源时，名称和 namespace 都重要。

## 当前代码中的对应关系

仓库默认配置：

```yaml
k8s_runner:
  namespace: default
```

构造器读取它：

```python
self._namespace = str(self._runner_config.namespace)
```

查询时传入：

```python
namespace=self._namespace
```

在默认配置下，这次调用查询 `default` namespace 中的 Job。`default` 是这个作用域的名称；如果配置改为另一个名称，查询范围就相应改变。

查到这个范围后，还要满足 [label selector](labels-and-selectors.md) 的条件。

## 来源

- 固定源码：[Controller 默认配置](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/config/controller.yaml)、[构造器与查询](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L112)。
- Kubernetes 官方概念入口：[Namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)。
