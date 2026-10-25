# _grade_scaleswe

- 源码定位：[examples/coding_agent_rl/swe.py:304–340](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L304-L340)，由助手核对。
- 首次接触：Step 2，2026-10-21，作为独立评测的实际编排函数。
- 最近认识更新：2026-10-23，用户已概括评测结果包含两个字段；函数归属及父函数的组装职责由助手校准，完整内部实现未逐项确认。
- 本轮源码校准：2026-10-23，接回已读子函数，校准环境包装、追踪与返回交接；[旧版完整卡片](../../../../../references/grade-scaleswe-at-2f231865.md)保留，未将子函数复述扩展为已掌握父函数。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`run_evaluation` 选择 ScaleSWE 评分协议以后，进入这里评估 Agent 已生成的补丁。执行 Agent 的旧沙箱已经离开，本函数创建新的评测沙箱。

2. **具体内容**：读取镜像、工作目录和评分材料，准备独立环境，应用补丁，再按 `swepro → eval_cmd → f2p_script` 的优先级选择一种评分方法，返回 `EvalResult`。本例展开 `eval_cmd`，通过测试命令的退出码得到分数。

3. **建议构建的心智模型**：

   > 把 `_grade_scaleswe` 看成一次补丁评测的组织者：准备新环境 → 应用代码改动 → 运行选中的评分方法 → 返回奖励和补丁状态。
   >
   > Sandbox 提供执行与文件操作能力，评分规则由 SWE 层决定；离开环境上下文时会尝试回收这次评测资源。

4. **调用代码**：

   ```python
   # run_evaluation，swe.py:298
   return await _grade_scaleswe(md, diff_text, timeout_sec, trace=trace)
   ```

## 本场景的输入与输出

沿用本步 `calc.py` 的加法修复场景，选 `scaleswe → eval_cmd`。下面列出本函数相关的 `md` 字段，完整字典见 [_metadata_scaleswe](_metadata_scaleswe.md)；补丁沿用 [_apply_diff](_apply_diff.md) 的输入。假定任务镜像已含仓库和测试，未配置额外准备命令，未运行真实环境。

输入：

```python
md = {
    "protocol": "scaleswe",
    "instance_id": "calc-demo",
    "image": "teaching/calc:v1",
    "workdir": "/workspace/repo",
    "grading": {
        "swepro": None,
        "eval_cmd": "python -m pytest -q tests/test_calc.py",
        "eval_user": "agent",
        "f2p_script": None,
        "pre_commands": None,
    },
}
diff_text = """diff --git a/calc.py b/calc.py
--- a/calc.py
+++ b/calc.py
@@ -1,2 +1,2 @@
 def add(a, b):
-    return a - b
+    return a + b
"""
timeout_sec = 60
trace = base_sample  # 外层沿调用链传入的本任务追踪上下文
```

输出与副作用：假设补丁成功、测试命令退出码为 `0`。

| 结果 | 本场景的形态 | 去向 |
| --- | --- | --- |
| 返回值 | `EvalResult(reward=1.0, applied_cleanly=True)` | 经 `run_evaluation` 返回给 `_generate` |
| 环境内的变化 | 新沙箱里的 `/workspace/repo/calc.py` 应用补丁，随后运行测试 | 发生在本次评测环境中，不写回原执行环境 |
| 资源退出 | 离开 `async with` 时由 `_evaluation_sandbox` 等待所选后端的 `__aexit__` | 具体回收策略由后端决定；真实资源回收未验证 |

### 函数内部怎样完成这次评测

各段保留原执行顺序与所示调用的实参。`...` 省略本例不会进入的准备分支或检查；片段不是独立运行程序。每段使用“代码块 → 分条逻辑说明 → 子函数入口”的组织方式。

<a id="first-environment-call"></a>

#### 1. 任务配置 → 新的评测环境（308–327）

首次阅读先认出 `image`、`workdir` 和本例的 `eval_cmd`，再停在第 320 行。从 [_evaluation_sandbox](_evaluation_sandbox.md) 回查“怎样选择后端、进入并交付 `ev`”，读完回到第 322 行。

