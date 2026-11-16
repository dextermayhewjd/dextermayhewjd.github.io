# BaseEnvironment.download_dir

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.download_dir.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 源码定位：[src/harbor/environments/base.py:1154–1162](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L1154)，Harbor v0.25.0，固定提交 `fdba28fc411e47e8765420a1a063b4918fce3def`。
- 首次单独记录：Step 013，2026-11-13，用户确认本轮接口建卡范围。
- 最近认识更新：尚无针对本接口的个人复述；以下为 LLM 静态核对，建卡不代表已掌握。

[已读执行主线 SingleStepTrial._run](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run.md) → 日志收集中的 Trial._download_role_logs → **download_dir 接口** · [scope 3B](../../../../../../step-013-harbor-kubernetes-environment/01-scope.md#reading-sequence)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Agent 执行后收集日志/产物时，需要把环境目录取回本地。本例选择未挂载、没有日志筛选条件的分支。
2. **具体内容**：接收环境内 source_dir 与本地 target_dir；源码说明会覆盖目标目录中已存在的文件，具体下载由后端实现。
3. **建议构建的心智模型**：

   > 环境中的整份目录回到 Harbor 本地，供后续日志读取、产物处理或轨迹转换使用。

4. **调用代码**：Trial._download_role_logs:824–827 的真实节选：仅保留未挂载且无 include/exclude 过滤时的调用。

   ```python
   await self.agent_environment.download_dir(
       source_dir=source_dir.as_posix(), # 环境里的日志目录。
       target_dir=target_dir,           # 本地 Trial 的日志目录。
   )
   ```

## 本场景的输入与输出

本次从已读执行/产物主线回查接口；不是 _prepare 中的操作。调用前已有环境日志目录和本地 Trial 日志目录。

### 接口与输入

下面为固定版本的完整抽象方法声明。实际调用选定后端对象的方法；不会先由这段声明转发到后端。

```python
@abstractmethod
async def download_dir(self, source_dir: str, target_dir: Path | str):
    """
    Downloads a directory from the environment to the local machine. This overwrites
    existing files in the target directory.

    Args:
        source_dir: The path to the source directory in the environment.
        target_dir: The local path to which to copy the directory.
    """
```

| 输入 | 当前调用现场与接口要求 |
| --- | --- |
| self | 已用于本次执行的 self.agent_environment |
| source_dir: str | source_dir.as_posix()；日志源目录在环境里 |
| target_dir: Path 或 str | target_dir；接收日志的本地目录 |

### 输出与返回位置

副作用：目录内容回到本地 target_dir；源码明确已有同名文件会被覆盖。接口没有标注返回类型，上层仅 await；本轮未下载任何目录。

返回 _download_role_logs，再交回日志收集调用方。这里只完成文件交付；文件如何成为轨迹、Sample 或 reward 由后续各组件负责。挂载路径可能跳过下载，有筛选条件则走过滤辅助方法。

## 我的直接表述（原话）

尚无针对本接口的职责或机制的直接复述。本轮已确认建立这些接口卡片；确认原话统一保存在 [Step 013 形成过程](../../../../../../step-013-harbor-kubernetes-environment/04-flow.md#environment-interface-cards-20261113)，不将授权建卡记成个人技术结论。

## 尚不清楚

- 目标后端如何落实目录层级、覆盖、权限与传输失败。
- 过滤和挂载优化的内部实现暂缓；当前只认识它们是不同调用分支。

<details>
<summary>来源、验证与完整例子</summary>

- 使用本地 `/home/fredkeira/projects/harbor` 的 `git show v0.25.0:src/harbor/environments/base.py`，通过 AST 核对方法签名、文档和行号；未混用当前 main。
- [_download_role_logs 的挂载、过滤和普通下载分支](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L805)：仅核对本页调用现场。
- 接口与调用代码均为静态源码材料；调用节选已标注所在分支，变量值未通过真实运行取得。没有选定或执行任何具体后端，也没有启动沙箱、安装 Agent 或操作集群。
- [Step 013 本次建卡与边界](../../../../../../step-013-harbor-kubernetes-environment/04-flow.md#environment-interface-cards-20261113)。

</details>
