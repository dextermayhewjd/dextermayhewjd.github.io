# instance_id：当前正在解决哪一道题

[返回参考目录](generate-input-context.md) · [题目信息 md](metadata.md) · [执行编号 session_id](../../step-003-trajectory-to-samples/references/session-id.md)

**`instance_id` 是题目编号。** 在当前调用处，它从整理后的题目信息中取得：

```python
instance_id = md["instance_id"]
```

例如 `"issue-123"` 可以用作教学中的题目编号；它不是本轮实际运行值。

## 与执行编号怎样区分

- `instance_id` 回答“正在解决哪一道题”。同一道题可以让 Agent 独立尝试多次。
- `session_id` 回答“这是哪一次执行”。同题的不同独立执行应使用不同的执行编号。
- 当前把 `instance_id` 交给 `_session_id(base_sample, instance_id)`，作为生成编号时可能使用的组成部分；存在已有执行编号时也可能直接沿用。
- 题目编号后续还用于日志和结果元数据，帮助识别结果属于哪道题。

> 题目编号区分题目；执行编号区分对题目的每次独立执行。

关于会话、多轮请求和轨迹树的关系，直接复用 [Step 003 的 session_id 说明](../../step-003-trajectory-to-samples/references/session-id.md#what-session-identifies)。编号的具体生成规则见 [_session_id 函数卡片](../02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_session_id.md)。

<details>
<summary>源码与原始讨论</summary>

- 固定提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`；以上为静态源码说明。
- [取得题目编号与传给编号函数](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L186-L194)；[写入结果元数据](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L237-L245)；[编号函数](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L308-L313)。
- [原合并说明的讨论](../../step-004-agent-preparation/04-flow.md#shared-input-reference)；[本次拆分](../../step-004-agent-preparation/04-flow.md#split-input-references)。整理不表示新增掌握或运行证据。

</details>
