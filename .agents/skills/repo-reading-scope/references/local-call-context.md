# 局部导航：从整体骨架进入本步调用

本 reference 配合 [scope skill](../SKILL.md)的局部分支使用。三段 scope 的外层结构不变，下面的内容放在第 3 部分；单函数的完整输入输出、实现解释与个人理解仍归函数卡片。

## 根据当前问题选择展开方式

| 当前情况 | scope 中怎样处理 |
| --- | --- |
| 只建立整体概览，尚未选择下钻点 | 给整体骨架和停止位置，使用 [Coding Agent 整体样例](coding-agent-scope.md) |
| 已选定一个需要展开的核心调用 | 保留整体位置，再给局部骨架、阅读入口与返回位置 |
| 调用对象、关键输入或进入的实现还不清楚 | 先补缺失的来源关系，再接到当前调用；明确具体类或继承的共同实现 |
| 调用简单，来源与交接已经清楚 | 几行局部代码配一句返回说明即可 |

“暂不写函数卡片”与“只定位、不展开内部”是不同的阅读边界。前者仍可准备局部导航；后者只给调用处与待解决的问题。

## 样例：展开启动执行沙箱

来源：[Step 005 scope](../../../../00-repo-reading/repositories/slime/steps/step-005-agent-sandbox/01-scope.md)。下例是局部导航的格式参考，绑定 Slime 提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`，不表示其他项目也需要同样的生命周期或五个动作。

### 3.1 整体位置

本步 scope 完整保留[整体样例](coding-agent-scope.md)中的七项骨架与上下文嵌套，将第 2 项 `boot_agent_sandbox` 标为本步。其余六项保留短注释；`open_session` 是前一处登记，`prepare_workspace` 是取得沙箱后的接收方，后面的执行、差异提取、评测和样本导出也继续保留位置。

调用入口在 [generate.py:203](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L203-L215)，实际进入同文件的 `boot_agent_sandbox:96–134`。本例调用对象已可定位，不必先展开全部配置。

### 3.2 局部骨架

以下是 [boot_agent_sandbox](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L95-L134)一次启动成功路径的教学裁剪。省略实参、并发限流、重试、日志与失败处理，保留交付和退出关系。

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

`sb` 交给 `generate:203` 的 `as sb`，随后供 204–213 行使用；调用方离开该 `async with` 时执行退出回收。这个时机关系属于本步导航，内部资源实现留在对应卡片。

### 3.3 阅读导航与停止位置

先看本步入口的局部骨架，再按卡点进入下面的位置。当前路径由 [generate.py:45–52](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L45-L52)选中 `ClaudeCodeHarness`，沙箱使用 `E2BSandbox`。

| 局部位置 | 要解决的问题与阅读深度 | 读完回到哪里 |
| --- | --- | --- |
| `106–109`：创建并进入沙箱 | 本地对象怎样接上远端沙箱；按需回查[已有进入卡片](../../../../00-repo-reading/repositories/slime/steps/step-005-agent-sandbox/03-long-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md) | `111`：把同一对象交给安装入口 |
| `111`：安装 CLI | 定位 [ClaudeCodeHarness.install_cli](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/claude_code.py#L36-L42)，先看用途，安装命令暂不下钻 | `115、132`：接住对象并交给调用方 |
| `132–134`：交付与退出 | 看清使用期和清理时机；按需回查[已有退出卡片](../../../../00-repo-reading/repositories/slime/steps/step-005-agent-sandbox/03-long-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md) | 交付时回到 `generate:203`；使用期结束后继续 `generate:215` 的评测 |

停止条件：能说明镜像怎样进入启动入口、准备好的 `sb` 交给谁、何时退出回收。本轮不展开安装内部、并发重试、工作区准备或评测，也不因导航列出了某个函数就自动创建卡片。

## 变体：先补对象或输入的来路

[Step 004 的局部骨架](../../../../00-repo-reading/repositories/slime/steps/step-004-agent-preparation/01-scope.md#adapter-to-open-session)展示另一种情况：读者尚不清楚 `state.adapter` 和 `session_id`，直接列出 `open_session` 函数体不足以进入阅读。

此时只补两条必要关系：`_AdapterService` 持有哪个 Adapter，以及 `_session_id` 的结果怎样交给 `open_session`。注明首次初始化与已有对象复用的区别，再接到实际方法实现；完整服务启动、tokenizer 加载等仍保持折叠。来源已经清楚时直接回查既有记录，无需重复这段追溯。
