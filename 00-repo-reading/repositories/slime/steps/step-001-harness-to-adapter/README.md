# Step 1 · 从 Harness 启动到 Adapter 收到请求

[前一步：Coding Agent 核心骨架](../step-000-coding-agent/README.md) · [当前阅读进度](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

本步围绕用户明确提出的问题：`HARNESS_CLS().run(...)` 怎样接到 `BaseAdapter._run_turn(...)`？先连通启动、外部 CLI、HTTP 路由三个环节，不把每个辅助调用拆成一个新步骤。

本步的连续调用关系和关键数据交接集中在 [05 · 任务链路](05-task-flow.md)，下方保留快速定位入口。

当前讨论进入[为什么有 HTTP 服务、请求和响应怎样往返](05-task-flow.md#http-round-trip)。需要回查函数链时，使用[文件、调用行与返回位置](05-task-flow.md#source-jump-map)：从 `slime/agent/harness/common.py:97`，经第 104 行进入 `harness/claude_code.py:57`。长篇逐句说明放在同页的可展开部分。

## 当前位置与来路

前一步的七项核心骨架说明整次任务有哪些环节；下面的面包屑说明当前函数在其中哪里。缩进用于阅读定位，CLI 到 Adapter 的边明确经过 HTTP。

```text
generate()                              # 整次任务
└─ HARNESS_CLS().run(...)                # 启动并等待 CLI
   └─ 外部 Claude Code CLI 运行期间
      └─ HTTP POST /v1/messages
         └─ BaseAdapter._run_turn(...)  # 本步追踪到的请求入口
            └─ self._translate(body)   # 数据格式的局部入口，已有记录可复用
```

本步沿 `_run_turn` 收到请求的位置，进一步交代 HTTP 服务怎样监听、读取请求，以及响应怎样回到 CLI。`_translate` 标出模型处理中的局部入口，其[已有函数记录](03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._translate.md)可直接回查；本轮不展开模型生成内部过程。

调用关系中的关键跳转见[源码导航](../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#source-jump-map)，或直接打开[网页中的对应位置](http://localhost:1313/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/task-walkthrough/#source-jump-map)。导航标出具体对象、实现文件、调用行、阅读范围和返回位置；`harness/common.py` 与 `adapters/common.py` 分开标明。

## 本步材料

- [01 · 阅读范围](01-scope.md)：本步目标、入口与连接骨架。
- [02 · 本步函数记录](02-short-term-memory/overview.md)：记录 `BaseHarness.run` 的职责和边界。
- [03 · 前序函数记忆](03-long-term-memory/overview.md)：继承 Step 0 的转换函数记录。
- [04 · 问题与澄清](04-flow.md)：原话、源码证据、助手解释和仍待反馈的关系。
- [05 · 任务链路](05-task-flow.md)：启动、HTTP 请求与退出码返回怎样连接，及本步尚未展开的部分。
- [完整讲解](../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#harness-to-adapter)：同一内容见 [Hugo 预览](http://localhost:1313/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/task-walkthrough/#harness-to-adapter)。

前一步提供七个外层环节。本步连接 Harness 启动、CLI 运行、Adapter 接收和响应；实际反馈保存在 `04-flow.md`，当前理解与接续位置统一见[阅读进度](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。
