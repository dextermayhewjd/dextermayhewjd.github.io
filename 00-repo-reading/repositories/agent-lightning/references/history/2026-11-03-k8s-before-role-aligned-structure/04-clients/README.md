> 历史快照：2026-11-03，落实已确认的八类知识目录之前。本文保留当时结构，现行内容从项目 k8s/ 入口查看。

# 客户端库：从程序中使用 Kubernetes API

[Kubernetes 资料总入口](../README.md)

这一层保存客户端工具与语言库的用法。它们运行在调用 Kubernetes API 的一侧，需要与前三层的 Kubernetes 自身组件、资源概念区分。

## Python

- [kr8s：模块、资源对象与异步查询](python/kr8s.md)

`kr8s` 是第三方 Python 客户端库，不是 Kubernetes 内置组件。它提供对 Kubernetes 资源与操作的 Python 封装。
