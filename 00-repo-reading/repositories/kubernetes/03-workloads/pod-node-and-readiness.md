# Pod、节点与就绪：对象创建之后，还发生什么

[工作负载](README.md) · [整体运行流程](../00-overview/job-lifecycle.md)

**Pod 是运行单元的描述与状态，Node 是承载它的节点。** 创建了 Pod 对象，还要经过节点选择、容器启动与就绪判断。

## 1. 沿正常路径看几个不同事实

| 观察到的事实 | 能说明什么 |
| --- | --- |
| API 接受 Pod 创建 | 集群中已有这份运行需求，不保证容器已启动 |
| Pod 的 spec.nodeName 已填写 | Pod 已关联一个节点；不单凭这个字段判断节点健康 |
| Pod 的 status.podIPs 有地址 | 已有报告的 Pod 地址；不保证应用端口可访问 |
| Pod 的 phase 为 Running | 已进入运行阶段；Running 不等于 Ready |
| Pod 的 Ready condition 为 True | 满足当前 Pod 配置下的就绪要求；不等于特定业务任务或评分完成 |

默认调度路径由 Scheduler 选择节点；节点上的 kubelet 联合运行时与网络、存储能力继续推进。具体机制按实际问题展开。

## 2. 字段摘取与健康检查

程序从已经取得的 Pod 对象读取 spec.nodeName，只是在读一个字段。将它复制到上层资源的 status，不等于额外查询了 Node 对象，更不等于对节点做了健康诊断。

类似地，读取 Pod IP 与实际建立连接是两种操作。尚未分配节点或地址时，对应字段可以为空。

## 3. 上层资源有自己的状态规则

Job、自定义资源等可以观察 Pod 的状态，再计算自己的状态。不同类型的 Ready、完成和失败规则可能不同，不能把某个控制器的判定当作所有资源的统一规则。

Pod 归属与数量约束也要区分：某些控制器允许管理多个 Pod，某些项目要求单个运行 Pod。见[所有者关系](../02-resource-model/ownership-and-identity.md)。

## 来源

- [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Nodes](https://kubernetes.io/docs/concepts/architecture/nodes/)
- [阅读来源记录](../references/learning-sources.md)
