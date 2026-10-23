# _apply_diff

- 本次继承：2026-10-23，[Step 7 · 03 完整记录](../../../../../../step-008-harness-communication/03-long-term-memory/functions/examples/coding_agent_rl/swe.py/_apply_diff.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

- 源码定位：[examples/coding_agent_rl/swe.py:299–313](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L299-L313)，由助手核对。
- 首次接触：Step 2，2026-10-21，在评测环境中应用补丁。
- 最近认识更新：2026-10-21，用户表示“大概理解”，已表达先写入补丁、再由 exec 应用修改的初步认识；本次用途与两个通用方法的能力边界仍在澄清。

- 本次继承自：[Step 2 的完整记录](../../../../../../step-003-swe-evaluation/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_apply_diff.md)；仅复制、补来源与重算链接，原话、认识时间和未知保留。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`_grade_scaleswe` 已创建新评测环境并完成必要准备，需要把 Agent 交出的补丁应用到该环境的工作区，随后才能测试。

2. **具体内容**：先把 `diff_text` 保存为沙箱里的临时补丁文件，再执行补丁命令，按照其中的修改说明更新 `workdir` 中的仓库文件；最后返回是否应用成功。空补丁直接返回 `True`。

3. **建议构建的心智模型**：

   > `_apply_diff` 把 Agent 给出的补丁应用到已有的评测仓库：`write_file` 先保存修改说明，`exec` 再运行读取这份说明的补丁工具，真正修改仓库文件。
   >
   > 两次调用通过同一沙箱中的补丁文件衔接。函数返回是否应用成功，随后由调用方继续测试。

4. **调用代码**：

   ```python
   applied = await _apply_diff(ev, workdir, diff_text)
   if not applied:
       return EvalResult(0.0, False)
   ```

## 本场景的输入与输出

沿用本步加法修复的教学场景；`ev` 是父函数已创建、已准备 agent 用户的评测沙箱对象。镜像和仓库未实际运行，下面假设补丁能够应用。

**输入：已有评测沙箱、仓库目录和补丁文本。**

```python
# ev：父函数的 E2BSandbox 实例
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
| 沙箱内的 `/workspace/__cagent_patch__.diff` | 保存输入的 `diff_text`，应用后仍保留在沙箱中 |
| 沙箱内的 `/workspace/repo/calc.py` | 原来的 `return a - b` 已改成 `return a + b` |

**输入怎样得到上述结果（`swe.py:299–313`，完整函数）：**

```python
async def _apply_diff(ev: Sandbox, workdir: str, diff_text: str) -> bool:
    if not diff_text.strip():
        return True
    await ev.write_file(_PATCH, diff_text, user="agent")
    # First-success-wins ladder collapsed into one exec (one sandbox round-trip).
    ladder = " || ".join(
        f"({cmd})"
        for cmd in (
            f"git apply --3way --whitespace=nowarn {_PATCH}",
            f"git apply --whitespace=nowarn {_PATCH}",
            f"patch -p1 --no-backup-if-mismatch < {_PATCH}",
        )
    )
    ec, _, _ = await ev.exec(f"cd {workdir} && ({ladder})", user="agent", check=False, timeout=120)
    return ec == 0
```

- **补丁文本 → 补丁文件**：`write_file` 把 `diff_text` 原样写到 `_PATCH` 指定的 `/workspace/__cagent_patch__.diff`，包括其中的 `-`、`+` 修改行。这已经是真实的文件写入；写哪个文件由路径决定，本例写的是补丁文件，仓库中的 `calc.py` 仍是减法。
- **候选命令 → `ladder`**：两种 `git apply` 和一种 `patch` 用 `||` 连接，前一个失败才尝试下一个，任一个成功便停止尝试。这几行只组装命令字符串，尚未执行。
- **补丁文件 → 仓库修改**：`exec` 在同一个沙箱中执行整条命令，先 `cd` 到 `workdir`，再运行补丁工具。工具通过 `_PATCH` 读取刚才保存的说明，找到 `calc.py` 并把指定的减法语句改成加法。两次调用靠这份文件衔接；`exec` 负责运行命令，`git apply` 或 `patch` 负责解释补丁并修改文件。
- **执行结果 → 调用方**：`exec` 返回 `(exit_code, stdout, stderr)`，这里只保留退出码 `ec`。退出码为 `0` 时返回 `True`，否则返回 `False`；[_grade_scaleswe](_grade_scaleswe.md) 用 `applied` 判断是否继续测试。补丁应用成功与测试通过分别由两步判断。本函数不删除补丁文件；整轮评测退出 `async with`、正常回收沙箱时，文件才随环境一起清理。

空白补丁在入口直接返回 `True`，不写文件、不执行命令，允许调用方继续测试；这不表示已经修改了文件。

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

## 尚不清楚

- 用户已表达先写补丁、再应用修改的初步理解；“只有 exec 才真正改动”已限定为本次仓库源码修改，通用方法的能力边界尚待确认。
- 本次教学补丁没有在真实任务镜像中应用。
- 三种补丁工具各自的冲突处理细节尚未展开。
- 底层写文件或命令通信抛异常时，不会在本函数中自动变成 `False`；后续异常处理尚未实测。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：`2f2318653f6f794dddd321eff7c9d4b7b174643f`，`swe.py:56、277–279、299–313`；`Sandbox` 返回约定见 `sandbox.py:23、46–55`。
- 两次沙箱操作的实现：`sandbox.py:309–340` 的 `E2BSandbox.exec` 把命令交给 `self._sb.commands.run`；`sandbox.py:342–378` 的 `E2BSandbox.write_file` 在本例字符串分支把路径和内容交给 `self._sb.files.write`。两者使用同一个已创建的 SDK 沙箱对象，本处只核对职责与交接，传输和重试内部未展开。
- 样例与验证：输入与 [run_evaluation](run_evaluation.md) 相同，输出为成功应用假设下的静态推导；没有执行补丁工具。
- 形成过程：[Step 2 的首轮材料](../../../../../../step-003-swe-evaluation/04-flow.md#first-reading)。
- 本轮职责澄清：[写入补丁文本与修改仓库文件](../../../../../../step-003-swe-evaluation/04-flow.md#patch-text-versus-file)。
- 本次编排调整：[让卡片按保存补丁、应用修改来解释](../../../../../../step-003-swe-evaluation/04-flow.md#apply-diff-two-actions)。
- 后续关系澄清：[write_file 与 exec 通过哪个文件衔接](../../../../../../step-003-swe-evaluation/04-flow.md#write-file-exec-handoff)。
- 本次按既有卡片收拢：[一组输入输出、连续源码与分条解释](../../../../../../step-003-swe-evaluation/04-flow.md#apply-diff-consolidated-card)。
- 本次理解反馈：[写入补丁也是真实写入，本次 exec 改的是仓库源码](../../../../../../step-003-swe-evaluation/04-flow.md#apply-diff-understanding-feedback)。
- 补丁保留与清理：`_apply_diff` 没有删除补丁的语句；调用方退出上下文时，`sandbox.py:302–307` 的 `__aexit__` 尝试调用 `self._sb.kill()` 回收整个沙箱。这里描述正常回收，未实测回收结果；[本次追问](../../../../../../step-003-swe-evaluation/04-flow.md#patch-file-lifetime)。

</details>
