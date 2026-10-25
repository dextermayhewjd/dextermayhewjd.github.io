# _apply_diff

- 源码定位：[examples/coding_agent_rl/swe.py:352–366](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L352-L366)，由助手核对。
- 首次接触：Step 2，2026-10-21，在评测环境中应用补丁。
- 最近认识更新：2026-10-23，用户已复述“先保存补丁文件，再应用，再判断是否应用成功”的主线；工具冲突处理和通用方法的能力边界仍未逐项展开。
- 本轮源码校准：2026-10-23，更新临时路径、命令顺序和后端边界；[旧版完整卡片](../../../../../references/apply-diff-at-2f231865.md)保留，源码更新不计为个人新增认识。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`_grade_scaleswe` 已创建新评测环境并完成必要准备，需要把 Agent 交出的补丁应用到该环境的工作区，随后才能测试。

2. **具体内容**：先把 `diff_text` 保存为沙箱里的临时补丁文件，再执行补丁命令，按照其中的修改说明更新 `workdir` 中的仓库文件；最后返回是否应用成功。空补丁直接返回 `True`。

3. **建议构建的心智模型**：

   > `_apply_diff` 把 Agent 给出的补丁应用到已有的评测仓库：`write_file` 先保存修改说明，`exec` 再运行读取这份说明的补丁工具，真正修改仓库文件。
   >
   > 两次调用通过同一沙箱中的补丁文件衔接。函数返回是否应用成功，随后由调用方继续测试。

4. **调用代码**（`swe.py:329–331`）：

   ```python
   applied = await _apply_diff(ev, workdir, diff_text)
   if not applied:
       return EvalResult(0.0, False)
   ```

## 本场景的输入与输出

沿用本步加法修复的教学场景；`ev` 已由 [_evaluation_sandbox](_evaluation_sandbox.md)交付，并经过 [ensure_agent_user](../../../slime/agent/sandbox.py/ensure_agent_user.md) 准备。镜像和仓库未实际运行，下面假设补丁能够应用；本轮仅用替身验证调用与返回。

**输入：已有评测沙箱、仓库目录和补丁文本。**

```python
# ev：父函数持有的已就绪评测沙箱对象，由所选后端提供
workdir = "/workspace/repo"
diff_text = """diff --git a/calc.py b/calc.py
--- a/calc.py
+++ b/calc.py
@@ -1,2 +1,2 @@
 def add(a, b):
-    return a - b
+    return a + b
"""
```

**成功后的输出与文件变化：**

| 项目 | 结果 |
| --- | --- |
| 返回值 | `True`，由调用方的 `applied` 接住 |
| 沙箱内的 `/tmp/__cagent_patch__.diff` | 保存输入的 `diff_text`；本函数应用后不删除它 |
| 沙箱内的 `/workspace/repo/calc.py` | 原来的 `return a - b` 已改成 `return a + b` |

**输入怎样得到上述结果（`swe.py:352–366`，完整函数）：**

```python
async def _apply_diff(ev: Sandbox, workdir: str, diff_text: str) -> bool:
    if not diff_text.strip():
        return True
    await ev.write_file(_PATCH, diff_text, user="agent")
    # First-success-wins ladder collapsed into one exec (one sandbox round-trip).
    ladder = " || ".join(
        f"({cmd})"
        for cmd in (
            f"git apply --whitespace=nowarn {_PATCH}",
            f"git apply --3way --whitespace=nowarn {_PATCH}",
            f"patch -p1 --no-backup-if-mismatch < {_PATCH}",
        )
    )
    ec, _, _ = await ev.exec(f"cd {shlex.quote(workdir)} && ({ladder})", user="agent", check=False, timeout=120)
    return ec == 0
```

- **补丁文本 → 补丁文件**：`write_file` 把 `diff_text` 原样写到 `_PATCH` 指定的 `/tmp/__cagent_patch__.diff`，包括其中的 `-`、`+` 修改行。这已经是真实的文件写入；写哪个文件由路径决定，本例写的是补丁文件，仓库中的 `calc.py` 仍是减法。
- **候选命令 → `ladder`**：先普通 `git apply`，失败再尝试 `git apply --3way`，仍失败才尝试 `patch -p1`。三条命令用 `||` 连接，任一个成功便停止尝试。这几行只组装命令字符串，尚未执行。
- **补丁文件 → 仓库修改**：`exec` 在同一个沙箱中执行整条命令，先 `cd` 到 `workdir`，再运行补丁工具；工作目录经过 `shlex.quote`，作为一个路径参数传入。工具通过 `_PATCH` 读取刚才保存的说明，找到 `calc.py` 并把指定的减法语句改成加法。两次调用靠这份文件衔接；`exec` 负责运行命令，`git apply` 或 `patch` 负责解释补丁并修改文件。
- **执行结果 → 调用方**：`exec` 返回 `(exit_code, stdout, stderr)`，这里只保留退出码 `ec`。`check=False` 让非零退出码交回这里判断：为 `0` 时返回 `True`，否则返回 `False`；[新版调用方](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L329-L340) 用 `applied` 判断是否继续测试。补丁应用成功与测试通过分别由两步判断。

