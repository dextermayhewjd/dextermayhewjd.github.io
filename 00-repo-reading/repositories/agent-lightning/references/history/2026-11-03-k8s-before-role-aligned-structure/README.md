> 历史快照：2026-11-03，落实已确认的八类知识目录之前。本文保留当时结构，现行内容从项目 k8s/ 入口查看。

# Kubernetes 分层知识目录

这里保存可独立复习的 Kubernetes 知识。前三层介绍 Kubernetes 自身，第四层单列访问 Kubernetes 的客户端工具与语言库。

```text
k8s/
├── 01-architecture/
│   └── api-server.md
├── 02-resources/
│   ├── namespaces.md
│   └── labels-and-selectors.md
├── 03-workloads/
│   └── pods-and-jobs.md
└── 04-clients/
    └── python/
        └── kr8s.md
```

## 1. 架构：请求通过谁进入集群

[本层入口](01-architecture/README.md) · [API Server](01-architecture/api-server.md)

区分 Kubernetes API、提供 API 的服务组件，以及发起请求的客户端。

## 2. 资源组织：在哪里找资源，怎样选资源

[本层入口](02-resources/README.md) · [Namespace](02-resources/namespaces.md) · [Labels 与 Selectors](02-resources/labels-and-selectors.md)

先确定资源的命名作用域，再理解按标签选择资源。

## 3. 工作负载：资源怎样承载执行

[本层入口](03-workloads/README.md) · [Pod 与 Job](03-workloads/pods-and-jobs.md)

区分 Pod 的执行承载、Job 的任务管理，以及 Kubernetes 内置 Job 控制器的职责。

## 4. 客户端工具：从语言和程序中操作资源

[本层入口](04-clients/README.md) · [Python / kr8s](04-clients/python/kr8s.md)

这一层属于客户端生态用法。`kr8s` 的模块、Python 类和异步迭代接口，与 Kubernetes 资源概念分别归位。

以上按已经涉及的主题组织；需要查阅某个概念时，可直接进入相应层次。
