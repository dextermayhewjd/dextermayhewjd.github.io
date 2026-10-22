# 01 · 阅读范围：理解 Coding Agent 的核心骨架

[本步入口](README.md) · [下一步：一次模型请求](../step-001-harness-to-adapter/01-scope.md)

## 1. 阅读目标：理解 Coding Agent

先理解一份代码任务怎样被执行、怎样取得代码改动、怎样评测并交回样本，建立 Coding Agent 的整体工作轮廓。

本步按[代码阅读指南](../../../../code-reading-guide.md#方法一先剪枝再沿主线下钻)先看正常路径，不从配置、日志或辅助函数逐行读起。

## 2. 找到指挥官函数：`generate`

源码入口：[examples/coding_agent_rl/generate.py · generate](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L182)。

选择它，是因为它串联了一份任务的主要阶段：登记会话、准备执行环境和工作区、运行 Agent、收集改动、评测、导出样本。

先把它作为阅读主线。本步只了解骨架，不展开函数实现，也不建立函数分析卡片；具体代码从 Step 1 的 `_run_turn` 开始。

## 3. 给出真正干活的核心骨架

以下为 `evaluation=False` 正常路径的教学裁剪，保留函数名、执行顺序与返回值，调用参数统一用 `...` 省略。配置、检查、日志、异常、附加元数据和最终清理也暂时略去；这不是可直接运行的完整代码。

```python
state.adapter.open_session(...)                          # 1. 登记本次会话
async with boot_agent_sandbox(...) as sb:                 # 2. 启动执行沙箱
    await swe.prepare_workspace(...)                     # 3. 准备工作区
    agent_exit_code = await HARNESS_CLS().run(...)        # 4. 运行 Coding Agent
    diff_text = await swe.git_diff(...)                   # 5. 取得代码改动

reward, applied_cleanly = await swe.run_evaluation(...)   # 6. 独立评测
samples = await state.adapter.finish_session(...)        # 7. 导出本次会话的样本
return samples
```

本步读到能够沿这七个步骤说明任务的整体流转。暂不展开每个子函数，也不把骨架中出现的函数都记成已理解；后续下钻继续先确认本轮问题。
