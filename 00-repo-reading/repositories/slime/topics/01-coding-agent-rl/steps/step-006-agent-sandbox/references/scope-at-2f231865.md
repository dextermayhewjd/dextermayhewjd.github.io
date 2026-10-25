> 2026-10-24 校准 Step 006 scope 前的完整快照。原稿绑定 `2f231865`，正文保留，仅调整相对链接。当前范围见 [01-scope.md](../01-scope.md)。

---

# 01 · 阅读范围：启动执行沙箱

[本步入口](../README.md) · [前一步任务总结](../../step-005-agent-preparation/05-task-flow.md) · [前序记忆](../03-long-term-memory/overview.md)

## 1. 阅读目标

沿用理解 Coding Agent / Coding RL 的目标。会话配置登记之后，本步准备弄清：**任务的镜像怎样通过 `boot_agent_sandbox` 变成可供后续代码使用的执行沙箱 `sb`？**

先看正常启动与交接。调用处把 `md["image"]` 作为镜像输入，同时传入题目编号 `instance_id`；已有 Sandbox 认识按需回查前序记忆，具体函数卡片等实际阅读时再写。

## 2. 指挥官函数与本步入口

整体编排仍是 `examples/coding_agent_rl/generate.py::generate`（182 行）。本步先定位 [203 行的启动调用](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L203-L215)，再进入同文件的 [boot_agent_sandbox（96–134 行）](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L96-L134)。它串起沙箱启动、CLI 准备、交付与退出回收，适合作为本步的局部入口。

源码固定为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。本页确定入口与阅读边界，输入输出及内部交接见 [boot_agent_sandbox 函数卡片](../02-short-term-memory/functions/examples/coding_agent_rl/generate.py/boot_agent_sandbox.md)。

## 3. 给出真正干活的核心骨架

### 3.1 继承整体骨架，定位第 2 项

继承前几步的完整骨架，本步只聚焦第 2 项。以下为 `evaluation=False` 正常路径的教学裁剪：省略参数、配置解析、前置检查、日志计时、超时异常与失败包装，暂不展开外层清理；保留真实顺序、返回值与环境上下文。

```python
state.adapter.open_session(...)                          # 1. 登记会话配置；Step 5
async with boot_agent_sandbox(...) as sb:                 # 2. 本步：启动执行沙箱，取得 sb
    await swe.prepare_workspace(...)                     # 3. 后续交接：准备工作区
    agent_exit_code = await HARNESS_CLS().run(...)        # 4. 运行 Agent；接回 Step 1
    diff_text = await swe.git_diff(...)                   # 5. 取得改动

reward, applied_cleanly = await swe.run_evaluation(...)   # 6. 独立评测；Step 3
samples = await state.adapter.finish_session(...)        # 7. 导出训练样本；Step 4
...  # generate 检查空结果，并给每个样本补 agent_exit_code
return samples
```

<a id="boot-agent-sandbox-local-skeleton"></a>

### 3.2 展开 boot_agent_sandbox 的局部骨架

以下从 `generate.py:96–134` 裁剪，只保留一次启动成功的路径；暂时折叠并发限流、重试、日志与安装失败处理，保留交付和退出回收的关系。参数仍用 `...` 省略。

```python
cand = E2BSandbox(...)                       # 106：创建本地沙箱对象
await cand.__aenter__()                      # 109：申请并连接远端沙箱
await HARNESS_CLS().install_cli(...)         # 111：在沙箱中准备 Agent CLI
sb = cand                                   # 115：接住准备好的对象
try:
    yield sb                                # 132：交给调用处的 as sb
finally:
    await sb.__aexit__(...)                  # 134：调用方退出上下文时回收沙箱
```

`sb` 交回 `generate:203`，供 204–213 行的工作区准备、Agent 执行和 diff 提取使用；离开该 `async with` 后才进入上面的退出回收。这些后续调用在本步只标出位置。

### 3.3 沿局部骨架阅读，按需复用已有记录

第一处仍从 `boot_agent_sandbox` 整体看起。沿用此前 Claude Code 路径，[`HARNESS_CLS` 选中 `ClaudeCodeHarness`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L45-L52)；沙箱实现是 `E2BSandbox`。

| 按顺序看哪里 | 本步要接清什么 | 阅读深度与回查 |
| --- | --- | --- |
| `generate.py:106–109`：创建对象并进入沙箱 | 本地对象何时取得远端沙箱，准备好后继续做什么 | 复用 [E2BSandbox.__aenter__](../03-long-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md)，随后回到 111 行 |
| `generate.py:111`：`install_cli` | 已有沙箱怎样接住安装材料，安装后改变什么 | 重点读 [common.py::install_npm_cli](../02-short-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md)，区分本机包、远端包文件与安装命令；[ClaudeCodeHarness.install_cli](../02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.install_cli.md) 只定位参数适配与委托，完成后返回 115 行 |
| `generate.py:115、132–134`：交出对象与退出回收 | 谁使用 `sb`，何时回到这里清理 | 看清交接时机；回收动作复用 [E2BSandbox.__aexit__](../03-long-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md) |

**停止位置**：能沿“镜像输入 → 沙箱启动与 CLI 准备 → 交出 `sb` → 退出回收”说明本步，并指出调用方接下来使用它的位置。本轮沿 `install_cli` 接到 `install_npm_cli`，看清“本机材料 → 上传文件 → 远端安装与检查”；Node 准备只说明必要动作，SDK 传输、命令等待、并发与重试的内部机制，以及工作区准备暂不展开。导航中出现函数不表示已完成阅读或需要立即新建卡片。
