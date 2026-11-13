# 资源对象：标识、期望与观察

[资源模型入口](README.md) · [控制器与协调循环](../01-architecture/reconciliation.md)

Kubernetes 使用资源对象描述集群中的工作与配置。阅读 Job、Pod 等对象时，先区分下面几项。

| 部分 | 回答什么问题 |
| --- | --- |
| `apiVersion`、`kind` | 这是哪种 API 版本中的哪类对象？ |
| `metadata` | 它是谁、在哪里、有哪些标记？ |
| `spec` | 希望它按什么配置运行、达到什么目标？ |
| `status` | 系统观察到它当前处于什么情况？ |

具体字段由资源类型定义；不是每一类资源都有相同的 `spec` 和 `status` 结构。

## 用一项完成目标作对照

下面是两个时间点的字段节选，不是完整部署清单：

| 信息 | 工作尚未完成 | 已观察到一次成功完成 |
| --- | --- | --- |
| Job 的期望：`spec.completions` | `1` | `1` |
| Job 的观察：`status.succeeded` | 尚无成功记录或为 `0` | `1` |

期望保持为 1，观察随着执行推进而变化。是否完整达成目标以及失败如何处理，还要遵循 Job 的其他配置和状态条件。

## metadata 怎样连接对象

- `name`：资源名称；对有 namespace 的资源，结合 [Namespace](namespaces.md) 确定作用域。
- `labels`：可供 [Selector](labels-and-selectors.md) 匹配的键值标记。
- 其他标识和关联字段：实际需要定位所有者、版本或生命周期关系时再展开。

查询资源得到的是一份对象数据，既可能包含期望，也可能包含观察结果。看到 `status` 时要先确认它属于哪种对象；Pod 与 Job 各有自己的状态。

<a id="local-object-and-api"></a>

## 本地对象与 API 中的记录

1. 客户端先在程序内准备接收数据的对象，再把读取结果填进去；建立本地变量不会自动创建集群资源。
2. 读取的是 API 资源数据，客户端也可能通过缓存读取；这与查找或拉取容器镜像是不同的动作。
3. 修改本地对象中的 status，只改变程序持有的数据；需要相应的 API 写请求，才会更新集群中的记录。
4. 对提供 status 子资源的类型，客户端可以通过专门的状态接口更新观察结果。控制器依据该类型的规则计算状态，不是把 spec 原样复制到 status。

## 版本标记与更新依据

metadata.resourceVersion 是服务器提供的版本标记，客户端将其视为不透明字符串。它可参与并发更新控制；当写入所依据的版本已过期时，带版本条件的写请求可能被拒绝。

保存旧状态可用于比较变化、构造差异；保存旧版本可用于约束写入依据。它们并不自动提供回滚容器或恢复磁盘的功能。具体采用更新、补丁还是其他写入方式，由客户端和控制器实现决定。

## 自定义类型与具体对象

CRD 用来向 Kubernetes 声明一种自定义资源类型及其结构规则；创建该类型的一份对象，才是在提交一个具体实例。对象的 spec/status 含义由该类型定义，不应把某个项目的字段名当成 Kubernetes 所有资源的共同字段。

标识与关系继续见[名称、UID 与所有者引用](ownership-and-identity.md)。

## 官方来源

- [Objects In Kubernetes](https://kubernetes.io/docs/concepts/overview/working-with-objects/)
- [Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [API resource versions](https://kubernetes.io/docs/reference/using-api/api-concepts/#resource-versions)
- [Custom Resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
