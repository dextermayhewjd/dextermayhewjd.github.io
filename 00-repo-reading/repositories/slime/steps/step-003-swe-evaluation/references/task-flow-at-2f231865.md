# 05 · 任务链路：从代码补丁到评测奖励

> `run_evaluation` 接收任务信息和代码补丁，选择评分器；本例由 `_grade_scaleswe` 在新的评测环境中应用补丁、执行测试，再把奖励与补丁状态交回 `generate`。

[本步范围](../01-scope.md) · [步骤入口](../README.md) · [函数记录](../02-short-term-memory/overview.md) · [本次收拢](../04-flow.md#evaluation-flow-closure)

## 1. 本步在任务中的位置

Step 1 跟随 CLI 运行期间的一次模型请求，看到消息和生成数据被记录进 manager。Step 2 接在 CLI 整体结束之后：`generate` 已取得工作区的 `diff_text`，离开原执行沙箱，接下来评测这份代码改动。

- **起点**：`md` 提供任务镜像、工作目录和评分配置；`diff_text` 提供代码改动。
- **终点**：`generate.py:215` 接到 `reward, applied_cleanly`；评测环境已经过退出处理。
- **本例**：`scaleswe → eval_cmd`，没有 `swepro`、`f2p_script` 或 `pre_commands`；使用既有 `calc.py` 教学例。图中成功值是静态假设，未执行真实沙箱或测试。

## 2. 已读函数怎样把数据交接起来

下图的主文件为 `examples/coding_agent_rl/swe.py`；环境操作另标 `slime/agent/sandbox.py`。进入和退出方法由 `async with` 协议触发，调用实参按需省略。

```text
generate.py:215：交入 md、diff_text、timeout_sec
└─ run_evaluation                                  swe.py:239
   └─ _grade_scaleswe                              swe.py:253
      │
      ├─ 进入评测上下文：E2BSandbox.__aenter__      sandbox.py:281
      │  → 新的评测环境；本地用 ev 操作它
      ├─ ensure_agent_user(ev, workdir)            sandbox.py:390
      │  → 用户与目录权限准备完成
      ├─ _apply_diff(ev, workdir, diff_text)        swe.py:299
      │  → 本例 calc.py 的减法改成加法；applied=True
      ├─ _run_eval_cmd(ev, workdir, eval_cmd, ...)  swe.py:341
      │  → 本例假设测试命令退出码为 0；r=1.0
      └─ 形成 EvalResult(r, True)                  swe.py:287
         → 离开评测上下文，等待 __aexit__ 完成退出处理
         → 经 run_evaluation 原样返回

generate.py:215：接到 reward=1.0、applied_cleanly=True
```

按需回到单函数实现，读完再回到图中的交接：

- 分派与编排：[run_evaluation](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/run_evaluation.md)、[_grade_scaleswe](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md)。
- 环境能力：[__aenter__](../02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md)、[ensure_agent_user](../02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md)、[__aexit__](../02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md)。
- 改动与评分：[_apply_diff](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_apply_diff.md)、[_run_eval_cmd](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_run_eval_cmd.md)。

## 3. 两项结果分别说明什么

| 本例路径 | 交回结果 | 含义 |
| --- | --- | --- |
| 补丁处理成功，测试命令成功 | `EvalResult(1.0, True)` | 获得奖励；补丁阶段成功 |
| 补丁处理成功，测试命令非零退出 | `EvalResult(0.0, True)` | 未获得奖励；补丁阶段成功 |
| 补丁处理失败 | `EvalResult(0.0, False)` | 未进入测试；补丁阶段失败 |

表格覆盖本例正常取得返回值的路径。底层抛出的异常并不都被转成零分；回收失败也不一定阻止返回已有评分。具体边界保留在函数卡片中。

新环境用于重新评测提交的改动，不代表测试已对 Agent 隐藏或免于篡改。当前补丁路径没有过滤测试文件；这项澄清和真实任务的未知继续保留在 [测试可见性讨论](../04-flow.md#test-visibility-boundary)。

## 4. 回到 Coding RL 的下一次交接

现在可以把前两步放在一起看：

```text
Step 1：模型请求期间，manager 留下会话轨迹
Step 2：CLI 结束后，评测代码改动，得到 reward
                       ↓
下一问：会话轨迹 + reward + base_sample 怎样导出 Sample？
```

沿 `evaluation=False` 的训练路径，下一处候选是 `generate.py:237` 调用的 `BaseAdapter.finish_session`（`slime/agent/adapters/common.py:245`）。当前只定位这个接口：调用方交入会话 ID、基础样本、奖励及附加元数据，接收样本列表；内部的轨迹导出和样本组装尚未作为下一步展开。`evaluation=True` 则在前面的分支返回评估结果，不会经过这次样本导出。

下一步建议围绕 `finish_session` 确定范围，短期记忆保留其输入、输出样本和关键数据交接。此建议待用户确认，不因本页总结而自动开始新 step。

<details>
<summary>源码与验证范围</summary>

- 固定提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。
- 调用方：`generate.py:203–245`；评分分派与编排：`swe.py:239–287`；补丁和命令评分：`swe.py:299–343`；环境进入、退出和用户准备：`sandbox.py:281–307、390–399`。
- 上图整条成功路径为源码核对和教学假设，不是实际运行日志。已有局部替身验证见各函数来源；没有新增真实沙箱、pytest 或训练执行。
- 本页是对已发生阅读的 LLM 整理。用户的原话和明确理解保留在 `04-flow` 与函数卡片；不把总结完成视为全部掌握。

</details>
