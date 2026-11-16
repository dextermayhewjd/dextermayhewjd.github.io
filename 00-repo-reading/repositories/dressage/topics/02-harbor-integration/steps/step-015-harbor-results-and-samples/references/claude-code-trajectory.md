# Claude Code 的执行记录如何变成 Harbor 轨迹

[返回本步 scope](../01-scope.md) · [返回日志上传函数卡](../02-short-term-memory/functions/harbor/trial/trial.py/Trial._upload_agent_logs.md)

本文说明跨函数的数据交接，供 Agent 执行、日志上传和结果分析处共同引用。CLI 原生日志与 Harbor 的统一轨迹是不同产物；上传日志只是后续传输动作。

源码依据：本地 Harbor v0.25.0，提交 `fdba28fc411e47e8765420a1a063b4918fce3def`。下列数据是依据源码和测试字段构造的教学例子，不是真实运行输出。

## 先分清：本文是谁的代码？

**本文 1–4 节围绕 Harbor 的日志整理链路。CLI 是被启动的外部程序；这些转换函数都不是 Dressage 的实现。**

| 名称或位置 | 属于谁 | 本文中的作用 |
| --- | --- | --- |
| Claude Code CLI | 外部 Agent 程序 | 执行任务，写原生会话 JSONL |
| `src/harbor/agents/installed/claude_code.py` 中的 `ClaudeCode` | **Harbor** | 启动 CLI；读取、转换原生日志，写统一轨迹 |
| `src/harbor/trial/` 中的 `Trial`、`SingleStepTrial` | **Harbor** | 安排执行、日志同步、产物收集和评测 |
| `dressage/integrations/harbor/` | **Dressage** | 将 Harbor 接入 Dressage；不是上面这些函数所在的目录 |
| `dressage/proxy/` | **Dressage** | 在模型请求链路记录 token/logprob 等信息；不属于本文的 JSONL 转换链 |

**双方都有记录结构，但这里不是两套相同的轨迹模板。** Harbor 的 ATIF 轨迹统一表达 Agent 执行步骤；Dressage Proxy 的记录服务于模型交互采集及后续训练数据处理。相同的 trajectory 名称不能作为数据格式或来源相同的依据。

## 安装时是否需要修改 Agent，才能产出轨迹？

**需要针对具体 Agent 编写适配，但当前 Harbor 的 Claude Code 路径并不是修改 CLI 源码以注入轨迹功能。** 适配由 Harbor 的 `ClaudeCode` 类承担；它与外部 `claude` 可执行程序不是同一个东西。

| 阶段 | Harbor 中的实现 | 做什么 |
| --- | --- | --- |
| 安装 | `BaseInstalledAgent.setup` → `ClaudeCode.install` | 检查 CLI 版本；必要时安装官方包或使用官方安装脚本 |
| 运行 | `ClaudeCode.run` | 设置 `CLAUDE_CONFIG_DIR`，以 `--verbose --output-format=stream-json --print` 启动 CLI，并用 tee 保存输出 |
| 整理 | `ClaudeCode.populate_context_post_run` → `convert_trajectory` | 读取 CLI 原生会话 JSONL，转换并写出 Harbor 统一轨迹 |

安装本身不产生本次任务轨迹。接入新 Agent 时需要确认它如何留下日志，并提供对应解析逻辑；若本身没有合适的记录能力，才需要另外设计采集方式。不能据此推断所有 Agent 都必须修改 CLI。

本轮证据：[通用 setup](/home/hongshi/projects/harbor/src/harbor/agents/installed/base.py:1126)、[ClaudeCode.install](/home/hongshi/projects/harbor/src/harbor/agents/installed/claude_code.py:635)。安装实现检查已有版本，必要时使用 `@anthropic-ai/claude-code` 或官方 bootstrap 脚本；在该函数中没有为轨迹修改 CLI 源码的步骤。运行及整理的证据见后文。

### 已有 function memory：从这里回看

以下都是 **Harbor 函数**，卡片最初写于 Step 014；此处链接原卡顶部，供按需回查，不新增或重复创建卡片。

| 想回看什么 | 已有函数卡 | 已记录的范围 |
| --- | --- | --- |
| 谁调用 Agent 的准备入口 | [Trial._setup_agent](../../step-014-model-routing-and-api-contract/02-short-term-memory/functions/harbor/trial/trial.py/Trial._setup_agent.md) | Trial 委派选定 Agent 的 setup |
| 安装准备如何组织 | [BaseInstalledAgent.setup](../../step-014-model-routing-and-api-contract/02-short-term-memory/functions/harbor/agents/installed/base.py/BaseInstalledAgent.setup.md) | 创建目录、委派具体 install、按需查询版本；未在该卡展开 ClaudeCode.install 内部 |
| 如何启动 CLI 并保存输出 | [ClaudeCode.run](../../step-014-model-routing-and-api-contract/02-short-term-memory/functions/harbor/agents/installed/claude_code.py/ClaudeCode.run.md) | 运行配置、CLI 命令、输出保存；收尾轨迹整理已有职责提示 |

