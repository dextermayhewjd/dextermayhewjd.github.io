# U57 · Harbor Task 读取 Dressage 生成的题目目录

<a id="u57"></a>

[题目文件与可选后端目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[prepare_dataset.py 340–341](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dataset_tools/dapo/prepare_dataset.py#L340-L341)

```python
_write_text(task_dir / "instruction.md", record.prompt.rstrip() + "\n")
_write_text(task_dir / "task.toml", _task_toml(record))
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage prepare_dataset.py 335–347](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dataset_tools/dapo/prepare_dataset.py#L335-L347) | 从生成器取出一道题，记录输出目录、`instruction.md` 原文与 `task.toml` 中的 task name。 |
| ② 结果　[Harbor task.py 73–90](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/task/task.py#L73-L90) | 在 Harbor 构造 Task 后核对 `task.name` 和 `task.instruction`。对同一个生成目录比较三版。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/task/task.py#L52-L81) | Dressage 给出包含 `task.toml`、`instruction.md`、环境目录和 `tests/` 的本地题目目录 | 同一份生成输入实测可被 `Task(path)` 接收 | `Task.name` 和 `Task.instruction` 供 Job 或 Agent 使用 | 实测读到 `dressage/dapo_math_00000` 与 `What is 2 + 2?` |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/task/task.py#L51-L91) | Dressage 给出包含 `task.toml`、`instruction.md`、环境目录和 `tests/` 的本地题目目录 | 同一份生成输入实测可被 `Task(path)` 接收 | `Task.name` 和 `Task.instruction` 供 Job 或 Agent 使用 | 实测读到 `dressage/dapo_math_00000` 与 `What is 2 + 2?` |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/task/task.py#L51-L91) | Dressage 给出包含 `task.toml`、`instruction.md`、环境目录和 `tests/` 的本地题目目录 | 同一份生成输入实测可被 `Task(path)` 接收 | `Task.name` 和 `Task.instruction` 供 Job 或 Agent 使用 | 实测读到 `dressage/dapo_math_00000` 与 `What is 2 + 2?` |

**接续**　读题文件已验。要验实际 Agent 收到题目，可沿这道题运行一条完整 Trial。 [prepare_dataset.py 335-347](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dataset_tools/dapo/prepare_dataset.py#L335-L347) · [三版 DAPO 文件交接原始输出](../evidence/dapo-files.txt) · [文件探测与断言](../evidence/dapo_files.py) · [问题 18](../../investigations/18-example-configs/README.md)
