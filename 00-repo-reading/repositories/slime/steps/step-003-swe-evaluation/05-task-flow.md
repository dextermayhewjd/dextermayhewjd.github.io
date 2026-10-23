# 05 · 任务链路：从代码补丁到评测奖励

> `run_evaluation` 接收任务信息和代码补丁，选择评分器；本例由 `_grade_scaleswe` 在新的评测环境中应用补丁、执行测试，再把奖励与补丁状态交回 `_generate`。

[本步范围](01-scope.md) · [步骤入口](README.md) · [函数记录](02-short-term-memory/overview.md) · [本次收拢](04-flow.md#evaluation-flow-closure-18868a79) · [旧版完整总结](references/task-flow-at-2f231865.md)

## 1. 本步在任务中的位置

Step 1 跟随 CLI 运行期间的一次模型请求，看到消息和生成数据被记录进 manager。Step 2 接在 CLI 整体结束之后，收集运行统计并提取工作区的 `diff_text`。Step 3 从这些结果继续：`_generate` 离开原执行沙箱，评测这份代码改动。

- **起点**：`md` 提供任务镜像、工作目录和评分配置；`diff_text` 提供代码改动。调用方另传测试时间预算与追踪上下文。
- **终点**：`generate.py:301–306` 接到 `reward, applied_cleanly`；本例评测环境已经过退出处理。
- **本例**：`scaleswe → eval_cmd`，没有 `swepro`、`f2p_script` 或 `pre_commands`；沿用 `calc.py` 教学例。图中成功值是明确假设下的结果，未执行真实沙箱或测试。

`md` 的完整字典见 [_metadata_scaleswe](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_metadata_scaleswe.md)。它在进入评测之前整理好，不是 `run_evaluation` 内部再调用的步骤。阅读时回查输入的顺序保留在 [scope 导航](01-scope.md#reading-path)。

## 2. 已读函数怎样把数据交接起来

下图按 `18868a79` 的调用归属与执行顺序整理，主文件为 `examples/coding_agent_rl/swe.py`。追踪包装、未选评分分支和无评分材料的提前返回暂时折叠。进入与退出由 `async with` 驱动，③–⑥共用②交出的同一个 `ev`。

```text
generate.py:301：交入 md、diff_text、timeout_sec、trace
└─ run_evaluation                                  swe.py:290–298
   └─ 本例选择 _grade_scaleswe                     swe.py:304–340
      │
      ├─ ① 读取镜像、目录与 grading               swe.py:308–314
      │  → 本例选择 eval_cmd 评分材料
      │
      ├─ ② 进入 _evaluation_sandbox 上下文         swe.py:320 → 278–284
      │  ├─ create_sandbox(image)                  coding_agent_rl/sandbox.py:8–16
      │  │  → 根据配置选择后端对象
      │  └─ await sandbox.__aenter__()             swe.py:282
      │     → yield ev，评测环境交给父函数继续使用
      │
      ├─ ③ ensure_agent_user(ev, workdir)           swe.py:322
      │  └─ ev.exec(...)                           slime/agent/sandbox.py:409–420
      │     → 准备用户、目录权限与 Git 设置
      │
      ├─ ④ _apply_diff(ev, workdir, diff_text)      swe.py:329 → 352–366
      │  ├─ ev.write_file(...) → 保存补丁说明
      │  └─ ev.exec(...)       → 应用改动，取得 applied
      │     → True：继续⑤；False：形成 EvalResult(0.0, False)，转入退出处理
      │
      ├─ ⑤ _run_eval_cmd(..., user=eval_user)       swe.py:337 → 394–418
      │  └─ ev.exec(...) → 退出码 → 分数 r
      │     → 本例假设退出码为 0，得到 r=1.0
      │
      └─ ⑥ 形成 EvalResult(r, True)                swe.py:340
         → 离开上下文，回到 _evaluation_sandbox 的 finally
         → await sandbox.__aexit__(...)           swe.py:285–287
         → 正常退出后，经 run_evaluation 原样返回

generate.py:301：解包得到 reward=1.0、applied_cleanly=True
```

工厂所在文件的完整路径是 `examples/coding_agent_rl/sandbox.py`，用户准备所在文件是 `slime/agent/sandbox.py`。工厂默认选择 Sunabako，显式选择 `e2b` 时才对应 E2B 实现；评分协议与后端选择是两层配置。

按需回到单函数实现，读完再回到图中的交接：

- 分派与编排：[run_evaluation](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/run_evaluation.md)、[_grade_scaleswe](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md)。
- 环境交付与准备：[_evaluation_sandbox](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_evaluation_sandbox.md)、[ensure_agent_user](02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md)。E2B 分支按需回查 [__aenter__](02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md)、[__aexit__](02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md)，两张旧卡保留原版本证据。
- 改动与评分：[_apply_diff](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_apply_diff.md)、[_run_eval_cmd](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_run_eval_cmd.md)。长命令转脚本等细节由评分卡片承接。

## 3. 两项结果分别说明什么

返回值要按层区分：`_run_eval_cmd` 只返回浮点分数 `r`；`_grade_scaleswe` 组成 `EvalResult`；`run_evaluation` 原样返回；`_generate` 才解包为两项变量。

| 本例路径 | 交回结果 | 含义 |
| --- | --- | --- |
| 补丁处理成功，测试命令成功 | `EvalResult(1.0, True)` | 获得奖励；补丁阶段成功 |
| 补丁处理成功，测试命令非零退出 | `EvalResult(0.0, True)` | 未获得奖励；补丁阶段成功 |
| 补丁处理失败 | `EvalResult(0.0, False)` | 未进入测试；补丁阶段失败 |

`reward` 表示评分结果，`applied_cleanly` 表示补丁处理状态。`True` 不表示测试通过；空白补丁也按 `_apply_diff` 的规则视为处理成功。

表格覆盖本例正常取得返回值的路径。评分或退出处理向外抛出异常时，正常结果交付会被打断；后端若自行处理了回收错误，则按其实际返回行为继续。调用退出接口不等于已验证远端资源回收成功。

新环境用于重新评测提交的改动，不代表测试已对 Agent 隐藏或免于篡改。当前补丁路径没有过滤测试文件；这项澄清和真实任务的未知继续保留在 [测试可见性讨论](04-flow.md#test-visibility-boundary)。

## 4. 本步的收束与后续衔接

本轮已覆盖既定 scope 的主线：任务信息与补丁 → 选择评分器 → 新环境中的准备、补丁与测试 → 退出环境 → 两项结果回到调用方。用户已概括取得 `EvalResult` 中两个字段，助手校准了具体返回它的函数。因此可以收束本步的主线阅读，不要求把所有依赖内部实现都展开。

| 继续保留的边界 | 什么时候再读 |
| --- | --- |
| `swepro`、`f2p_script`、SWE-bench 的具体评分规则 | 需要接入或排查对应任务协议时 |
| 具体沙箱后端的通信、并发与完整回收实现 | 需要解释环境故障、部署或资源管理时 |
| 长命令 shell 处理的逐项细节 | 遇到命令长度或引号问题时；现有卡片已保留入口 |
| 真实测试覆盖、测试隔离与实际资源状态 | 有相应任务环境后做运行验证；本轮未取得这些证据 |

回到 Coding RL 的整体交接：

```text
Step 1：模型请求期间，manager 留下会话轨迹
Step 2：CLI 结束后，收集统计并提取代码补丁
Step 3：评测代码改动，得到 reward 与 applied_cleanly
                       ↓
下一问：会话轨迹 + reward + base_sample 怎样导出 Sample？
```

这接回已有 [Step 004](../step-004-trajectory-to-samples/README.md)。当前源码在训练路径中由 `generate.py:326` 调用 `adapter.finish_session`；`evaluation=True` 则先返回评估结果，不经过该次样本导出。本页只定位后续接口，Step 004 的新版校准仍须与用户确认，不因本步收束而自动展开。

<details>
<summary>源码、形成依据与验证范围</summary>

- 固定提交：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`。旧版 `2f231865` 的完整总结保存在[归档](references/task-flow-at-2f231865.md)，其中旧步骤编号保留当时语境。
- 调用与返回：[generate.py:296–336](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L296-L336)。返回类型与输入：[swe.py:79–120](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L79-L120)。
- 环境包装、分派与编排：[swe.py:278–340](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L278-L340)。补丁与命令：[swe.py:352–418](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L352-L418)。
- 工厂：[examples/coding_agent_rl/sandbox.py:8–16](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sandbox.py#L8-L16)。用户准备：[slime/agent/sandbox.py:409–420](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L409-L420)。
- 本页是对已发生阅读的 LLM 整理。用户原话、函数名校准及收束判断见 [04-flow](04-flow.md#evaluation-flow-closure-18868a79)；未把总结完成记为已掌握全部实现。
- 已有验证见[结果交接记录](04-flow.md#grade-result-return-refresh)：原函数配合替身检验六种结果或异常路径；其他局部检查随各卡片保留。本次更新总结只复核源码、链接与材料一致性，没有新增真实沙箱、pytest、模型或训练执行。

</details>
