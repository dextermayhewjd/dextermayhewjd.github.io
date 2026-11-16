# BaseEnvironment.upload_dir

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.upload_dir.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 源码定位：[src/harbor/environments/base.py:1134–1141](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L1134)，Harbor v0.25.0，固定提交 `fdba28fc411e47e8765420a1a063b4918fce3def`。
- 首次单独记录：Step 013，2026-11-13，用户确认本轮接口建卡范围。
- 最近认识更新：尚无针对本接口的个人复述；以下为 LLM 静态核对，建卡不代表已掌握。

[Trial._prepare：skills 上传](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-mainline) → _upload_injected_skills → **upload_dir 接口** · [scope 3B](../../../../../../step-013-harbor-kubernetes-environment/01-scope.md#reading-sequence)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：_prepare 已完成环境启动，配置了注入 skills 时，需要把本地 skill 目录送入环境。
2. **具体内容**：接收本地 source_dir 与环境内 target_dir，等待目录上传；基类不实现实际传输。
3. **建议构建的心智模型**：

   > 把 Harbor 本地已有的一整份目录交给环境，使后续 Agent 可以使用其中的文件。

4. **调用代码**：Trial._upload_injected_skills:1829–1833 的真实节选；前置检查、目标目录清理和后续权限处理省略。

   ```python
   for skill, target_dir in zip(self._injected_skills, target_dirs, strict=True):
       await self.agent_environment.upload_dir(
           source_dir=skill.source,          # 本地 skill 目录。
           target_dir=target_dir.as_posix(), # 环境内目标目录。
       )
   ```

## 本场景的输入与输出

来自已读准备主线的条件动作：没有注入 skills 就不走这次上传。上传目录不等于已经安装或运行 Agent。

### 接口与输入

下面为固定版本的完整抽象方法声明。实际调用选定后端对象的方法；不会先由这段声明转发到后端。

```python
@abstractmethod
async def upload_dir(self, source_dir: Path | str, target_dir: str):
    """
    Adds a local directory to the environment.

    Args:
        source_dir: The path to the source local directory.
        target_dir: The path to which to copy the directory.
    """
```

| 输入 | 当前调用现场与接口要求 |
| --- | --- |
| self | 已启动的 self.agent_environment |
| source_dir: Path 或 str | skill.source；本地已有的 skill 目录 |
| target_dir: str | target_dir.as_posix()；环境内对应的 skill 目录 |

### 输出与返回位置

副作用：本地目录内容传入环境目录。接口没有标注返回类型，上层仅 await，随后使用环境路径；未取得真实传输结果。

返回 _upload_injected_skills 的循环，继续下一份 skill；上传后按需调整读取权限，再返回 _prepare，进入默认用户上下文与 _setup_agent。

## 我的直接表述（原话）

尚无针对本接口的职责或机制的直接复述。本轮已确认建立这些接口卡片；确认原话统一保存在 [Step 013 形成过程](../../../../../../step-013-harbor-kubernetes-environment/04-flow.md#environment-interface-cards-20261113)，不将授权建卡记成个人技术结论。

## 尚不清楚

- 目标后端的目录复制、层级、权限和失败语义，待适配核对。
- 本轮不追压缩包、网络传输或批量上传实现。

<details>
<summary>来源、验证与完整例子</summary>

- 使用本地 `/home/fredkeira/projects/harbor` 的 `git show v0.25.0:src/harbor/environments/base.py`，通过 AST 核对方法签名、文档和行号；未混用当前 main。
- [_upload_injected_skills 与返回后续位置](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L1818)：仅核对本页调用现场。
- 接口与调用代码均为静态源码材料；调用节选已标注所在分支，变量值未通过真实运行取得。没有选定或执行任何具体后端，也没有启动沙箱、安装 Agent 或操作集群。
- [Step 013 本次建卡与边界](../../../../../../step-013-harbor-kubernetes-environment/04-flow.md#environment-interface-cards-20261113)。

</details>
