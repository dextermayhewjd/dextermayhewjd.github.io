# Step 004 · 环境需求怎样变成可使用的 state

> 编号调整：本目录由 Step 001 顺延为 Step 004。正文中的早期编号、原话及记忆快照保留历史语境；现行顺序见[编号与范围对照](../../../../step-numbering-2026-11-05.md)。

[项目目标与当前接续](../../../../README.md) · [前一步：generate 整体交接](../step-000-slime-bridge-and-interfaces/README.md) · [采用的 reference1](../step-000-slime-bridge-and-interfaces/references/reference1.md)

本步从 generate 的环境未命中路径进入 BlackboxAgentPaddock.init，理解环境需求怎样交给 provider、怎样取得服务地址，以及 state 怎样返回给调用方。业务方法 init 与对象构造方法 __init__ 分开辨认。

现行阅读位置：[Step 003 · Paddock 准备](../step-003-paddock-selection/01-scope.md) → 本步（保留已读状态） → [Step 005 · 注册准备](../step-005-agent-registration/01-scope.md)。

## 从这里开始

本步原阅读已按共同接口与正常交接的深度收束。本次承接 Step 003，只回顾输入、取得环境和返回 state 三项交接，不重新通读全部辅助入口。回顾先看 [05 · 任务交接总结](05-task-flow.md)，再按下列入口回查；具体后端和失败机制仍保留未知。

1. 打开 [scope 3.1](01-scope.md#whole-flow)，在完整 generate 骨架里定位本步。
2. 进入 [scope 3.2](01-scope.md#reading-navigation)，按三段顺序阅读 init。
3. 在 init 第 2 段接续 [get_public_url 的条件调用](02-short-term-memory/functions/dressage/sandbox/provider.py/SandboxProvider.get_public_url.md)；[create 的约定](02-short-term-memory/functions/dressage/sandbox/provider.py/SandboxProvider.create.md)保留回查，必要时用 [local_bwrap](references/local-bwrap-create.md)对照 spec 怎样变成 lease。
4. 带着 lease 回到 [init 第 2 段](02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#acquire-environment)，继续 endpoint 与 state；最后返回 generate 的注册位置。

| 材料 | 用途 |
| --- | --- |
| [01 · scope](01-scope.md) | 上层背景、本步问题、内部阅读顺序与停止位置 |
| [02 · 本步函数与类索引](02-short-term-memory/overview.md) | init 为父流程，provider 共同约定为本轮重点；具体实现作例子，类卡解释数据 |
| [03 · 前序函数索引](03-long-term-memory/overview.md) | Step 000 的 generate 快照，保留来源与未知 |
| [04 · 实际讨论](04-flow.md) | 分步原因、用户确认与后续理解反馈 |
| [05 · 任务交接总结](05-task-flow.md) | 从环境需求到 state 的完整交接、结果含义和本步边界 |

## 记录边界

init 正式归属本步短期记忆；早期在 Step 000 目录中展开的事实保留在来源与归档，不作为前序长期记忆继承。generate 的原六段说明保留；回查它不意味着本步要重新深读全部流程。本轮从已读例子提取 provider 的共同约定；local_bwrap 的管理器、槽位池及其他后端内部不继续下钻。Kubernetes 需要实际后端实现，接口阅读不等同于已经学会 Pod 管理。

源码版本：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。用户已概括环境取得的总体作用；按本步深度收束，精确机制的未知仍保留；没有运行真实环境。唯一实时进度在项目入口维护。
