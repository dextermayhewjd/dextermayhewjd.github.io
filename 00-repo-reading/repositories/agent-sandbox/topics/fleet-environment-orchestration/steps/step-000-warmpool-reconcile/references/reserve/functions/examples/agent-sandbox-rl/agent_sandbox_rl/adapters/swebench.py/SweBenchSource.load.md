# SweBenchSource.load

[返回调用方 main](../../../../../../../../02-short-term-memory/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md) · [同文件的执行探针](swebench_probe.md) · [本轮讨论](../../../../../../../../04-flow.md#swebench-source-role)

- 源码定位：[adapters/swebench.py:66](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py#L66)。
- 首次接触：Step 000，2026-11-04，用户询问 SweBenchSource 的工作。
- 最近认识更新：用户进一步追问 Source 在流水线中何时出现；本轮明确它在 main 中创建，并在进入 fleet.run/setup 前完成任务加载，尚待理解反馈。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：main 在进入 fleet.run 之前创建 SweBenchSource 并交给 fleet.load_tasks；后者经 to_tasks 调用这个 load 方法。执行到 setup 或 acquire 时，Task 已经存在。
2. **具体内容**：读取选定的数据集范围，把每行转换成 Task，返回任务列表。
3. **建议构建的心智模型**：

   > SweBenchSource 是数据入口。构造时记住从哪里读、读多少；load 才执行读取，并将数据集字段翻译成 Fleet 使用的任务格式。

4. **调用代码**：实际示例调用 fleet.load_tasks，内部的 to_tasks 在识别到 TaskSource 后执行以下分支：

   ```python
   if isinstance(source, TaskSource):
       return source.load()
   ```

## 本场景的输入与输出

### 1. 输入

load 没有额外显式参数，使用构造时保存在 self 中的读取条件。

| 设置 | 本轮示例 |
| --- | --- |
| dataset | 默认 R2E-Gym/SWE-Bench-Verified |
| split | test |
| limit / offset | 1 / 0，读取一条 |
| id_field / image_field | instance_id / docker_image |
| keep_row | False，只保留基本附加信息 |

以下假设本次读到一行数据，用于说明字段映射；不是实际下载结果。

```python
r = {
    "instance_id": "case-001",
    "docker_image": "example/swe-env:case-001",
    "repo": "example/project",
    "base_commit": "abc123",
    "problem_statement": "Example issue description",
}
```

### 2. 输出

```python
[
    Task(
        id="case-001",
        image="example/swe-env:case-001",
        metadata={"repo": "example/project", "base_commit": "abc123"},
    )
]
```

1. instance_id 转成 Task.id。
2. docker_image 转成 Task.image，保存的是镜像名称。
3. repo 和 base_commit 放入 metadata。
4. 本场景 keep_row=False，因此没有保留整条原始记录。keep_row=True 时，原始行的深拷贝另存到 metadata["ds"]，供需要完整题目信息的回调或 R2E-Gym 使用。

### 3. 读取与转换的代码

下面裁剪 limit=1、offset=0 且依赖可用的正常路径。省略导入检查与日志，保留读取范围、转换和返回。

```python
# [1] select the dataset slice
split = self.split
if self.offset or self.limit is not None:
    end = self.offset + self.limit if self.limit is not None else ""
    split = f"{self.split}[{self.offset}:{end}]"

# [2] read rows
rows = list(load_dataset(self.dataset, split=split))

# [3] convert rows to tasks
tasks = []
for i, r in enumerate(rows):
    meta = {"repo": r.get("repo", ""), "base_commit": r.get("base_commit", "")}
    if self.keep_row:
        meta["ds"] = copy.deepcopy(dict(r))
    tasks.append(Task(id=str(r.get(self.id_field, i)),
                      image=r[self.image_field], metadata=meta))

# [4] return task descriptions
return tasks
```

1. **[1] 选择范围**：本例得到 test[0:1]。
2. **[2] 读取数据**：调用 Hugging Face datasets 的 load_dataset。
3. **[3] 转成 Task**：逐行按上面的字段关系构造任务对象。
4. **[4] 返回列表**：列表经 to_tasks 回到 fleet.load_tasks，后者保存为 fleet.tasks。

这一阶段准备的是任务数据。完整调用时间线见 [scope 的调用方前置阶段](../../../../../../../../01-scope.md#task-loading-before-setup)。创建环境、领取 handle 和执行 process_fn 属于后续流程。

<details>
<summary>本轮先保留的边界</summary>

1. SweBenchSource(...) 的 __init__ 只保存读取条件，不在构造时读取数据集。
2. 直接使用本类时，limit=None 表示全部，limit=0 立即返回空列表。示例脚本把环境变量 TASKS_LIMIT=0 转成 None，这是调用方的约定。
3. 行中缺少 ID 字段时，使用本次读取范围内的枚举序号；镜像字段是必需的，缺少时会抛出 KeyError。
4. 本方法不运行探针、解题或评分；同文件中的 swebench_probe 是另一个执行阶段的函数。

</details>

## 我的直接表述（原话）

> 好的好的
> 也就是这里只是执行了这里的swebench probe的部分?
> 还有做别的方面的吗?
> 这里的swebenchsource在做什么呢?

尚无对数据转换实现的独立复述。

随后用户询问来源和时机：

> 我有点没理解
> 我的理解是这里的executor是这里的process parallel
> 然后准备好的task也是fleet acquire中就生成好了这样子的一个pod
> 然后直接执行的份额时候就是process fn以及这里的task和handle了
> 但是这个source是在哪里出现的呢?
> 是我们一开始没有注意的和关注的fleet set up时候创建的吗?
> 这样子就在哪一步source load了对应的task
> 是我的理解?
>
> 我们一开始的流水线上是否差了那么一步呢?

## 尚不清楚

1. Source 构造、Task 加载、setup 准备环境、acquire 领取的先后关系，尚待用户确认。
2. 数据集字段与 Task 字段的对应，尚待用户确认。
3. 完整题目记录在后续环境和评分逻辑中怎样使用，尚未展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 构造参数：swebench.py:54–64；本方法：66–94；Task 定义：sources.py:159–171。
- 调用衔接：run_swebench_fleet.py:85–87；fleet.py:429–453；sources.py:308–319。
- 输入行和输出示例为教学构造；本次仅静态核对，没有访问或下载真实数据集。
- 原始过程：[Step 000 · 数据来源与执行探针](../../../../../../../../04-flow.md#swebench-source-role)。

</details>