```python
image = md["image"]
workdir = md["workdir"]
grading = md.get("grading") or {}
swepro = grading.get("swepro")
eval_cmd = grading.get("eval_cmd")
f2p_script = grading.get("f2p_script")
pre_commands = grading.get("pre_commands")
...  # 没有任何评分材料时提前返回，本例 eval_cmd 有值
async with _evaluation_sandbox(image, trace) as ev:
    with trace_span(trace or [], "evaluation_prepare", record_error=False):
        await agent_sandbox.ensure_agent_user(ev, workdir)
        ...  # 本例无 swepro 准备、无 pre_commands；随后仍在此追踪阶段内应用补丁
```

- **`md` → 环境与评分配置**：`image` 指定任务镜像，`workdir` 指出仓库位置，`eval_cmd` 保存稍后执行的测试命令；后端类型另由工厂配置选择。
- **镜像与追踪上下文 → 环境包装**：`_evaluation_sandbox(image, trace)` 负责取得后端对象，等待其进入方法，随后交付 `ev`。工厂默认选择 Sunabako，配置为 `e2b` 时才进入原 E2B 分支。
- **进入上下文 → `ev`**：`ev` 是用于访问本次新评测环境的对象，与先前运行 CLI 的 `sb` 是不同实例；后续准备、补丁应用和测试共用这个 `ev`。
- **本次局部展开的停止点**：看清交付与退出接口后返回第 322 行，准备执行用户和目录权限。后端连接、重试等内部机制按需另读。
- **环境接口 → 部署边界**：两个 grader 都使用共同环境包装；选择 grader 决定评测协议，选择后端决定环境实现，实际部署仍需另查，不能据此断言使用 Kubernetes。
- **`ev`、`workdir` → 可用的执行用户**：`ensure_agent_user` 准备 agent 用户和目录权限；本例镜像已提供仓库与测试，不把此调用误解成克隆仓库。
- **已有环境基线 → 后续补丁应用**：如果任务提供 `pre_commands`，实际代码会在这里执行；本例为 `None`。执行侧与评测侧基线是否一致，会影响补丁能否应用。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [_evaluation_sandbox，swe.py:278–287](_evaluation_sandbox.md) | 接住就绪的 `ev`，返回第 322 行准备用户与目录权限 |
| [ensure_agent_user，sandbox.py:409–420](../../../slime/agent/sandbox.py/ensure_agent_user.md) | 用户与目录权限准备后，继续应用补丁 |

#### 2. 补丁文本 → 环境中的代码改动（329–331）

```python
# 仍在同一个 async with 环境和 evaluation_prepare 追踪阶段内
applied = await _apply_diff(ev, workdir, diff_text)
if not applied:
    return EvalResult(0.0, False)
```

- **`diff_text` → 新沙箱里的工作区**：将补丁写入环境并尝试应用；不是把原执行沙箱的整个目录复制过来。
- **补丁命令结果 → `applied`**：本例假设成功，得到 `True`，继续评分。失败时返回 `(0.0, False)`，跳过测试。
- **提前返回 → 环境退出**：失败返回也会离开当前上下文，触发资源回收尝试。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [_apply_diff](_apply_diff.md)：文本怎样进入工作区 | 接住 `applied`，决定是否可以继续测试 |

<a id="scoring-result"></a>
<a id="environment-exit"></a>

#### 3. 测试执行 → 评分结果与环境退出（333–340）

```python
# 仍在同一个 async with 环境中，已离开 evaluation_prepare
with trace_span(trace or [], "evaluation_tests", record_error=False):
    if swepro:
        r = await _run_swepro(ev, workdir, swepro, timeout_sec)
    elif eval_cmd:
        r = await _run_eval_cmd(ev, workdir, eval_cmd, timeout_sec, user=grading.get("eval_user", "agent"))
    else:
        r = await _run_f2p_script(ev, workdir, f2p_script, timeout_sec)
return EvalResult(r, True)
```

