# Trial._load_task

- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../step-012-task-agent-verifier/02-short-term-memory/functions/harbor/trial/trial.py/Trial._load_task.md) 完整继承；复制不改变原认识时间或已掌握状态。

- 源码：[src/harbor/trial/trial.py:532–550](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L532)，Harbor v0.25.0，固定提交 fdba28fc411e47e8765420a1a063b4918fce3def。
- 首次单独展开：Step 012，2026-11-13，用户确认建立本卡。
- 最近认识更新：2026-11-13，用户已将 path、url、download_dir 和 instruction 归为题目相关内容，追问 verifier 的作用；材料取得与读取的主线由助手核对，verifier 用途解释尚待反馈。

[从 Trial.create 的调用行进入](Trial.create.md#load-task-handoff) → **Trial._load_task** → [返回 Trial.create，继续类型选择](Trial.create.md#trial-create-mainline) · [本步导航](../../../../../../step-012-task-agent-verifier/01-scope.md#current-reading)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Trial.create 已拿到一份 TrialConfig，需要先取得题目，才能按题目内容创建具体 Trial。
2. **具体内容**：把题目来源配置转成 task_id，交给 TaskClient 取得材料目录，再从该目录构造 Task；将 Task 与材料取得记录一起返回。
3. **建议构建的心智模型**：

   > 先按地址找到题目材料，再把这些文件读成题目对象；两样结果一起交回 Trial.create。

4. **调用代码**（父函数 Trial.create:474）：

   ```python
   task, task_download_result = await cls._load_task(config)
   # 返回后先检查配置，再根据 task.has_steps 选择具体 Trial 类型。
   ```

## 本场景的输入与输出

<a id="load-task-mainline"></a>
<a id="caller-context"></a>

### 从父函数带着什么进来？

我们停在 Trial.create 的上述 await 调用。config 已经说明题目来源、Agent、环境与评测安排；当前只要先把题目准备好。**这次进入的问题是：只有题目来源配置，怎样得到后面可读取内容的 Task？**

这里的 Task 是 Harbor 的题目对象，保存题目配置、instruction 和文件位置，与前面负责调度协程的 asyncio.Task 区分。

沿用 hello-world 的静态场景，只列本函数读取的输入字段；题目根目录是占位路径，未在本机运行：

```text
config: TrialConfig
├─ task: 题目来源配置
│  ├─ path: <Harbor源码目录>/examples/tasks/hello-world
│  ├─ git_url / name: None，使用本地题目来源
│  ├─ overwrite: False
│  └─ download_dir: None
├─ extra_instruction_paths: []
├─ extra_instructions: []
└─ verifier.disable: False
```

这里 config.task 的 TaskConfig 描述“从哪里取得题目”；返回 task.config 则是从题目目录的 task.toml 解析出的内容。两者处于不同阶段，不能只因都叫 config 就当成同一份对象。

### 核心代码：取得标识 → 取得目录 → 构造并返回

下面保留原函数签名、所有实参和两个返回项，只增加旁注；这是源码阅读片段，需要 Harbor 依赖和题目文件，不能独立运行。

```python
@staticmethod
async def _load_task(config: TrialConfig) -> tuple[Task, TaskDownloadResult]:
    client = TaskClient()
    task_id = config.task.get_task_id()  # [1] 将来源配置转成客户端使用的题目标识。
    download_result = (
        await client.download_tasks(
            task_ids=[task_id],         # [2] 此处只请求一份题目，客户端接口接收列表。
            overwrite=config.task.overwrite,
            output_dir=config.task.download_dir,
        )
    ).results[0]                       # 从批量结果中取出这份题目的材料记录。
    return (
        Task(
            task_dir=download_result.path,  # [3] 从取得的本地目录构造题目对象。
            extra_instruction_paths=config.extra_instruction_paths,
            extra_instructions=config.extra_instructions,
            disable_verification=config.verifier.disable,
        ),
        download_result,               # 材料记录原样保留，作为第二个返回项。
    )
```

1. **取得标识**：本例 path 指向本地题目，get_task_id 得到 LocalTaskId。它只是材料定位信息，此时还不是读取后的 Task。
2. **取得目录**：TaskClient 负责按来源取得材料；本函数只使用返回记录的 path。download_tasks 是统一接口名，不据此断定每次都会从网络重新下载。具体来源适配与缓存策略暂不展开。
3. **构造题目**：Task 使用这个目录读取 task.toml；普通单步题目还读取 instruction.md。附加 instruction 的文件和文本继续传入，disable_verification 控制构造时是否跳过主机侧评测材料检查，不是在这里执行评分。

### 为什么加载题目还要传 verifier.disable？

题目材料除了给 Agent 的 instruction，也可以包含供后续评测使用的测试脚本。Task 构造时要按本次运行是否启用评测，决定是否检查这些材料。_load_task 把运行配置里的开关传进去：

```python
# _load_task 传入 Task(...) 的参数：
disable_verification=config.verifier.disable

# Task.__init__ 内的真实条件与调用：
if not disable_verification:
    self._validate_tests(self.config, self.paths, file_filter=self.file_filter)
```

- `verifier.disable=False`：本次需要评测，加载时检查所需评测材料；普通单步、未内置测试的路径会查找适合评测环境操作系统的测试脚本，缺少时提前报错。
- `verifier.disable=True`：在这个构造位置跳过 `_validate_tests`；其他配置读取和路径检查仍会进行。

当前只检查材料，实际执行评测在后面的 Trial 运行阶段。这个参数让题目加载遵循同一份评测安排。当前函数还要记住两项输出：读取好的 Task，以及材料取得记录 TaskDownloadResult；不必为了读懂它继续展开所有下载后端。

### 返回什么，父函数接着做什么？

沿用官方 hello-world 文件，以下是**静态字段示意**，不是本次函数调用的真实输出。材料目录用“客户端返回的本地目录”表示，不虚构下载日志或缓存结果。

```text
返回二元组 (Task, TaskDownloadResult)
├─ task: Task
│  ├─ name: "harbor/hello-world"
│  ├─ instruction: 'Create a file called hello.txt with "Hello, world!" as the content.'
│  ├─ config: 从 task.toml 解析的题目配置
│  └─ has_steps: False
└─ task_download_result: TaskDownloadResult
   └─ path: 客户端返回的题目材料本地目录
```

父函数左边的 task 和 task_download_result 分别接住两项。随后 task.has_steps 决定 Trial 类型；本例进入 SingleStepTrial(config, _task=task, _task_download_result=task_download_result)，把两份结果都传给构造器。

**读到这里返回 [Trial.create](Trial.create.md#trial-create-mainline)。** 此时只是取得题目和创建题目对象，还没有运行题目指令；Agent/Environment 对象创建与后面的 trial.run 按父函数主线继续。

## 我的直接表述（原话）

用户在确认入口与本轮重点后要求：

> 好的 那么就来建立一下这个task卡吧

用户随后阅读本函数并表述：

> 好的 那么我们来看一下这个load task吧
> 这里其实就是非常清楚这个题目的path啊 url啊
> download dir或者instruction
>
> 所有都是和题目相关的部分
> 但是为什么还有一个verifier？
> 不过应该就是这些内容还有别的什么吗？

用户已表达题目相关配置的归类；verifier 的检查用途与两个返回项由助手补充，不记为用户已独立说清。


## 尚不清楚

- TaskClient 对不同来源怎样取得材料、怎样处理缓存和 overwrite，本轮按接口使用，未深入实现。
- Task 构造器中具体怎样解析、校验文件与追加 instruction，当前只核对输出所需的行为，未单独精读。
- TaskDownloadResult 除 path 之外的完整字段与后续用途，按父函数需要再回查。

<details>
<summary>来源、版本与验证边界</summary>

- 当前函数与父调用均依据 Harbor v0.25.0 的固定提交 fdba28fc411e47e8765420a1a063b4918fce3def；[Trial.create](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L469)、[Trial._load_task](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L532)。
- 题目来源的 get_task_id 与输入默认字段：[models/trial/config.py](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/config.py)。Task 的读取行为：[models/task/task.py](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/task/task.py#L51)。本轮没有将这两个依赖提前建成独立函数卡。
- 静态场景使用官方 [hello-world/instruction.md](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/examples/tasks/hello-world/instruction.md) 与 [task.toml](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/examples/tasks/hello-world/task.toml)。名称来自 task.toml 的 task.name；该文件未定义 steps，普通题目路径的 has_steps 为 False。
- 原本地 Harbor checkout 在当前环境不可用，本轮读取官方固定版本源码；TaskClient 内部未展开，材料路径只按调用处的接口表示。没有真实调用 _load_task、下载题目、创建运行环境或执行模型；示例不代表完成运行验证。
- 本次 verifier 追问核对了固定版本 [Task 构造与 _validate_tests](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/task/task.py) 的条件与检查路径；只作静态核对，未执行评测。
- [Step 012 本轮建卡经过](../../../../../../step-012-task-agent-verifier/04-flow.md#load-task-card-created-20261113)。

</details>
