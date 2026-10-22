# Step 1 · 从 Harness 定位到一次模型请求的处理

[前一步：Coding Agent 核心骨架](../step-000-coding-agent/README.md) · [当前阅读进度](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

本步沿 `BaseAdapter._run_turn` 逐段读清一次模型请求。此前讨论过的 Harness → CLI → HTTP 路由保留为来路说明；Step 0 只负责整体骨架，具体函数记录从这里开始收录。

先看 [scope 中的整体骨架与面包屑](01-scope.md#step-1-branch)，从中定位要读的函数；本步进入 [_run_turn 函数卡片](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md)，建立该函数的职责、输入输出和内部处理模型，按需进入子函数记录。本步读完后，再用 [task flow](05-task-flow.md#run-turn-flow) 总结本 scope 内各函数如何配合完成请求。阅读中实际发生的问题与修正保存在 [04-flow](04-flow.md)。

需要恢复上游来路时，再查[为什么有 HTTP 服务、请求和响应怎样往返](05-task-flow.md#http-round-trip)与[文件、调用行及返回位置](05-task-flow.md#source-jump-map)。这些材料继续保留，无需每次从启动代码重读。

## 当前位置与来路

前一步的七项核心骨架说明整次任务有哪些环节；下面的面包屑说明当前函数在其中哪里。缩进用于阅读定位，CLI 到 Adapter 的边明确经过 HTTP。

```text
generate()                              # 整次任务
└─ HARNESS_CLS().run(...)                # 启动并等待 CLI
   └─ 外部 Claude Code CLI 运行期间
      └─ HTTP POST /v1/messages
         └─ BaseAdapter._run_turn(...)  # 本步逐段阅读的请求编排器
            ├─ 输入转换与编码 → 模型生成
            ├─ 解码与解析 → 协议回复材料
            └─ HTTP 响应、轨迹记录与请求收尾
```

`_translate` 的[已有函数记录](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._translate.md)已从 Step 0 移入本步 `02`，原话、样例和来源保持不变。Step 0 没有函数分析记录，因此本步 `03` 暂无前序函数可继承。

调用关系中的关键跳转见[源码导航](../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#source-jump-map)，或直接打开[网页中的对应位置](http://localhost:1313/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/task-walkthrough/#source-jump-map)。导航标出具体对象、实现文件、调用行、阅读范围和返回位置；`harness/common.py` 与 `adapters/common.py` 分开标明。

## 本步材料

- [01 · 阅读范围](01-scope.md)：整体位置、`_run_turn` 的处理顺序与逐段阅读边界。
- [02 · 本步函数记录](02-short-term-memory/overview.md)：本次请求各函数的输入输出、内部解释、个人表述与未知，以及用于回查的 `BaseHarness.run`。
- [03 · 前序函数记忆](03-long-term-memory/overview.md)：暂无前序函数继承。
- [04 · 问题与澄清](04-flow.md)：原话、源码证据、助手解释和仍待反馈的关系。
- [05 · 任务链路总结](05-task-flow.md)：本步阅读后，汇总 scope 内各函数的配合、数据交接与整体结果；此前的启动与 HTTP 来路折叠保留，供按需回查。
- [当前逐段讲解](../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#run-turn-step-by-step)：同一内容见 [Hugo 预览](http://localhost:1313/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/task-walkthrough/#run-turn-step-by-step)。

前一步提供七个外层环节，本步沿其中一次模型请求读实现。实际反馈保存在 `04-flow.md`，当前理解与接续位置统一见[阅读进度](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。