- **评分材料 → 一种评分方式**：本例 `swepro` 无值、`eval_cmd` 有值，进入中间分支。实际优先级保留，避免将三种方法误读为依次运行。
- **测试命令 → `r`**：本例命令退出码假设为 `0`，得到 `r = 1.0`；这条命令型路径不会在这里逐项解析测试断言。
- **`r`、已成功的补丁处理 → `EvalResult`**：第一个字段 `reward` 接收 `_run_eval_cmd` 返回的 `r`；第二个字段 `applied_cleanly` 写为 `True`，因为前面的 `if not applied` 已经让补丁处理失败的路径提前返回。两个字段分别记录评分与补丁状态。
- **对照返回值**：两个字段分工如下。`EvalResult` 定义在 `swe.py:79–83`，是带字段名的 tuple，不是两份评分。
- **退出上下文 → 交回结果**：先构造 `EvalResult`，随后 `return` 触发离开已进入的 `async with`；`_evaluation_sandbox` 在 `finally` 中等待后端退出。正常退出完成后，结果才经 `run_evaluation` 交回 `_generate:301`，解包为 `reward, applied_cleanly`。若退出处理抛异常，这次正常返回会被打断。

| 本例路径 | `reward` | `applied_cleanly` |
| --- | --- | --- |
| 补丁成功，测试命令退出码为 0 | `1.0` | `True` |
| 补丁成功，测试命令非零退出 | `0.0` | `True` |
| 补丁失败，在第 331 行提前返回，未执行测试 | `0.0` | `False` |

空白补丁按 `_apply_diff` 的规则视为处理成功；“没有评分材料”的提前返回属于下面单列的边界，不混入这三条正常评测路径。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [_run_eval_cmd](_run_eval_cmd.md)：命令退出码怎样变成分数 | 接住 `r`，组成 `EvalResult(r, True)` |
| [_evaluation_sandbox](_evaluation_sandbox.md)：使用结束后怎样退出 | 退出处理完成后，继续交回已有 `EvalResult` |
| [run_evaluation](run_evaluation.md) | 原样交回结果，`_generate` 接住两项字段，本步停在这里 |

<details>
<summary>必要的 Sandbox 能力与关键失败边界</summary>

`Sandbox` 接口定义从 `sandbox.py:33` 开始。本函数通过 `_evaluation_sandbox → create_sandbox` 接入后端；当前工厂实现了 Sunabako 和 E2B 的选择，不意味着任意新后端无需接入即可使用。

| 能力 | 本条链怎样使用 |
| --- | --- |
| 创建与退出 | 创建评测实例，离开时尝试回收 |
| `write_file` | `_apply_diff` 写入补丁文件；返回 `None`，产生文件副作用 |
| `exec` | 执行应用补丁与测试的命令，返回 `(exit_code, stdout, stderr)` |
| `read_file` | 接口提供该能力；本例的直接命令评分不需要它，其他评分路径可能读取结果文件 |

本例的 `timeout_sec=60` 被传到测试命令。它不是整个评测流程的统一截止时间；补丁应用在 `_apply_diff` 中使用自己的 120 秒预算，资源创建也有各自设置。

| 情况 | 当前行为 |
| --- | --- |
| 补丁应用失败 | `(0.0, False)`，不运行测试 |
| 补丁成功、命令退出码非零 | `(0.0, True)`；命令执行错误也可能非零，不能只据此判断模型能力 |
| 底层操作抛异常 | 本函数没有统一捕获并转换成分数，异常向外传播，同时退出已进入的环境上下文 |
| 直接调用时没有任何评分材料 | `(0.0, True)`，甚至尚未创建环境；外层 `_generate` 另有可评测性检查，不能把这个边界当成正常训练路径 |

新环境减少了旧工作区状态对评分的影响；本轮没有证明其排除了所有测试篡改或奖励漏洞。

</details>

## 我的直接表述（原话）

