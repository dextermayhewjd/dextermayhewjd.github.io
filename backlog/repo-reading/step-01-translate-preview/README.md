# Step 1 推演：从请求 body 到消息与工具定义

这是工作流与 skill 重构时的具体填表示例，不是新的已完成学习步骤。它沿用用户认可的 [Translate & Forward 页面](http://localhost:1313/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/2-translate-forward/)及同一份请求，不从头重讲 generate。2026-10-19 用户要求先在本 Step 01 采用短期与长期记忆分开的结构。

- [01-scope.md](01-scope.md)：为什么进入这里、本步核心问题、进入条件、源码范围和阅读边界。
- [02 短期记忆](02-short-term-memory/overview.md)：本步由用户表达的新认识、修正和实现留白。
- [03 长期记忆](03-long-term-memory/overview.md)：从前序步骤继承的完整模型；本步作为独立试用起点，暂无导入。
- [04-flow.md](04-flow.md)：按实际问题连接用户表述、源码材料、助手提示和后续修正，保存认识形成的过程。
- [可选参考讲解](references/translation-explanation.md)：保留此前助手写出的详细示例，按需查阅。

个人记忆已按用户原话建立；更多具体实现仍留白。此前助手代写的详细说明已移到参考，不作为用户自己的认知，也不因此增加已掌握进度。

scope 与 flow 已按用户确认的[职责规范](../2026-10-19-step-folder-format.md#scope-flow-conventions)整理：scope 控制本步阅读范围，flow 记录有源码依据的理解过程，形成的认识进入 `02`。目录与模板的调整历史保留在格式讨论中。

```text
step-01-translate-preview/
├── README.md
├── 01-scope.md
├── 02-short-term-memory/
│   ├── overview.md
│   └── functions/slime/agent/adapters/
│       ├── common.py/BaseAdapter._translate.md
│       └── anthropic.py/AnthropicAdapter._translate.md
├── 03-long-term-memory/
│   └── overview.md
├── 04-flow.md
└── references/translation-explanation.md
```

## 怎样进入下一步

下一步的 `03-long-term-memory/` 由本步的 `03` 与 `02` 合并形成：保留已有整体地图与函数记录，再按对应位置加入本步的理解、修正和未知。下一步的 `02-short-term-memory/` 留给新的理解。本步保持原样，以后仍能回看当时的认知。

本步 `03` 暂无前序模型，所以首次交接时主要继承本步 `02`。`step-000-initial-model` 中尚未由用户表述的技术模型不自动填入；已读 generate 的历史继续保留在[唯一阅读路线](../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。

短期与长期表示本步形成、后续继承，不表示掌握程度。两层记忆都只保存用户实际表达过的认识；`references/` 中的助手解释按需查阅。

本页取材的原页面与 JSON 样例使用历史提交 `8c17b676cb57af1d17ee4402e91e9209af84b60b`。本轮仅对照当前本地 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 中的转换调用及函数，不修改原页面的版本标签。
