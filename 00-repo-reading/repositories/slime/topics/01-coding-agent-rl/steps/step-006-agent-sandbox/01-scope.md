# 01 · 阅读范围：启动执行沙箱

[本步入口](README.md) · [前一步任务总结](../step-005-agent-preparation/05-task-flow.md) · [前序记忆](03-long-term-memory/overview.md) · [旧版 scope](references/scope-at-2f231865.md)

## 1. 阅读目标

- **整体目标**：理解 Coding Agent / Coding RL 的运行流程。
- **本步问题**：已有任务镜像怎样变成可供 Agent 使用的执行沙箱 `sb`，并在使用结束后回收？
- **阅读范围**：沿 `boot_agent_sandbox` 一次正常启动的路径，读清对象创建、环境就绪、CLI 准备、交付与退出；具体后端和失败机制按需展开。

## 2. 指挥官函数

- **整体位置**：`_generate` 已登记本次会话，现在准备执行环境；取得 `sb` 后，调用方才能准备工作区并运行 Agent。
- **本步指挥官**：[boot_agent_sandbox:111–164](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L110-L164)，入口是 [_generate:283](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L283-L298) 的 `async with`。
- **选择理由**：它串起取得沙箱、安装 CLI、交出对象和退出回收，能够在同一条主线中看清环境的完整使用边界。

## 3. 给出真正干活的核心骨架

### 3.1 继承整体骨架，定位第 2 项

沿用前几步的 `evaluation=False` 正常路径。以下为教学裁剪：省略多数参数、配置检查、追踪、日志、超时和失败包装，保留实际调用顺序与环境上下文；`baseline` 和运行统计接回 Step 002。

```python
adapter.open_session(...)  # 1. Step 005：登记会话
async with boot_agent_sandbox(...) as sb:  # 2. 本步：准备并交出执行沙箱
    baseline = await swe.prepare_workspace(...)  # 3. 准备工作区，取得初始快照
    agent_exit_code = await harness.run(...)  # 4. 运行 CLI，等待结束
    # CLI 运行期间，通过 HTTP 进入 Step 001 的模型请求流程
    agent_metrics = await harness.collect_metrics(...)  # Step 002：收集运行统计
    diff_text = await swe.git_diff(...)  # 5. Step 002：提取代码补丁

reward, applied_cleanly = await swe.run_evaluation(...)  # 6. Step 003：独立评测
samples = await adapter.finish_session(...)  # 7. Step 004：导出样本
...  # 返回前的结果处理，以及最终会话清理
return samples
```

本步进入第 2 项。沙箱在上下文块中持续供后续调用使用，离开该块时回收；本页只展开沙箱的准备与交接，块内工作区和 CLI 运行保留位置。

### 3.2 接住已有输入，展开局部骨架

- **题目输入，复用前序认识**：`image` 来自 `md["image"]`，`instance_id` 来自同一份题目信息。`md` 的整理已在 [Step 003](../step-003-swe-evaluation/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_metadata_scaleswe.md) 阅读；本步只跟住镜像标识怎样交给沙箱工厂。
- **执行工具**：调用方传入本次 Agent 对应的 `harness`，供安装 CLI 使用。本轮沿用 Claude Code 示例，先看未指定 native 安装包时的 npm 路径；其他安装方式保留分支入口。
- **追踪上下文**：调用处传入 `trace=base_sample`。本步保留其传递关系，追踪实现暂不展开。

完整传参位置见 [_generate:283](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L283)。

<a id="boot-agent-sandbox-local-skeleton"></a>

以下从 `boot_agent_sandbox` 裁剪：只保留一次准备成功的路径，暂时折叠并发限流、重试、日志、追踪与失败回收；保留成功交付后的退出清理。

```python
cand = create_sandbox(...)  # 121：按后端配置构造沙箱对象
await cand.__aenter__()  # 132：使该对象对应的执行环境就绪
await (harness or HARNESS_CLS()).install_cli(...)  # 135：在环境中准备 CLI
sb = cand  # 143：接住已经准备好的对象
try:
    yield sb  # 161：交给调用处的 as sb，本函数暂停
finally:
    await sb.__aexit__(...)  # 164：调用方离开上下文后执行回收
```

`yield sb` 将同一个对象交到 `_generate:283`，随后供 `285–298` 的工作区准备、CLI 运行和结果收集使用。外层离开这个 `async with` 后，才继续这里的 `finally`；正常退出后，调用方在 `301` 行进入评测。

