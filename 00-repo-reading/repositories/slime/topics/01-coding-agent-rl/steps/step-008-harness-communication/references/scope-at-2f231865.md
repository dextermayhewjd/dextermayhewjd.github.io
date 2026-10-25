> 2026-10-24 更新 scope 前的完整记录，保留 `2f231865` 的源码位置与当时范围，仅重算相对链接。更早的宽范围另见 scope-before-step-008.md。

---

# 01 · 阅读范围：Harness 启动 CLI 与等待返回

[步骤入口](../README.md) · [本步函数](../02-short-term-memory/overview.md) · [前序记忆](../03-long-term-memory/overview.md)

## 1. 阅读目标

继续理解 Coding Agent / Coding RL。本步弄清准备好的沙箱与任务参数怎样变成一次 CLI 运行，以及整次 CLI 结束后，退出码怎样回到 `generate`。

2026-10-23 按用户确认收束此范围；HTTP 接收入口转到 [Step 9](../../step-009-adapter-request-entry/01-scope.md)。此前的较宽范围保留在[原 scope 快照](scope-before-step-008.md)，调整缘由见[本次记录](../04-flow.md#close-launch-open-request-entry)。

前序准备作为已有输入使用，有疑问时回查对应卡片。这里不重新讲解安装、工作区初始化或 `_run_turn` 的全部转换细节，也不把准备记录存在当成用户已掌握全部实现。

## 2. 找到指挥官函数

整体指挥官仍是 `examples/coding_agent_rl/generate.py::generate`。本步聚焦它第 205 行的 `HARNESS_CLS().run(...)`，实际展开的是 [slime/agent/harness/common.py 中的 BaseHarness.run](../02-short-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md)（81–104 行）。

`common.py` 是文件名，`BaseHarness` 是其中定义的类，`run` 是这个类的方法，因此完整定位写作 `common.py → BaseHarness.run`。当前 `HARNESS_CLS` 是 `ClaudeCodeHarness`，它继承 `BaseHarness` 的 `run` 实现；具体的 `write_config` 与 `launch_and_wait` 定义在 `harness/claude_code.py` 的 `ClaudeCodeHarness` 类中。`run` 串联用户准备、运行上下文、CLI 配置和启动等待；首先深入 [ClaudeCodeHarness.launch_and_wait](../02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md)，因为它直接决定启动什么程序，以及程序拿到哪个 API 地址。

源码固定于 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。当前前提是：CLI 已安装，题目文件已放入工作目录，Adapter 已监听，会话已登记，Adapter 持有 SGLang Router 地址。上述服务的实际可达性未运行验证。

## 3. 给出真正干活的核心骨架

### 3.1 继承整体骨架，定位第 4 项

以下沿用 `evaluation=False` 正常路径的教学裁剪。按五类过滤规则折叠通用配置解析、前置检查、日志计时、超时异常和失败包装；保留业务顺序、返回值与上下文嵌套。局部涉及目标地址和会话标识的配置是本步问题，继续保留。

```python
state.adapter.open_session(...)                          # 1. 登记会话；Step 5
async with boot_agent_sandbox(...) as sb:                 # 2. 沙箱与 CLI 就绪；Step 6
    await swe.prepare_workspace(...)                     # 3. 工作区与题目准备；Step 7
    agent_exit_code = await HARNESS_CLS().run(...)        # 4. 本步：启动 CLI，等待整次运行结束
    diff_text = await swe.git_diff(...)                   # 5. CLI 结束后取得改动

reward, applied_cleanly = await swe.run_evaluation(...)   # 6. 独立评测；Step 3
samples = await state.adapter.finish_session(...)        # 7. 导出训练样本；Step 4
...  # generate 的结果检查、附加元数据与外层清理暂时折叠
return samples
```

### 3.2 展开本地启动的局部骨架

进入 `harness/common.py` 中的 `BaseHarness.run` 时，`sb` 仍是 Slime 一侧的本地对象。`adapter_url`、`session_id`、`workdir` 和 `prompt` 均由 `generate:205–212` 传入；具体输入与返回值见函数卡片。

```python
# slime/agent/harness/common.py · BaseHarness.run
await _sandbox.ensure_agent_user(...)       # 97：复用用户与目录准备
ctx = HarnessContext(...)                  # 98–102：组合运行上下文
await self.write_config(...)               # 103：ClaudeCodeHarness 写 CLI 配置
return await self.launch_and_wait(...)      # 104：交给具体实现启动，等待并返回退出码
```

第 104 行进入 `ClaudeCodeHarness.launch_and_wait:57–71`：组装 `cmd`，把 Adapter 地址和会话标识放入 `env`，再交给 `run_agent`。`run_agent` 进一步调用 `exec_and_wait`，由沙箱接口写启动脚本并执行。CLI 整体退出后，退出码沿这条本地调用链返回 `generate:205`，随后才进入 213 行的改动提取。

### 3.3 等待期间的分支留给 Step 9

```text
本步：启动 CLI → 等待 CLI 整次运行 → 取得退出码，回到 generate
                        │
               Step 9：CLI 经 HTTP 请求 Adapter
                        └─ Adapter 请求 SGLang，回复再回 CLI
```

这里保留交接位置；接收与分派的具体机制在 [Step 9](../../step-009-adapter-request-entry/01-scope.md)展开。步骤编号表示阅读顺序，这个分支发生在本步等待期间。

<a id="harness-local-navigation"></a>

### 3.4 阅读导航与停止位置

局部接续沿 `run:97 → 98–102 → 103 → 104`：[ensure_agent_user](../02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md) 已从前序记忆调入本步 `02`，先短回顾；接着说明 `ctx` 如何组合输入、`write_config` 写入什么，再深入启动与等待。下表的“首先深入”表示重点展开处，前面的交接仍按顺序说明。

| 顺序 | 从哪里进入 | 本轮看清什么，读完回到哪里 |
| --- | --- | --- |
| 1 · 定位局部组织 | [common.py · BaseHarness.run，81–104](../02-short-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md) | 接清输入、`ctx`、两个具体实现与退出码；用户准备复用本步调取的旧卡，重点停在 104 行 |
| 2 · 首先深入 | [ClaudeCodeHarness.launch_and_wait，57–71](../02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) | `prompt → cmd`，`adapter_url / session_id → env`，随后交给 `run_agent`；返回值仍是退出码 |
| 3 · 接上远端启动 | [run_agent，107–122](../02-short-term-memory/functions/slime/agent/harness/common.py/run_agent.md) → [exec_and_wait，82–145](../02-short-term-memory/functions/slime/agent/sandbox.py/exec_and_wait.md) | 看清命令、环境、输出文件怎样交给远端执行，以及完成标记怎样带回退出码；底层 SDK 保持接口边界 |
| 4 · 整次运行结束 | `exec_and_wait → run_agent → launch_and_wait → run → generate:205` | 退出码回到外层，接续 213 行 `swe.git_diff`；一次模型回复与 CLI 整体退出分开 |

**停止位置**：能串起运行前提、CLI 配置、命令与环境、远端启动及退出码返回。接收入口、两次模型 HTTP 往返由 Step 9 接续；SDK 编码、完整超时恢复和 CLI 内部工具循环仍按需展开。已读关系的收拢见 [task flow](../05-task-flow.md)。
