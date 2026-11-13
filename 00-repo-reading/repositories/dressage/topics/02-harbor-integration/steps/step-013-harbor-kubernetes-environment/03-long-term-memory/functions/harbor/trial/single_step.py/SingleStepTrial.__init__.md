# SingleStepTrial.__init__

- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../step-012-task-agent-verifier/02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial.__init__.md) 完整继承；复制不改变原认识时间或已掌握状态。

- 源码：[src/harbor/trial/single_step.py:20](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/single_step.py#L20)，Harbor v0.25.0，固定提交 fdba28fc411e47e8765420a1a063b4918fce3def。
- 首次单独展开：Step 012，2026-11-13。
- 最近认识更新：尚无用户对初始化内部的独立表述；本轮按确认范围提供材料。

[调用方 Trial.create](../trial.py/Trial.create.md) → **SingleStepTrial.__init__** → [基类 Trial.__init__](../trial.py/Trial.__init__.md) · [scope](../../../../../../step-012-task-agent-verifier/01-scope.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Trial.create 已取得题目，普通单步分支需要创建 SingleStepTrial 对象。
2. **具体内容**：检查题目没有非空 steps，原样转交三份材料给基类初始化，再将产物收集标记设为 False。
3. **建议构建的心智模型**：

   > 单步子类只补自己的约束与状态；这次尝试共用的准备工作交给 Trial 基类完成。

4. **调用代码**（Trial.create 的普通单步分支）：

   ```python
   trial = SingleStepTrial(
       config,
       _task=task,
       _task_download_result=task_download_result,
   )
   ```

## 本场景的输入与输出

### 带着什么进入？

沿用 hello-world 静态例子：config 是此前组成的 TrialConfig，指定主 Agent 与运行环境，user_agent=None；task 已由 _load_task 读取，has_steps=False；task_download_result 保存材料取得记录。当前要把这些已有材料组织成一次尝试对象。

### 真实初始化代码

以下保留本方法完整签名与语句，只增加阅读注释；依赖 Harbor，并非独立运行例子。

```python
def __init__(
    self,
    config: TrialConfig,
    *,
    _task: Task | None = None,
    _task_download_result: TaskDownloadResult,
):
    if _task is not None and _task.has_steps:
        raise ValueError("SingleStepTrial requires a task without [[steps]].")
    super().__init__(                     # [1] 当前实例交给 Trial.__init__ 初始化。
        config,
        _task=_task,
        _task_download_result=_task_download_result,
    )
    self._are_artifacts_collected = False  # [2] 返回后，补上本类的产物收集状态。
```

- hello-world 不触发前面的检查错误，进入 super().__init__；三份输入原样转交，并未重新加载题目。
- 这里的基类是 Trial；基类初始化仍是在准备同一个 SingleStepTrial 实例，没有另外创建一个 Trial 对象。
- 基类初始化正常完成后，才设置 _are_artifacts_collected=False。这个标记供后面的产物收集方法避免重复收集，初始化时只设初值。

| 当前入口 | 需要展开时进入哪里 | 返回后继续哪里 |
| --- | --- | --- |
| super().__init__(...) | [Trial.__init__](../trial.py/Trial.__init__.md) | 回到本方法设置 _are_artifacts_collected=False |
| 本方法正常结束 | [Trial.create](../trial.py/Trial.create.md) | SingleStepTrial(...) 调用交出初始化后的实例，由 trial 接住，随后经过 _create_bridge 和 return trial |

### 输出与副作用

__init__ 没有业务返回值；外层类调用 SingleStepTrial(...) 得到初始化后的实例。静态状态示意：

```text
trial: SingleStepTrial
├─ config                         ← 传入的运行安排
├─ task                           ← 刚读取的同一个题目对象
├─ _task_download_result          ← 同一份材料取得记录
├─ 本次身份、目录与共用依赖       ← Trial.__init__ 准备
└─ _are_artifacts_collected: False ← 本方法最后设置
```

基类构造包含本地目录、记录和运行组件的准备。实际执行题目由队列后面的 await trial.run() 启动；本轮不重读 Step 011 已讨论的完整运行生命周期。

## 我的直接表述（原话）

用户指定本轮入口：

> 好的 那么看一下这个trial在做什么吧
> 也就是这里的这个single step trial吧

尚无用户对本方法内部的独立解释；上述用途与输入输出由助手按源码整理。

## 尚不清楚

- 基类准备的字段怎样在运行阶段逐一被使用，不在本次初始化入口全部展开。
- _are_artifacts_collected 在失败恢复与产物收集中的详细路径，后续按问题回查。

<details>
<summary>来源、版本与验证边界</summary>

- [固定版本 single_step.py](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/single_step.py)：核对继承关系、构造器，以及产物收集方法对标记的使用。
- [固定版本 trial.py](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py)：核对 Trial.create 的调用与 Trial.__init__ 的交接。
- 当前原本地 checkout 不可用，使用官方固定提交读取；没有构造真实实例、启动环境或调用模型。状态图为静态示意。
- [Step 012 本次过程](../../../../../../step-012-task-agent-verifier/04-flow.md#single-step-init-entry-20261113)。

</details>
