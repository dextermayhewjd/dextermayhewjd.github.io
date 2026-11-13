# Kubernetes：知识目录与整体心智模型

这是供 Agent Lightning、Agent Sandbox 等源码阅读共同引用的基础专题，不是 Kubernetes 核心源码阅读项目。原 Agent Lightning 下的 20 份资料已整体迁入，保留八类职责结构；各项目的函数卡、个人理解与进度仍留在原项目。

这里按知识职责组织资料，供独立阅读与复习。目录分类不等同于 Kubernetes 运行时依次经过的层次：总览连接整体，主题目录保存各概念的唯一正文，客户端工具引用这些概念。

贯穿各目录的主线是：

> **用资源对象表达期望 → 控制器持续协调 → 调度到节点 → 容器实际执行 → 状态反馈。**

`spec` 表达期望，`status` 记录系统观察到的情况；控制器按资源的规则持续推进工作。这些组件通过 API 对象协作，需要把对象、组件和实际进程分别看清。

## 按职责归类

```text
kubernetes/
├── 00-overview/
├── 01-architecture/
├── 02-resource-model/
├── 03-workloads/
├── 04-runtime-environment/
├── 05-security-and-isolation/
├── 06-operations/
└── 90-clients/
```

| 目录 | 要帮助回答的问题 | 当前入口 |
| --- | --- | --- |
| [00-overview](00-overview/README.md) | 一项任务从提交到运行、结束，整体发生了什么？ | [一次 Job 生命周期](00-overview/job-lifecycle.md) |
| [01-architecture](01-architecture/README.md) | API Server、控制器、Scheduler、kubelet、运行时分别负责什么？ | [API Server](01-architecture/api-server.md)、[协调循环](01-architecture/reconciliation.md) |
| [02-resource-model](02-resource-model/README.md) | 怎样用对象表达需求？标识、期望、状态和筛选条件是什么关系？ | [对象模型](02-resource-model/objects-spec-status.md)、[Namespace](02-resource-model/namespaces.md)、[Labels](02-resource-model/labels-and-selectors.md) |
| [03-workloads](03-workloads/README.md) | Pod、Job 等对象分别表达什么运行目标？ | [Pod 与 Job](03-workloads/pods-and-jobs.md)、[Job status](03-workloads/job-status.md) |
| [04-runtime-environment](04-runtime-environment/README.md) | 工作运行需要哪些计算资源、网络、存储和配置？ | [镜像、命令与环境变量](04-runtime-environment/container-image-and-env.md)及运行条件的归属 |
| [05-security-and-isolation](05-security-and-isolation/README.md) | 谁能访问什么？工作之间、容器与宿主机之间怎样隔离？ | 权限、执行边界与运行时隔离 |
| [06-operations](06-operations/README.md) | 怎样观察状态、查看日志事件、定位失败并验证恢复？ | 从现象回到对象和责任组件 |
| [90-clients](90-clients/README.md) | 怎样通过命令行或程序操作上述对象？ | [Python / kr8s](90-clients/python/kr8s.md) |

## 从整体返回局部

初次建立整体模型，先看 [Job 生命周期](00-overview/job-lifecycle.md)，再按卡点回查 [spec/status](02-resource-model/objects-spec-status.md) 和 [协调循环](01-architecture/reconciliation.md)。进入具体接口或代码后，保留来路，读完带着输入输出关系返回原位置。

同一概念只在一个主题中维护完整说明。例如 Namespace 放在资源模型中，安全、运维与客户端文章引用它；总览连接它在任务中的位置，不另写一套定义。

## 本轮可直接回查

1. [对象数据与 API 写回](02-resource-model/objects-spec-status.md#local-object-and-api)：本地变量改变与集群记录改变有什么区别。
2. [标签、UID 与所有者关系](02-resource-model/ownership-and-identity.md)：找到候选资源与确认归属有什么区别。
3. [Pod、节点与就绪](03-workloads/pod-node-and-readiness.md)：创建对象、分配节点、取得 IP、Ready 分别表示什么。
4. [Volume、PVC 与挂载](04-runtime-environment/volumes-and-pvc.md)：存储申请与实际存储怎样接到容器目录。
5. [Pod 地址与 Service](04-runtime-environment/service-and-pod-address.md)：访问入口对象与网络实际连通有什么区别。

这些资料按遇到的问题回查，不要求先通读后再继续源码。[材料来源与项目入口](references/learning-sources.md)记录它们与实际阅读的关系。

## 内容逐步补充

当前先建立总览、对象模型和协调循环，并保留已有 API、Namespace、Labels、Pod/Job 与 kr8s 材料。运行环境、安全与运维目录先明确职责和观察问题，详细内容在实际遇到问题后补充。

运行环境和隔离需要区分：Namespace 的资源组织、Pod 的执行承载，并不独自说明不可信代码的隔离强度。运行时配置与部署方式决定实际边界，相关知识集中在安全与隔离目录。

## 官方基础

- [Objects In Kubernetes](https://kubernetes.io/docs/concepts/overview/working-with-objects/)
- [Controllers](https://kubernetes.io/docs/concepts/architecture/controller/)
- [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/)
