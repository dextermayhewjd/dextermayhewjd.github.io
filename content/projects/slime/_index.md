---
title: "Slime：架构与实践目录"
description: "先从一个 Agent 样本的任务生命周期建立整体认识，再进入架构图与各动作的阅读材料。"
weight: 20
ShowToc: false
---

<span id="agent-lifecycle"></span>

## 先看一个 Agent 样本的任务生命周期

以下总览对应固定版本 `coding_agent_rl` 示例的正常任务路径：外层 `generate()` 组织一个样本，Harness 准备并启动 CLI，CLI 请求 Adapter，由 SGLang 提供模型生成。先看任务顺序，再进入各动作的具体数据流。

CLI 运行在沙箱内，Adapter HTTP 服务运行在 Slime 侧；图中的嵌套表示任务与请求的包含关系，连接它们的是 HTTP 请求。

{{< figure src="/images/slime-lifecycle/overview.svg" link="/images/slime-lifecycle/overview.svg" alt="一个 Agent 样本的任务生命周期：准备、启动、CLI 模型请求循环与收尾" >}}

[放大生命周期总览](/images/slime-lifecycle/overview.svg)

```text
generate()：整次任务
  ├─ 准备模型入口、会话、沙箱和题目
  ├─ Harness.run()：准备配置、启动 CLI、等待结束
  │    └─ CLI 运行：请求模型、执行工具、继续工作
  │         └─ Adapter._run_turn()：一次模型请求
  │              ├─ 2：Translate & Forward
  │              ├─ 3：Generate Tokens
  │              └─ 3.5：响应返回与本轮轨迹记录
  └─ 收集 diff、评分、导出结果、清理资源
```

**每个动作页先标出在这个生命周期中的位置，再展开本章负责的交接。** Manage Sandbox 的环境能力贯穿准备、运行和回收；Exec Commands 展开 CLI 进程的启动与完成等待。

| 从哪里读 | 这部分回答什么 |
| --- | --- |
| [4. Launch Agent](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/4-launch-agent/) | 启动参数从哪里来，怎样形成 CLI 配置、命令与环境 |
| [5. Manage Sandbox](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/5-manage-sandbox/) | 怎样提供和操作任务的执行环境 |
| [6. Exec Commands](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/6-exec-commands/) | 怎样启动 CLI、接收输出、等待退出与处理预算耗尽 |
| [7. Make API Calls](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/7-make-api-calls/) | CLI 怎样回连 Adapter，HTTP 路由怎样接收请求 |
| [2. Translate & Forward](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/2-translate-forward/) | 请求中的消息与工具怎样交给共享处理流程 |
| [3. Generate Tokens](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/3-generate-tokens/) | 怎样准备输入并向 SGLang 请求生成 |
| [3.5. 完成一次模型请求](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/3-5/) | 怎样返回客户端响应并保存本轮模型轨迹 |

CodeWiki 原图用于组件导航，箭头编号不是任务执行顺序。**本例没有独立的 External Platforms 实现：直接 HTTP 客户端是沙箱中的 CLI，Anthropic / OpenAI 表示适配的协议。** 原图动作 1 的请求接收与动作 7 一起定位；动作 8 的响应返回在 3.5 展开。模型请求不是经由 Adapter 转发给 Anthropic / OpenAI 服务，而是交给本例的 SGLang 后端生成。

总览依据源码 `8c17b676cb57af1d17ee4402e91e9209af84b60b` 的 `examples/coding_agent_rl/generate.py` 与 `slime/agent/`。Slime 的训练后端、分布式编排与其他示例继续按下面的原始目录阅读。

## 面向项目实践的阅读路线

[Slime 全仓代码复用与项目路线](/projects/slime/reuse-roadmap/) 从整个仓库梳理 Agent 执行、批量评测、Trace、数据队列、Kubernetes 适配、自部署模型和训练能力，区分可以直接复用的代码与需要适配的边界。

## 原始章节目录

从下面的章节或左侧导航继续。编号与原始章节顺序一致；各节保留原图和对应阅读入口。

[查看全部原始材料](<https://github.com/dextermayhewjd/dextermayhewjd.github.io/tree/main/slime_photo>)
