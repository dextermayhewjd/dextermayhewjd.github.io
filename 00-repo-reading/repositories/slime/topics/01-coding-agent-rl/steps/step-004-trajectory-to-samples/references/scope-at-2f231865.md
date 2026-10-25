# 01 · 阅读范围：从会话轨迹到 Sample 列表

> 旧版 scope，源码基准为 `2f231865`。2026-10-24 从本仓库 `75740ae` 中归档更新前全文，仅调整相对链接；[当前 scope](../01-scope.md)单独维护。

[本步入口](../README.md) · [Step 0 核心骨架](../../step-000-coding-agent/01-scope.md) · [前序函数记忆](../03-long-term-memory/overview.md)

## 1. 阅读目标

沿用理解 Coding Agent / Coding RL 的目标。本步回答：**已经记录的会话轨迹，怎样结合评测得到的 `reward` 和任务的 `base_sample`，成为交回 `generate` 的 `Sample` 列表？**

进入时只需接回两项已有结果：`manager.record_turn` 留下同一 `sid` 的逐轮记录；`swe.run_evaluation` 返回奖励与补丁状态。本步沿 `evaluation=False` 路径，先看样本导出的输入输出与责任交接。`evaluation=True` 会提前返回评估结果，不经过下面的 `finish_session` 调用。

## 2. 指挥官函数与本步入口

整体指挥官仍是 `examples/coding_agent_rl/generate.py::generate`。从其第 237 行进入本步入口 [BaseAdapter.finish_session](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md)，定义在 `slime/agent/adapters/common.py:245–276`。

它适合作为本步锚点，因为它串起会话收尾、轨迹导出和样本文本补全。`get_trajectory` 承担具体的轨迹到样本转换；先认清它接到什么、交回什么，再根据问题深入。

源码固定为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`；沿用[已核对的版本边界](../../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前源码与已有材料的版本边界)。

## 3. 给出真正干活的核心骨架

### 3.1 继承整体骨架，定位第 7 项

教学裁剪：省略参数、配置、检查、日志与异常包装；保留当前正常路径的真实顺序。

```python
state.adapter.open_session(...)                          # 1. 登记会话
async with boot_agent_sandbox(...) as sb:                 # 2. 启动执行环境
    await swe.prepare_workspace(...)                     # 3. 准备工作区
    agent_exit_code = await HARNESS_CLS().run(...)        # 4. 运行 Agent；期间逐轮记录轨迹
    diff_text = await swe.git_diff(...)                   # 5. 取得改动

reward, applied_cleanly = await swe.run_evaluation(...)   # 6. 独立评测；承接 Step 3
samples = await state.adapter.finish_session(...)        # 7. 本步：导出训练样本
...  # generate 检查空结果，并给每个样本补 agent_exit_code
return samples
```

### 3.2 展开 finish_session 的局部骨架

以下仍为教学裁剪；数据字段与完整实参在函数卡片中保留。

```python
await self.shutdown_session(...)                 # 261：关闭会话入口，处理尚未结束的请求
session = self.store.pop(...)                    # 262：取出并移除会话配置
max_sample_tokens = ...                          # 263：取得样本长度上限
samples = self.manager.get_trajectory(...)        # 264–270：轨迹、任务基础字段与奖励 → 样本列表
for s in samples:                                # 271–275
    rlen = int(s.response_length or 0)
    s.response = ...                             # 按 response_length 解码样本尾部
return samples                                   # 276：交回 generate
```

| 实际交接 | 本轮读到什么程度 | 回来接住什么 |
| --- | --- | --- |
| [finish_session 函数卡片](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md) | 完整输入输出、状态变化及三段编排 | 带 token、mask、logprob、reward 和文本的样本列表 |
| [shutdown_session](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md)，`common.py:225–243` | 关闭标记、待收尾任务、正常等待与超时取消；跨循环提交解释到本函数所需的交接，底层实现留白 | 返回 `None`，然后取会话配置并导出 |
| [get_trajectory](../02-short-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.get_trajectory.md)，`trajectory.py:307–344` | 取树、按叶子展开消息路径、委托组装、汇总、赋奖励与移除；具体样本字段怎样形成留给 `_chain_to_samples` | `samples`，随后逐个补 `response` |
| [此前的 decode](../03-long-term-memory/functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md) | 复用 token ID → 字符串的职责；这里换成样本尾部作为输入 | `s.response` |

本步围绕 `finish_session` 的输入、委托与返回，按需要进入请求收尾和轨迹导出的函数卡片。`_chain_to_samples` 怎样处理消息节点保留为后续问题，先回补用户指出的收尾与配置前置；实际接续以[唯一路线](../../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)为准。分叉、重分词对齐和训练端消费不在首轮同时展开，不提前创建子函数完成记录。
