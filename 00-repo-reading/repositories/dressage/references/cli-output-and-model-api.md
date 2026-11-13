# CLI 输出与模型 API：Dressage 从哪里取得哪些信息

> Claude CLI 同时向模型发送 API 请求，也向启动它的进程输出运行事件。两条通道分别记录模型交互和程序运行结果，不能互相替代。

[回到 _run_claude_turn](../topics/01-native-agent-rollout/steps/step-006-agent-execution/02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter._run_claude_turn.md) · [Python 管道基础](../topics/01-native-agent-rollout/steps/step-006-agent-execution/references/python-stdout-pipe.md) · [项目阅读入口](../README.md)

2026-11-08，从 Step 006 的反复追问中独立整理。本文用于定位应观察哪条通道、该看哪处代码，不改变正式阅读进度，也不增加一套必读课程。

## 1. 先看同一次运行的两条通道

下面使用 Python 高亮显示注释，是关系示意，不是可执行程序。

```python
Claude CLI
  -> stdout -> Python adapter -> logs / CLI events  # 观察 Claude 程序报告了什么
  -> model HTTP -> local proxy -> Dressage Proxy -> model  # 记录模型请求与生成数据
```

1. **程序输出通道**：stdout 包含 CLI 主动报告的事件，Python 收集它们，整理运行结果。
2. **模型请求通道**：Claude 调用模型时经过代理，代理处理请求、回复并记录生成数据。
3. **两条通道同时存在**：输出文字可能重叠，但 CLI JSON 事件不是原始 HTTP 通信的完整副本。

<a id="stdout-content"></a>

## 2. stdout 里具体是什么

**这里收集的是 Claude CLI 自己输出的 stream-json 事件流，既包含过程事件，也包含结果事件。它不是原样转储的模型 HTTP 请求，也不是只打印最后一句答案。**

下面依据仓库测试缩减为三行格式示意，不是本次实际运行日志；省略了其他字段和内容块：

```json
{"type":"system","subtype":"init","session_id":"sess"}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"visible"}]}}
{"type":"result","is_error":false,"num_turns":2}
```

1. system/init：CLI 初始化时报告的会话等信息。
2. assistant：CLI 报告的助手消息，其中可以有文字、工具调用等内容块；测试还包含 Bash 工具调用。
3. result：本次运行的结果事件，可以带成功/错误、轮数和结果文字等信息。

这段代码设置了 stdout=PIPE，所以这些行不会由这里直接打印到控制台。它们先被 Python 从管道读到，再写入 `runtime_dir/logs/claude_code.stdout.log`，同时解析进 events 列表。不同 CLI 版本和启动选项可能影响事件内容，不能把示意当作固定事件全集或逐 token 输出保证。

格式依据：[test_convert_claude_code_stream_events_extracts_reasoning_text_tool_and_usage](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/blackbox_server/test_claude_code_adapter.py#L531)。

不是每个模型 token 都必然作为一行 stdout 输出；此处的 stream-json 是 CLI 的事件格式。stderr 和进程退出码还提供另外的运行诊断。

<a id="api-channel"></a>

## 3. 有 API 记录，为什么还要 CLI 输出

Dressage 同样会设置 ANTHROPIC_BASE_URL：先把 Claude 的模型请求送到沙箱内 RolloutLLMProxy，再转发给配置好的外部 Dressage Proxy。它没有把 API 采集替换成读取 stdout。

| 通道 | 回答的问题 | 本次使用位置 |
| --- | --- | --- |
| 模型 API 请求与回复 | 模型看到了什么、生成了什么；对应的 token/logprob 等是什么 | Proxy 的请求处理和 step 记录 |
| CLI stdout、stderr 与退出码 | Claude 程序报告了哪些消息/事件、整次运行怎样结束 | _run_claude_turn 与 CLI 事件转换 |

一次模型请求成功，不保证 Claude 随后的本地操作和整次运行成功。当前适配器会把 CLI 输出整理成 outputs、trace_events、usage，再组成 AdapterResponse；Proxy 中的训练轨迹仍是另一份数据。

### 3.1 与已读 Slime 对齐

1. Slime BaseAdapter._run_turn 接收 Claude 发来的模型 HTTP 请求，调用模型后通过 manager.record_turn 记录轨迹。
2. Slime 的 Harness 同时也把 CLI 输出写入 `.harness/trajectory.jsonl`。文件名里有 trajectory，不代表它就是 token 级训练轨迹。
3. Dressage BlackboxServer._run_turn 组织一次 Agent 调用；_run_claude_turn 启动 CLI、收集 stdout。这两个函数不能按名字与 Slime 的 BaseAdapter._run_turn 当作同一层。

Slime 对照使用此前学习版本 18868a79，Dressage 使用当前固定版本 3e3142fe；不作最新版本的全面优劣比较。

<a id="where-to-read"></a>

## 4. 想分析哪件事，就从哪个入口看

| 当前问题 | 对应入口 | 读到哪里停 |
| --- | --- | --- |
| Claude 怎样启动，stdout 去哪里 | [_run_claude_turn](../topics/01-native-agent-rollout/steps/step-006-agent-execution/02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter._run_claude_turn.md) | 看创建进程、管道读取、退出和返回 |
| CLI 事件怎样变成结果 | [convert_claude_code_stream_events](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/adapters/claude_code.py#L939) | 看 outputs、trace_events、usage 的来路；不自动精读每类事件 |
| 模型请求为什么经过代理 | [build_env](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/adapters/claude_code.py#L211) 与 [_start_proxy](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/adapters/claude_code.py#L609) | 对上本地代理地址与外部上游地址 |
| 模型生成数据怎样被记录 | [Proxy 的 step 记录位置](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/server.py#L2479) | 先追一份请求与 token/logprob 的交接 |
| 记录怎样交给训练消费 | [generate 中的轨迹读取](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L301) 与 [expand_segments_to_samples](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/multi_segment.py#L118) | 分清 CLI 结果与训练 Sample，后续按正式 scope 展开 |

这张表是来源索引，不表示以上函数都已读过，也不要求现在一起展开。当前继续读 _run_claude_turn 的四步主线即可；读到不同问题时再按表回查。

## 5. 资料与验证边界

- [Slime BaseAdapter._run_turn](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L387)、[record_turn 调用](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L463)、[Harness 的 CLI 日志出口](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/common.py#L111)。
- CLI 事件示例来自已核对的仓库测试，经缩减展示；不是本次真实 Agent 输出。
- 本文是源码对照。只有另页的 Python 管道小例子有本地执行记录，没有运行 Claude、模型或完整训练。
- [拆分前完整卡片](../topics/01-native-agent-rollout/steps/step-006-agent-execution/references/history/run-claude-turn-before-split-2026-11-08.md)保留原有全部解释、问题和原话；[本次整理过程](../topics/01-native-agent-rollout/steps/step-006-agent-execution/04-flow.md#stdout-notes-split)记录迁移范围。
