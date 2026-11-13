# API Server：Kubernetes 的 API 入口

[本层入口](README.md) · [资料总入口](../README.md)

**Kubernetes API Server 是控制平面中提供 Kubernetes API 的组件。** 客户端通过它查询或修改资源，例如 Pod、Job、Namespace。

```text
kubectl / program client -> Kubernetes API Server -> resource objects
```

## API 与客户端的区别

| 名称 | 含义 |
| --- | --- |
| Kubernetes API | 查询、创建、更新、删除资源等操作的接口约定 |
| API Server | 对外提供这些接口的服务组件 |
| 客户端 | 发起请求的程序，例如 kubectl，或使用 Python 客户端库的程序 |

客户端对象保存访问服务所需的连接与请求能力。创建一个客户端对象，与创建 Pod 或 Job 是不同的操作；后者需要向 API Server 提交相应资源请求。

## 查询与提交分别意味着什么

- **查询资源**：读取集群当前保存的资源对象。例如列出一个 namespace 中的 Job。
- **提交或修改资源**：描述希望系统达到的状态。相关控制器观察资源变化，推进后续工作。

例如，提交 Job 后，Kubernetes 的 Job 控制器负责推进相应 Pod 的创建与完成管理；API Server 提供资源操作入口。

一个 Job 列表请求的路径示例：

```text
GET /apis/batch/v1/namespaces/default/jobs
```

其中 `batch/v1` 是 API 组与版本，`default` 是 namespace，`jobs` 是资源类型。资源的命名与筛选见[资源组织](../02-resource-model/README.md)，Job 与 Pod 的关系见[工作负载](../03-workloads/pods-and-jobs.md)。

<a id="list-and-get"></a>

## List 与 Get：按条件找一组，按名字取一个

| 操作语义 | 选择条件 | 结果与边界 |
| --- | --- | --- |
| List | 某类资源、作用域，以及支持的标签等筛选条件 | 取得一组匹配对象；查询成功时也可以为空 |
| Get | 某类资源的具体名称；有命名空间的资源还要指定 namespace | 读取指定对象；不存在时返回 NotFound，其他读取失败不能当成不存在 |

例如，列出 default 下符合标签条件的 Pod，与读取 default 下名为 worker-a 的 Pod，是两次不同的操作。结果可以重合；一次按名读取不是前面列表查询的后半段实现。

如果调用方对取得的列表继续按所有者筛选，那是在处理已有结果，不自动产生新的查询。是否同时使用 List 和 Get、怎样综合结果，由具体控制器决定，不能推广为所有 Kubernetes 客户端都必须遵循的流程。

客户端可能用缓存回答读取请求；这里解释操作语义，不保证每次代码调用都直接请求 API Server。客户端自行注册的索引与 Kubernetes API 原生支持的选择器也需区分，不能把某个项目的索引键当成所有 API 都能查询的字段。

读取、修改本地对象与持久化的关系见[对象数据与 API 写回](../02-resource-model/objects-spec-status.md#local-object-and-api)；多个筛选条件的组合继续复用[标签选择器说明](../02-resource-model/labels-and-selectors.md)。

## 官方来源

- [Kubernetes API](https://kubernetes.io/docs/concepts/overview/kubernetes-api/)
- [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/)
