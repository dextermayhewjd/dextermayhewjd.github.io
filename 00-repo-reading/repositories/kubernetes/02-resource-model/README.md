# 资源模型：怎样表达、标识和观察工作

[Kubernetes 资料总入口](../README.md)

| 要解决的问题 | 概念 |
| --- | --- |
| 对象怎样表达期望，系统怎样报告观察结果？ | [metadata、spec 与 status](objects-spec-status.md) |
| 资源的名称属于哪个作用域？ | [Namespace](namespaces.md) |
| 怎样给资源分类，并按条件选出一组？ | [Labels 与 Selectors](labels-and-selectors.md) |
| 查到的对象是谁、属于谁？ | [名称、UID 与所有者引用](ownership-and-identity.md) |

先理解对象的身份、期望和状态，再看 Namespace 与标签选择器怎样共同限定查询范围。它们最终都服务于查到正确的对象、读懂对象以及按需求操作对象。
