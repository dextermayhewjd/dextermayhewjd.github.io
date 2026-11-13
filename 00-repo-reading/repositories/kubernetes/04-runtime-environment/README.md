# 运行环境：工作执行需要哪些条件

[资料总入口](../README.md) · [一次 Job 的整体流程](../00-overview/job-lifecycle.md)

工作负载对象描述要运行什么；正常执行还依赖计算资源、网络、存储与配置。本目录按这些条件归纳问题，具体机制随使用场景展开。

已展开：[镜像、启动命令与环境变量](container-image-and-env.md)。

本轮补充：[Volume、PVC 与挂载](volumes-and-pvc.md)、[Pod 地址与 Service](service-and-pod-address.md)。只覆盖已经遇到的基础关系，具体驱动和网络实现仍按需深入。

| 方向 | 首先要能说明的关系 | 后续遇到问题时查什么 |
| --- | --- | --- |
| 计算资源 | 请求的资源影响调度，限制影响运行时可用资源 | CPU/内存 requests 与 limits、配额、资源不足与超限 |
| 网络与发现 | 程序通过什么地址与名称访问所需服务 | Pod 网络、Service、DNS、端口与连接路径 |
| 存储 | 工作目录与输出文件来自哪里，执行结束后怎样保留 | Volume、持久存储声明、挂载位置与生命周期 |
| 配置与环境 | 程序运行时从哪里取得参数和配置 | 环境变量、配置挂载、ConfigMap 与 Secret 的使用位置 |

复习时始终接回同一个工作负载：它需要什么、集群提供了什么、二者哪里不一致。网络访问权限与身份授权的边界见[安全与隔离](../05-security-and-isolation/README.md)，具体现象定位见[运维排查](../06-operations/README.md)。

## 官方入口

- [Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Services, Load Balancing, and Networking](https://kubernetes.io/docs/concepts/services-networking/)
- [Storage](https://kubernetes.io/docs/concepts/storage/)
- [Configuration](https://kubernetes.io/docs/concepts/configuration/)
