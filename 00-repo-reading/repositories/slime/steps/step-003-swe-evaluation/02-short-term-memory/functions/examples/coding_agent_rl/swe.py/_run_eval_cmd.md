# _run_eval_cmd

- 源码定位：[examples/coding_agent_rl/swe.py:394–418](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L394-L418)，由助手核对。
- 首次接触：Step 2，2026-10-21，补丁成功后执行命令型评分。
- 最近认识更新：2026-10-23，用户已概括通过得 `1`、未通过得 `0`；助手补充命令来自已有配置、实际按退出码评分。长命令分支尚无个人理解反馈。
- 本轮源码校准：2026-10-23，补充执行用户、长命令分支和工作目录引用；[旧版完整卡片](../../../../../references/run-eval-cmd-at-2f231865.md)保留，未据此新增个人掌握结论。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：父函数已成功处理补丁，并选择 `eval_cmd` 作为评分方式。接下来在同一个评测沙箱的工作目录内执行测试命令。

2. **具体内容**：用指定用户在 `workdir` 内运行 `cmd`；默认用户为 `agent`。命令编码后超过 64 KiB 时，先写成评测脚本，再执行加载脚本的命令。最后保留退出码：`0` 对应 `1.0`，其他正常返回的退出码对应 `0.0`。

3. **建议构建的心智模型**：

   > `_run_eval_cmd` 是命令型评分规则：执行提供的命令，把退出码映射成一个分数。测试了什么由 `cmd` 决定，函数本身不判断代码的业务正确性。
   >
   > 短命令直接执行；长命令先写成脚本再执行。两条路径使用同一条退出码评分规则。

4. **调用代码**：

   ```python
   # _grade_scaleswe 的 eval_cmd 分支，swe.py:337；省略并列分支
   r = await _run_eval_cmd(
       ev, workdir, eval_cmd, timeout_sec,
       user=grading.get("eval_user", "agent"),
   )
   return EvalResult(r, True)
   ```

## 本场景的输入与输出

教学构造，承接 [_apply_diff](_apply_diff.md) 的成功结果。沙箱内的 `calc.py` 已假设改为正确加法；测试脚本检查 `add(2, 3) == 5`，本轮未实际运行。

**输入：同一个评测沙箱、仓库目录、测试命令、时间预算与执行用户。** `cmd` 接收父函数的 `eval_cmd`，来自任务配置 `md["grading"]["eval_cmd"]`；`user` 来自其中的 `eval_user`。这些字段见 [_metadata_scaleswe](_metadata_scaleswe.md) 的完整字典。本函数使用已提供的命令，测试文件在当前教学场景的仓库中已存在。

```python
# ev：已经应用补丁的同一个评测沙箱
workdir = "/workspace/repo"
cmd = "python -m pytest -q tests/test_calc.py"
timeout = 60
user = "agent"
```

输出：假设 `ev.exec` 返回的退出码为 `0`。

```python
r = 1.0  # 当前函数直接返回的 float

# 父函数随后才组成：
# EvalResult(reward=1.0, applied_cleanly=True)
```

两条路径只改变命令怎样交给沙箱，返回值都是分数：

```text
① 按 cmd 编码后的长度准备执行入口
   ├─ 不超过 64 KiB → 保留 cmd                    ← 本例
   └─ 超过 64 KiB   → write_file 保存评测脚本
                      → cmd 改为加载脚本的命令

② 两条路径汇合：ev.exec(...) → 退出码 ec
                              ├─ 0    → 1.0
                              └─ 非 0 → 0.0
```

长命令分支会额外写入 `/tmp/__cagent_eval__.sh`；本例短命令跳过该分支。

**主例实际执行的末尾两行（`swe.py:417–418`，函数内片段）：**

```python
ec, _, _ = await ev.exec(f"cd {shlex.quote(workdir)} && {cmd}", user=user, check=False, timeout=timeout)
return 1.0 if ec == 0 else 0.0
```

- **`workdir`、`cmd` → 实际命令**：本例在 `/workspace/repo` 执行 `python -m pytest -q tests/test_calc.py`，使用 agent 用户，命令时间预算为 60 秒。
- **`exec` 结果 → `ec`**：接口返回 `(exit_code, stdout, stderr)`，本函数只用第一个值，输出文本没有随评分返回。
- **`ec` → 分数**：`0` 对应 `1.0`；例如测试失败的非零退出，或者找不到命令的退出码 `127`，在此规则下都会得到 `0.0`。单看分数无法区分原因。
- **返回父函数**：父函数把分数与此前补丁处理状态组合；本函数既不产生 `applied_cleanly`，也不导出训练样本。

`check=False` 允许后端将命令非零退出作为结果交回。超时或通信异常仍可能抛出，不会由这两行统一改成零分。真实调用中的超时行为需要后续运行验证。

<details>
<summary>长命令分支：写什么脚本，随后执行什么</summary>

进入条件是 `len(cmd.encode()) > 64 * 1024`，比较的是编码后的字节数。源码先保留待执行内容，再把执行入口改为脚本路径：

```python
script = cmd
cmd = f". {shlex.quote(_EVAL_SCRIPT)}"
...  # 此处省略受支持 shell 包装的识别，见下面说明
await ev.write_file(_EVAL_SCRIPT, script, user=user)
```

