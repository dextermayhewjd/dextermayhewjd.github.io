# Trial._upload_injected_skills

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../step-014-model-routing-and-api-contract/03-long-term-memory/functions/harbor/trial/trial.py/Trial._upload_injected_skills.md) 完整继承；不改变原认识时间或掌握状态。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/trial/trial.py/Trial._upload_injected_skills.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 源码：[trial.py:1818–1843](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L1818)，Harbor v0.25.0，固定提交 `fdba28fc411e47e8765420a1a063b4918fce3def`。
- 首次单独展开：Step 013，2026-11-13。
- 最近认识更新：2026-11-13，用户已概括把 skills 放到对应文件夹；具体传输与 Agent 如何使用仍未展开。

[Trial._prepare：健康检查返回之后](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-skills-call) → **当前 _upload_injected_skills** → [upload_dir](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.upload_dir.md) → 返回本函数 → 返回 _prepare。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：健康检查正常返回，准备把配置的技能目录交给 Agent 使用。
2. **具体内容**：确定每个技能的目标目录，清理后上传，并在非 Windows 环境补充访问权限。
3. **建议构建的心智模型**：

   > 把本地准备好的技能文件放入环境，供后续 Agent 使用。

4. **调用代码**（Trial._prepare:648–652，当前 user_agent=None 分支节选）：

   ```python
   await self._upload_injected_skills()  # 当前进入，正常返回 None。
   with self.agent_environment.with_default_user(self.task.config.agent.user):
       await self._setup_agent()         # 后续准备 Agent，属于 Step 014。
   ```

## 本场景的输入与输出

初始化时已保存 `_injected_skills` 与 `_effective_skills_dir`。本函数直接读取它们；每个 skill 的 `name` 用于命名目标子目录，`source` 是本地源目录。正常返回 None，新增内容保存在环境目录中。

<a id="upload-skills-mainline"></a>

下面保留完整函数，仅添加阶段注释；当前先看目录准备与上传，权限细节按需回查。

```python
async def _upload_injected_skills(self) -> None:
    # 没有待注入技能或目标目录就跳过。
    if not self._injected_skills:
        return
    effective_skills_dir = self._effective_skills_dir
    if effective_skills_dir is None:
        return

    # 每个技能占一个同名子目录，上传前清理目标。
    skills_root = PurePosixPath(effective_skills_dir)
    target_dirs = [skills_root / skill.name for skill in self._injected_skills]
    await self.agent_environment.empty_dirs(target_dirs, chmod=False)

    # 把每个 skill.source 本地目录传到对应的环境目录。
    for skill, target_dir in zip(self._injected_skills, target_dirs, strict=True):
        await self.agent_environment.upload_dir(
            source_dir=skill.source,
            target_dir=target_dir.as_posix(),
        )

    # 非 Windows：补充读取权限和目录访问所需权限。
    if self.task.config.environment.os != TaskOS.WINDOWS:
        chmod_targets = " ".join(
            quote_shell_arg(target_dir, self.task.config.environment.os)
            for target_dir in target_dirs
        )
        await self.agent_environment.exec(
            f"chmod -R a+rX {chmod_targets}",
            user="root",
        )
```

| 按需进入 | 读完回来哪里 |
| --- | --- |
| [BaseEnvironment.upload_dir](../../../../../../step-013-harbor-kubernetes-environment/02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.upload_dir.md) | 回到 for 循环，继续下一份技能；最后处理权限并返回 _prepare |

## 我的直接表述（原话）

> 那么我们继续吧
> 下一个我们需要看的部分应该是这个upload injected skills了对吗?

本轮职责复述：

> 简单的来说就是在对应的地方安装上这个skills
> 到对应的文件夹部分是我的理解

这里的“安装”具体指复制技能目录并补充访问权限；当前函数不执行技能内容，也不完成 Agent 本身的安装。

## 尚不清楚

- 技能目录解析与具体传输后端暂缓；本轮先接清 source → target_dir。
- Agent 如何发现并使用上传后的技能，留到 Agent 准备与执行阶段。

<details>
<summary>来源与验证</summary>

- 完整函数、调用方与字段初始化（Trial.__init__:188–189）均通过本地 `git show v0.25.0:src/harbor/trial/trial.py` 核对。
- `_resolve_effective_skills_dir:1801` 优先使用任务配置的 skills_dir，有注入技能时可回退至默认技能目录；此处只定位，不另建解析器卡片。
- `chmod -R a+rX` 递归增加读取权限，并为目录或已有执行位的文件增加执行位；不会执行技能文件。
- 没有运行上传、权限命令或 Agent。[本轮接续](../../../../../../step-013-harbor-kubernetes-environment/04-flow.md#injected-skills-entry-20261113)。

</details>
