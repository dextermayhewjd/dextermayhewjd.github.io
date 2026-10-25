# _run_eval_cmd

- 源码定位：[examples/coding_agent_rl/swe.py:341–343](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L341-L343)，由助手核对。
- 首次接触：Step 2，2026-10-21，补丁成功后执行命令型评分。
- 最近认识更新：尚无用户对本函数的直接解释；以下为 LLM 静态整理。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：父函数已成功处理补丁，并选择 `eval_cmd` 作为评分方式。接下来在同一个评测沙箱的工作目录内执行测试命令。

2. **具体内容**：用 agent 用户运行 `cd {workdir} && {cmd}`，保留命令退出码；退出码为 `0` 时返回 `1.0`，其他正常返回的退出码得到 `0.0`。

3. **建议构建的心智模型**：

   > `_run_eval_cmd` 是命令型评分规则：执行提供的命令，把退出码映射成一个分数。测试了什么由 `cmd` 决定，函数本身不判断代码的业务正确性。

4. **调用代码**：

   ```python
   # _grade_scaleswe 的 eval_cmd 分支
   r = await _run_eval_cmd(ev, workdir, eval_cmd, timeout_sec)
   return EvalResult(r, True)
   ```

## 本场景的输入与输出

教学构造，承接 [_apply_diff](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_apply_diff.md) 的成功结果。沙箱内的 `calc.py` 已假设改为正确加法；测试脚本检查 `add(2, 3) == 5`，本轮未实际运行。

**输入：同一个评测沙箱、仓库目录、测试命令与时间预算。** `cmd` 接收父函数的 `eval_cmd`，它来自任务配置 `md["grading"]["eval_cmd"]`；本函数使用已提供的命令，测试文件在当前教学场景的仓库中已存在。

```python
# ev：已经应用补丁的同一个评测沙箱
workdir = "/workspace/repo"
cmd = "python -m pytest -q tests/test_calc.py"
timeout = 60
```

输出：假设 `ev.exec` 返回的退出码为 `0`。

```python
r = 1.0  # 当前函数直接返回的 float

# 父函数随后才组成：
# EvalResult(reward=1.0, applied_cleanly=True)
```

**输入怎样得到上述结果（`swe.py:341–343`，完整函数）：**

```python
async def _run_eval_cmd(ev: Sandbox, workdir: str, cmd: str, timeout: int) -> float:
    ec, _, _ = await ev.exec(f"cd {workdir} && {cmd}", user="agent", check=False, timeout=timeout)
    return 1.0 if ec == 0 else 0.0
```

- **`workdir`、`cmd` → 实际命令**：本例在 `/workspace/repo` 执行 `python -m pytest -q tests/test_calc.py`，使用 agent 用户，命令时间预算为 60 秒。
- **`exec` 结果 → `ec`**：接口返回 `(exit_code, stdout, stderr)`，本函数只用第一个值，输出文本没有随评分返回。
- **`ec` → 分数**：`0` 对应 `1.0`；例如测试失败的非零退出，或者找不到命令的退出码 `127`，在此规则下都会得到 `0.0`。单看分数无法区分原因。
- **返回父函数**：父函数把分数与此前补丁处理状态组合；本函数既不产生 `applied_cleanly`，也不导出训练样本。

`check=False` 允许后端将命令非零退出作为结果交回。超时或通信异常仍可能抛出，不会由这两行统一改成零分。真实调用中的超时行为需要后续运行验证。

**测试是否对 Agent 隐藏，是另外一个边界：**

- 本函数只执行命令、读取退出码，没有隐藏测试或检查测试是否被修改。教学例子的 `tests/test_calc.py` 假设已在仓库中，不代表真实任务采用隐藏测试。
- 当前 Agent 提示词要求只改源码、不要改测试，并要求运行相关测试；没有禁止读取测试。读取已有测试来理解需求，与只针对已知用例硬编码答案，需要区分。
- 新评测沙箱从任务镜像重新开始，再接收补丁；它不会自动隐藏镜像内的测试。当前 `git_diff` 与 `_apply_diff` 也没有过滤测试文件，包含在补丁中的测试修改仍可能进入评测环境。完整依据见[本次讨论](../04-flow.md#test-visibility-boundary)。

返回 [_grade_scaleswe](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md) 继续组成结果并退出环境。

## 我的直接表述（原话）

用户对测试可见性的追问：

> 但是这里是怎么做到不会直接看这里的test文件来直接写的呢？

这条表述记录疑问，不代表已确认理解评分或测试隔离机制。

## 尚不清楚

- 真实测试命令的输出、覆盖范围与耗时未取得。
- 具体任务镜像包含哪些测试、是否另有仅在评测端提供的测试，尚未核对；不能从新建沙箱推断它们已隐藏。
- 怎样在框架中进一步区分测试失败和环境故障，是本步暴露的后续问题，尚未修改实现。
- 其他评分协议怎样解析测试报告，本函数不涉及。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：`2f2318653f6f794dddd321eff7c9d4b7b174643f`，`swe.py:283–287、341–343`；具体 `E2BSandbox.exec` 见 `sandbox.py:309–340`。
- 样例与验证：与本步其他卡片保持同一场景，数值是给定退出码后的静态推导，未执行 pytest。
- 形成过程：[Step 2 的首轮材料](../04-flow.md#first-reading)。
- 实际进入阅读：[从应用补丁接到运行测试并评分](../04-flow.md#read-run-eval-cmd)。本轮核对命令来源、同一沙箱中的执行和退出码映射；尚无用户对本函数的理解反馈。
- 测试可见性核对：同一固定版本的 `swe.py:61–68、230–247、269–287、299–313、341–343`；仅静态核对提示词、补丁范围与执行路径，未验证真实镜像或运行防篡改实验。

</details>
