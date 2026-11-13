# 名称、标签与归属：找到资源之后，怎样确认它是谁

[资源模型](README.md) · [对象与状态](objects-spec-status.md) · [标签与选择器](labels-and-selectors.md)

**查到一个对象，不代表它就属于当前控制器正在处理的工作。** 名称、UID、标签和所有者引用回答不同问题。

| 信息 | 作用 |
| --- | --- |
| 资源类型、namespace、name | 定位一份有命名空间的对象；Node 等集群级对象没有 namespace |
| metadata.uid | 标识这一次创建的对象；删除后以同名重建，UID 会改变 |
| metadata.labels | 分类和筛选对象，一组对象可以有相同标签 |
| metadata.ownerReferences | 表达对象之间的所有者与依赖关系，引用包含所有者的 UID |
| ownerReferences 中的 controller 标记 | 表示其中哪个所有者承担控制关系；不同于执行进程的登录身份 |

## 1. 标签先帮助筛选

控制器可以按标签找出一组 Pod，再检查哪些确实对应当前工作。标签可被设置和修改，本身不是全局唯一标识，也不能替代所有者检查。

给名称计算哈希再写入标签，是某些项目的实现选择；哈希算法和标签键不属于 Kubernetes 对所有工作负载的统一要求。

## 2. 所有者引用表达关系

例如一个 Job 管理的 Pod，可以把该 Job 记录为所有者。控制器比较所引用的 UID，避免把同名但重新创建的另一个 Job 当成原对象。

检查所有者是在回答“这个 Pod 属于哪个对象”，并不诊断它所在的 Node 是否健康，也不是一次网络访问权限检查。

<a id="write-and-read-owner-reference"></a>

### 写入归属与读取归属怎样相接

1. 创建依赖资源前，程序可以在本地对象的 metadata.ownerReferences 中填写其所有者信息。例如在 Pod 上记录控制它的 Job。
2. 这份关系随创建或相应更新请求保存到 API 中；只修改本地结构体，还没有持久化。
3. 后续取得这个 Pod 时，程序可以读取其所有者引用并比较 UID，确认它属于哪一份对象。

因此，归属保存在依赖资源的元数据中，不只是控制器进程内的一张私有表。模板描述“怎样运行”，所有者引用描述“由谁控制”；同名对象重建后 UID 不同，查询时仍应辨认具体身份。

## 3. 归属与回收有关，但不等于即时删除

Kubernetes 的垃圾回收会使用所有者引用处理依赖资源。删除传播方式、阻止删除的条件等会影响实际过程；不能只凭看到 ownerReferences 就断言所有子资源已被删除。

当前先理解标识与归属的区别，完整垃圾回收机制遇到删除场景再读。

## 来源

- [Object Names and IDs](https://kubernetes.io/docs/concepts/overview/working-with-objects/names/)
- [Owners and Dependents](https://kubernetes.io/docs/concepts/overview/working-with-objects/owners-dependents/)
- [阅读来源记录](../references/learning-sources.md)
