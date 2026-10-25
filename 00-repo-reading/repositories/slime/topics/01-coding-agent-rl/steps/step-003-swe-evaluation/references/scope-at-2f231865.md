> 历史快照：2026-10-23 在新版 scope 校准前保存。正文依据 Slime `2f2318653f6f794dddd321eff7c9d4b7b174643f`；除复制位置所需的相对链接调整外，原文完整保留。文中“当前”、行号与实现选择属于当时记录。新版入口见 [当前 scope](../01-scope.md)。

# 01 · 阅读范围：从代码补丁到评测奖励

[本步入口](../README.md) · [Step 0 核心骨架](../../step-000-coding-agent/01-scope.md) · [前序函数记忆](../03-long-term-memory/overview.md)

## 1. 阅读目标

沿用理解 Coding Agent / Coding RL、对齐框架工程岗位的目标。本步回答：**Agent 修改代码以后，系统怎样在独立环境中评测，并把结果交成 `reward` 与 `applied_cleanly`？**

阅读重点是评测接口、环境边界与结果含义，对应[岗位中的组件封装、评测接入和稳定性要求](../../../../../../../../slime_photo/code-reading/job-alignment.md#step-2-evaluation-choice)。进入时先知道：CLI 已结束，执行工作区的补丁已取得，`md` 保存任务镜像、工作目录与评分配置。需要恢复补丁来路时，短看 `prepare_workspace:177` 与 `git_diff:230`，不重读整个启动过程。

## 2. 指挥官函数与本步入口

整体指挥官仍是 `examples/coding_agent_rl/generate.py::generate`。本步从其第 215 行进入 [swe.run_evaluation](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/run_evaluation.md)，再到实际组织新环境、补丁和评分的 [_grade_scaleswe](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md)。

`run_evaluation` 按协议选择 `_grade_swebench` 或 `_grade_scaleswe`，一次调用只进入其中一个。先在入口认清两个分支的选择条件、共同返回类型与评分依据，再深入本例的 `scaleswe → eval_cmd`。

<a id="why-scaleswe-first"></a>

**为什么两个 grader 中先选 `_grade_scaleswe` 的 `eval_cmd` 分支：**

1. **保留完整评测链，首轮需要的新概念较少。** 这一分支只需跟随“新环境 → 应用补丁 → 执行给定命令 → 退出码转为奖励”。SWE-bench 在这条链上还需要理解任务实例如何生成 `TestSpec / eval_script`，以及测试日志如何由评测框架解析成报告，再读取 `resolved`。这些是有价值的协议细节，但不是先理解奖励来源的必要前置。
2. **先建立后续能复用的共同模型。** 独立环境、补丁交接、测试执行、返回 `EvalResult` 都能在首个例子里看见。再读 `_grade_swebench` 时，就能聚焦它在测试准备、执行和报告解释上的差异，明确新协议接入影响哪些环节。这与当前理解 RL 框架及评测接入的目标一致。
3. **默认配置仅作为辅助依据。** 当前源码的训练和评估协议都默认 `scaleswe`；这支持用它作首例，但不能证明实际数据一定使用 `eval_cmd`，也不能证明它在行业里更常见。两种 grader 共用 `E2BSandbox`，部署方式不构成先后理由。

这里判断较简单的是选定的 `eval_cmd` 路径，不能推广为 ScaleSWE 所有分支都简单。如果目标改成复现或排查 SWE-bench 的基准结果，应优先 `_grade_swebench`。本次选读理由的澄清见 [讨论记录](../04-flow.md#grader-priority-reason)。

源码固定为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。当前本地版本与官方 main 有差异，继续沿用已读版本，具体核对见[版本记录](../../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前源码与已有材料的版本边界)。

## 3. 给出真正干活的核心骨架

### 3.1 继承整体骨架，定位第 6 项

沿用 Step 0 的 `evaluation=False` 正常路径。下面是教学裁剪，参数用 `...`；配置、前置检查、日志、调试及外层异常清理暂时略去。

```python
state.adapter.open_session(...)                          # 1. 登记本次会话
async with boot_agent_sandbox(...) as sb:                 # 2. 启动执行沙箱
    await swe.prepare_workspace(...)                     # 3. 准备工作区
    agent_exit_code = await HARNESS_CLS().run(...)        # 4. 运行 Coding Agent；Step 1 在此期间读 _run_turn
    diff_text = await swe.git_diff(...)                   # 5. 取得代码改动

reward, applied_cleanly = await swe.run_evaluation(...)   # 6. 本步：独立评测
samples = await state.adapter.finish_session(...)        # 7. 后续：导出样本
return samples
```

离开执行沙箱以后才进入评分。多轮请求的轨迹已经记录在 manager；本步评测输入是任务信息与代码补丁，不是 `TurnRecord`。

<a id="step-2-branch"></a>

### 3.2 从评分入口进入实际编排

```text
generate                                       examples/coding_agent_rl/generate.py:215
└─ swe.run_evaluation                           examples/coding_agent_rl/swe.py:239
   ├─ _grade_swebench                           swe.py:440；protocol == "swebench"
   │  └─ 运行评测脚本 → 解析报告 → 按 resolved 评分
   └─ _grade_scaleswe                           swe.py:253；其余值，本例是 "scaleswe"
      ├─ E2BSandbox 的上下文                     slime/agent/sandbox.py:281、302
      ├─ _apply_diff                            swe.py:299；补丁是否应用成功
      └─ _run_eval_cmd                          swe.py:341；本轮选 eval_cmd
```

两个 grader 都在新环境中评测补丁，并返回 `EvalResult`；所需任务材料与评分规则不同。具体对照放在 [run_evaluation 函数卡片](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/run_evaluation.md#two-graders)。这里先保留完整分支地图，SWE-bench 的内部脚本和报告解析尚未逐层展开。

以下裁剪自 `_grade_scaleswe`，只展示本场景：有 `eval_cmd`、无 `swepro`、无 `f2p_script`、无 `pre_commands`。保留补丁失败出口，因为它直接影响返回值含义；`async with` 的退出负责尝试回收评测环境。

```python
async with E2BSandbox(...) as ev:             # 新建评测环境
    await agent_sandbox.ensure_agent_user(...)  # 准备执行用户与工作目录权限
    applied = await _apply_diff(...)          # 把 diff_text 应用到该环境
    if not applied:
        return EvalResult(0.0, False)
    r = await _run_eval_cmd(...)              # 执行指定评分命令
    return EvalResult(r, True)
```

### 3.3 本轮读到哪里

| 位置 | 读清什么 | 回来接住什么 |
| --- | --- | --- |
| [run_evaluation](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/run_evaluation.md) | `md` 如何决定协议；共同输入与返回类型 | `EvalResult`，外层可解包成两个值 |
| [_grade_scaleswe](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md) | 新环境、补丁应用、评分与环境退出如何组合 | `reward` 和补丁状态各表示什么 |
| [E2BSandbox.__aenter__](../02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md) | 已有配置怎样传给创建接口，SDK 对象怎样被保存 | 返回本地 `ev`，继续准备用户与目录权限 |
| [ensure_agent_user](../02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md) | 接受满足 Sandbox 协议的对象，组织用户、目录权限与 Git 准备命令 | 无新返回对象；环境准备后继续使用 `ev` |
| [_apply_diff](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_apply_diff.md) | 文本补丁如何成为工作区变化 | `applied: bool` |
| [_run_eval_cmd](../02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_run_eval_cmd.md) | 命令退出码如何映射成分数 | `r: float` |
| [E2BSandbox.__aexit__](../02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md) | 退出时怎样调用 SDK 回收环境 | 退出处理完成，父函数继续交回已有评测结果 |

从分派入口向下最多展开两层，Sandbox 的底层 SDK 和重试先停在接口。理解正常路径后，再对照“补丁失败”“命令非零退出”“异常传播”三个关键出口；`swepro` / SWE-bench 完整协议留到需要时。

本步以能够解释评测的输入、环境边界、两个返回字段和关键失败含义为停止点。奖励与轨迹怎样导出成训练样本是下一问，尚未在本步展开。

<a id="environment-reading-depth"></a>

### 3.4 环境部分需要读到多深

沿用已确认的评测主线，本步先掌握调用环境所需的关系。公开项目的运行方式与本次取舍见 [运行环境讨论](../04-flow.md#runtime-options-and-depth)。

| 深度 | 具体内容 |
| --- | --- |
| 本步读清 | 两个 grader 的分派与共同返回值；主例怎样用任务镜像准备新环境、写入补丁、执行测试、取得退出码并返回奖励；正常返回与异常退出时谁负责回收 |
| 本步知道边界 | `E2BSandbox` 通过 SDK 操作服务端；`exec` 返回退出码、stdout、stderr，文件操作改变远端工作区；评分协议不决定底层部署；当前后端是否使用 Kubernetes 尚未核实 |
| 后续单独展开 | 对齐岗位中的 Kubernetes 能力：环境创建与就绪、并发与资源限制、网络和文件访问、日志、取消与回收；届时沿具体部署实现和实验学习 |
| 遇到问题再深入 | SDK 连接池与重试、容器或虚拟机运行时内部、gVisor / Kata / Firecracker 的实现；不要求本步逐个掌握所有方案 |

本步的检验问题是：给出一份任务和补丁，能否指出它在哪个环境被测试、怎样交回分数，以及运行故障可能在哪一层出现？能连贯说明这些关系后，再回到奖励与训练数据的交接。