本函数不删除补丁文件，也不负责回收环境。后续保留或清理由所选后端的退出策略决定，不能把“离开 `async with`”直接等同于所有后端都立即删除文件。

空白补丁在入口直接返回 `True`，不写文件、不执行命令，允许调用方继续测试；这不表示已经修改了文件。

返回后，父函数在 `330–331` 行处理应用失败；成功则进入评分阶段。本例有 `eval_cmd`，因此下一处是 `337` 行的 `_run_eval_cmd`，届时才运行测试命令。

## 我的直接表述（原话）

2026-10-21，对函数职责的初步理解：

> 我可以简单理解是这里把要写的文件放进去？
> 我可以这么理解吗？

同日继续追问两次调用的关系：

> 不是我的意思是这里的_apply_diff应该做的事情不应该是考虑一下这里通过要写清楚这里的ev.write和这里的exec的关系
> 至少需要简单写一下这一个apply之后具体做什么吧
> 是做到了直接在当前的基础上先通过write file在sandbox中直接写了呢？
> 那么下面的exec做的又是什么呢？
> 我不是特别理解

随后反馈“大概理解”，并继续核对：

> 好的我大概理解了 这里的write file负责把补丁写上去 也就是只是和写什么相关
> 或者说是改动相关
> 只有exec才是真的改动？

随后询问文件的保留时间：

> 那么实现这里的exec的时候我只是回校要知道这里的补丁文件就直接消失吗了吗？
> 用后就消失了还是一直保存的？

2026-10-23，新版校准后对函数主线的复述：

> 好的 简单来说就是先吧补丁文件保存下来 然后再应用
> 然后再看一下这里的有没有应用成功是我的理解

这段表述与保存补丁、应用修改、判断执行结果的主线对应。这里的“成功”指补丁应用成功，测试评分在后续进行；[本次反馈记录](../../../../../04-flow.md#apply-diff-user-model)保留接续。

## 尚不清楚

- 已复述保存、应用与判断结果的主线；`write_file` 和 `exec` 在其他使用场景中的能力边界，尚未在本次进一步展开。
- 本次教学补丁没有在真实任务镜像中应用。
- 三种补丁工具各自的冲突处理细节尚未展开。
- 底层写文件或命令通信抛异常时，不会在本函数中自动变成 `False`；后续异常处理尚未实测。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`，`swe.py:64、329–340、352–366`；[临时路径与说明](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L61-L67)。
- 两次操作均交给同一个 `ev` 提供的 `write_file` 与 `exec`，不限定为 E2B；具体传输和重试内部未展开。旧版 E2B 的源码说明保留在完整快照。
- 样例与验证：输入沿用 [run_evaluation](run_evaluation.md) 的加法修复场景；使用新版原始函数与替身后端，核对先写文件再执行命令、候选顺序、路径引用、执行参数、成功／失败返回及空白补丁直接返回。输出表中真实文件的变化仍是成功应用假设下的静态推导，没有执行补丁工具或远端评测。
- 形成过程：[Step 2 的首轮材料](../../../../../04-flow.md#first-reading)。
- 本轮职责澄清：[写入补丁文本与修改仓库文件](../../../../../04-flow.md#patch-text-versus-file)。
- 本次编排调整：[让卡片按保存补丁、应用修改来解释](../../../../../04-flow.md#apply-diff-two-actions)。
- 后续关系澄清：[write_file 与 exec 通过哪个文件衔接](../../../../../04-flow.md#write-file-exec-handoff)。
- 本次按既有卡片收拢：[一组输入输出、连续源码与分条解释](../../../../../04-flow.md#apply-diff-consolidated-card)。
- 本次理解反馈：[写入补丁也是真实写入，本次 exec 改的是仓库源码](../../../../../04-flow.md#apply-diff-understanding-feedback)。
- 补丁保留与清理：`_apply_diff` 没有删除补丁的语句；[_evaluation_sandbox](_evaluation_sandbox.md) 交给具体后端退出。[Sunabako 的退出实现](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sunabako_sandbox.py)可按配置延后清理，不能沿用旧 E2B 场景推定实际删除时刻。历史[文件保留追问](../../../../../04-flow.md#patch-file-lifetime)及当时的说明继续保留。
- 新版接续：[Step 003 · 应用补丁](../../../../../04-flow.md#apply-diff-refresh)；本轮源码核对与局部验证不改变原认识时间。

</details>
