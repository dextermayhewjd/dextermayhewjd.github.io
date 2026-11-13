> 历史快照：2026-11-03，Kubernetes 基础与项目专属说明分开、按主题分层之前。本目录保留当时内容，不是当前通用基础入口。

# API 与客户端：当前代码访问两个服务

[基础入口](README.md) · [回到 _get_k8s_api](../../../steps/step-000-k8s-controller-entry/02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._get_k8s_api.md)

**API 是服务提供的操作接口；客户端是 Python 程序用来调用这些接口的对象。** 当前 Controller 同时需要访问 Agent Lightning Gateway 和 Kubernetes。

| 服务 | 当前负责的内容 | 代码里的客户端 |
| --- | --- | --- |
| Agent Lightning Gateway | 保存 rollout 任务及其状态，提供查询、状态更新等接口 | `self._api`，类型为 `AgentLightningAsyncClient` |
| Kubernetes API Server | 提供对 Job、Pod 等集群资源的操作接口 | `self._k8s_api`，由 `kr8s` 取得；父函数用局部 `api` 接住 |

在 `_reconcile_once` 中，先通过 Gateway 取得任务记录，再通过 Kubernetes 客户端查询实际存在的 Job，然后将两边对应起来。

```text
_query_rollouts -> self._api -> Agent Lightning Gateway
Job.async_list -> api       -> Kubernetes API Server
```

`_get_k8s_api` 获取并缓存的是客户端对象。后面的 `Job.async_list(..., api=api)` 才使用它查询 Job。客户端的变量名不会决定请求目标，应追溯它是由哪一种客户端类、用什么连接配置创建的。

## 当前代码中的来源

- `_run_controller` 创建 `AgentLightningAsyncClient`，传给 `K8sReconciler`，构造器保存为 `self._api`。
- `_get_k8s_api` 调用 `kr8s.asyncio.api()`，保存为 `self._k8s_api`。
- 更具体的缓存过程、输入输出与个人记录保留在 `_get_k8s_api` 函数卡。

## 来源

- 固定源码：[Controller 创建客户端](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/__main__.py#L17)、[保存与获取客户端](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L112)。
- Kubernetes 官方概念入口：[Kubernetes API](https://kubernetes.io/docs/concepts/overview/kubernetes-api/)。
