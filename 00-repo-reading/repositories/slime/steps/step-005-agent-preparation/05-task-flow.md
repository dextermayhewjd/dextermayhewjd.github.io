# 05 · 任务链路：为本次 Agent 执行登记会话配置

> `generate` 先取得 Adapter 和本次执行的 sid，再通过 `open_session` 将采样默认值与上下文长度登记为 `store[sid]` 中的 Session。后续请求按 sid 使用这份配置，结束时再取走。

[本步 scope](01-scope.md) · [步骤入口](README.md) · [函数与类记录](02-short-term-memory/overview.md) · [本次收拢](../step-005-agent-preparation/04-flow.md#session-registration-flow-closure)

## 1. 本步补齐了哪一段

- Step 1 已读到 `_run_turn` 按 sid 取得配置，用它处理模型请求。
- Step 3 已读到 `finish_session` 取走配置，将长度上限交给轨迹导出。
- Step 4 回到二者之前：接清这个 Adapter 从哪里来、执行编号怎样取得，以及配置怎样登记进去。

本页终点是 `open_session` 返回：本次执行的配置已经保存在 Adapter 中。题目的镜像、工作目录和问题描述仍由 `base_sample` / `md` 承载。

## 2. 已读函数怎样完成交接

以下是固定版本正常路径的导航，省略完整服务初始化、检查与无关参数；行号供回到源码定位。首次初始化才创建 Adapter，后续可以复用已有服务状态。

```text
generate                                                    generate.py:182
├─ state = _AdapterService(args)                             184
│  └─ 首次初始化：_AdapterService.__init__                   138
│     └─ self.adapter = ADAPTER_CLS(...)                     150–156
│        → state.adapter 持有后面接收调用的 Adapter
├─ md = swe.get_metadata(base_sample, protocol)              186–187
│  └─ instance_id = md["instance_id"]                        → 取出题目编号
├─ session_id = base_sample.session_id = _session_id(...)    194；函数定义 308–313
│  └─ 返回本次执行编号；本例为 cagent-demo-1-0-0
└─ state.adapter.open_session(...)                          195–199
   └─ BaseAdapter.open_session                              common.py:210–223
      ├─ 检查这个 sid 是否已经登记
      ├─ 用两项配置创建 Session，放入 self.store[sid]
      └─ 返回 None；配置留在 Adapter 中
```

- [_AdapterService.__init__](02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.__init__.md)：接清 `state.adapter` 的来源。当前 Claude Code 路径选择 `AnthropicAdapter`，它继承 `BaseAdapter.open_session`。
- [_session_id](02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_session_id.md)：已有编号优先沿用，否则按索引拼接或使用随机后缀；调用方保存返回的字符串，再交给登记方法。
- [open_session](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md)：接收编号、`sampling_params` 与 `state.max_context_len`。其中两项配置构成 [Session 实例](02-short-term-memory/classes/slime/agent/adapters/common.py/Session.md)，sid 用作字典键。

## 3. 登记后，什么保存在哪里

沿用本步的同一例子：题目编号为 `demo-1`，样本 `index=0`、`group_index=0`，此前没有 session_id，因而取得 `cagent-demo-1-0-0`。采样参数和长度仍为教学构造值。

登记后的 `state.adapter.store` 如下，只展示本例这一项：

```python
{
    "cagent-demo-1-0-0": Session(
        sampling_defaults={"temperature": 0.7, "top_p": 0.9},
        max_context_tokens=4096,
    )
}
```

| 内容 | 保存或使用的位置 |
| --- | --- |
| 题目描述、镜像标识、工作目录等任务信息 | `base_sample` / `md`，由后续任务准备与执行使用 |
| 本次执行编号 `cagent-demo-1-0-0` | 调用方的 `session_id`、`base_sample.session_id`，以及 store 的键 |
| 采样默认值与上下文长度 | `state.adapter.store[sid]` 对应的 Session 实例 |

- store 保存“编号 → 配置对象”的对应关系；Session 自身只有两项配置字段，没有 sid、题目描述、image 或 workdir 字段。
- 同一个 Adapter 可以按不同 sid 保存多份配置；一次执行中的多轮模型请求可以取用同一份配置。
- `open_session` 返回 `None`，其结果体现在 Adapter 的状态变化上；重复登记已有 sid 会报错，不覆盖原配置。

## 4. 怎样接回前面读过的流程

这里接回 `evaluation=False` 的样本导出路径，只回顾前序已读关系。

| 时机 | 对同一份配置做什么 |
| --- | --- |
| 本步：准备运行 Agent | `open_session` 在 `store[sid]` 登记配置 |
| CLI 运行期间：处理模型请求 | [_run_turn](03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md) 按 sid 取得 Session，交给 `call_sglang_generate` |
| 本次执行结束：导出样本 | [finish_session](03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md) 取出并移除 Session，读取长度配置用于导出；题目基础字段仍由另外传入的 `base_sample` 提供 |

到这里，本步“对象来源 → 执行编号 → 配置登记 → 后续用途”的主线可以收拢。完整服务初始化、索引的上游分配、采样参数合并和长度限制的具体算法继续保留为按需回查项；沙箱与工作区准备仍在本步范围之外。

本次用户复述中的“题目基础信息都存入 store”已在上面的字段对应中校正。该校正由助手根据源码给出，尚未收到进一步反馈；本页总结不将这一表述记录为已确认正确，也不代表整条 Coding Agent 流程已经读完。

<details>
<summary>源码、形成依据与验证范围</summary>

- 固定提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。
- 对象与调用：[generate.py:138–199](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L138-L199)；编号规则：[308–313 行](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L308-L313)。
- Session 字段：[common.py:33–42](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L33-L42)；配置登记：[210–223 行](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L210-L223)。
- 后续取用：[common.py:335–344](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L335-L344)；取走与导出：[261–269 行](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L261-L269)。
- 本页由 LLM 收拢已发生的阅读；用户原话与本次澄清见[Step 4 的收拢记录](../step-005-agent-preparation/04-flow.md#session-registration-flow-closure)。
- 示例沿用函数卡片中已有的局部构造与验证。本次静态复核源码，没有新增完整 Adapter、模型、HTTP 或沙箱运行。

</details>
