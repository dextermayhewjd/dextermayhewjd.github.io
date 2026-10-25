# 01 · 阅读范围：从会话轨迹到 Sample 列表

[本步入口](README.md) · [Step 0 核心骨架](../step-000-coding-agent/01-scope.md) · [前序函数记忆](03-long-term-memory/overview.md) · [旧版 scope](references/scope-at-2f231865.md)

## 1. 阅读目标

- **整体目标**：理解 Coding Agent / Coding RL 的运行流程。
- **本步问题**：已有会话轨迹怎样结合评测得到的 `reward` 和基础样本 `base_sample`，导出交回主流程的 `Sample` 列表？
- **阅读范围**：沿 `evaluation=False` 路径，从 `finish_session` 进入，读清会话收尾、轨迹导出和文本补全，到样本列表返回为止。

## 2. 指挥官函数

- **整体位置**：Step 003 返回评测结果后，`_generate` 进入样本导出阶段，将已有轨迹、奖励和基础样本接起来。
- **本步指挥官**：[BaseAdapter.finish_session](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md)，新版源码位于 [slime/agent/adapters/common.py:314–345](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L314-L345)；调用位置为 [generate.py:326–336](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L326-L336)。
- **选择理由**：它先收尾会话，再委托轨迹导出，最后补齐样本文本并返回列表，串联了本步需要理解的完整交接。

## 3. 给出真正干活的核心骨架

### 3.1 继承整体骨架，定位第 7 项

沿用 Step 0 的 `evaluation=False` 正常路径。以下为教学裁剪：省略大部分参数、配置、检查、追踪、日志与异常包装，保留核心调用及其顺序；`baseline` 保留以接回 Step 002 的补丁来源。

```python
adapter.open_session(...)                               # 1. 登记会话
async with boot_agent_sandbox(...) as sb:                # 2. 启动执行沙箱
    baseline = await swe.prepare_workspace(...)         # 3. 准备工作区，取得初始快照
    agent_exit_code = await harness.run(...)             # 4. 运行 CLI，等待结束
    # CLI 运行期间，通过 HTTP 进入 Step 001 并逐轮记录轨迹
    agent_metrics = await harness.collect_metrics(...) # Step 002：读取运行统计
    diff_text = await swe.git_diff(sb, ..., baseline)     # 5. Step 002：提取代码补丁

reward, applied_cleanly = await swe.run_evaluation(...)  # 6. Step 003：独立评测
samples = await adapter.finish_session(...)              # 7. 本步：导出训练样本
...  # 检查空结果，附加退出信息与截断状态；最终还有会话清理
return samples
```

本步进入第 7 项，此时执行沙箱已退出，评测也已返回。`evaluation=True` 会在此前返回评估结果，不进入这次样本导出。

<a id="input-bridge"></a>

### 3.2 本步接住什么

- **已有轨迹**：Step 001 通过 `manager.record_turn` 留下逐轮记录，保存在 manager 中；调用处的 `session_id` 传入后名为 `sid`，用于找到本次会话。
- **基础字段与奖励**：`base_sample` 提供编号、prompt 等任务基础字段，`reward` 来自 Step 003；轨迹仍从 manager 中取得。
- **附加信息**：Step 002 的 `agent_metrics` 随 `extra_metadata` 传入，与任务标识等信息一起用于样本记录。

实际调用见 [generate.py:326–336](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L326-L336)。

<a id="32-展开-finish_session-的局部骨架"></a>
<a id="reading-path"></a>

### 3.3 局部骨架与阅读导航

以下从 [finish_session:330–345](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L330-L345)裁剪：参数与长度上限的读取细节省略，保留处理顺序和解码条件。

```python
await self.shutdown_session(...)                 # 330：关闭入口，处理未结束的请求
session = self.store.pop(...)                    # 331：取出并移除会话配置
max_sample_tokens = ...                          # 332：取得样本长度上限
samples = self.manager.get_trajectory(...)        # 333–339：导出样本列表
for s in samples:                                # 340–344：补上样本文本
    rlen = int(s.response_length or 0)
    s.response = self.tokenizer.decode(...) if rlen and s.tokens else ""
return samples                                   # 345：交回 _generate
```

本轮按用户要求先走完样本导出主线：`shutdown_session` 先按收尾职责使用，跨循环细节后续回访。下表及三张主流程卡片已同步当前源码位置，数值样例仍保留其历史验证依据。

| 阅读位置与入口 | 看清什么 | 返回或继续位置 |
| --- | --- | --- |
| 会话收尾：[shutdown_session:294–312](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L294-L312) · [函数卡片](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md) | 关闭会话入口，等待并处理未结束的请求 | 回到 `finish_session:331` 取配置 |
| 取配置：[331–332 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L331-L332) | 取走会话配置，得到导出所需的长度上限 | 到 `333` 委托导出 |
| 轨迹导出：[get_trajectory:405–442](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L405-L442) · [函数卡片](02-short-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.get_trajectory.md) | 按 `sid` 取轨迹路径、委托组装、赋奖励并返回样本 | 回到 `finish_session:340` 接住列表 |
| 补文本：[340–344 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L340-L344) · [decode 记录](03-long-term-memory/functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md) | 按 `response_length` 解码样本尾部 token，写入 `response` | 到 `345` 返回列表 |
| 返回：[345 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L345) | 完整样本列表交回调用方 | 外层从 `_generate:337` 继续处理；本步在交回列表处停止 |

**停止条件**：能接清“会话收尾 → 配置取出 → 轨迹与奖励交成样本 → 补文本 → 返回列表”。跨循环提交、`_chain_to_samples`、分段、mask 算法及训练端消费留待按需深入；外层的空结果检查、状态处理和最终清理先保留位置。实际接续以[唯一路线](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)为准。

## 版本说明

- **源码基准**：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`；本页入口、整体骨架、局部骨架与导航行号已按此版本校准，见[本轮核对](04-flow.md#scope-core-refresh-18868a79)。
- **历史版本**：[旧版 scope](references/scope-at-2f231865.md)保留 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 下的原文与来源。
- **本轮校准**：三张主流程卡片与 task flow 已按 `18868a79` 对齐。历史实验与数值样例保留原依据；内层组装算法及附加字段的完整行为未在本轮展开。