**未找到独立函数卡**：`ClaudeCode.install`、`Trial._sync_agent_output`、`ClaudeCode.populate_context_post_run`、`ClaudeCode.convert_trajectory`。这些仍使用本文的源码链接和说明，不为补齐列表新建卡片。

## 1. 【CLI → Harbor】先看文件如何交接

**核心原理：CLI 写原生日志，Harbor 通过文件读取，再转换为自己的轨迹格式。** 当前跟随的是执行结束后的整理路径：

```text
运行环境里的 Claude Code CLI
  │ Harbor 设置 CLAUDE_CONFIG_DIR=/logs/agent/sessions
  │ CLI 执行过程中保存原生会话事件
  ▼
/logs/agent/sessions/projects/<cwd-slug>/<session-id>.jsonl
  │ _download_agent_logs：下载目录，或直接访问挂载目录
  ▼
宿主机 <trial_dir>/agent/sessions/projects/.../*.jsonl
  │ open 逐行读文件 + json.loads 转成 Python 字典
  │ 按事件类型、消息和工具调用 ID 整理为 Step
  ▼
Harbor 的 Trajectory 对象
  │ json.dump 写文件
  ▼
宿主机 <trial_dir>/agent/trajectory.json
```

JSONL 就是“一行一个 JSON 对象”的文本文件。Harbor 不需要读取 CLI 的内存，也不是等待 CLI 返回一个 Trajectory 对象；它读取 CLI 留在磁盘上的记录。`claude-code.txt` 是另外由 tee 保存的终端输出，不要与这里主要读取的原生会话 JSONL 混为一份文件。

读取动作的教学裁剪，来自 `_convert_events_to_trajectory`（省略空行和坏行处理）：

```python
for session_file in session_files:
    with open(session_file, "r", encoding="utf-8") as handle:
        for line in handle:
            raw_events.append(json.loads(line.strip()))
```

当前的 `_upload_agent_logs` 位于这次整理之后：它把本地已有的 agent 目录同步回环境，自己不负责生成轨迹。

## 2. 【CLI 产生，Harbor 取回】同一次执行留下什么

统一场景：Agent 修复 `/app/calc.py` 的加法函数，运行 `pytest -q`，得到 `1 passed`，最后回复“修复完成”。只观察其中一次工具调用，不要求先读完所有转换函数。

Linux 场景在环境中先写 `/logs/agent/`。取回宿主机后，目录可呈现为：

```text
<trial_dir>/agent/
├── claude-code.txt
└── sessions/
    └── projects/
        └── <cwd-slug>/
            └── <session-id>.jsonl
```

**claude-code.txt** 保存 CLI 的输出流（stderr 也重定向进来），因此不是保证每行均为合法 JSON 的纯数据文件。最后一条结果事件可以是下面这样的节选：

```json
{"type":"result","subtype":"success","result":"修复完成","total_cost_usd":0.001}
```

这里的费用是教学值。Harbor 的 `_parse_total_cost_from_stream_json` 会从这种 result 事件读取费用；文件不存在或事件不符合预期时可能取不到。

**session JSONL** 保存会话事件。一行一个 JSON 对象；下面根据 Harbor 单元测试的事件字段缩减，展示“要求执行工具”和“工具执行结果”两行：

```jsonl
{"type":"assistant","sessionId":"session-A","timestamp":"2026-11-16T10:00:00Z","message":{"id":"msg-test-1","role":"assistant","content":[{"type":"tool_use","id":"call-test-1","name":"Bash","input":{"command":"pytest -q"}}]}}
{"type":"user","sessionId":"session-A","timestamp":"2026-11-16T10:00:01Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"call-test-1","content":"1 passed"}]}}
```

这里第二行 type 为 user 是会话协议的记录形式，不表示真人手工输入了测试输出。tool_use_id 将结果关联到具体调用。

转换器主要读取 sessions 下的会话事件组织轨迹，也会从 claude-code.txt 等资料补充信息；不能将所有日志统称为一个只有最终答案的文件。


## 3. 【Harbor】把这些事件整理成什么

`_sync_agent_output` 先取回/访问日志，AgentContext 为空时委派当前 Agent 整理。Claude Code 转换成功后，可将日志组织为结构化轨迹并写入本地 agent/trajectory.json。

以下只展示同一次 Bash 调用对应的一个步骤；使用真实字段，省略完整文件的 Agent 元信息、其他步骤和统计等，不能直接当作完整 schema 测试样例：

