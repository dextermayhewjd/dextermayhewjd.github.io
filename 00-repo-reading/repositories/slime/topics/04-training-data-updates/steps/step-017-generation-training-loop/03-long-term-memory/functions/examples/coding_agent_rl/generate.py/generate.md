# coding_agent_rl.generate

- 源码定位：[examples/coding_agent_rl/generate.py:225](/home/hongshi/projects/slime/examples/coding_agent_rl/generate.py:225)，本轮核对版本 `18868a79`。
- 首次接触：主题 01 的既有 Agent 主线阅读；此前累计同名文件为空白占位，本卡于 Step 015 首次填充。
- 最近认识更新：2026-10-28，用户初步表述前三个参数按位置对应，并追问签名是否足够；结果与状态约束尚待进一步反馈，具体函数内部尚未在本步重读。
- 原始占位：[本步 03 快照](generate.md)。旧步骤、旧占位与既有阅读历史均保留。

## LLM 整理：使用场合、具体内容与心智模型

以下是助手根据真实调用与固定源码整理的参考。

1. **使用场合**：`generate_and_rm` 通过配置路径选中这个函数，为一个输入 Sample 执行 Coding Agent 任务。

2. **具体内容**：接收配置、基础 Sample、采样参数和评估标志；调用已读的内层 `_generate`，正常返回其样本列表。入口还包裹 Trace，并在配置输出目录时记录摘要；这些观测细节本步不展开。

3. **建议构建的心智模型**：

   > 这是一个实际接入 Slime 的 Agent 入口：按照调用方能传入的参数接收任务，把内部 Agent 流程交付的样本列表返回。内部怎样组织任务与外部怎样调用它，是两个需要对齐的层次。

4. **调用代码**：

   ```python
   # generate_and_rm:342；generate_func 已指向本函数
   generate_call = generate_func(args, sample, sampling_params, evaluation=evaluation)
   # 本例没有 abort_mode="request"，接回 349
   sample = await _run_server_abort_generate(state, generate_call)
   ```

## 本场景的输入与输出

本轮先对齐输入。以下是配置与对象的字段节选，未启动真实任务，未构造完整运行环境。

```python
# 调用方已有的数据（教学构造，仅观察参数交接）
sample = Sample(index=0, prompt="修复给定仓库中的问题")
sampling_params = {"temperature": 0.3}
evaluation = False
args.custom_generate_function_path = "examples.coding_agent_rl.generate.generate"
```

真实接收方签名：

```python
async def generate(args, base_sample: Sample, sampling_params: dict[str, Any], evaluation: bool = False):
```

| 调用方传入 | 接收方参数 | 本次交接 |
| --- | --- | --- |
| 第一个位置的 args | args | 配置对象 |
| 第二个位置的 sample | base_sample | 同一个基础 Sample 引用，改名没有复制对象 |
| 第三个位置的 sampling_params | sampling_params | 本次采样参数字典 |
| evaluation=evaluation | evaluation | 关键字参数，本例值为 False |

**本次调用先得到**：协程对象 `generate_call`。这是调用的中间结果，尚未得到生成后的 Sample。

**等待结束后的正常返回**：内层 `_generate` 交回的 `list[Sample]`。实际列表长度、token、reward 等取决于任务；本轮没有执行，不填造具体输出。第二步从下面的返回来源开始，再核对父函数如何使用结果。

用于定位正常返回的教学裁剪，省略 Trace 和 finally 中的可选摘要写入：

```python
# generate.py:230–231；位于真实函数内部
samples = await _generate(args, base_sample, sampling_params, evaluation)
return samples
```

<a id="returned-samples"></a>

### 第二步：先找到返回值的来源

本轮接续的问题是：**这个实现交回的 samples 从哪里来，为什么一个输入 Sample 能返回列表？** 选择 `evaluation=False`、轨迹非空、无异常/截断的正常训练路径。

下面是内层 `_generate` 的局部教学裁剪，保留返回数据相关的真实调用。前面的 Agent 执行、补丁提取，以及中间的 Trace、日志、附加 metadata、状态分支和 finally 清理均未在片段中展开；它们在源码中仍存在。

```python
# _generate:301，Agent 任务的评估结果
reward, applied_cleanly = await swe.run_evaluation(...)

# _generate:326，把这次会话的轨迹交成 Sample 列表
samples = await adapter.finish_session(
    session_id,
    base_sample=base_sample,
    reward=float(reward),
    extra_metadata=...,
)

# _generate:367，补完 metadata / 状态后返回
return samples
```

