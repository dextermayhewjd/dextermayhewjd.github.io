> 历史快照：2026-11-03，Kubernetes 基础与项目专属说明分开、按主题分层之前。本目录保留当时内容，不是当前通用基础入口。

# Labels 与 Selector：给资源加标记，再按标记筛选

[基础入口](README.md) · [Namespace](namespace.md) · [回到 Job 查询](../../../steps/step-000-k8s-controller-entry/02-short-term-memory/functions/kr8s/_objects.py/APIObject.async_list.md)

**Label 是资源上的键值标记；label selector 是查询时使用的标签匹配条件。** 资源的标签保存在 `metadata.labels` 中。

当前项目使用的 Job 元数据可简化为：

```yaml
metadata:
  name: job-a
  namespace: default
  labels:
    app.kubernetes.io/managed-by: agentlightning
```

对应的筛选常量是：

```python
MANAGED_BY_SELECTOR = "app.kubernetes.io/managed-by=agentlightning"
```

这里等号左侧是标签键，右侧是要求匹配的值。它要求返回的 Job 带有“由 agentlightning 管理”的标记。

## 与 namespace 一起使用

假设本次查询的 namespace 为 `default`，下表中的资源是教学构造：

| Job | namespace | `app.kubernetes.io/managed-by` | 是否匹配 |
| --- | --- | --- | --- |
| job-a | default | agentlightning | 是 |
| job-b | default | other | 否：标签值不同 |
| job-c | experiments | agentlightning | 否：namespace 不同 |

两项条件共同限定结果。当前选择器筛选管理标签，具体执行状态由后续代码读取 `status` 再判断。

## 来源

- 固定源码：[管理标签常量](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L34)、[当前查询调用](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L165)。
- Kubernetes 官方概念入口：[Labels and Selectors](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)。
