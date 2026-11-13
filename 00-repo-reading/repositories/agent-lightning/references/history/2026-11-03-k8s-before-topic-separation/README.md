> 历史快照：2026-11-03，Kubernetes 基础与项目专属说明分开、按主题分层之前。本目录保留当时内容，不是当前通用基础入口。

# Kubernetes 基础：随 Agent Lightning 阅读积累

[Agent Lightning 阅读入口](../../../README.md) · [当前步骤](../../../steps/step-000-k8s-controller-entry/README.md)

这里集中保存阅读中实际遇到的 Kubernetes 基础，以及本项目如何使用这些概念。函数卡只保留当前调用的场景、输入输出、实现与返回位置，需要背景时链接到这里。

## 当前已有内容

| 当前想弄清什么 | 入口 |
| --- | --- |
| Gateway API 与 Kubernetes API 是什么关系？两个客户端分别访问谁？ | [API 与客户端](api-and-clients.md) |
| Job 是什么？它与 Pod、Agent 的执行有什么关系？ | [Job 与 Pod](job-and-pod.md) |
| `namespace="default"` 限定了什么范围？ | [Namespace](namespace.md) |
| Job 的标签写在哪里？`label_selector` 怎样筛选？ | [Labels 与 Selector](labels-and-selectors.md) |
| `k8s_objects.Job` 从哪里来？Job 类、实例与 `.raw` 有什么区别？ | [kr8s 与资源对象](kr8s-resource-objects.md) |

## 怎样与函数阅读配合

当前入口是 [Job.async_list 的函数卡](../../../steps/step-000-k8s-controller-entry/02-short-term-memory/functions/kr8s/_objects.py/APIObject.async_list.md)：从调用处查一个概念，再回到该卡继续理解查询和返回；函数卡最终返回 `_reconcile_once` 的列表推导式。

- 基础笔记回答“这个概念是什么、在当前代码里对应哪里”。
- `steps/.../02-short-term-memory/` 回答“这个函数这次接收什么、怎样处理、返回给谁”，并保存个人表述与未知。
- 当前阅读进度只保存在[项目入口](../../../README.md#current-reading)。基础资料的存在不表示已经读懂或运行过。

首批内容来自已发生的提问与源码核对。后续遇到新的基础问题再补充，不预生成尚未接触的课程、步骤或函数卡。本文档在本地 Markdown 中维护。