输入与输出先只追踪这三项：

| 已有数据 | 此处的用途 |
| --- | --- |
| session_id 对应的已记录轨迹 | 提供这次 Agent 执行产生的内容 |
| base_sample | 提供原任务的信息，供导出结果沿用 |
| reward | 提供刚才评估得到的分数 |

它们经 `finish_session` 整理后得到 `list[Sample]`。这是一个输入任务导出的训练样本列表，并非外层 worker 一次领取的整个 prompt group。具体条数由轨迹与分段决定，本轮没有运行，不给假定数量。

```text
_generate:326 取得 samples
  → _generate:367 返回
  → generate:230 接住，231 返回
  → generate_and_rm:349 接住，继续样本后处理
```

`finish_session` 内部的轨迹整理已有阅读基础，本轮先按输入输出作为黑箱，暂不重读消息树和分段算法。接下来先用 [Sample 类卡的字段视图](../../../../classes/slime/utils/types.py/Sample.md#step015-field-view)观察列表中的一份返回样本，再沿 [父函数读取 status、reward 的位置](../../../slime/rollout/sglang_rollout.py/generate_and_rm.md#returned-sample-fields)追踪用途。完整字段不先逐项展开；核对当前返回约定后，再进入第三步的测试验证。

读完回到 [generate_and_rm 的接收点](../../../slime/rollout/sglang_rollout.py/generate_and_rm.md#step015-call-contract)，源码 349 后接 353 的样本后处理。内层失败返回、完整字段和评估差异尚未在本步展开。

**本轮补充：参数对齐只是调用入口。** 还需让调用产生可等待对象，并在等待后交回下游可处理的样本内容。实际 Coding Agent 使用 async def，正常返回样本列表；后续将从这两行的返回结果进入样本约定。完整边界说明见[调用方卡片](../../../slime/rollout/sglang_rollout.py/generate_and_rm.md#step015-call-contract)。

## 我的直接表述（原话）

本轮接口理解的原话节选：

> 这里是只需要参数位置对应就可以了对吧 是我的理解

用户同时追问是否只满足签名即可。前三个位置实参的判断与源码一致；可等待结果、返回数据与关键字参数的约束是助手本轮补充，不能提前写成用户已掌握。完整原话见[本轮过程](../../../../../../../../02-rollout-reward/steps/step-015-custom-generate-contract/04-flow.md#signature-is-not-the-whole-contract)。

以下保留用户此前核对学习目标时的原话节选：

> 所以需要了解的是这样子的一个generate 应该怎么写？
> 我可以这么理解吗？

## 尚不清楚

- 用户已初步表述前三项按位置传参；evaluation 的关键字匹配与条件传递、协程/最终结果的区别仍待反馈。
- 新接入实际需要维护哪些样本字段、状态和奖励边界，留到第二步。
- 如何选择合适的测试，以及既有测试未覆盖的形式，留到第三步。

<details>
<summary>来源、验证与完整例子</summary>

- 真实源码：[接收方 225](/home/hongshi/projects/slime/examples/coding_agent_rl/generate.py:225)、[调用方 338](/home/hongshi/projects/slime/slime/rollout/sglang_rollout.py:338)。
- 返回来源：[内层 _generate 的会话导出 326](/home/hongshi/projects/slime/examples/coding_agent_rl/generate.py:326)、[finish_session 314](/home/hongshi/projects/slime/slime/agent/adapters/common.py:314)。本轮只核对正常返回的接口，未运行真实任务；[第二步接续记录](../../../../../../../../02-rollout-reward/steps/step-015-custom-generate-contract/04-flow.md#normal-return-entry)。
- [本步形成过程](../../../../../../../../02-rollout-reward/steps/step-015-custom-generate-contract/04-flow.md#first-call-observation)保存范围确认、助手解释和反馈边界。
- [前一轮目标澄清](../../../../../../../../../slime后续阅读顺序/current-goal-slime-reading-order.md#generate-integration-versus-repeat-reading)保存用户对“generate 应该怎么写”的提问与回应。
- 固定版本、片段校验见[源码证据](../../../../../../../../02-rollout-reward/steps/step-015-custom-generate-contract/references/source-evidence.json)。这里只做静态核对，示意输入不能当作完整可运行 Agent 配置。

</details>
