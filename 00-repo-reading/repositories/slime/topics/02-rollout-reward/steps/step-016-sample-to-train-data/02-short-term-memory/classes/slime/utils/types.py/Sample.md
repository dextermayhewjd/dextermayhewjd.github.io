# Sample

> Step 016 调取：完整沿用本步 03 中的 Sample 记录，用于阅读生成结果到训练输入的字段交接。本次复制与链接重算不改变原认识时间；转换操作记录在 BatchBuilder.convert 卡片。

- 源码定位：[slime/utils/types.py:107](/home/hongshi/projects/slime/slime/utils/types.py:107)，本轮核对版本 `18868a79`。
- 本步调取：2026-10-28，从 [03 中的完整类卡](../../../../../03-long-term-memory/classes/slime/utils/types.py/Sample.md)调入；保留此前认识与来源，不因整理字段视图而更新个人认识时间。
- 最近认识更新：2026-10-28，用户初步联系生成结果与补分，并将 Sample 及内容字段与测试中的检查联系起来；reward 缺失的精确含义、通过局部检查与满足全部使用要求的区别仍待校准。此前认识时间保留在下方原卡中。

<a id="step015-field-view"></a>

## Step 015：先看返回样本的够用结构

当前问题是“自定义 generate 要交回什么数据”。先从 Coding Agent 返回的 `list[Sample]` 中观察一份 Sample；这里列的是当前路径的字段视图，完整类定义保留为查询入口。

| 字段组 | 当前先认的字段 | 阅读深度 |
| --- | --- | --- |
| 任务来源 | `index`、`group_index`、`prompt` | 知道结果沿用哪份基础任务的信息；不展开编号分配机制 |
| 生成内容 | `tokens`、`response`、`response_length` | 区分 token 序列、响应文本和响应区域长度；不能把 response_length 当作字符数 |
| 状态与评分 | `status`、`reward` | 本轮优先追踪：父函数据此判断中止和哪些样本需要补分 |
| 训练附带数据 | `loss_mask`、`rollout_log_probs` | 先知道是训练位置标记和生成时的 logprob；具体对齐与训练消费留到后续 |

**这些字段不等于“每个 generate 都必须手工填全的清单”。** 具体实现可以调用已有导出组件；有些字段保留默认值，reward 是否由框架补齐也取决于当前分支。完整训练要求需要结合实际消费方核对。

**本步的测试检查也是局部要求。** 用户已把 Sample、tokens、response、response_length 与 assert_sample_contract 联系起来；该辅助函数还要求 reward 非 None。通过这些检查表示满足这几项基本条件，不保证字段内容、长度关系或全部训练要求都成立。具体检查与本轮原话保存在[测试父卡](../../../../../03-long-term-memory/functions/tests/plugin_contracts/test_plugin_generate_contracts.py/test_custom_generate_function_path_supports_user_override.md)。

<a id="status-and-reward"></a>

**本轮展开 status 与 reward。** `Sample.status` 是单份样本的执行状态，和共享运行对象 `GenerateState` 分开。`reward` 是评估分数，默认 `None` 表示还没有提供分数；`0.0` 是已有分数。因此 `status=COMPLETED, reward=0.0` 是可以成立的组合：生成已完成，评估得到零分。具体的状态判断、奖励筛选和回填放在 [generate_and_rm 的处理段](../../../../../03-long-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md#returned-sample-fields)。这项是助手源码说明，尚待用户理解反馈。

本卡保存“对象有什么、字段是什么意思”。字段由谁写入，接回 [generate 的结果交付](../../../../../03-long-term-memory/functions/examples/coding_agent_rl/generate.py/generate.md#returned-samples)；字段被谁读取，接回 [generate_and_rm 的接收处理](../../../../../03-long-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md#returned-sample-fields)。按一份返回样本观察，不代表它必定与入口的 base_sample 是同一个对象。

完整字段按需查 [Sample 类定义](/home/hongshi/projects/slime/slime/utils/types.py:107)。queue、trace 等运行时附加信息不在当前表中，不能把这张表当成运行时对象的全部属性。

用户先询问应先建类卡、追踪后续使用，还是先看完整字段，[原话与安排](../../../../../../step-015-custom-generate-contract/04-flow.md#sample-class-view)单独保存；随后明确要求继续看状态与奖励处理，已展开上述两个字段及父函数使用，见[展开过程](../../../../../../step-015-custom-generate-contract/04-flow.md#status-reward-processing)。在补分阶段的表述是“给出这里的reward 如果这里的samples没有的话”；助手将其校准为已有 Sample 的 reward 为 None 时补分，不能据此认定状态条件和全部字段已掌握。[完整原话与校准](../../../../../../step-015-custom-generate-contract/04-flow.md#reward-restatement-next-fields)。

<details>
<summary>此前完整类卡：对象职责、已读字段、原话、未知与来源</summary>

- Step 012 继承：来自 [Step 011 完整记录](../../../../../../step-011-generate-and-rm-group/03-long-term-memory/classes/slime/utils/types.py/Sample.md)；保留原话、未知、版本与认识日期，仅重算链接。

- Step 011 继承：来自 [Step 010 · 02-short-term-memory](../../../../../../step-010-generate-and-rm/02-short-term-memory/classes/slime/utils/types.py/Sample.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

## 1. 对象职责

一份任务与生成结果的数据记录：进入生成前携带输入与状态，生成后记录回答、token 和奖励等信息。

本步的 `sample` 由调用者传入；同一次生成也可能交回多个新的 Sample。它们的执行由共享 [GenerateState](../../../../../03-long-term-memory/classes/slime/rollout/sglang_rollout.py/GenerateState.md) 控制。

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

在 [generate_and_rm](../../../../../03-long-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md) 入口，`sample` 是一个 Sample 对象。等待生成返回后，同名变量可能接住 `list[Sample]`；后面的 `samples = sample` 是给这个列表取另一个变量名。

**类名 `Sample`、一个实例 `sample`、实例列表 `samples` 要分开看。**

本轮进入第三部分：生成结果列表交给 [apply_rollout_sample_hooks](../../../../../03-long-term-memory/functions/slime/rollout/sample_hooks.py/apply_rollout_sample_hooks.md) 逐项处理。hook 可以原地更新单个 Sample，也可以返回替换对象；因此同名 sample 不能仅凭名字判断始终是入口处那个对象。

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
- [本轮建卡记录](../../../../../../step-010-generate-and-rm/04-flow.md#sample-state-class-cards)。未运行生成或训练。
- [本轮对象区别的复述与校准](../../../../../../step-010-generate-and-rm/04-flow.md#sample-state-user-model)。

</details>

</details>
