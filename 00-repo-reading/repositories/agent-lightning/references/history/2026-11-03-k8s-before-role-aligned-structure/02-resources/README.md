> 历史快照：2026-11-03，落实已确认的八类知识目录之前。本文保留当时结构，现行内容从项目 k8s/ 入口查看。

# 资源组织：在哪里找到资源，怎样选出资源

[Kubernetes 资料总入口](../README.md)

| 要解决的问题 | 概念 |
| --- | --- |
| 资源的名称属于哪个作用域？ | [Namespace](namespaces.md) |
| 怎样给资源分类，并按条件选出一组？ | [Labels 与 Selectors](labels-and-selectors.md) |

Namespace 与标签选择器可以共同限定查询范围。两者作用不同，复习时先分别理解，再看组合示例。
