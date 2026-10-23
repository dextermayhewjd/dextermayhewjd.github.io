# generate 的输入背景：分开阅读

[回到本步阅读入口](../01-scope.md#adapter-to-open-session)

2026-10-22 按用户要求，参照 Step 003 将不同对象与概念分开说明。本页保留原链接，作为按需回查的目录；各页分别保存定义、用途和源码依据。

| 想弄清什么 | 打开哪份说明 |
| --- | --- |
| 传给 generate 的基础样本是什么？ | [base_sample](base-sample.md) |
| 本次按哪套约定整理题目和评测？ | [protocol](protocol.md) |
| 整理后的题目信息是什么？ | [md](metadata.md) |
| 当前正在解决哪一道题？ | [instance_id](instance-id.md) |
| 这是 Agent 的哪一次执行？ | [session_id / sid](../../step-004-trajectory-to-samples/references/session-id.md)——复用 Step 003 的独立说明 |

各函数卡片继续解释自己实际接收的参数与输入输出。整体位置见本步 scope，调用处的衔接保留在[输入背景的原始讨论](../../step-005-agent-preparation/04-flow.md#session-id-reading-boundary)。

[本次拆分记录](../../step-005-agent-preparation/04-flow.md#split-input-references) · [此前合并说明的讨论](../../step-005-agent-preparation/04-flow.md#shared-input-reference)