```json
{
  "schema_version": "ATIF-v1.7",
  "session_id": "session-A",
  "steps": [
    {
      "step_id": 4,
      "source": "agent",
      "message": "",
      "tool_calls": [
        {"tool_call_id":"call-test-1","function_name":"Bash","arguments":{"command":"pytest -q"}}
      ],
      "observation": {
        "results": [{"source_call_id":"call-test-1","content":"1 passed"}]
      }
    }
  ]
}
```

原始事件只有工具调用、没有文字说明，所以此例 message 为空，不凭空补出 Agent 说过的话。step_id=4 只是示意它位于整段任务中间。

**两份数据相似是正常的：统一轨迹由原生会话事件整理而来，不是重新执行一次，也不是另一套独立采集。**

```text
CLI：原生会话日志                       Harbor：统一轨迹
一行 assistant，含 tool_use       ┐
  id: call-test-1                 ├─ 关联、整理 ─→ 一个 Step
一行 user，含 tool_result         │               tool_calls: 要执行什么
  tool_use_id: call-test-1        ┘               observation: 实际返回什么
```

这里跨日志行按调用 ID 配对；文件格式也从原生事件流，整理为 Harbor 的统一 Trajectory/Step 结构，便于统一查看、分析不同 Agent 的执行。并非只是改文件名。

具体来源链（**下面四项全部属于 Harbor 仓库**，只定位，不要求同时深入所有函数）：

1. [_sync_agent_output](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:1167) 取回日志，并在适用条件下委派补充记录。
2. [populate_context_post_run](/home/hongshi/projects/harbor/src/harbor/agents/installed/claude_code.py:1860) 调用 convert_trajectory。
3. [convert_trajectory](/home/hongshi/projects/harbor/src/harbor/agents/installed/claude_code.py:809) 找到会话目录，委派 [_convert_events_to_trajectory](/home/hongshi/projects/harbor/src/harbor/agents/installed/claude_code.py:1327) 读取、整理 JSONL；[_convert_event_to_step](/home/hongshi/projects/harbor/src/harbor/agents/installed/claude_code.py:833) 产生统一 Step。
4. 回到 populate_context_post_run，写 trajectory.json，并补充 AgentContext 摘要。

原生 JSONL 是外部 CLI 写的，Harbor 仓库能定位的是配置目录、启动 CLI、读取文件和转换逻辑，不能把这些入口称为 CLI 内部的日志生产实现。

日志中的 tool_use 与 tool_result，在这里整理成 tool_calls 与 observation。完整轨迹还可以容纳用户任务、其他动作、最终回复及统计，转换器并非每遇到一行日志就机械生成一步。

随后可把 token 用量、费用等摘要填入 AgentContext；**AgentContext 并不等于整个 trajectory.json**。已有记录可能使整理跳过，解析也可能失败，故该文件不是每次保证生成。


## 4. 【Harbor】回到当前阅读位置

```text
SingleStepTrial._run
  → _run_agent
      → 执行 Agent
      → finally: _sync_agent_output
          → 取得日志
          → 按条件整理轨迹与摘要       ← 本文解释的交接
  → _upload_agent_logs                ← 当前函数卡：同步已有日志目录
  → _collect_artifacts                ← 后续：按配置收集任务文件
  → _run_verifier
```

回到 scope 第 3 项后才涉及另一条交接：**Harbor 发出 END 事件 → Dressage 插件回调 → Dressage ProxyClient.read_trajectory**。后者读取 Proxy 服务里的模型交互记录，并非打开本文的 `agent/trajectory.json`。

依据：[Dressage `_commit_attempt_once` 调用 ProxyClient](/home/hongshi/projects/Dressage/dressage/integrations/harbor/artifacts.py:391)。当前说明不展开 Proxy 存储。

<details>
<summary>来源与验证边界</summary>

- [ClaudeCode.run：设置会话目录](/home/hongshi/projects/harbor/src/harbor/agents/installed/claude_code.py:2152)、[启动 CLI 并保存输出流](/home/hongshi/projects/harbor/src/harbor/agents/installed/claude_code.py:2205)。
- [Trial._download_agent_logs](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:787)、[Trial._sync_agent_output](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:1167)。
- [会话事件转换测试](/home/hongshi/projects/harbor/tests/unit/agents/installed/test_claude_code_trajectory.py:20)：样例字段的参考依据。
- [本步讨论记录](../04-flow.md)：保留原问题及理解修正；迁移说明不代表用户已掌握全部实现。
- 本文只说明当前跟随的执行后整理路径，不断言轨迹只能在执行结束后产生，也不保证缺失或解析失败的日志能生成轨迹。

</details>
