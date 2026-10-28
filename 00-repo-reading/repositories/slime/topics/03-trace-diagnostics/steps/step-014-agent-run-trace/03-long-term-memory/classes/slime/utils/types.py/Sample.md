# Sample

- Step 012 继承：来自 [Step 011 完整记录](../../../../../../../../02-rollout-reward/steps/step-011-generate-and-rm-group/03-long-term-memory/classes/slime/utils/types.py/Sample.md)；保留原话、未知、版本与认识日期，仅重算链接。

- Step 011 继承：来自 [Step 010 · 02-short-term-memory](../../../../../../../../02-rollout-reward/steps/step-010-generate-and-rm/02-short-term-memory/classes/slime/utils/types.py/Sample.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

## 1. 对象职责

一份任务与生成结果的数据记录：进入生成前携带输入与状态，生成后记录回答、token 和奖励等信息。

本步的 `sample` 由调用者传入；同一次生成也可能交回多个新的 Sample。它们的执行由共享 [GenerateState](../../rollout/sglang_rollout.py/GenerateState.md) 控制。

## 2. 本步先看的字段

这里只列当前阅读需要的字段，完整定义见文末源码。

| 字段 | 含义 | 本步用法 |
| --- | --- | --- |
| `prompt` | 任务输入文本或消息列表 | 交给选中的生成实现 |
| `metadata` | 任务相关的业务信息字典 | 由具体生成实现读取；沿用 Coding Agent 的题目信息 |
| `status` | 当前状态，默认 `PENDING` | 已完成结果可提前返回；中止时标为 `ABORTED` |
| `generate_function_path` | 本样本指定的生成函数路径，可为 `None` | 优先于全局生成配置 |
| `response_length` | 已记录的响应 token 数 | 部分续跑时用于处理已有响应的 mask |
| `response`、`tokens` | 回答文本与 token 序列 | 生成实现返回的结果数据；具体填充方式由该实现负责 |
| `reward` | 奖励值或字典；`None` 表示尚未提供奖励 | 非组评分路径只补 `None`，`0.0` 也是已有分数 |
| `loss_mask`、`rollout_log_probs` | 训练位置标记与生成时的 logprob | 接回前一主题的样本导出；本轮暂不展开其内部结构 |

## 3. 回到当前函数

在 [generate_and_rm](../../../../functions/slime/rollout/sglang_rollout.py/generate_and_rm.md) 入口，`sample` 是一个 Sample 对象。等待生成返回后，同名变量可能接住 `list[Sample]`；后面的 `samples = sample` 是给这个列表取另一个变量名。

**类名 `Sample`、一个实例 `sample`、实例列表 `samples` 要分开看。**

本轮进入第三部分：生成结果列表交给 [apply_rollout_sample_hooks](../../../../functions/slime/rollout/sample_hooks.py/apply_rollout_sample_hooks.md) 逐项处理。hook 可以原地更新单个 Sample，也可以返回替换对象；因此同名 sample 不能仅凭名字判断始终是入口处那个对象。

## 4. 我的直接表述与尚不清楚

本轮对两个对象的初步概括：

> 好的我大概理解了 简单来说就是这里的sample是单个样本的状态
> 然后这里的generate state是群体的状态

助手校准：Sample 保存单份样本的数据与状态，包含输入、生成结果和奖励；`status` 只是其中一个字段。用户已开始区分单份样本与共享运行状态，这项范围补充尚待后续反馈。

- 本卡未展开全部训练、多模态与重放字段。
- 哪些字段在输入对象上更新、哪些随新 Sample 返回，需要结合具体生成实现判断。

## 5. 来源

<details>
<summary>源码、认识时间与记录范围</summary>

- 固定版本：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`。
- [字段定义：slime/utils/types.py:106–244](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/types.py#L106-L244)。
- [传入位置：sglang_rollout.py:419–425](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L419-L425)，[本步使用：289–380](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L289-L380)。
- 首次接触：前一主题的样本导出已涉及；2026-10-25 在 Step 010 首次建立独立类卡。
- 最近认识更新：2026-10-25，用户初步概括 Sample 对应单份样本；字段范围与具体机制继续保留待核对。
- [本轮建卡记录](../../../../../../../../02-rollout-reward/steps/step-010-generate-and-rm/04-flow.md#sample-state-class-cards)。未运行生成或训练。
- [本轮对象区别的复述与校准](../../../../../../../../02-rollout-reward/steps/step-010-generate-and-rm/04-flow.md#sample-state-user-model)。

</details>
