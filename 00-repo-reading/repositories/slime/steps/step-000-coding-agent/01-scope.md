# 01 · 阅读范围：理解 Coding Agent 的核心骨架

[本步入口](README.md) · [旧版 scope](references/scope-at-2f231865.md) · [本次校准](04-flow.md#recalibrate-step-zero) · [下一步：一次模型请求（待校准）](../step-001-harness-to-adapter/01-scope.md)

## 1. 阅读目标：理解 Coding Agent

先理解一份代码任务怎样被执行、怎样取得代码改动、怎样评测并交回样本，建立 Coding Agent 的整体工作轮廓。

本步按[代码阅读指南](../../../../code-reading-guide.md#方法一先剪枝再沿主线下钻)先看正常路径，不从配置、日志或辅助函数逐行读起。本轮对照新版校准这张整体地图，原先的理解与来源保留。

## 2. 找到指挥官函数：`generate → _generate`

源码版本：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`。

- 对外入口：[examples/coding_agent_rl/generate.py · generate，225–251 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L225-L251)。它包装 trace，在第 230 行调用 `_generate`。
- 实际业务编排：[同文件的 _generate，254–413 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L254-L413)。它串联登记会话、准备执行环境和工作区、运行 Agent、收集改动、评测与导出样本。

因此本次沿 `generate` 定位后，进入 `_generate` 看核心骨架。函数名是否带下划线只提供线索，实际职责决定从哪里读。

本步只了解骨架，不展开各函数内部，也不建立函数分析卡片；具体函数及其新旧变化随对应步骤逐项校准。

## 3. 给出真正干活的核心骨架

以下为 `evaluation=False` 正常路径的教学裁剪，保留函数名、执行顺序与返回值。先沿用 Claude Code / Anthropic 场景；`_generate` 根据当前样本选取 `harness`，并经 `state.endpoint(agent_name)` 取得 `adapter` 与地址，对象来路由 Step 5 校准。

参数通常用 `...` 省略；为看清新交接，`git_diff` 保留 `baseline` 参数。通用配置、检查、trace、异常、附加元数据和最终清理暂时折叠；这不是可直接运行的完整代码。

```python
# examples/coding_agent_rl/generate.py · _generate
adapter.open_session(...)                              # 1. 登记本次会话；Step 5
async with boot_agent_sandbox(...) as sb:                # 2. 启动执行沙箱；Step 6
    baseline = await swe.prepare_workspace(...)         # 3. 准备工作区并取得初始 Git 树；Step 7
    agent_exit_code = await harness.run(...)             # 4. 运行 CLI 并等待结束；Step 8
    # 等待期间：CLI --HTTP--> Step 9 接收与路由 --> Step 1 模型处理与回复
    agent_metrics = await harness.collect_metrics(...) # Step 2：读取运行统计，供后续标记截断等状态
    diff_text = await swe.git_diff(sb, ..., baseline)     # 5. 相对初始状态取得本次改动；Step 2

reward, applied_cleanly = await swe.run_evaluation(...)  # 6. 独立评测；Step 3
samples = await adapter.finish_session(...)              # 7. 导出本次会话的样本；Step 4
...  # 附加结果与截断状态；最终还需会话清理
return samples
```

代码中的 1–7 是业务环节，Step 编号是阅读顺序。Step 1、Step 9 的请求处理发生在 Step 8 等待 CLI 期间；CLI 收到回复后仍可能继续执行。

<a id="trace-span-boundary"></a>

**`trace_span` 的折叠边界**：新版在业务阶段外增加执行追踪，记录阶段开始、结束、嵌套关系及附加结果。Step 0 先认识这层职责，核心骨架折叠重复的追踪包装，保留里面实际执行的业务调用。

<details>
<summary>对照源码：追踪包装与业务调用怎样对应</summary>

以下只省略 `harness.run` 的参数，保留真实的包装关系：

```python
with trace_span(base_sample, "agent_run", record_error=False) as span:
    agent_exit_code = await harness.run(...)  # 执行业务：启动 CLI 并等待结果
    span.set("exit_code", agent_exit_code)    # 将退出码补入这个阶段的追踪记录
```

骨架保留中间的 `harness.run`；外层 `trace_span` 与结果记录仍存在于实际源码。退出追踪范围时会记录阶段结束，并恢复上一层追踪上下文。

源码：[generate.py:286–295](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L286-L295) · [trace_span 实现](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L345)。

</details>

剪枝依据是数据用途：`collect_metrics` 的 `compact_limit_reached` 会参与后续样本截断状态的判断，因此这行仍保留在骨架中；不能把所有看起来像“统计”的代码一并略去。

这次相对旧版需要重新对准四个关系：

1. **入口位置**：`generate` 委派给 `_generate`，主要业务职责仍由后者串联。
2. **运行对象**：本次样本选定 `harness` 和 `adapter`；此处使用的已不只是全局 `HARNESS_CLS` 与 `state.adapter`。
3. **改动基线**：`prepare_workspace` 返回初始 Git 树 `baseline`；`git_diff` 比较它与运行后的状态，提取本次改动。
4. **运行统计**：CLI 结束后先 `collect_metrics`，其中压缩限制等结果会参与后续样本状态标记；内部机制留待对应步骤。

**停止位置**：能把新版的入口与这七个业务环节接起来，并指出 `baseline` 的来源和去向。沙箱 provider、历史 token 复用、部分生成续接、轨迹扩展字段与失败处理仍需逐步校准，本页不将它们写成已经理解。

本页由助手按新版源码静态核对；你的新版理解反馈继续记录在本步 `04-flow.md`。旧版 scope、两层 memory 与历史原话保留。