<a id="reading-path"></a>

### 3.3 阅读导航与停止位置

先从主函数看完整交接，再进入下面的局部职责。**后端选择决定实际执行体**：当前 [create_sandbox](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sandbox.py#L8-L16) 默认选择 Sunabako；`SWE_SANDBOX_PROVIDER=e2b` 时选择 E2B。已有 E2B 卡片用于相应分支的回顾，不能将它当成新版的唯一实现。

2026-10-24 用户确认将 Sunabako 的 `__init__`、`__aenter__`、`__aexit__` 连起来阅读：先认清初始字段，再看环境创建与退出回收；SDK 内部和部署机制仍留在本轮边界之外。

| 阅读位置与入口 | 本步看清什么 | 返回或继续位置 |
| --- | --- | --- |
| 对象创建：`generate.py:121` → [create_sandbox](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sandbox.py#L8-L16) | 镜像标识怎样交给所选后端，返回哪个沙箱对象 | `cand` 回到主函数，继续 `132` 的进入操作 |
| 初始字段：工厂构造 → [SunabakoSandbox.__init__](02-short-term-memory/functions/examples/coding_agent_rl/sunabako_sandbox.py/SunabakoSandbox.__init__.md) | 六个字段起初记录什么；此时尚未创建执行环境 | 工厂交回 `cand`，继续进入方法 |
| 环境进入：`132` → [SunabakoSandbox.__aenter__](02-short-term-memory/functions/examples/coding_agent_rl/sunabako_sandbox.py/SunabakoSandbox.__aenter__.md) / [E2BSandbox.__aenter__](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L298-L317) | 从本地对象到可操作的执行环境；先停在后端接口边界 | 返回 `135`，把同一个 `cand` 交给安装方法 |
| CLI 准备：`135` → [ClaudeCodeHarness.install_cli](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L38-L55) | 当前 npm 路径怎样委托公共安装函数，使 CLI 可用；native 路径仅定位 | 返回 `143`，再到 `161` 交付 |
| 对象交付：`143、161` | `sb` 是准备好的 `cand`；交付后由调用方继续使用 | 暂停本函数，回到 `_generate:283`，从 `285` 开始使用 |
| 退出回收：`164` → [SunabakoSandbox.__aexit__](02-short-term-memory/functions/examples/coding_agent_rl/sunabako_sandbox.py/SunabakoSandbox.__aexit__.md) | 调用方离开上下文时，按配置保存产物、请求回收，并处理一种已停止环境的异常 | 正常返回外层后，继续 `_generate:301` 的评测 |

安装内部需要时再下钻一层：[install_npm_cli:129–155](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/common.py#L129-L155)。已有[公共安装卡片](02-short-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md)与 [E2B 类卡](02-short-term-memory/classes/slime/agent/sandbox.py/E2BSandbox.md)保留旧版内容，当前源码与旧认识分开核对。两个后端的退出入口分别见 [Sunabako](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sunabako_sandbox.py#L84-L103) 和 [E2B](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L319-L324)。

**停止条件**：能接清“镜像输入 → 环境就绪与 CLI 准备 → 交出 sb → 使用后退出回收”。单次下钻不超过两层，SDK 传输、后端部署、命令等待、完整并发限流与故障重试留待按需深入；工作区准备仍属于后续步骤。

## 版本说明

- **源码基准**：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`，本机 checkout 为 `/home/fredkeira/projects/slime`；本页入口、骨架与导航已按此版本核对。
- **主要变化**：通过 `create_sandbox` 选择后端；调用处传入本次 `harness` 和追踪上下文；最终回收使用当前异常信息。Claude Code 安装还增加了 native 包分支，本页主例保留 npm 路径。
- **历史与本轮边界**：[旧版 scope](references/scope-at-2f231865.md)保留原文。scope、[boot_agent_sandbox 主卡](02-short-term-memory/functions/examples/coding_agent_rl/generate.py/boot_agent_sandbox.md)、Sunabako 三张方法卡与 [task flow](05-task-flow.md)均已对应当前主线。npm 安装已核对实现未变并补当前调用说明，完整旧例和认识日期保留；E2B 与长期继承仍保留各自历史来源。过程见[scope 校准](04-flow.md#scope-refresh-18868a79)、[方法连读](04-flow.md#sunabako-lifecycle-methods)与[本次收束](04-flow.md#agent-sandbox-closure-18868a79)。
