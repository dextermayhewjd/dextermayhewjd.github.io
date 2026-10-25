# BaseHarness.run

首次接触：Step 1｜最近认识更新：尚无用户新增职责表述；本步建立助手解释。

**我的理解（原话）**

尚无直接职责复述。用户当前的问题（节选）是：

> 这里是怎么从harness_cls().run到这里的baseAdapter._run_turn的呢？

**使用场景与源码**

`generate` 已准备工作区和会话，调用选中的 Harness 运行 Agent，收到退出码后继续收集代码改动。以下省略调用参数，保留实际接收返回值的方式：

```python
agent_exit_code = await HARNESS_CLS().run(...)
diff_text = await swe.git_diff(...)
```

**Input → Output**

教学构造，假设沙箱和工作区已存在，CLI 正常结束；以下返回值用于说明接口，未实际运行 Agent。

```python
# Input
# sb 已由调用方准备，是已有的 Sandbox 实例
workdir = "/workspace/repo"
session_id = "sid-demo"
adapter_url = "http://adapter-host:18001"
time_budget_sec = 300
prompt = "读取工作区中的任务并修复代码"

# Output：假设本次 CLI 以退出码 0 正常结束
agent_exit_code = 0
```

副作用：确保运行用户、构造上下文、写入配置，并由具体 Harness 启动和等待 CLI。CLI 运行期间可以向 Adapter 发送模型请求；每次请求的 HTTP 响应是 `_run_turn` 的产物，`run` 自身返回的是 CLI 退出码。

**LLM 根据调用处补充的模型**

> `BaseHarness.run` 将准备好的任务环境交给具体 Harness，运行外部 CLI 并等待退出。CLI 通过配置的地址向 Adapter 发起 HTTP 请求，路由再进入 `_run_turn`；两者之间通过运行中的 CLI 和 HTTP 相连。

**暂时不清楚**

- 用户尚未反馈是否已区分 Harness 的等待与一次 HTTP 请求的处理。
- CLI 内部怎样组织多轮模型请求与工具执行，尚未展开。
- 运行用户、配置写入、命令等待与取消的内部实现，尚未展开。

**来源**

静态源码：固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `generate.py:205`、`harness/common.py:81`、`harness/claude_code.py:57`、`adapters/anthropic.py:48` 与 `adapters/common.py:318`。完整关系与固定源码链接见[任务讲解](../../../../../../../../../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#harness-to-adapter)。形成过程见 [Step 1 的问题与澄清](../../../../../../../step-001-harness-to-adapter/04-flow.md#从启动到请求入口)。

- 继承自：[Step 1 的完整函数记录](../../../../../../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md)；只继承与重算链接，原认识时间、原话和未知保留。

- 本次继承自：[Step 2 的完整记录](../../../../../../../step-003-swe-evaluation/03-long-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md)；仅复制、补来源与重算链接，原话、认识时间和未知保留。
