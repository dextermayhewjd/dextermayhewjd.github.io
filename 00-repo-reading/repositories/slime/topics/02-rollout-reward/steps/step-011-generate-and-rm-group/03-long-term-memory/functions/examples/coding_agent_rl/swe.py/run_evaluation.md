# run_evaluation

- Step 011 继承：来自 [Step 010 · 03-long-term-memory](../../../../../../step-010-generate-and-rm/03-long-term-memory/functions/examples/coding_agent_rl/swe.py/run_evaluation.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

- Step 010 继承：2026-10-25，来自 [Step 009 · 03-long-term-memory 完整记录](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/examples/coding_agent_rl/swe.py/run_evaluation.md)。正文、原话、认识日期、源码版本与未知沿用来源；仅继承和重算链接。

- 本次继承：2026-10-23，[Step 7 · 03 完整记录](../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/03-long-term-memory/functions/examples/coding_agent_rl/swe.py/run_evaluation.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

- 源码定位：[examples/coding_agent_rl/swe.py:239–247](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L239-L247)，由助手核对。
- 首次接触：Step 2，2026-10-21，用户确认从独立评测与奖励来源展开。
- 最近认识更新：本步尚无用户对函数职责的直接解释；以下为 LLM 静态整理。

- 本次继承自：[Step 2 的完整记录](../../../../../../../../01-coding-agent-rl/steps/step-003-swe-evaluation/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/run_evaluation.md)；仅复制、补来源与重算链接，原话、认识时间和未知保留。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`generate` 已等待 CLI 退出、取得 `diff_text` 并离开执行沙箱，现在评估这份代码改动。训练路径也会调用评测，并非只有 `evaluation=True` 才评分。

2. **具体内容**：读取任务信息 `md` 中的协议，选择相应评分器，将任务信息、补丁文本和时间预算传入；返回评分器的 `EvalResult`。本例选择 `_grade_scaleswe`。

3. **建议构建的心智模型**：

   > `run_evaluation` 是统一的评测入口：把同一组“任务、补丁、时间预算”交给选中的评分器，取回“奖励、补丁状态”。
   >
   > 环境准备、应用补丁和运行测试由评分器完成；外层 `generate` 继续使用返回结果。

4. **调用代码**：

   ```python
   # generate.py:213–219，离开执行沙箱后评分
   reward, applied_cleanly = await swe.run_evaluation(
       md,
       diff_text=diff_text,
       timeout_sec=CONFIG.eval_timeout_sec,
   )
   ```

## 本场景的输入与输出

教学构造，采用源码支持的 `scaleswe → eval_cmd` 路径。假设任务镜像中已有 Git 仓库与测试，原来的 `add(2, 3)` 错误返回 `-1`，测试要求结果为 `5`。镜像名为占位，未创建真实沙箱、未运行 pytest。`md` 是 `get_metadata` 处理后的字段节选；保留本条评测路径会读取的字段。

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
```

输出：明确假设补丁成功应用，且测试命令退出码为 `0`。

```python
result = EvalResult(reward=1.0, applied_cleanly=True)

# generate 中的解包
reward, applied_cleanly = result
# reward == 1.0
# applied_cleanly is True
```

`EvalResult` 是有字段名的 tuple，定义在 `swe.py:70–74`。两个字段分别来自评分结果与补丁处理状态；不是两份模型回复，也不是训练后的权重。训练路径随后把 `reward` 交给 `finish_session`，本步先停在评测交接。

实际分派只有这几行：

```python
if md.get("protocol") == PROTOCOL_SWEBENCH:
    return await _grade_swebench(md, diff_text, timeout_sec)
return await _grade_scaleswe(md, diff_text, timeout_sec)
```

- **`md["protocol"]` → 评分器**：本例值为 `"scaleswe"`，进入最后一行。该函数对不是 `"swebench"` 的值均走这条后备路径，未在这里验证未知协议。
- **三个实参 → 评分执行**：继续使用同一个任务信息、补丁文本和秒数，本层不修改补丁。
- **评分器返回值 → 外层结果**：直接返回 `EvalResult`；评分器抛出的异常也不会在此层转换成分数。

<a id="two-graders"></a>

### 为什么有两个 grader，本例却只进入一个

这是按任务协议选择的两个并列实现。一次 `run_evaluation` 只调用一个 grader；两者都接收 `md、diff_text、timeout_sec`，但 `md["grading"]` 内需要的材料不同。

| 比较项 | `_grade_scaleswe` | `_grade_swebench` |
| --- | --- | --- |
| 本次进入条件 | 非 `"swebench"` 的后备分支；主例为 `"scaleswe"` | `md["protocol"] == "swebench"` |
| 评分材料 | `swepro`、`eval_cmd`、`f2p_script` 按优先级选一个；主例只给 `eval_cmd` | `grading["sweb_instance"]`，用于构造测试规格与评测脚本 |
| 评分依据 | 主例按命令退出码评分；另外两种材料有各自处理逻辑 | 执行评测脚本，解析测试日志，按报告中的 `resolved` 得到奖励 |
| 共同交接 | 在新环境中应用补丁并评分，返回 `EvalResult` | 在新环境中应用补丁并评分，返回 `EvalResult` |

- **先读主例的理由**：默认训练协议为 `scaleswe`，其中的 `eval_cmd` 能用较少调用展示“补丁 → 测试 → 奖励”。这是教学取舍，尚未证明真实任务使用哪一种评分材料。
- **共用接口仍须看见差异**：只读这一条命令路径，无法了解其他任务协议如何接入。先对照上表，再逐层阅读选中的实现；不能把 `eval_cmd` 的退出码规则套到所有 grader。
- **切换需要匹配的数据**：不能只把本页示例的 `protocol` 改为 `"swebench"` 就认为输入有效，还需提供该协议的任务实例材料。训练或评估模式会选择对应配置，但 `run_evaluation` 自身依据的是协议值，不是两个 grader 分别固定负责训练和评估。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [_grade_scaleswe](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md)：本例怎样准备环境并评分 | 接住 `EvalResult`，返回给 `generate` |
| [_grade_swebench 源码](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L440-L492)：另一种协议的实现 | 已比较输入与评分依据；内部细节尚未展开 |

## 我的直接表述（原话）

用户此前提出范围要求（节选）：

> 或者起码需要考虑这里的swe.run evaluation 请给出理由呢？

随后确认开启 Step 2；目前尚无对本函数输入输出的个人解释。范围确认见下方形成过程。

看到首轮材料后，用户追问：

> 主要是这里不是有两个grade吗 为什么只是使用了其中的一个呢？

对应的解释与阅读取舍见 [两个 grader 的澄清](../../../../../../../../01-coding-agent-rl/steps/step-003-swe-evaluation/04-flow.md#two-graders)。尚未得到用户对这项解释的理解反馈。

## 尚不清楚

- 尚未得到用户对两个返回字段及分派关系的理解反馈。
- 已由助手比较两个 grader 的接口与评分依据；SWE-bench 内部的脚本构造、报告解析和失败出口尚未逐层展开。
- 本场景的实际测试输出、耗时和沙箱运行状态没有取得。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：`2f2318653f6f794dddd321eff7c9d4b7b174643f`；`swe.py:70–74、239–247`，调用处 `generate.py:213–249`。
- 两个 grader 的对照依据：`swe.py:83–137、253–287、440–492`；模式与协议配置的关系见 `generate.py:76–77、185–186`。
- 场景依据：默认训练协议见 `generate.py:77`；`eval_cmd` 分支见 `swe.py:283–287`。`tests/test_agent/test_agent_rollout_cpu.py:95–104` 使用 `eval_cmd="true"`，仅用来核对接口存在，本轮未执行该测试。
- 样例与验证：补丁和测试命令为教学构造；输出是在应用成功、命令成功两项假设下的静态推导，非真实实验结果。
- 形成过程：[Step 2 的范围与首轮材料](../../../../../../../../01-coding-agent-rl/steps/step-003-swe-evaluation/04-flow.md#first-reading)。

</details>
