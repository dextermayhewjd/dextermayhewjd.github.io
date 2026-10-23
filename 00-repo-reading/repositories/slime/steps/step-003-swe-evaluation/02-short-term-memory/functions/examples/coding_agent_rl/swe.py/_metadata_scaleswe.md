# _metadata_scaleswe

- 源码定位：[examples/coding_agent_rl/swe.py:92–120](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L92-L120)，由助手核对。
- 首次接触：元数据概念此前见 Step 005 的参考说明；2026-10-23 在 Step 003 开始独立阅读本函数并建卡。
- 最近认识更新：2026-10-23，用户已初步概括从这里取得所需任务信息；字段回退与缺失值规则尚未逐项复述。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`_generate` 准备一次任务时调用 `get_metadata`；当前采用 `scaleswe` 场景，后者进入 `_metadata_scaleswe`。现在为读懂评测输入，回查这份任务字典的生成位置；实际运行时它在启动沙箱、执行 CLI 之前已经生成。

2. **具体内容**：接收 `Sample` 对象，从其 `metadata`、`prompt`、`label` 等属性取得题目资料；整理出题目编号、镜像、目录、问题描述和 `grading` 评测配置，返回一个新的 `md` 字典。配置缺项按源码回退或保留为空，不在这里检查镜像或测试能否运行。

3. **建议构建的心智模型**：

   > - 把样本中分散的题目、环境和评测资料，整理成后续统一取用的 `md` 字典。
   > - `grading` 保存“怎样评测”的配置与材料，实际评分由后面的评测函数完成。
   > - 这里只整理已有信息；不创建沙箱、不执行测试，也不产生补丁或奖励。

4. **调用代码**：

   ```python
   # _generate，generate.py:261；本例 protocol == "scaleswe"
   md = swe.get_metadata(base_sample, protocol)
   ```

   `get_metadata` 在本场景执行 `return _metadata_scaleswe(sample)`（`swe.py:89`），将返回字典交回调用方。

## 本场景的输入与输出

沿用本步 `calc.py` 的教学场景：修复加法函数，后续用指定命令检查。镜像名为占位，未创建真实环境。输入只设置本场景需要的 `Sample` 属性；输出展示本函数返回的全部字段。本页局部验证方式见末尾来源。

**输入：一个 `Sample` 对象。** `metadata` 是其中的原始信息字典，本例的 `eval_cmd` 直接放在它里面，尚未整理进 `grading`。

```python
from slime.utils.types import Sample

sample = Sample(
    prompt="请修复 calc.py 中的 add 函数，使 add(2, 3) 返回 5。",
    label=None,
    metadata={
        "instance_id": "calc-demo",
        "image": "teaching/calc:v1",
        "workdir": "/workspace/repo",
        "eval_cmd": "python -m pytest -q tests/test_calc.py",
    },
)
```

**输出：`_metadata_scaleswe(sample)` 返回的字典，外层用 `md` 接住。**

```python
md = {
    "protocol": "scaleswe",                  # 当前资料组织方式
    "instance_id": "calc-demo",              # 题目编号
    "image": "teaching/calc:v1",              # 创建环境时使用的镜像标识
    "workdir": "/workspace/repo",             # 环境内的项目目录
    "problem_statement": "请修复 calc.py 中的 add 函数，使 add(2, 3) 返回 5。",
    "looks_swebench": False,                  # 输入是否呈现出另一种协议的特征
    "grading": {
        "swepro": None,                      # 本例没有这类评测配置
        "eval_cmd": "python -m pytest -q tests/test_calc.py",
        "eval_user": "agent",                # 未提供时，命令执行用户默认是 agent
        "f2p_script": None,                  # 本例没有自带的 pytest 脚本
        "pre_commands": None,                # 本例没有额外前置命令
    },
}
```

对照输入输出，只跟住这四个关系：

- **题目与环境字段保留**：本例直接使用 `sample.metadata` 中的编号、镜像和目录；`protocol` 由本函数写为 `"scaleswe"`。
- **问题描述补齐**：本例未提供 `metadata["problem_statement"]`，于是调用 `_coerce_prompt(sample.prompt)`；输入已经是字符串，原样成为问题描述。
- **评测资料集中到 `grading`**：原始 `metadata["eval_cmd"]` 放到 `md["grading"]["eval_cmd"]`；未提供 `eval_user` 时补上 `"agent"`，本例未提供的其他评测资料保留为 `None`。这些是配置值，此时还没有运行命令。
- **格式提示与结果分开**：`looks_swebench` 是供后续检查使用的输入特征标记；本例为 `False`。奖励和补丁状态不在这个返回字典里，`diff_text` 也由另一段流程提供。

读完回到 [scope 的评分入口①](../../../../../01-scope.md#reading-path)：`run_evaluation` 接收这份 `md` 和 Step 002 生成的 `diff_text`，再选择评分器。这里的 `md` 提前准备，不能把本次回查的阅读顺序当成实际运行顺序。

## 我的直接表述（原话）

2026-10-23，用户提出记录要求：

> 好的那么现在是否应该先给出以下这里关于metadata_scaleswe部分的字典呢
> 是否应该给这一个函数建立一个函数卡片呢？

这是本次阅读范围与记录方式的确认，尚不是对函数职责或字段规则的个人复述。此前对 `md` 的整体认识保留在原参考与讨论中，未据此推定本函数内部规则已掌握。

随后用户概括（节选）：

> 好的我大概理解了
> 就是从这里拿到了需要的所有的相关信息

助手据源码补充边界：这里整理已有的任务资料，未提供的字段仍可能为空；不能仅凭获得了 `md` 就认为资料齐全或评测一定可运行。原话与接续见[本轮讨论](../../../../../04-flow.md#evaluation-environment-entry)。

## 尚不清楚

- 已初步概括资料整理的职责；各字段的缺失、默认值和回退规则尚未逐项确认理解。
- 原始 `Sample` 如何从数据集构造，以及 `remote_env_info` 的完整结构与各字段回退次序，尚未在本次阅读中展开。
- `swepro`、`f2p_script`、`pre_commands` 的具体内容和执行方式，留到对应分支；当前先使用 `eval_cmd` 场景。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`；[get_metadata 与当前函数](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L86-L120)、[调用方](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L254-L262)。
- `Sample` 的相关属性见 [slime/utils/types.py:107–160](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/types.py#L107-L160)；字符串问题描述的处理见 [_coerce_prompt](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L150-L158)，格式标记的下游用途见 [evaluability_check](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L161-L164)。
- 样例来自本步 [run_evaluation 旧卡](run_evaluation.md) 的 `calc.py` 场景，本页补出原始输入，并按新版完整列出返回字段。相对旧版，当前函数只增加 `grading.eval_user`，见[版本核对](../../../../../references/scope-version-review-2026-10-23.md#first-function-after-input-gap)。
- 局部验证：从固定源码提取并执行 `_metadata_scaleswe` 和 `_coerce_prompt`，以仅承载相同输入属性的 `SimpleNamespace` 代替完整 `Sample`，核对本页返回字典及输入未被改写。验证限定于本例的字符串 prompt 和 `eval_cmd` 场景，没有运行完整任务、沙箱或测试命令。
- 历史资料：[Step 005 的 md 说明](../../../../../../step-005-agent-preparation/references/metadata.md)保留此前概念认识与原讨论；其存在不作为本轮已经理解全部输入的依据。
- 形成过程：[Step 003 · 独立整理元数据字典与函数卡片](../../../../../04-flow.md#metadata-scaleswe-card)。

</details>
