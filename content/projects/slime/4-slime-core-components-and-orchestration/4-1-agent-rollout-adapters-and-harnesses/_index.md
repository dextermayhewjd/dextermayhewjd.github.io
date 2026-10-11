---
title: "4.1. Agent Rollout Adapters and Harnesses"
summary: "架构图、阅读材料与下级章节。"
weight: 10
ShowToc: false
ShowReadingTime: false
ShowPostNavLinks: false
hideMeta: true
---

**当前推荐先读：[沿 generate 走完一次 Agent 任务](./task-walkthrough/)。** 先按完整任务顺序进入各职责组件，讲完回到主线，再用下面的动作页展开具体交接。

## 按任务阶段阅读

| 阶段 | 从这里读 | 这一段在做什么 |
| --- | --- | --- |
| 1 启动条件 | [Pre-4. 启动前准备](./pre-4/) | Adapter 入口、任务、Session、执行环境和题目准备好，走到 Harness.run 前 |
| 2 Agent 启动 | [4. Launch Agent](./4-launch-agent/) → [5. Manage Sandbox](./5-manage-sandbox/) / [6. Exec Commands](./6-exec-commands/) | 配置和命令怎样形成，环境怎样落实，CLI 怎样启动并等待 |
| 3 模型请求循环 | [7. Make API Calls](./7-make-api-calls/) → [2. Translate & Forward](./2-translate-forward/) → [3. Generate Tokens](./3-generate-tokens/) → [3.5. 完成一次模型请求](./3-5/) | CLI 已在运行；一次请求从回连、转换到生成、响应和轨迹，可能重复多轮 |
| 4 回到任务收尾 | [完整任务主线的第 7、8 步](./task-walkthrough/) | CLI 结束后收集 diff，独立评估，返回结果或导出训练轨迹，再清理 |

Pre-4 在目录中放于 3.5 后、4 前，表示给动作 4 增加前置阅读。**真实执行先准备和启动，再发生模型请求；组件动作编号不表示这个时间顺序。**

先看[项目开头的任务生命周期总览](/projects/slime/#agent-lifecycle)，再从各动作页的定位图进入具体数据流。

下面保留 CodeWiki 原图作为组件导航。原图的启动调用实际由外层 `generate()` 发起；本例的直接 HTTP 客户端是沙箱中的 CLI，没有独立 External Platforms 实现。原图动作 1 的接收入口与动作 7 一起说明，动作 8 的响应返回在 3.5 展开。

{{< figure src="diagram.svg" alt="CodeWiki 组件关系概览，用于选择阅读主题" class="slime-diagram" >}}

## 每章正在跟随哪一层调用

`generate()` 编排一次样本任务。进入 Harness 后，运行中的 CLI 可以多次发起模型请求；2 → 3 → 3.5 展开的是每次请求内部的 `_run_turn()`。5 提供环境能力，6 组合这些能力执行长命令；它们会被任务中的多个位置调用。

因此，同一个文件可以出现在多个章节中，阅读时只展开当前职责。各章的“本章主要源码文件与入口”可以点开查看文件、符号和行号。

{{< slime-action-context-overview >}}

## 阅读材料

- [本节 README](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/blob/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/README.md>)
- [Slime Core 完整请求流程](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/blob/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/Slime%20Core%20%E5%AE%8C%E6%95%B4%E8%AF%B7%E6%B1%82%E6%B5%81%E7%A8%8B.md>)

[CodeWiki 原始章节](<https://codewiki.google/github.com/thudm/slime#slime-core-components-and-orchestration-agent-rollout-adapters-and-harnesses>) · [本节资料文件夹](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/tree/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses>)
