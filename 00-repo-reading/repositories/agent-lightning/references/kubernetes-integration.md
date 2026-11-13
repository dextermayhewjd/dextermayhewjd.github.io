# Agent Lightning 与 Kubernetes：项目专属对应关系

[项目入口](../README.md) · [通用 Kubernetes 资料](../../kubernetes/README.md) · [当前接续](../README.md#current-reading)

这里保存业务代码与 Kubernetes 的对应关系。通用定义在 `k8s/`；本页保存 Gateway、K8sReconciler、客户端变量和项目配置，供源码阅读时回查。

<a id="two-clients"></a>

## 两个服务与两个客户端

| 服务 | 当前职责 | 客户端 |
| --- | --- | --- |
| Agent Lightning Gateway | 保存 rollout 及状态，提供任务查询、状态回写等业务接口 | `self._api`，类型为 `AgentLightningAsyncClient` |
| Kubernetes API Server | 提供对 Job、Pod 等集群资源的操作接口 | `self._k8s_api`，父函数通过局部变量 `api` 接住 |

`_run_controller` 创建 Gateway 客户端，传给 `K8sReconciler` 保存。`_get_k8s_api` 通过 `kr8s.asyncio.api()` 取得 Kubernetes 客户端并缓存。

```text
_query_rollouts -> self._api -> Agent Lightning Gateway
Job.async_list -> api       -> Kubernetes API Server
```

具体缓存与返回见 [_get_k8s_api 函数卡](../steps/step-000-k8s-controller-entry/02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._get_k8s_api.md)。

## 应用控制器与 Kubernetes 内置控制器

**`K8sReconciler` 是 Agent Lightning 自己实现的应用控制器。** 它调用 Kubernetes API 创建、查询和观察 Job。Kubernetes 内置的 Job 控制器则负责推进 Job 所需的 Pod 执行。

```text
Agent Lightning K8sReconciler -> Kubernetes API: Job
                                             |
                                             v
                                  Kubernetes Job controller
                                             |
                                             v
                                        Pod -> Agent
```

`rollout` 是业务任务记录，Job 是 Kubernetes 资源。当前项目用它们的关联标记把运行状态对应起来；二者的具体交接保存在 [_reconcile_once 函数卡](../steps/step-000-k8s-controller-entry/02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md)。

## 当前项目的 namespace 与标签

- `self._namespace` 来自 `config.k8s_runner.namespace`，仓库默认值为 `default`。
- `MANAGED_BY_SELECTOR` 为 `app.kubernetes.io/managed-by=agentlightning`，选择由本应用管理的 Job。
- `Job.async_list` 同时使用这两项条件与 Kubernetes 客户端。通用的作用域与匹配规则分别见 [Namespace](../../kubernetes/02-resource-model/namespaces.md)和 [Labels/Selectors](../../kubernetes/02-resource-model/labels-and-selectors.md)。

<a id="build-job-spec-knowledge-boundary"></a>

## build_job_spec 阅读中，哪些内容进入 Kubernetes 基础

归类依据是：换成其他项目后仍成立的 Kubernetes 概念，进入 `k8s/`；当前项目怎样使用这些概念，保留在函数卡与本页。基础内容按真实问题逐步补充，不因源码出现一个字段就预写整套课程。

| 内容 | 归属 | 当前处理 |
| --- | --- | --- |
| Job 清单、`spec.template` 与 Pod/容器的层级关系 | `03-workloads/` | 已写入 [Job 清单与 Pod 模板](../../kubernetes/03-workloads/job-manifest-and-pod-template.md) |
| `containers[].image`、`command/args`、`env` 的作用，以及 `imagePullPolicy` | `04-runtime-environment/` | 已写入 [镜像、命令与环境变量](../../kubernetes/04-runtime-environment/container-image-and-env.md)；目前只解释已遇到的基本用法 |
| 地址要从容器所在网络可达，默认 Pod 网络中 localhost 的含义 | `04-runtime-environment/` | 已在同一篇记录基本边界，后续遇到具体网络问题再展开 |
| Namespace、Labels 和 Selector 的通用作用 | `02-resource-model/` | 复用已有 [Namespace](../../kubernetes/02-resource-model/namespaces.md) 与 [Labels/Selector](../../kubernetes/02-resource-model/labels-and-selectors.md)，不另写一份 |
| Pod 的 `restartPolicy`、Job 的 `backoffLimit`、`activeDeadlineSeconds`、`ttlSecondsAfterFinished` | `03-workloads/` | 字段语义属于 Kubernetes；尚未逐项阅读的部分，等实际展开时再补正文 |
| `resources.requests/limits`、`volumes/volumeMounts` 的机制 | `04-runtime-environment/` | 当前只定位模板字段，正式阅读时再补 |

以下仍留在 [build_job_spec 函数卡](../steps/step-002-build-job-spec/02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/build_job_spec.md)：

- Jinja2 的 `Environment()`、模板渲染，以及 Python 变量名 `env` 的复用。
- `agent_base_url` 的取值规则、`AGL_OPENAI_BASE_URL` 等变量的具体名称与用途、Gateway 的代理路径。
- `input.image_name` 怎样拼成 `:openai` 镜像引用，以及本项目的 `pull_images.py` 如何准备镜像。
- 本项目选了哪个 namespace、用了什么标签键值、为何采用某个重试或清理参数。

例如，“容器通过 env 取得服务地址”是 Kubernetes 基础；“这个地址指向 Agent Lightning Gateway，再转发给模型服务”是项目关系。二者互相链接即可，不将项目设定写成 Kubernetes 的通用规则。

## 来源与版本

- Agent Lightning 固定提交：`0029dbb35c467799d35fee81d15d80264b0d1bd3`。
- [控制器入口](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/__main__.py#L17)、[K8sReconciler](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L104)、[默认配置](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/config/controller.yaml)。
- 依赖版本由项目 `uv.lock` 锁定为 `kr8s==0.20.15`；这属于项目版本选择，不是 Kubernetes 核心概念。
