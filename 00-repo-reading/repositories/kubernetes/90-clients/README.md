# 客户端库：从程序中使用 Kubernetes API

[Kubernetes 资料总入口](../README.md)

这一层保存客户端工具与语言库的用法。它们运行在调用 Kubernetes API 的一侧，借助已有的架构、资源模型和工作负载知识来操作集群。命令行工具与程序客户端都从这里归类，不把工具语法当作系统运行原理。

共同操作先回查 [List 与 Get](../01-architecture/api-server.md#list-and-get)：按条件列出对象、按名字读取对象，以及查询后的本地筛选。具体客户端的参数和缓存机制仍按各自版本理解。

## Python

- [kr8s：模块、资源对象与异步查询](python/kr8s.md)

`kr8s` 是第三方 Python 客户端库，不是 Kubernetes 内置组件。它提供对 Kubernetes 资源与操作的 Python 封装。

命令行操作涉及的对象状态与证据解释，回查[运维与排查](../06-operations/README.md)；具体 kubectl 用法在实际使用时再补充。
