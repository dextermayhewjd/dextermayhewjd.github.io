> 历史快照：2026-11-03，落实已确认的八类知识目录之前。本文保留当时结构，现行内容从项目 k8s/ 入口查看。

# Namespace：资源名称的作用域

[本层入口](README.md) · [资料总入口](../README.md)

**Namespace 为集群中的一部分资源提供命名作用域。** Pod 和 Job 都属于 namespace 中的资源。

同一种资源在同一个 namespace 内名称必须唯一；不同 namespace 可以存在同名资源。因此，定位一个 Job 时，namespace 与名称共同提供位置。

| 资源类型 | Namespace | 名称 |
| --- | --- | --- |
| Job | test | daily-report |
| Job | production | daily-report |

上面是两个不同的 Job，即使名称相同。

## 查询时的含义

```text
GET /apis/batch/v1/namespaces/default/jobs
```

这表示查询 `default` namespace 中的 Job。`default` 是 Kubernetes 初始提供的 namespace 之一；它是作用域名称，不是“所有 namespace”的意思。

Namespace 的作用不是筛选运行状态。需要按资源标记进一步筛选时，可同时使用 [label selector](labels-and-selectors.md)。

## 官方来源

- [Namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)
