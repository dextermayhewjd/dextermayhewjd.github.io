# base_sample：传给 generate 的基础样本

[返回参考目录](generate-input-context.md) · [题目信息怎样整理成 md](metadata.md)

**`base_sample` 是调用方交给 `generate` 的一个 `Sample` 对象。** 它携带题目信息、样本索引，以及可能已有的 `session_id`。进入当前函数时，这个对象已经存在。

类定义就在 [`slime/utils/types.py:107`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/utils/types.py#L107-L169)。`Sample` 是类型名，`base_sample` 是当前调用场景中的变量名。

## 当前需要看哪些内容

下面只表示相关属性的归属，其他训练字段暂时省略：

```text
base_sample：Sample 对象
├─ metadata      题目相关的原始信息
├─ prompt        输入的问题内容
├─ index         样本索引，可能为 None
├─ group_index   样本分组索引，可能为 None
└─ session_id    已有的执行编号，可能为 None
```

## 源码中现成的构造示例

Coding Agent 的 CPU 测试在 [`_base_sample`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_agent/test_agent_rollout_cpu.py#L96-L105) 中构造了一个样本，并把它交给 `generate`。下面按该示例整理：把局部变量 `meta` 内联，省略测试辅助函数接收额外字段覆盖的 `**md`，保留原有数据值。

```python
from slime.utils.types import Sample

base_sample = Sample(
    index=0,
    group_index=0,
    prompt="fix the bug",
    metadata={
        "instance_id": "demo-1",
        "image": "fake-image",
        "workdir": "/workspace/repo",
        "problem_statement": "fix the bug",
        "eval_cmd": "true",
    },
)
```

- `metadata` 字典是 `Sample` 对象中的一个属性；`index`、`group_index`、`prompt` 则是这个对象的其他属性。
- 这里没有传入 `session_id`，所以它保留类定义中的默认值 `None`。
- `demo-1`、`fake-image` 是源码测试使用的值；本轮没有运行该测试或创建沙箱。它们与 md 参考页中 `issue-123` 的教学示意是不同的例子。

按 `scaleswe` 路径，把这个对象交给后续调用：

```python
md = swe.get_metadata(base_sample, "scaleswe")
instance_id = md["instance_id"]  # "demo-1"
```

这里的题目字段来自 `base_sample.metadata`，任务约定由调用方传入。`get_metadata` 将它们整理为新的 `md` 字典；它本身不是原始题目信息的最初来源。

## 在当前链条中怎样使用

- `get_metadata(base_sample, protocol)` 从这个对象整理出后续使用的[题目信息 md](metadata.md)。
- [_session_id](../02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_session_id.md) 根据已有编号或相关字段取得执行编号；进入这个函数后，形参 `sample` 对应这里的 `base_sample`。本函数只读取样本的 `session_id`、`index`、`group_index`，另接收 `instance_id`；不把 `metadata` 或 `prompt` 一起拼进编号。
- 调用方把返回的编号写回 `base_sample.session_id`，同时保存在局部变量 `session_id` 中。
- 后续 `finish_session(..., base_sample=base_sample, ...)` 使用它作为导出样本的基础。

> `base_sample` 是本次 generate 接到的基础样本；当前从中取题目信息，后面还会用它组织结果。

本页先认清对象和用途。它最初怎样加载、索引怎样分配，以及全部训练字段的作用，按后续问题展开。

<details>
<summary>源码与原始讨论</summary>

- 固定提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`；以上为静态源码说明。
- [Sample 的属性定义](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/utils/types.py#L107-L169)；[generate 接收与使用对象](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L182-L245)。
- [测试中的构造与调用](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_agent/test_agent_rollout_cpu.py#L96-L105)，实际交给 generate 的位置见 [175–181 行](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_agent/test_agent_rollout_cpu.py#L175-L181)。示例字段与类默认值已静态核对，未执行测试中的 HTTP 或沙箱替身。
- [原始输入背景问题](../04-flow.md#session-id-reading-boundary)；[本次拆分](../04-flow.md#split-input-references)。由原合并说明整理，不表示新增掌握或运行证据。
- [从 md 回查 Sample 定义与实例的追问](../04-flow.md#sample-definition-and-example)：用户已初步复述 md，Sample 对象关系的补充说明仍待反馈。

</details>
