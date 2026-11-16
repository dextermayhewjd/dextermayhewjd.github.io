# SingleStepTrial._collect_artifacts

- 代码归属：**Harbor**，不是 Dressage 插件。
- 源码：[single_step.py:61](/home/hongshi/projects/harbor/src/harbor/trial/single_step.py:61)，v0.25.0，提交 `fdba28fc411e47e8765420a1a063b4918fce3def`。
- 首次单独展开：2026-11-16，Step 015；用户确认建立本函数卡，尚无本函数的个人机制复述。
- 验证：静态核对本地源码。下面文件内容与路径实例为教学构造，没有执行收集、容器或评测。

[本步 scope](../../../../../01-scope.md) · [返回父函数 SingleStepTrial._run](SingleStepTrial._run.md) · [前一函数：日志上传](../trial.py/Trial._upload_agent_logs.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Agent 已执行，日志已尝试同步回环境；在评测之前收集本次任务的文件产物。恢复输出路径也会调用它。
2. **具体内容**：检查本次是否已收集，委派父类的分阶段收集方法，正常返回后设置收集标记。
3. **建议构建的心智模型**：

   > 把本次应保留的文件收进本地 artifacts 目录，并记住已经走过收集流程。它不生成评分，也不自动寻找所有改动。

4. **调用代码**（父函数节选）：

   ```python
   await self._upload_agent_logs()
   await self._collect_artifacts(
       stop_main_before_sidecars=(mode == VerifierEnvironmentMode.SEPARATE)
   )
   # 返回后：SEPARATE 先停止 Agent 环境；随后进入 _run_verifier。
   ```

## 本场景的输入与输出

### 1. 带着什么进入

对象已有 `self.agent_environment`、`self.paths.artifacts_dir`、收集配置和 `_artifact_handler`；不接收 Sample，也不接收 Proxy trajectory。

| 输入 | 本轮代表场景 |
| --- | --- |
| `self._are_artifacts_collected` | 初始为 False |
| `self.paths.artifacts_dir` | `<trial_dir>/artifacts` |
| 收集配置 | 假设 task 的 `artifacts` 包含 `/app/calc.py`；Trial 配置也可补充条目 |
| `stop_main_before_sidecars` | SHARED 传 False；SEPARATE 传 True，控制辅助服务采集前是否尝试停主服务 |

这里只先跟主服务中的文件。该布尔值不是“不收集/收集”的开关，也不是直接决定整个环境何时停止。

### 2. 本函数的完整小骨架

保留真实函数体，只增加解释注释：

```python
async def _collect_artifacts(
    self, *, stop_main_before_sidecars: bool = False
) -> None:
    if self._are_artifacts_collected:
        return  # 本次已经收集过，避免再次执行。

    await self._collect_artifacts_phased(
        artifacts_dir=self.paths.artifacts_dir,  # 本地输出目录。
        stop_main_before_sidecars=stop_main_before_sidecars,
    )
    self._are_artifacts_collected = True  # 委派正常返回后设置。
```

这三段分别是：**避免重复 → 等待收集 → 标记已执行**。标记为 True 不代表每个文件均成功取得：下游采用尽力收集，并在 manifest 中记录结果；若异常直接向上抛出，则不会执行最后这次赋值。

### 3. 委派到底收集什么

下面都是 **Harbor** 内部，作为本函数的必要背景，不分别新建卡片：

```text
SingleStepTrial._collect_artifacts
  → Trial._collect_artifacts_phased
      → 执行主服务的 collect hooks（有配置时）
      → ArtifactHandler.download_artifacts
          → 收集约定目录及配置路径，写 manifest
      → 若有辅助服务，再按配置处理辅助服务的产物
  ← 正常返回后：_are_artifacts_collected = True
```

收集集合来自任务配置与 Trial 配置的 artifacts；当前单步调用不额外传 step_artifacts。下游还会加入约定发布目录：Linux 场景是 `/logs/artifacts/`。所以**没有显式填写 `/app/calc.py`，不等于会自动发现并保存这个改动文件**；可显式配置，也可把要保留的内容放进约定目录。

**collect hook 与文件收集分工不同**：这里不是必须靠 post hook 上传文件。Harbor 先运行配置中的 collect hooks（如导出一份数据快照），再由 `download_artifacts` 收集已有文件。没有 hook 时仍可收集配置中的文件。修改后的代码、报告或快照都可以是产物，不限于代码，也不自动提取 Git diff。依据：[hooks 的来源与执行](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:1584)。

| 按需查看真实子函数 | 带着什么问题进入、读完回哪里 |
| --- | --- |
| [Trial._collect_artifacts_phased:1623](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:1623) | 主服务与辅助服务如何分阶段；返回当前函数的标记赋值 |
| [ArtifactHandler.download_artifacts:140](/home/hongshi/projects/harbor/src/harbor/trial/artifact_handler.py:140) | 配置路径如何落到本地文件及 manifest；返回分阶段收集。传输后端暂不展开 |

### 4. 同一个 calc.py 例子：调用前后留下什么

假设配置包含 `/app/calc.py`，不改 destination，文件存在且收集成功：

```text
调用前：Agent 环境                         调用后：Harbor 本地
/app/calc.py                              <trial_dir>/artifacts/app/calc.py
  def add(a, b):                            def add(a, b):
      return a + b                              return a + b

/logs/artifacts/                          <trial_dir>/artifacts/logs/artifacts/
  （约定发布目录）                         （该目录存在且成功取得时）
                                         <trial_dir>/artifacts/manifest.json
```

这是保存文件内容，不是生成 Git diff。目录已正确挂载时可以直接使用共享文件，无需再下载同一份。

<details>
<summary>manifest 的具体样例：仅展示 calc.py 的一条记录</summary>

```json
[
  {
    "source": "/app/calc.py",
    "destination": "artifacts/app/calc.py",
    "type": "file",
    "status": "ok",
    "service": null,
    "exclude": []
  }
]
```

真实清单可能还有约定目录及其他条目，status 应看实际结果。本例不是真实运行产物。

</details>

**当前函数正常返回 None**；新增内容是本地文件、manifest 及对象上的标记。下游 download_artifacts 虽有 manifest 返回值，当前这层并不把它返回给 `_run`。

返回父函数后，在 SEPARATE 模式先停止 Agent 环境，然后调用 `_run_verifier`；SHARED 模式先评测，再停止环境。产物收集本身不说明答案正确，评分是下一项职责。

## 我的直接表述（原话）

用户明确本轮入口与记录要求：

> 加入一个upload agent logs？
> 然后再看一下这里的这个collet artifacts
> 生成一下这里的short term memory吧

本轮初步理解（原话）：

> 其实就是和刚才的差不了太多一个是上传一个部分
> 一个是上传另一个部分？
> 这里的执行的artifacts
> 基本上是变动的代码对吗
> 通过post hook的方式来实现是我的理解

助手校准：两者都涉及文件，但日志上传是本地到环境，产物收集是环境到本地（挂载可能省去复制）。修改后的代码是一类产物，报告、图片或数据快照也可以是产物，取决于配置和约定目录。源码称 collect hooks，在收集前按配置运行命令以准备文件；真正的文件收集由 download_artifacts 完成。没有 hook 也能收集已有文件。用户对校准的理解尚待反馈。

## 尚不清楚

- 真实任务的 artifacts、collect hooks 如何配置：当前只用最小路径实例，不表示已跑通。
- 辅助服务的取证与各环境下载实现：只保留分阶段边界，暂不精读。
- Verifier 如何运行检查和写回评分：下一入口，尚未在本卡展开。

<details>
<summary>来源、版本与验证边界</summary>

- [当前函数及调用方](/home/hongshi/projects/harbor/src/harbor/trial/single_step.py:37)：_run、_recover_outputs、_collect_artifacts。
- [配置交给 ArtifactHandler](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:1511)：任务配置与 Trial 配置合并。
- [分阶段收集](/home/hongshi/projects/harbor/src/harbor/trial/trial.py:1623)：collect hooks、主服务、辅助服务与停止条件。
- [约定目录条目](/home/hongshi/projects/harbor/src/harbor/models/task/artifacts.py:66)、[条目归一化](/home/hongshi/projects/harbor/src/harbor/trial/artifact_handler.py:260)、[下载与 manifest](/home/hongshi/projects/harbor/src/harbor/trial/artifact_handler.py:140)。
- [本地目标路径映射](/home/hongshi/projects/harbor/src/harbor/trial/artifact_handler.py:28)。
- [本步形成过程](../../../../../04-flow.md)。本次仅静态核对，不运行安装、Agent、模型或容器。

</details>
