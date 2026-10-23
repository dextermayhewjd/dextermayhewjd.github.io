# sid 与 inflight：分开阅读

[返回 shutdown_session](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md)

2026-10-22 按用户要求，将原说明拆成两份。本页保留旧链接入口，原有内容与源码依据已迁入下列对应文件。

<a id="what-session-identifies"></a>

1. **先读 [sid：标识 Agent 对一道题的一次执行](session-id.md#what-session-identifies)**。解释它与题目、镜像、消息历史和轨迹树的关系，以及编号的来路。
2. **再读 [inflight：按 sid 登记正在处理的请求](inflight.md)**。解释 Task 登记表的形状、状态变化和关闭时的使用。

[本次拆分记录](../04-flow.md#split-sid-inflight-references) · [最初合并说明的讨论](../04-flow.md#sid-inflight-background)
