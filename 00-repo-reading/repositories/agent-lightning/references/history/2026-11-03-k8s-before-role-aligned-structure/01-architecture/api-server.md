> 历史快照：2026-11-03，落实已确认的八类知识目录之前。本文保留当时结构，现行内容从项目 k8s/ 入口查看。

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

其中 `batch/v1` 是 API 组与版本，`default` 是 namespace，`jobs` 是资源类型。资源的命名与筛选见[资源组织](../02-resources/README.md)，Job 与 Pod 的关系见[工作负载](../03-workloads/pods-and-jobs.md)。

## 官方来源

- [Kubernetes API](https://kubernetes.io/docs/concepts/overview/kubernetes-api/)
- [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/)
