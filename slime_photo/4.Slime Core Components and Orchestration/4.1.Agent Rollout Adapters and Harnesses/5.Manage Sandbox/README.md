# 动作 5 Manage Sandbox 渐进阅读

## 在任务生命周期中的位置

本章：环境能力贯穿准备、运行、收尾；不是仅在启动前执行的一步。

[![当前位置：动作 5：Manage Sandbox](../../../../static/images/slime-lifecycle/action-5.svg)](../../../../static/images/slime-lifecycle/action-5.svg)

[返回生命周期总览](../README.md#任务生命周期与原图的用途) · [放大当前位置图](../../../../static/images/slime-lifecycle/action-5.svg)

## 应该看哪些 Python 文件

```text
sandbox.py：认识接口和 E2BSandbox 实现
  → generate.py：读 boot_agent_sandbox()，看谁创建和释放
  → Harness 文件：看调用方怎样使用 sb
  → 回到 sandbox.py：看具体操作怎样落实
```

下面的路径相对于本地 Slime 源码仓库 `/home/hongshi/projects/slime/`，链接指向本文固定版本 `8c17b676`。本章的主要实现集中在 `sandbox.py`，其余文件帮助你找到创建者和调用者。

| 顺序 | Python 文件与入口 | 本章重点 |
| --- | --- | --- |
| 1 | [slime/agent/sandbox.py:28](https://github.com/dextermayhewjd/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/sandbox.py#L28) — `Sandbox`；`:160` 的 `E2BSandbox` | 先认出 `exec()`、`write_file()`、`read_file()` 接口；再读 `:281` 的创建、`:302` 的释放、`:309` 的命令执行、`:342` / `:380` 的文件读写实现 |
| 2 | [examples/coding_agent_rl/generate.py:96](https://github.com/dextermayhewjd/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/examples/coding_agent_rl/generate.py#L96) — `boot_agent_sandbox()` | 谁创建沙箱、调用 `install_cli()`、交出 `sb` 并在退出时释放；再看 `:203` 的任务代码如何进入这个上下文 |
| 3 | [slime/agent/harness/common.py:81](https://github.com/dextermayhewjd/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/harness/common.py#L81) — `BaseHarness.run()` | 找到 `ensure_agent_user()` 的调用；再读 `:107` 的日志目录准备、`:125` / `:154` 的 CLI 和 Node 安装怎样使用沙箱接口 |
| 4A | [slime/agent/harness/claude_code.py:36](https://github.com/dextermayhewjd/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/harness/claude_code.py#L36) — `install_cli()`、`:44` 的 `write_config()` | Claude Code 分支向沙箱提交哪些安装与配置操作；先选这一分支或下一分支 |
| 4B | [slime/agent/harness/codex.py:48](https://github.com/dextermayhewjd/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/harness/codex.py#L48) — `install_cli()`、`:56` 的 `write_config()` | Codex 分支向沙箱提交哪些安装与配置操作 |
| 按需 | [examples/coding_agent_rl/swe.py:177](https://github.com/dextermayhewjd/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/examples/coding_agent_rl/swe.py#L177) — `prepare_workspace()`、`:230` 的 `git_diff()` | 工作区和题目文件怎样准备，任务结束后怎样从沙箱收集代码 diff |

`sandbox.py` 建议分两遍读：第一遍读接口、创建、释放、命令和文件操作，以及 `:390` 的 `ensure_agent_user()`；第二遍再读 `:237` 的 `_rpc_retry()`。`:82` 的 `exec_and_wait()` 是与 Exec Commands 相接的部分，先认出调用入口，再到动作 6 细读启动脚本与等待机制。

两章会出现同一批文件：Launch Agent 看 Harness 怎样组织启动要求；Manage Sandbox 看这些要求怎样经 `sb` 落到执行环境。章节按职责划分，一个 Python 文件可以同时参与多个动作。

![Agent Rollout Adapters and Harnesses 架构图](<../Agent Rollout Adapters and Harnesses.svg>)

[返回架构图与源码文件对应](../README.md) · [上一站 Launch Agent](<../4.Launch Agent/README.md>)

先从[纵向数据流](纵向数据流/README.md)开始，或直接[打开图文预览](纵向数据流/index.html)：顶部局部图沿同一份任务参数向下展开，每一步展示命令、文件内容与返回值，源码位置放在末尾折叠中。下面的渐进阅读作为补充。

这条箭头连接 **Agent Harnesses (ClaudeCodeHarness, CodexHarness)** 和 **Sandbox Environment (E2BSandbox)**。本章沿用 Translate & Forward 的阅读顺序：先理解目的与最小模型，再看具体输入输出，最后对应源码函数和生命周期。

## 先理解动作 5 为了什么

**动作 5 的目的是让 Harness 能够在沙箱中准备和使用 Agent 的执行环境。**

例如，要让 Claude Code 在 `/workspace/demo` 修改代码，光有任务指令还不够。环境中需要装好 CLI，有能够访问仓库的用户，CLI 的配置要落在这个用户的目录里，启动时还要传入模型入口等环境变量。Harness 通过沙箱接口完成这些操作。

| 问题 | 答案 |
| --- | --- |
| 谁需要这一步？ | 要安装、配置和运行 Claude Code / Codex 的 Harness |
| 为什么需要沙箱接口？ | Harness 提交命令和文件操作，由具体后端把操作送到执行环境 |
| 完成后得到什么？ | 可供 CLI 使用的环境，以及命令的退出码、输出或读回的文件内容 |

图中的 **Manage Sandbox** 覆盖 Harness 对执行环境的使用。对应到这个版本，职责需要分清：

| 部件 | 实际负责什么 |
| --- | --- |
| 外层 `boot_agent_sandbox()` | 创建 E2B 沙箱，调用 Harness 安装 CLI，离开上下文时释放沙箱 |
| `BaseHarness` 与两个子类 | 准备用户、写 CLI 配置、组织启动命令并等待结束 |
| `Sandbox` | 规定执行命令、读写文件和异步上下文管理的接口 |
| `E2BSandbox` | 实现这些接口，调用 E2B SDK，处理返回值和传输重试 |

**传入 `Harness.run()` 的 `sb` 已经是创建好的沙箱对象。**`run()` 内的 `ensure_agent_user()` 准备的是沙箱中的用户与权限。创建、安装和收尾的位置在第三篇展开。

## 先建立最小心智模型

```text
Harness holds sb: Sandbox
    -> sb.exec(cmd, user=..., env=...)
    -> E2BSandbox.exec()
    -> E2B SDK commands.run()
    -> command runs inside sandbox
    -> (exit_code, stdout, stderr) returns to caller
```

文件操作走另外两个接口：

```text
sb.write_file(path, content) -> E2B SDK files.write() -> sandbox file
sb.read_file(path)          -> E2B SDK files.read()  -> text string
```

Harness 的参数类型写成 `Sandbox`，本例传入的实际对象是 `E2BSandbox`。`Sandbox` 是 `Protocol`，描述调用方需要的能力；`E2BSandbox` 按这些方法提供实现，类定义没有继承 `Sandbox`。

| 数据 | 此时只需理解的含义 |
| --- | --- |
| `sb` | 执行环境的操作对象；CLI 和工作目录在该环境中 |
| `cmd` | 交给沙箱执行的 shell 命令字符串 |
| `user` | 命令或文件操作使用的沙箱用户，默认 `root` |
| `env` | 给这次命令传入的环境变量 |
| `ExecResult` | `(exit_code, stdout, stderr)` 三元组 |

## 用一条短命令看交接

以下是教学调用；假设 `sb` 已创建，且沙箱中已有 `agent` 用户。

```python
exit_code, stdout, stderr = await sb.exec(
    "id agent",
    user="root",
    timeout=15,
    check=True,
)
```

假设命令成功，返回值可能是：

```python
(0, "uid=1000(agent) gid=1000(agent) groups=1000(agent)\n", "")
```

用户编号和输出是示意值。关键是：**命令在沙箱里执行，调用方收到的是退出码和两个输出字符串。**它不会把 `agent` 用户创建在运行 Slime 的宿主机上。

现在把它换成 `BaseHarness.run()` 中的真实第一步：

```python
await _sandbox.ensure_agent_user(sb, workdir)
```

这个辅助函数内部调用 `sb.exec()`，确认或创建 `agent` 用户、调整目录所有权，并设置 Git 的安全目录配置。它的成果主要是执行环境发生变化，函数本身返回 `None`。

## 认出最短的真实调用链

```text
BaseHarness.run()
    -> ensure_agent_user(sb, workdir)
        -> sb.exec(..., user="root", check=True)
            -> E2BSandbox.exec()
                -> self._sb.commands.run(...)
                -> return (exit_code, stdout, stderr)
```

用户准备完成后，同一个 `sb` 继续用于子类的 `write_config()` 和公共 `run_agent()`。需要等待整段 CLI 运行时，`exec_and_wait()` 把任务拆成“写启动脚本 → 后台启动 → 轮询结束标记”，底层仍使用这些沙箱接口。

## 按这个顺序继续阅读

| 阅读顺序 | 文档 | 这一层要理解什么 |
| --- | --- | --- |
| 主入口 | [纵向数据流](纵向数据流/README.md) · [图文预览](纵向数据流/index.html) | 沿同一份例子，看局部图和每一步的输入输出 |
| 1 | [命令和文件操作](1.命令和文件操作.md) | 从短命令开始，逐步增加用户、配置、文件和长命令 |
| 2 | [主路径和源码函数](2.主路径和源码函数.md) | 找到 Harness 调用处、沙箱实现、输入输出与副作用 |
| 3 | [创建入口和生命周期](3.创建入口和生命周期.md) | 谁创建与释放沙箱，怎样处理失败、重试和等待超时 |

## 与 run 调度及动作 6 的边界

`run()` 调度 `write_config()` 和 `launch_and_wait()`。动作 4 读清它们在 Harness 中怎样准备配置与启动信息，动作 5 从 `sb` 操作继续读两端：Harness 提交什么要求，Sandbox 接收什么参数、落实哪些环境变化。

Manage Sandbox 不只等于 `write_config()`；用户与权限、目录与文件、启动脚本和执行准备都在其中。`sb.exec()` 是通用命令接口，准备环境也会使用它；图中的动作 6 专指通往 Coding Agent CLIs 的执行。

**准备主线读到 CLI 启动请求就绪、进入执行后端的接缝为止**。`exec_and_wait()` 的脚本写入与旧状态清理属于准备；`:129` 提交后台启动命令、`:132` 的 `setsid bash` 使 CLI 开始执行，随后进入动作 6。等待标记与输出收集在本章作为接缝上下文标出，深入归动作 6。

## 动作 5 的说明到哪里结束

本章解释 Harness 怎样通过 `Sandbox` 接口操作环境，追踪到 `E2BSandbox` 调用 E2B SDK 的位置。动作 6 **Sandbox Environment → Coding Agent CLIs / Exec Commands** 与这里在执行命令处相接；CLI 内部的工具循环、E2B 网关和远端资源实现留在外部边界。

模型请求的转换继续见[动作 2 Translate & Forward](<../2.Translate & Forward/README.md>)；启动参数如何传入 Harness 见[动作 4 Launch Agent](<../4.Launch Agent/README.md>)。

固定源码版本：`8c17b676cb57af1d17ee4402e91e9209af84b60b`，与相邻动作 3、4 一致。路径均相对于 Slime 仓库根目录。补充文档的教学调用与输出为示意；纵向数据流中的命令、脚本和返回路径由真实函数配合沙箱记录器校验。具体范围见[源码与校验](纵向数据流/README.md)，本次没有连接 E2B 或运行真实 CLI。
