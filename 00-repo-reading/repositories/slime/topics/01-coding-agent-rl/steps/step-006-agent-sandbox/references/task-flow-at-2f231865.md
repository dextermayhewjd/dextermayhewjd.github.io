本文件保存 Step 006 在 `2f231865` 下的完整任务总结。2026-10-24 更新当前总结时归档，仅调整相对链接；原编号、来源与理解状态保留。

---

# 05 · 任务链路：准备、交付与回收执行沙箱

> `boot_agent_sandbox` 根据任务镜像申请远端环境、准备 Agent CLI，再把操作这份环境的本地对象交给调用方。调用方在其中准备工作区、运行 Agent 并提取 diff；离开上下文时，再尝试回收远端环境。

[本步 scope](../01-scope.md) · [步骤入口](../README.md) · [函数与类记录](../02-short-term-memory/overview.md) · [本次收拢](../04-flow.md#agent-sandbox-flow-closure)

## 1. 本步补齐了哪一段

- Step 4 已按 sid 在 Adapter 中登记模型请求需要的会话配置。
- Step 5 补齐执行环境：`generate.py:203` 把 `md["image"]` 交给启动入口，取得可供后续操作的 `sb`。
- 下一处交接是 `generate.py:204` 的 `swe.prepare_workspace`。本步先接清它拿到什么，工作区的具体准备内容留待下一轮。

会话配置与执行环境是两份准备结果：前者保存在 Adapter 中，后者由 `sb` 操作。`instance_id` 在本函数中用于失败日志，不决定远端的 `sandbox_id`。

## 2. 已读组件怎样把镜像变成可用环境

以下是固定版本的一次正常准备路径。行号用于回到真实源码；限流、日志与失败重试暂时折叠。

```text
generate.py:203 进入 async with boot_agent_sandbox(...)
  ↓
boot_agent_sandbox                                      generate.py:96–134
├─ cand = E2BSandbox(image)                             106
│  └─ 本地对象保存镜像等配置
├─ await cand.__aenter__()                              109
│  └─ 申请远端沙箱，保存 SDK 客户端与 sandbox_id          sandbox.py:281–300
├─ await HARNESS_CLS().install_cli(cand)                 111
│  └─ ClaudeCodeHarness.install_cli：选择参数             claude_code.py:36–42
│     └─ install_npm_cli：组织实际安装                    harness/common.py:125–151
│        └─ 准备 Node → 上传 CLI 包 → 远端安装并检查
├─ sb = cand                                           115
└─ yield sb                                            132
   └─ 交给 generate.py:203 的 as sb，接着执行调用方的缩进块
```

- [E2BSandbox 类卡片](../02-short-term-memory/classes/slime/agent/sandbox.py/E2BSandbox.md)解释本地对象与远端环境的关系。进入操作复用 [__aenter__](../03-long-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md)；旧卡采用评测场景，此处用于执行环境。
- [install_npm_cli 主记录](../02-short-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md)解释安装过程；[ClaudeCodeHarness.install_cli](../02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.install_cli.md)是参数适配与委托入口。
- [boot_agent_sandbox 函数卡片](../02-short-term-memory/functions/examples/coding_agent_rl/generate.py/boot_agent_sandbox.md)解释准备、交付和回收怎样组合在同一使用期内。

到 `yield sb` 时，`cand` 与 `sb` 指向同一个本地对象，远端环境已经创建且 CLI 安装检查成功。安装函数返回的 `None` 表示调用完成；实际交付给 `as sb` 的是这个 `E2BSandbox` 对象。

## 3. 交出 sb 之后，谁使用它、何时回收

下面是 `generate.py:203–219` 的教学裁剪：保留真实调用顺序，省略参数和外层超时处理。三个缩进调用只用于说明沙箱的使用期，本页不展开它们的内部实现。

```python
async with boot_agent_sandbox(...) as sb:                 # 203：接到已准备好的对象
    await swe.prepare_workspace(...)                     # 204：准备工作区
    agent_exit_code = await HARNESS_CLS().run(...)        # 205–212：运行 Agent
    diff_text = await swe.git_diff(...)                   # 213：在环境仍可用时取得 diff
# 离开 async with：回到 boot_agent_sandbox:134，等待 __aexit__ 的回收处理
reward, applied_cleanly = await swe.run_evaluation(...)   # 215：进入已有的独立评测链路
```

- **交付之后继续使用**：`yield sb` 暂停启动函数，调用方开始执行缩进块。工作区准备、Agent 运行和 diff 提取共享这一份环境。
- **使用结束再回收**：离开缩进块时回到启动函数的 `finally`，调用 [E2BSandbox.__aexit__](../03-long-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md)，请求销毁远端环境。它会记录捕获到的回收错误，因此完成退出处理不等于已经验证远端销毁成功。
- **结果继续向后交接**：正常路径先把改动取成 `diff_text`，随后退出执行环境，再进入 Step 2 已读的独立评测。块内异常也会触发回收处理，但不会因此自动转成正常评测路径。

## 4. 当前可以收束的范围

本步的“镜像输入 → 环境与 CLI 就绪 → 交出 sb → 调用方使用 → 退出回收”已形成连续的任务链路，符合原 scope 的停止位置。用户表示已基本完成对 `boot_agent_sandbox` 的理解；本页收拢已读关系，不把它扩展为所有异常和 SDK 内部实现均已掌握。

以下内容保留为后续按需深入项，不作为这次总结的前置条件：

- `exec_and_wait` 怎样等待长命令，以及底层 SDK 怎样传输文件和命令。
- 准备并发限制、内外两层重试、取消与回收失败怎样配合。
- 实际部署的地址、包版本和真实沙箱运行验证。

沿任务主线继续时，下一候选是 `swe.prepare_workspace`（调用处 `generate.py:204`，定义 `swe.py:177`），围绕“已就绪的沙箱怎样变成任务工作区”再确认范围；这里仅标出交接，不提前建立下一步或填写函数卡片。

<details>
<summary>源码、形成依据与验证范围</summary>

- 固定提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。
- 准备与交付：[generate.py:95–134](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L95-L134)；调用方的使用期与后续评测：[203–219](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L203-L219)。
- 远端环境的申请与回收：[sandbox.py:281–307](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L281-L307)；参数入口：[claude_code.py:36–42](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/claude_code.py#L36-L42)；安装实现：[harness/common.py:125–178](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L125-L178)。
- 本页由 LLM 根据本步已发生的阅读整理。用户原话、收束理由与待查项见 [Step 5 · 本次总结](../04-flow.md#agent-sandbox-flow-closure)。
- 本次静态复核真实调用和交接；原函数配替身的四条局部路径验证仍见函数卡片。没有新增真实沙箱、CLI 或 Agent 运行证据。

</details>
