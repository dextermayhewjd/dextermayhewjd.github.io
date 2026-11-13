> 历史快照：2026-11-03，Kubernetes 基础与项目专属说明分开、按主题分层之前。本目录保留当时内容，不是当前通用基础入口。

# Job 与 Pod：任务怎样落到执行单元

[基础入口](README.md) · [回到 Job 查询](../../../steps/step-000-k8s-controller-entry/02-short-term-memory/functions/kr8s/_objects.py/APIObject.async_list.md)

**Job 描述一项需要运行到完成的工作；Pod 是承载容器运行的基本单元。** 一个 Job 可以管理一个或多个 Pod，具体数量和运行约束由配置决定。

放回当前项目：Agent Lightning 的 Controller 提交 Job，Kubernetes 根据 Job 中的 Pod 模板组织执行，Agent 程序在相应容器中运行。

```text
Agent Lightning Controller -> Job -> Pod -> container running the Agent
```

当前只需区分三个对象：

| 对象 | 当前含义 |
| --- | --- |
| `rollout` | Agent Lightning Gateway 中的一条业务任务记录 |
| Kubernetes Job | 集群中用来执行工作的资源对象 |
| Python 中的 `kr8s` Job 实例 | 程序用来读取、操作该集群资源的封装，详见 [kr8s 资源对象](kr8s-resource-objects.md) |

## 读资源数据时先认三个部分

- `metadata`：名称、namespace、labels 等标识信息。
- `spec`：期望怎样运行，例如 Pod 模板与执行约束。
- `status`：系统观察到的当前情况，例如完成或失败信息。

`_reconcile_once` 先列出现有 Job，再根据名称和状态与 rollout 对应。更详细的创建、重试和 Pod 调度过程，等实际读到时再展开。

## 来源

- 当前项目：[Basics](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/docs/05-basics.md)。
- 已核对的库定义：[kr8s Job](https://github.com/kr8s-org/kr8s/blob/v0.20.15/kr8s/_objects.py#L1993)，资源类型为 `Job`、API 版本为 `batch/v1`。
- Kubernetes 官方概念入口：[Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)、[Pods](https://kubernetes.io/docs/concepts/workloads/pods/)。
