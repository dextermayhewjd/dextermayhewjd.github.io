# 运维与排查：从现象回到对象和责任组件

[资料总入口](../README.md) · [一次 Job 的整体流程](../00-overview/job-lifecycle.md)

排查先确定工作停在哪个阶段，再查看对应对象、事件和日志。不要仅凭一个界面状态猜测全部原因。

## 用同一条路径定位问题

| 当前现象 | 先核对什么 | 接回的知识主题 |
| --- | --- | --- |
| 请求未成功或找不到对象 | 集群上下文、namespace、名称与请求响应 | API 与资源模型 |
| Pod 尚未运行 | 是否已绑定节点、事件中是否有资源、镜像、卷等问题 | 调度与运行环境 |
| 容器退出或重启 | 容器状态、终止原因、退出码与日志 | 执行过程、资源与程序行为 |
| 程序连不上依赖 | 目标地址、DNS、端口与网络策略 | 网络与访问边界 |
| Pod 与 Job 表现不一致 | 是否观察了正确的关联对象、Job 的完成条件 | 对象关联与协调循环 |

## 一个排查过程应留下什么

1. 实际现象和复现条件。
2. 对象标识、配置、状态与相关事件/日志。
3. 根据证据形成的原因判断。
4. 修改的内容，以及重新验证后的结果。

读取、推测、实际修改和验证结果分别记录。命令与截图只是证据载体，关键是能解释它们如何支持结论。

## 官方入口

- [Troubleshooting Applications](https://kubernetes.io/docs/tasks/debug/debug-application/)
- [Debug Running Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/)
