# Volume、PVC 与挂载：程序怎样使用存储

[运行环境](README.md) · [Pod 与节点](../03-workloads/pod-node-and-readiness.md)

容器里的程序通过路径读写文件。希望工作数据独立于某次 Pod 的替换而保留时，需要明确路径背后的存储来源和生命周期。

## 1. 先分清四个位置

| 名称 | 表达什么 |
| --- | --- |
| PVC：PersistentVolumeClaim | 一份存储申请对象，描述容量、访问模式等需求 |
| PV：PersistentVolume | 集群中一份可供使用的持久卷资源，与存储系统有关 |
| Pod 的 volumes | 描述本 Pod 可使用的卷及其来源，其中一种来源是 PVC |
| 容器的 volumeMounts | 把某个卷挂载到这个容器的哪个目录 |

不是所有 Volume 都使用 PVC，也不是所有卷都在 Pod 删除后保留。这里聚焦通过 PVC 使用持久存储的路径。

## 2. 一份申请怎样接到目录

1. 提交 PVC，表达存储需求，例如申请 1Gi。
2. 集群的存储机制匹配或供给适当的持久卷，并处理绑定。有的存储配置会把绑定推迟到有消费者时。
3. Pod 的卷配置引用这个 PVC，容器的挂载配置指定目录，例如 /data。
4. 节点侧完成必要的存储准备和挂载后，程序通过 /data 读写。

这是职责关系，不保证所有存储配置都按严格的同步顺序完成。创建 PVC 成功只表示申请对象已提交，不等于已经提供了容量、挂载完成或应用可用。

## 3. 准备申请与检查容量的区别

应用控制器可以负责检查 PVC 是否存在、是否属于自己，需要时提交创建。这个动作本身不是读取节点磁盘空闲空间，也不保证这次申请最终被满足。

同样，删除或替换 Pod 不等于删除 PVC；PVC、PV 和实际存储的保留或删除受各自归属、回收策略与存储实现影响。不能仅凭“持久化”推断数据永远保留。

## 来源

- [Volumes](https://kubernetes.io/docs/concepts/storage/volumes/)
- [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [阅读来源记录](../references/learning-sources.md)
