# Labels 与 Selectors：标记资源，再按标记筛选

[本层入口](README.md) · [Namespace](namespaces.md) · [资料总入口](../README.md)

**Label 是资源上的键值标记，保存在 `metadata.labels` 中；label selector 是选择符合标签条件的资源的规则。**

下面只展示一个资源的元数据部分：

```yaml
metadata:
  name: report-a
  namespace: default
  labels:
    app: report-worker
    environment: test
```

例如选择器：

```text
app=report-worker
```

表示选出 `app` 标签值为 `report-worker` 的资源。标签键和值由使用者按需要定义，选择器只负责匹配。

## 多个条件怎样组合

```text
app=report-worker,environment=test
```

逗号连接的两个要求需要同时满足。如果请求本身又限定了 namespace，还需要满足该范围限制。

假设查询范围为 `default`，选择器为 `app=report-worker`：

| Job | Namespace | `app` 标签 | 是否匹配 |
| --- | --- | --- | --- |
| report-a | default | report-worker | 是 |
| cleanup-a | default | cleanup-worker | 否，标签不同 |
| report-b | test | report-worker | 否，namespace 不同 |

这类选择器匹配的是标签。资源处于什么运行状态，需要读取相应的 `status` 信息。

## 官方来源

- [Labels and Selectors](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)
