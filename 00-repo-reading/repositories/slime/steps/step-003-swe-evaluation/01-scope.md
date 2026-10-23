# 01 · 阅读范围：从代码补丁到评测奖励

[本步入口](README.md) · [Step 0 核心骨架](../step-000-coding-agent/01-scope.md) · [前一步：运行统计与补丁](../step-002-agent-results/01-scope.md) · [旧版 scope](references/scope-at-2f231865.md)

**版本说明**：本页入口、骨架和源码行号按 `18868a79b0b083a093798a94ed0f8cb4f71b9c14` 校准。`02` 的 `_metadata_scaleswe`、`_evaluation_sandbox`、`ensure_agent_user`、`_apply_diff`、`_run_eval_cmd`、`_grade_scaleswe` 和 `run_evaluation` 卡片使用本版本，见[函数索引](02-short-term-memory/overview.md)；两张 E2B 卡片的实现经核对未变，保留原版本证据。`03` 继续保留累计快照，`05-task-flow.md` 已同步本轮交接并归档旧版。[差异核对](references/scope-version-review-2026-10-23.md)保存具体变化。

## 1. 阅读目标

沿用理解 Coding Agent / Coding RL、对齐框架工程岗位的目标。本步回答：**Agent 修改代码以后，系统怎样在独立环境中评测，并把结果交成 `reward` 与 `applied_cleanly`？**