- **普通长命令**：原来的整段 `cmd` 写入 `_EVAL_SCRIPT`，即 `/tmp/__cagent_eval__.sh`；随后 `exec` 在工作目录中运行 `. /tmp/__cagent_eval__.sh`，让 shell 读取并执行这个文件。
- **受支持的 shell 包装**：若命令是 `bash/sh` 或其 `/bin/` 路径加 `-c/-lc`，并且后面的内容符合 `shlex.quote` 产生的规范引号形式，源码取出包装里的内容作为 `script`，再保留相同的 shell 和选项来加载脚本。
- **为什么多这一层识别**：若仅把 `bash -lc '很长的内容'` 原样搬进脚本，那段内容仍是一个很长的命令行参数。支持的包装被拆开后，长内容成为文件正文；不匹配的命令保持原样写入，源码没有通用解析所有 shell 写法。
- **最后仍走共同出口**：写脚本和执行都使用 `user`；`exec` 继续使用原来的工作目录和时间预算。这里不解析测试报告，最后仍按退出码评分。

具体的嵌套循环和引号还原规则暂不逐行展开；本轮先分清 `script` 是文件内容、改写后的 `cmd` 是执行入口。

</details>

<details>
<summary>此前问题：测试是否对 Agent 隐藏</summary>

- 本函数只执行命令、读取退出码，没有隐藏测试或检查测试是否被修改。教学例子的 `tests/test_calc.py` 假设已在仓库中，不代表真实任务采用隐藏测试。
- 默认 Agent 提示词要求只改源码、不要改测试，并要求运行相关测试；没有禁止读取测试。读取已有测试来理解需求，与只针对已知用例硬编码答案，需要区分。
- 新评测沙箱从任务镜像重新开始，再接收补丁；它不会自动隐藏镜像内的测试。当前 `git_diff` 与 `_apply_diff` 也没有过滤测试文件，包含在补丁中的测试修改仍可能进入评测环境。完整依据见[本次讨论](../../../../../../step-003-swe-evaluation/04-flow.md#test-visibility-boundary)。

</details>

返回 [_grade_scaleswe:340](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L340) 继续组成结果并退出环境；本函数已经完成的交接是“评测命令 → 退出码 → 分数”。

## 我的直接表述（原话）

用户对测试可见性的追问：

> 但是这里是怎么做到不会直接看这里的test文件来直接写的呢？

这条表述记录疑问，不代表已确认理解评分或测试隔离机制。

2026-10-23，用户对评分主线的复述：

> 好的 那么这里其实就是一个比较简单的部分 就是简单写一下评测的指令
> 如果通过了就是reward 为1 如果不是那么就是0
> 这是我的理解

助手校准：本函数执行任务配置中已有的命令，退出码为 `0` 返回 `1.0`，其他正常返回的退出码得到 `0.0`；它不负责设计评测指令。超时或通信异常仍可能向外抛出，不统一变成零分。这里保留用户对评分主线的理解，不推断已掌握长命令处理。

随后用户把取得 `EvalResult` 的位置称为“run eval cmd”。本次校准：本函数只返回浮点数；`EvalResult` 由父函数 `_grade_scaleswe` 组装，再经 `run_evaluation` 返回外层。完整原话与说明保存在 [run_evaluation 卡片](run_evaluation.md)和[本次记录](../../../../../04-flow.md#evaluation-flow-closure-18868a79)。

## 尚不清楚

- 真实测试命令的输出、覆盖范围与耗时未取得。
- 具体任务镜像包含哪些测试、是否另有仅在评测端提供的测试，尚未核对；不能从新建沙箱推断它们已隐藏。
- 怎样在框架中进一步区分测试失败和环境故障，是本步暴露的后续问题，尚未修改实现。
- 其他评分协议怎样解析测试报告，本函数不涉及。
- 长命令分支的 shell 引号还原与不受支持写法，尚未作为独立语法问题逐行展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`，`swe.py:67、333–340、394–418`；执行用户来源见同文件 `113–118`。具体命令执行仍委托给所选后端。
- 样例与验证：与本步其他卡片保持同一场景。以替身后端执行提取的原始函数，核对短命令的不同退出码、长度边界、长命令写入、规范 shell 包装的内容还原、未匹配包装的保留、执行用户与目录引用。数值仅对应给定退出码，没有运行真实 pytest、shell 或远端环境。
- 形成过程：[Step 2 的首轮材料](../../../../../../step-003-swe-evaluation/04-flow.md#first-reading)。
- 首次进入阅读：[从应用补丁接到运行测试并评分](../../../../../../step-003-swe-evaluation/04-flow.md#read-run-eval-cmd)。当时核对命令来源、同一沙箱中的执行和退出码映射；原始说明与版本证据保留在旧卡。
- 测试可见性：本轮静态复核 `swe.py:70–75、241–272、352–366`，默认提示词与补丁路径仍未建立隐藏测试的保证；未验证真实镜像或运行防篡改实验。
- 新版接续：[Step 003 · 命令执行与分数](../../../../../04-flow.md#run-eval-cmd-refresh)。
- 个人复述与返回父函数：[分数、补丁状态与退出后的交付](../../../../../04-flow.md#grade-result-return-refresh)。

</details>
