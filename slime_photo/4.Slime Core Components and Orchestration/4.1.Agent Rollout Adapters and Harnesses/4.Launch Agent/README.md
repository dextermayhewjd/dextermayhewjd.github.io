![Agent Rollout Adapters and Harnesses 架构图](<../Agent Rollout Adapters and Harnesses.svg>)

# 动作 4 Launch Agent 渐进阅读

[返回架构图与源码文件对应](../README.md) · [纵向交接数据](纵向数据流/README.md) · [图文预览](纵向数据流/index.html)

本章展开原图 **Slime Core → Agent Harnesses**：从启动请求进入 `run()`，读清 Harness 怎样组织用户准备、配置和启动信息。跨到 Sandbox 的操作由动作 5 深入；真正执行 CLI 的接缝归动作 6。

## 先理解动作 4 为了什么

**动作 4 的目的是把一次 Agent 任务的启动责任交给选定的 Harness。** Slime 侧已经知道任务、会话和模型入口，需要将这些信息交给负责 Agent 运行的组件。

例如，Slime 侧要启动一次代码任务。它把已准备的执行环境、工作目录、任务指令、会话 ID、模型入口和时间预算一起交给 Harness。调用者通过同一个 `run()` 接口，可以选择 Claude Code Harness 或 Codex Harness。

| 问题 | 答案 |
| --- | --- |
| 谁发起？ | 本地示例的外层 `generate()` |
| 接收者是谁？ | 选定的 `ClaudeCodeHarness` / `CodexHarness` 对象，其公共入口为继承的 `BaseHarness.run()` |
| 交接什么？ | 已有沙箱对象和五项启动参数 |
| 交接形式是什么？ | Python 异步函数调用 `await HARNESS_CLS().run(...)` |

## 图中的 Core 怎样对应到实际调用者

图把 Slime 侧组织 Agent 的职责画在 Core → Harness 这条边上。这个版本的实际组装入口是 `examples/coding_agent_rl/generate.py` 中的 `generate()`：它同时连接 Adapter 与 Harness。

**`BaseAdapter._run_turn()` 和 `TrajectoryManager` 不直接调用 Harness**。前者负责模型请求，后者负责轨迹；本章追踪外层任务入口怎样把启动责任交给 Harness，不能从图中推导出不存在的 `BaseAdapter → Harness.run()` 调用。

## 先建立最小心智模型

```text
Slime task side
    generate()
        → select HARNESS_CLS
        → pass sb + launch parameters
        → BaseHarness.run(...)
            → ensure_agent_user(sb, workdir)
            → create HarnessContext
            → write_config(sb, ctx)
            → launch_and_wait(sb, ctx, prompt, budget)
                → assemble command + environment
                → run_agent(sb, ...)
                    [Sandbox operations: action 5]
                    [CLI execution: action 6]
```

`run()` 是完整调度骨架。动作 4 要理解其中每一步的目的、输入和成果，包括 `write_config()` 和 `launch_and_wait()`；当它们调用 `sb` 时，动作 5 从同一调用处继续解释环境如何落实操作。

## 用一份启动信息看交接

以下为教学值；地址、目录和会话 ID 均为示意值。

```python
await HARNESS_CLS().run(
    sb,
    workdir="/workspace/demo",
    session_id="cagent-demo-0-0",
    adapter_url="http://192.0.2.10:18001",
    time_budget_sec=1800,
    prompt="Read PROBLEM_STATEMENT.md and resolve the issue.",
)
```

| 数据 | 在动作 4 中的含义 |
| --- | --- |
| `sb` | 已准备的执行环境对象，作为参数交给 Harness |
| `workdir` | 本次任务使用的工作目录 |
| `prompt` | 本次任务的启动指令 |
| `session_id` | 本次任务的会话标识 |
| `adapter_url` | 已准备的模型请求入口地址 |
| `time_budget_sec` | 本次运行的时间预算 |

动作 2 交接消息与工具定义；**动作 4 交接任务的运行上下文与启动责任**。

## 按这个顺序继续阅读

| 顺序 | 文档 | 看清什么 |
| --- | --- | --- |
| 1 | [启动参数与配置、命令](1.启动参数和模型入口.md) | 参数怎样进入上下文，再形成配置与启动信息 |
| 2 | [主路径和源码函数](2.主路径和源码函数.md) | 完整 `run()` 骨架、子类实现及沙箱调用位置 |
| 3 | [入口准备和动作边界](3.会话入口和生命周期.md) | 哪些条件已准备，哪些机制留给其他动作 |
| 图文 | [纵向交接数据](纵向数据流/README.md) · [预览](纵向数据流/index.html) | 同一份参数变成配置、命令和环境变量，并交给沙箱 |

## 在哪里停下

**本章读到 Harness 将配置与准备好的启动信息交给 Sandbox 的接口**。`write_config()`、`launch_and_wait()` 都展开 Harness 侧的工作；环境如何执行这些准备操作接动作 5，CLI 进程真正开始运行接动作 6。

这些动作按跨组件职责划分，同一函数可以连接多条边。运行时 `run()` 会等待下游完成；阅读时可以先读调度，再下钻[动作 5 Manage Sandbox](<../5.Manage Sandbox/README.md>)，最后进入动作 6 CLI 执行、动作 7 模型请求。不能把箭头编号当作互不重叠的函数清单。

固定源码：`8c17b676cb57af1d17ee4402e91e9209af84b60b`。源码路径相对于 Slime 仓库根目录；本章只核对交接接口，没有运行真实 Agent。