阅读重点是评测接口、环境边界与结果含义，对应[岗位中的组件封装、评测接入和稳定性要求](../../../../../slime_photo/code-reading/job-alignment.md#step-2-evaluation-choice)。先从 Step 002 已讨论的结果接起：CLI 已结束，工作区的改动已整理为 `diff_text`。本步新增的任务信息 `md` 先在 [3.2 输入衔接](#input-bridge)用小例子说明，再进入评分入口。补丁来路可回看 [Step 002 的 git_diff](../step-002-agent-results/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/git_diff.md)。

继续采用已有的 `scaleswe → eval_cmd` 教学场景。本轮先读环境的共同调用边界，明确怎样取得和使用 `ev`；后端选择在入口处说明，Sunabako 的内部实现暂不展开，E2B 的旧卡作为对应分支的回查材料。以评测结果回到 `_generate` 为本步终点。

## 2. 指挥官函数与本步入口

整体入口仍是 `examples/coding_agent_rl/generate.py::generate`，实际业务编排由 `_generate` 负责。本步从 [generate.py:301–306](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L301-L306)进入 [swe.run_evaluation:290–298](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L290-L298)，再到实际组织环境、补丁和评分的 [_grade_scaleswe:304–340](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L304-L340)。

`run_evaluation` 按协议选择 `_grade_swebench` 或 `_grade_scaleswe`，一次调用只进入其中一个。先在入口认清两个分支的选择条件、共同返回类型与评分依据，再深入本例的 `scaleswe → eval_cmd`。

<a id="why-scaleswe-first"></a>

**为什么两个 grader 中先选 `_grade_scaleswe` 的 `eval_cmd` 分支：**

1. **保留完整评测链，首轮需要的新概念较少。** 这一分支只需跟随“新环境 → 应用补丁 → 执行给定命令 → 退出码转为奖励”。SWE-bench 在这条链上还需要理解任务实例如何生成 `TestSpec / eval_script`，以及测试日志如何由评测框架解析成报告，再读取 `resolved`。这些是有价值的协议细节，但不是先理解奖励来源的必要前置。
2. **先建立后续能复用的共同模型。** 独立环境、补丁交接、测试执行、返回 `EvalResult` 都能在首个例子里看见。再读 `_grade_swebench` 时，就能聚焦它在测试准备、执行和报告解释上的差异，明确新协议接入影响哪些环节。这与当前理解 RL 框架及评测接入的目标一致。
3. **默认配置仅作为辅助依据。** 当前源码的训练和评估协议都默认 `scaleswe`；这支持用它作首例，但不能证明实际数据一定使用 `eval_cmd`，也不能证明它在行业里更常见。评分协议与沙箱后端分别选择，部署方式不构成先后理由。

这里判断较简单的是选定的 `eval_cmd` 路径，不能推广为 ScaleSWE 所有分支都简单。如果目标改成复现或排查 SWE-bench 的基准结果，应优先 `_grade_swebench`。本次选读理由的澄清见 [讨论记录](04-flow.md#grader-priority-reason)。

## 3. 给出真正干活的核心骨架

### 3.1 继承整体骨架，定位第 6 项

沿用 Step 0 的 `evaluation=False` 正常路径。下面是教学裁剪，参数通常用 `...`，保留与补丁来路相关的 `baseline`；配置、前置检查、追踪、日志及外层异常清理暂时折叠。

```python
adapter.open_session(...)                              # 1. 登记本次会话
async with boot_agent_sandbox(...) as sb:                # 2. 启动执行沙箱
    baseline = await swe.prepare_workspace(...)         # 3. 准备工作区，保存初始快照
    agent_exit_code = await harness.run(...)             # 4. 运行 CLI，等待结束
    # CLI 运行期间通过 HTTP 进入 Step 1 的 _run_turn
    agent_metrics = await harness.collect_metrics(...) # Step 2：取得运行统计
    diff_text = await swe.git_diff(sb, ..., baseline)     # 5. Step 2：取得代码改动

reward, applied_cleanly = await swe.run_evaluation(...)  # 6. 本步：独立评测
samples = await adapter.finish_session(...)              # 7. Step 4：导出样本
...  # 附加结果与截断状态；最终还有会话清理
return samples
```

离开执行沙箱以后才进入评分。多轮请求的轨迹已经记录在 manager；本步接收任务信息与 `diff_text`。运行统计另交给后续样本记录和状态处理。

<a id="input-bridge"></a>

### 3.2 从前两步的结果，补齐本步的新输入

这里按 Step 001、002 已经讨论过的内容衔接。源码执行到此处时已有这些变量，不代表前两步已经解释了它们；其他旧步骤里存在材料，也不作为当前已知前提。

| 内容 | 前两步涉及到哪里 | 本步怎样接上 |
| --- | --- | --- |
| `diff_text` | Step 002 已讲解：工作区改动形成一份补丁文本 | 直接接作“这次改了什么”，交给评测 |
| `workdir` | Step 002 已作为仓库目录路径使用 | 沿用路径含义；评测时操作的是新建环境中的这个目录 |
| 追踪的作用 | Step 001 已讨论 `trace_span` 记录执行阶段 | 可以唤起这项用途；`base_sample` 的结构和它如何提供追踪上下文仍未在这两步讲清楚 |
| `md`、`grading`、`eval_cmd` | 前两步没有展开这组评测输入 | 先用下面的小例子补齐，再进入 `run_evaluation` |

**本步先补的核心是 `md`：它是一份描述“这道题在哪里、按什么方式检查”的 Python 字典。** `grading` 是其中保存评分设置的小字典，`eval_cmd` 是本例要执行的测试命令。

下面沿用本步旧卡的 `calc.py` 教学场景，只看字段形状。镜像名是占位；假设该镜像中已有仓库和测试，没有运行真实环境。这是字段节选，不是完整任务数据：

```python
md = {
    "protocol": "scaleswe",          # 交给哪一类评分器
    "image": "teaching/calc:v1",     # 新评测环境从哪份镜像开始
    "workdir": "/workspace/repo",    # 进入环境后，项目放在哪里
    "grading": {
        "eval_cmd": "python -m pytest -q tests/test_calc.py",  # 用什么命令检查
    },
}
```

当前先接起两项：`diff_text` 告诉评测器改了什么，`md` 提供检查所需的任务信息。① `run_evaluation` 先读取 `protocol` 选择评分器；② `_grade_scaleswe` 再使用镜像、目录和评分设置。

另外两项先识别用途即可：

- `timeout_sec`：评测命令的时间预算，例如旧教学例使用 60 秒；`CONFIG` 如何创建暂不展开。
- `trace`：传下去用于记录评测阶段的追踪上下文。本次调用传入 `base_sample`；这里只接上用途，它的完整结构和创建来路仍留白。

原始样本怎样整理成这份字典，见 [_metadata_scaleswe 函数卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_metadata_scaleswe.md)：保留完整返回字段，按输入与输出一一对照。本轮先补清这项输入，再进入①；`Sample` 的完整构造、配置加载与环境实现仍不作为前置。

`eval_user` 的执行细节留到⑥说明；环境后端留到③创建环境时说明。

<details>
<summary>需要追查字段如何产生时：源码位置与后续用途</summary>

| 调用时使用的值 | 源码中的来路 | 用途与后续观察点 |
| --- | --- | --- |
| `diff_text` | Step 002，`generate.py:298` 的 `swe.git_diff` 返回 | 描述待评测的代码改动，交给新环境应用 |
| `md` | `generate.py:260–261` 选择协议并调用 `swe.get_metadata` | `protocol` 决定 grader；`image`、`workdir` 决定任务环境；`grading` 提供评分材料 |
| 本例的 `md["grading"]` | `swe.py:113–118` 整理任务元数据 | 使用 `eval_cmd`，`eval_user` 默认 `agent`；本例无 `swepro`、`f2p_script`、`pre_commands` |
| `timeout_sec` | `generate.py:304` 的 `CONFIG.eval_timeout_sec` | 传给评分执行阶段的时间预算 |
| `trace` | `generate.py:305` 传入 `base_sample` | 为本次评测的阶段记录提供关联上下文，和 `EvalResult` 分工不同 |

输入整理见 [generate.py:254–261](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L254-L261)、[swe.py:92–120](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L92-L120)。这些位置说明值在源码中怎样产生，不作为前两步已经学过的内容；需要理解其构造时再从这里回查。

</details>

<a id="step-2-branch"></a>
<a id="step-3-branch"></a>

### 3.3 局部执行骨架

先在评分入口保留分派关系。以下裁剪自 `swe.py:296–298`，调用参数省略：

```python
if md.get("protocol") == PROTOCOL_SWEBENCH:
    return await _grade_swebench(...)   # 本步只定位，脚本与报告解析暂不展开
return await _grade_scaleswe(...)       # 本例 protocol 为 scaleswe
```

然后进入 `_grade_scaleswe`。下列代码只展示本例的 `eval_cmd` 路径；其他评分材料的分支和无评分材料的提前返回暂时折叠。保留补丁失败出口，因为它直接影响结果含义。

```python
# examples/coding_agent_rl/swe.py:320–340，教学裁剪
async with _evaluation_sandbox(...) as ev:         # 取得并使用新评测环境
    with trace_span(..., "evaluation_prepare", record_error=False):
        await agent_sandbox.ensure_agent_user(...) # 准备用户、权限与 Git 设置
        applied = await _apply_diff(...)           # 把 diff_text 应用到该环境
        if not applied:
            return EvalResult(0.0, False)
    with trace_span(..., "evaluation_tests", record_error=False):
        r = await _run_eval_cmd(...)               # 本例：执行指定评分命令
    return EvalResult(r, True)                     # 先形成结果，退出环境后交回
```

`_evaluation_sandbox` 在进入时调用 `create_sandbox` 选择对象，再等待其 `__aenter__` 并交出 `ev`；使用期结束后调用同一对象的 `__aexit__`。创建与清理的追踪位于这个包装内部。这里先看交付、使用和退出的时机，后端的连接与执行机制保持接口边界。

准备和测试阶段的追踪范围以上述真实嵌套为准。`trace_span` 的既有模型可从 [Step 001 卡片](../step-001-harness-to-adapter/02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md)唤起；完整追踪传播与导出仍留在后续专题。

<a id="reading-path"></a>

### 3.4 每次读哪一段，读到什么程度

这张图是本次校准的阅读导航，指明下一处如何进入与返回；它不表示所有新版细节已经读懂。先在 [3.2](#input-bridge)补齐最小输入例子，再看评分分派，随后沿选定编排逐项补齐。图中 `swe.py` 指 `examples/coding_agent_rl/swe.py`。

```text
先看 3.2：接住 diff_text，认识最小 md 字典；其余参数先看用途
   └─ get_metadata → _metadata_scaleswe              swe.py:86–120
      对照原始 Sample 属性与返回字典，只补清本例的输入来源
    ↓
① run_evaluation                                     swe.py:290–298
   看清：md + diff_text + 时间预算 → 选择 grader → EvalResult
   └─ 对照小例子，先确认 protocol 怎样选择评分器
    ↓
② _grade_scaleswe                                    swe.py:304–340
   先看：本例如何把环境、补丁和命令评分串起来
    ↓ 遇到环境入口，局部回查
③ _evaluation_sandbox                                swe.py:278–287
   ├─ create_sandbox                                 coding_agent_rl/sandbox.py:8–16
   │  看清后端选择；具体实现先按进入、退出接口理解
   └─ 接住 ev，返回 _grade_scaleswe:322
    ↓
④ ensure_agent_user                                  slime/agent/sandbox.py:409–420
   看清：同一个 ev 上准备用户、权限与 Git 设置
   └─ 返回 _grade_scaleswe:329
    ↓
⑤ _apply_diff                                        swe.py:352–366
   看清：先写补丁文件，再执行应用命令 → applied
   └─ 返回 330–331 判断：失败则结束；成功才继续评分
    ↓ 成功路径
⑥ _run_eval_cmd                                      swe.py:394–418
   看清：命令 + 执行用户 + 时间预算 → 退出码 → r
   └─ 先读短命令路径，再定位长命令分支，返回 340
    ↓
⑦ 回到 _grade_scaleswe：形成 EvalResult
   → 离开 _evaluation_sandbox，等待环境退出处理
   → 经 run_evaluation 返回 _generate:301
```

按同一编号打开下面的材料，当前卡片与新版源码对应，旧版完整证据在各卡片的归档入口保留；③的 `_evaluation_sandbox` 已有独立卡片，`create_sandbox` 先在其中按后端选择规则理解。

| 观察点与材料 | 本处看清什么就停 | 读完回到哪里 |
| --- | --- | --- |
| 输入衔接：[_metadata_scaleswe 卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_metadata_scaleswe.md) | `Sample` 的原始信息怎样整理为 `md`，重点看镜像、目录、问题描述和 `grading.eval_cmd` | 接回①，使用这份字典和 `diff_text` 进入评分 |
| ① [run_evaluation 新版源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L290-L298) · [函数卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/run_evaluation.md) | `md` 如何选择 grader，`trace` 怎样向下传递，共同返回的两个字段是什么 | 进入②；最终返回 `_generate:301` |
| ② [_grade_scaleswe 新版源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L304-L340) · [函数卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md) | 先看环境、准备、评分、返回的组织；保持本例 `eval_cmd` 边界 | 遇到 `320` 的环境入口，去③ |
| ③ [_evaluation_sandbox 卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_evaluation_sandbox.md) → [create_sandbox 源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sandbox.py#L8-L16) | 选择对象、进入并交出 `ev`、退出时回收的边界；后端内部先不下钻 | `_grade_scaleswe:322` 使用 `ev`；到⑦再回看退出 |
| ④ [ensure_agent_user 新版源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L409-L420) · [函数卡片](02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md) | 准备哪些基础条件，`emulates_root` 怎样影响目录归属处理；`exec` 先按接口理解 | 返回 `329`，把同一 `ev` 交给补丁应用 |
| ⑤ [_apply_diff 新版源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L352-L366) · [函数卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_apply_diff.md) | 补丁文本、临时文件与真实工作区修改怎样交接；核对新路径和应用顺序 | `330–331` 根据 `applied` 决定是否继续 |
| ⑥ [_run_eval_cmd 新版源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L394-L418) · [函数卡片](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_run_eval_cmd.md) | 先看指定用户执行短命令及退出码评分；再定位超长命令如何转为脚本，不在此展开全部 shell 处理 | `340` 接住分数 `r`，进入⑦ |
| ⑦ [结果与退出](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L278-L298) · [EvalResult](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L79-L83) | 结果形成后先完成上下文退出，再向调用方交回；区分补丁失败、命令非零和异常传播 | `_generate:301` 接住 `reward, applied_cleanly`，本步收束 |

<details>
<summary>走到③或⑦时再看：环境后端选择与 E2B 分支记录</summary>

**评分协议与沙箱后端是两层选择：** `run_evaluation` 读取 `md["protocol"]`；环境工厂 [create_sandbox](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sandbox.py#L8-L16)读取 `SWE_SANDBOX_PROVIDER`。新版默认 `sunabako`，显式为 `e2b` 时返回 `E2BSandbox`。

本步先把 `ev` 理解为已进入使用期的环境操作对象，提供命令执行和文件操作能力。已有 E2B 进入/退出记录只用于 `e2b` 分支；本页的默认值说明来自静态源码，不代表已经运行过相应后端。

仅在选择 `SWE_SANDBOX_PROVIDER=e2b` 时对应这套实现。两方法经版本比较未发现实现变化，旧卡仍保留原行号和验证来源：

- [E2BSandbox.__aenter__](02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md)：新版位置为 `slime/agent/sandbox.py:298–317`；接住环境对象后回到③的交付位置。
- [E2BSandbox.__aexit__](02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md)：新版位置为 `319–324`；退出行为回接⑦。
- [原有环境、语法与实现说明](references/sandbox-entry.md)：按旧版本使用，不作为 Sunabako 的实现说明。

</details>

每次从当前观察点局部下钻，看清所需交接后返回。上述导航跨越多次观察，不要求从 `run_evaluation` 一次追到底；后端 SDK、shell 解析和追踪内部不成为本轮的全链前置。

<a id="environment-reading-depth"></a>

### 3.5 环境部分需要读到多深

沿用已确认的评测主线，本步先掌握调用环境所需的关系。此前运行方式的讨论保留在 [运行环境讨论](04-flow.md#runtime-options-and-depth)，其中原后端说明按当时版本理解。

| 深度 | 具体内容 |
| --- | --- |
| 本步读清 | grader 分派与共同返回值；主例怎样取得新环境、应用补丁、执行命令、取得退出码并返回奖励；正常和异常退出时调用谁做环境收尾 |
| 本步知道边界 | 环境由工厂选择；`exec` 返回退出码、stdout、stderr，文件操作改变环境工作区；评分协议不决定底层部署，E2B 旧卡只对应其分支 |
| 后续单独展开 | 具体后端的创建与就绪、并发与资源限制、网络和文件访问、日志、取消与回收；对齐岗位中的 Kubernetes 能力时另沿实际部署与实验学习 |
| 遇到问题再深入 | SDK 连接池与重试、容器或虚拟机运行时内部、gVisor / Kata / Firecracker 的实现；不要求本步逐个掌握所有方案 |

**停止条件**：能够连续说明“任务信息与补丁 → 选择评分器 → 新环境中的准备与测试 → `EvalResult` 回到调用方”，并区分两个结果字段及关键失败含义。奖励与轨迹怎样导出为训练样本，接回已有 Step 004；新版内部细节待对应步骤校准。

[Task flow](05-task-flow.md)已按本轮阅读收拢新版执行关系与结果，[旧版总结](references/task-flow-at-2f231865.md)完整保留；原始问题与修正继续保存到 `04-flow.md`。实际接续统一见[阅读路线](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)，主线收束不等于已掌握全部内部实现。
