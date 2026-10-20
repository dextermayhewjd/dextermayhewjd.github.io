# 局部示范 · 请求转换的职责分工

**本步问题：已经拿到请求 `body` 后，`_translate` 交回什么，这两份结果接下来交给谁？**

这是用已有转换步骤制作的局部结构示范。此前将它标为 Step 0 不符合用户要求；当前起点见 [Step 0 · 一次 Coding Agent 任务](../../../00-repo-reading/repositories/slime/steps/step-000-coding-agent/README.md)。本页用于主线到达模型请求时回查，原文件路径保留兼容；用户表述与认识更新仍来自原 Step 01。

## 先看本步在任务中的位置

```text
一次模型请求已到达 Adapter，得到 body
    ↓
_translate(body)                         ← 本步展开：转换的职责与两份结果
    ↓ translated、tools_schema
_render_token_ids(...)                   ← 只定位下一次交接
    ↓ prompt_ids
call_sglang_generate(...)                ← 只定位后续生成请求
```

这张图是助手根据源码提供的位置提示。本步已有个人认识集中在转换职责；渲染和生成的内部机制仍未展开。实际调用及证据见[短期记忆中的组合关系](02-short-term-memory/overview.md#源码中的交接位置)。

## 每份材料解决一个问题

| 你现在想看什么 | 打开哪里 | 这里保存什么 |
| --- | --- | --- |
| 这一步为什么读、读到哪里为止？ | [01 · 本步范围](01-scope.md) | 当前问题、入口条件、源码范围、停止位置 |
| `_translate` 到底做什么？ | [函数卡片：BaseAdapter._translate](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._translate.md) | 已认可的使用场合、完整代表性输入输出、模型、用户原话和未知 |
| 函数之间怎样连接，我已说清了哪些关系？ | [02 · 本步知识模型](02-short-term-memory/overview.md) | 已形成的关系、源码定位图、函数索引与整体未知 |
| 进入本步前可以复用什么？ | [03 · 前序累计模型](03-long-term-memory/overview.md) | 本示范暂无导入；不把当前的新认识倒填为前置知识 |
| 哪些问题使认识得到确认或修正？ | [04 · 关键学习记录](04-flow.md) | 四次实际问题及反馈、仍未确认的内容、原始讨论入口 |
| 想进一步看两路数据怎样进入转换 helper？ | [可选参考：转换内部的分工](references/translation-details.md) | 真实实现片段与参数去向，不再复制整套输入输出 |

**建议先看本页，再打开 common 函数卡片和 `02` 的组合关系。** 遇到“为什么这样转换”的问题再看参考；需要核对某条认识的来由再看 `04`。

## 这次实际怎样分工

- **函数卡片保存可复用的函数认识。** common 沿用你已认可的文字、代表性输入输出和引用格式；Anthropic 卡片保留具体实现的已有认识与未知。
- **overview 负责连接。** 它说明两份结果怎样交给下一环节，区分用户已经表达的关系与助手提供的源码定位。
- **形成过程保存关键事件。** `04` 不再重讲整套字段转换；函数卡片在来源里链接相关事件。
- **参考材料只展开额外机制。** 这份示范的参考只说明 helper 分工与参数去向；原 1.3 讲解保留在原步骤，可按需回查。

## 下一步怎样继承

```text
下一步的 03 = 本步的 03 + 本步的 02
下一步的 02 = 下一步实际新增或修正的认识
```

这里继承的是函数卡片、组合关系、未知和来源。形成过程与详细讲解通过来源链接回查，不在每一步重新复制成第二套说明。本示范不预建下一步。

## 对照与来源

- [原转换步骤](../step-01-translate-preview/README.md)：保留原目录、原始问答和 1.3 讲解。
- [已认可的 common 样例](../../../.agents/skills/repo-reading-memory/references/base-adapter-translate.md)：本示范函数卡片的正文来源。
- [本轮职责讨论](../2026-10-20-task-driven-cognitive-architecture/README.md)：说明为什么这样划分。

源码仍绑定 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。排版与归类不计为个人认识更新。