首轮尚无用户对本函数职责和输入输出的直接解释。用户已确认本步从 SWE 评测及必要 Sandbox 背景展开，完整表述见下方形成过程。

关于当前所选路径，用户追问：

> 所以我们首先选择的是一个会使用k8s的吗？

这是对环境部署方式的疑问，尚未得到用户对上述接口边界解释的理解反馈。见 [grader 与 Kubernetes 的关系](../../../../../04-flow.md#grader-and-kubernetes)。

随后用户同意先读 `_grade_scaleswe`，并询问第一个函数应该读哪里；本次定位到上述第一段，尚未表示理解其实现。原话见 [首个局部入口](../../../../../04-flow.md#first-scaleswe-function)。

在逐步阅读子函数后，用户确认返回父函数：

> 好的那么现在回到砸合理的grade scaleswe对吗？

这是对阅读位置的确认；当前从 `_run_eval_cmd` 返回的 `r` 接到 `EvalResult(r, True)`，尚无对两个结果字段的理解反馈。

用户随后要求继续：

> 好的那么请继续接下去看吧

本轮据此展开上下文退出与返回交接；这是继续阅读的授权，不代表已确认理解清理与返回顺序。

2026-10-23，用户已概括评测结果包含 `reward` 与 `applied_cleanly`，并询问本步能否结束。原话见 [run_evaluation 卡片](run_evaluation.md)；助手补清“分数由 `_run_eval_cmd` 返回，`EvalResult` 在本函数组装”的层级。主线收束依据见[本次记录](../../../../../04-flow.md#evaluation-flow-closure-18868a79)，不将整步收束写成全部实现已掌握。

## 尚不清楚

- 用户已概括结果包含两项字段；“补丁成功但测试失败”的组合及返回前清理尚未单独复述。
- `swepro`、`f2p_script`、SWE-bench 的具体评分协议未展开。
- 真实任务基线、测试可靠性、异常分类与资源回收状态尚未通过运行核验。
- E2B、Sunabako 的连接、重试与并发资源管理尚未作为本轮函数内部专题展开。
- 实际 E2B 兼容服务的部署方式尚未核对，不能由当前 SDK 调用推断它使用 Kubernetes。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`；`swe.py:79–83、278–298、304–340`，`generate.py:301–307`。
- 共同环境入口：`_grade_scaleswe` 与 `_grade_swebench` 都调用 `_evaluation_sandbox`；工厂见 `examples/coding_agent_rl/sandbox.py:8–16`。旧版直接使用 E2B 的证据保留在完整快照。
- 输入来源：同本步 [_metadata_scaleswe](_metadata_scaleswe.md) 与 [_apply_diff](_apply_diff.md)；镜像、补丁和测试为教学构造，成功结果是明确假设下的推导。
- 形成过程：[Step 2 的首轮材料](../../../../../04-flow.md#first-reading)。
- 首轮回到父函数：[评分与补丁状态怎样组成结果](../../../../../04-flow.md#return-to-grade-scaleswe)。该段保留原版本的学习过程，不作为当前行号依据。
- 退出与返回：[原始讲解](../../../../../04-flow.md#evaluation-context-exit)；随后按[记录归属纠正](../../../../../04-flow.md#aexit-record-ownership)，将完整实现、输入输出与回收边界移入 [E2BSandbox.__aexit__](../../../slime/agent/sandbox.py/E2BSandbox.__aexit__.md)。原有四条替身验证及语言依据随该卡片回查，未新增真实沙箱运行。
- 样例格式：沿用已认可的[锚点函数参考](../../../../../../../../../../../../.agents/skills/repo-reading-short-term-memory/references/base-adapter-run-turn.md)，阶段数量按本函数的实际交接决定。
- 新版接续：[Step 003 · 分数、补丁状态与退出后的交付](../../../../../04-flow.md#grade-result-return-refresh)。用原始父函数、环境包装和分派入口配合替身验证成功、零分、补丁失败、评分异常和无评分材料路径；正常结果先形成，再退出环境，最后交付。未运行真实沙箱或测试命令。

</details>
