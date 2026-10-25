# Step 003：scope 结构与源码版本核对

[当前 scope](../01-scope.md) · [本轮问题](../04-flow.md#scope-version-review) · [唯一进度](../../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

2026-10-23，用户要求检查 Step 003 是否需要修改。本次对照已认可的 Step 001、002 scope 与本地源码，保存修改建议；尚未改写本步 scope、函数卡片和 task flow，也未开始新函数的逐段教学。

后续落实：用户确认按上述建议逐步推进后，已先更新 [scope](../01-scope.md#reading-path)并完整保留[旧版](scope-at-2f231865.md)。以下内容保留审查时的判断；函数卡片与 task flow 仍待逐项校准，见[实施记录](../04-flow.md#scope-current-18868a79)。

## 1. 可以保留的部分

- 本步问题仍是：代码补丁怎样在独立环境中得到评测结果，交回 `reward` 与 `applied_cleanly`。
- `run_evaluation` 按协议分派；`_grade_scaleswe` 继续组织环境准备、补丁应用与评分。选择 `scaleswe → eval_cmd` 作为首个教学场景的理由仍成立。
- `EvalResult` 的两个字段及正常返回含义没有变化。评测输入是任务信息和补丁；模型轨迹由另一部分保存，后续才结合奖励导出样本。
- 环境深度边界、测试可见性的未知、个人原话与旧版验证证据继续保留。两份 E2B 进入/退出方法的实现未变，不需要从头重讲。

## 2. scope 需要调整的组织方式

当前 scope 已有整体骨架、评分分支和阅读表，但缺少独立的阅读路径图；3.3 是阅读表，3.4 则是环境深度说明。可参考 [Step 001](../../../../../../../../.agents/skills/repo-reading-scope/references/step-001-reading-path.md)与 [Step 002](../../../../../../../../.agents/skills/repo-reading-scope/references/step-002-reading-path.md)，按以下方式整理第 3 部分：

| 位置 | 调整重点 |
| --- | --- |
| 3.1 整体骨架 | 接回当前 `_generate`，包含 `baseline`、`collect_metrics` 与新的 `adapter/harness` 对象写法；标出本步的 `run_evaluation` |
| 3.2 输入与实现来路 | `diff_text` 直接接自 Step 002；列出本例需要的 `md.image/workdir/grading`、超时与追踪上下文；说明 grader 与 sandbox 后端是两层不同选择 |
| 3.3 局部执行骨架 | 保留 grader 分支；本例经 `_evaluation_sandbox` 进入环境，准备与测试由不同追踪阶段包围，退出后交回结果 |
| 3.4 阅读路径图与导航表 | 从评分入口进入编排；环境来源不清楚时回查工厂，补丁或命令细节从对应调用进入，读完回到父函数；表中注明位置、深度和返回点 |
| 后续深度说明 | 保留现有环境阅读边界，放到导航之后；后端内部与部署细节按需要展开 |

阅读图的具体路径要与选定的后端场景一致。新版可先定位 `_evaluation_sandbox → create_sandbox` 的接口；继续复用 E2B 旧卡时，明确是 `SWE_SANDBOX_PROVIDER=e2b` 分支。默认 Sunabako 的内部实现尚未因本次核对而进入阅读范围。

## 3. 源码变化与应更新的位置

旧记录绑定 `2f2318653f6f794dddd321eff7c9d4b7b174643f`；本地 checkout 为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`，核对时源码工作区干净。以下行号属于新版。

2026-10-23 后续逐张复核：本步 `02` 共有 7 张函数卡，对应的 **5 个函数有变化，2 个函数原文不变**。比较同时检查函数签名、函数体及本场景引用的路径常量；下表另外列出调用方、两个新增环境入口和返回类型。方法原文不变仅说明该方法本身，不代表整个沙箱后端或其依赖都没有变化。

| 位置 | 核对结果 | 对记录的影响 |
| --- | --- | --- |
| `_generate`，`generate.py:296–307` | 先收集指标、提取补丁；离开执行沙箱后在追踪阶段内调用评测，并传入 `trace=base_sample` | 旧 `generate:215` 入口和整体骨架需要校准；补丁来路应直接链接当前 Step 002 |
| `run_evaluation`，`swe.py:290–298` | grader 选择规则未变，新增 `trace` 并向下传递 | 保留心智模型，更新签名、调用代码与行号 |
| `_grade_scaleswe`，`swe.py:304–340` | 直接 `E2BSandbox(...)` 改为 `_evaluation_sandbox(...)`；新增准备、测试追踪阶段；评分命令接收 `grading.eval_user` | 必须改局部骨架；卡片区分环境交接、追踪包装和评分分支 |
| `_evaluation_sandbox`，`swe.py:278–287` | 新增：调用工厂取得对象，进入环境、交出 `ev`，退出时调用其退出方法；创建和清理分别记录追踪 | scope 需要补上这一层真实调用；是否单独建卡在逐段阅读时确定 |
| `create_sandbox`，`examples/coding_agent_rl/sandbox.py:8–16` | 按 `SWE_SANDBOX_PROVIDER` 选择，默认 `sunabako`，`e2b` 分支返回 `E2BSandbox` | 不能把直接进入 E2B 当作新版默认路径，也不据此要求同时读完两套实现 |
| `ensure_agent_user`，`slime/agent/sandbox.py:409–420` | `emulates_root` 为真时跳过 `chown`；工作目录进行 shell 引用；超时由 60 增到 600 秒 | 基础职责仍成立，函数卡需补条件与调用差异 |
| `_apply_diff`，`swe.py:352–366` | 普通 `git apply` 调到 `--3way` 之前；工作目录进行 shell 引用；补丁常量改为 `/tmp/__cagent_patch__.diff` | “先写补丁，再执行应用”模型保留，更新具体路径、命令顺序和示例 |
| `_run_eval_cmd`，`swe.py:394–418` | 新增 `user` 参数；命令超过 64 KiB 时先写脚本，对受支持的 shell 包装进一步处理，再执行；退出码到奖励的映射未变 | 旧卡仅三行实现已不完整；补正常短命令与长命令分支，细节不全部挤进 scope |
| `E2BSandbox.__aenter__`，`slime/agent/sandbox.py:298–317` | 函数原文与 AST 均相同，旧位置为 `281–300` | 继续作为 E2B 分支复用，保留个人原话与既有验证；不把它泛化为所有后端 |
| `E2BSandbox.__aexit__`，`slime/agent/sandbox.py:319–324` | 函数原文与 AST 均相同，旧位置为 `302–307` | 退出方法本身可复用；新版调用方经 `_evaluation_sandbox` 调用它 |
| `EvalResult`，`swe.py:79–83` | 类定义未变 | 原返回值模型继续使用 |

`md.grading.eval_user` 来自 `_metadata_scaleswe` 的 `m.get("eval_user", "agent")`（`swe.py:113–118`）。这让命令执行用户成为输入合同的一部分；scope 只需标出来源，具体命令行为留在函数卡片。

## 4. 建议的修订顺序与边界

1. 先保留旧 scope 快照，再按新版与已认可的图表方式更新 scope；先把输入、入口和后端选择说清楚。
2. 按用户接下来确认的观察点校准函数卡片。保持原话与认识时间，不把本次静态比较计为个人掌握；新函数先在 scope 定位，实际展开时再建卡。
3. 阅读后的 task flow 再同步真实交接。它目前仍属于旧版，并以历史 Step 2 指代评测；更新当前总结时应接上新 Step 002 的统计与补丁，把评测标为 Step 003、样本导出标为 Step 004，原文另存保留。
4. `03-long-term-memory` 是当时的累计快照，本轮不覆盖。需要把当前前序认识带入新版阅读时，另按继承规则处理，保留原来源和版本边界。

<a id="first-function-after-input-gap"></a>

## 5. 本轮推荐：先补清评测输入，再回到评分入口

用户指出 scope 3.2 的部分输入尚未从 Step 001、002 获得，随后要求逐个检查函数变化并推荐第一处入口。本轮按 `repo-reading-order` 回查必要前置：**先打开 `swe.get_metadata`（86–89），沿本场景进入 `_metadata_scaleswe`（92–120），重点看返回的 `md` 字典（106–120）。** `get_metadata` 只负责选择整理方式，字段的实际组织在后者。

| 必要前置 | 版本核对 | 本轮只看什么 |
| --- | --- | --- |
| `get_metadata`，`swe.py:86–89` | 函数原文不变，旧位置为 `77–80` | 当前 `scaleswe` 场景选择哪个整理函数 |
| `_metadata_scaleswe`，`swe.py:92–120` | 相比旧版 `83–110`，只新增返回字段 `grading.eval_user`，默认 `agent` | 原始样本信息怎样整理成 `md`；重点是 `protocol`、`image`、`workdir` 和 `grading.eval_cmd` |

以下是建议阅读路径；回到评分主线表示读完后继续的位置，不表示 `get_metadata` 直接调用评分函数：

```text
先补输入
get_metadata
    └─ _metadata_scaleswe：从返回字典看 md，再回查所需字段来源

回到评分主线
run_evaluation → _grade_scaleswe → 对应的环境、补丁与命令执行观察点
```

- **为何先补这里：** `diff_text` 已有 Step 002 的解释；当前缺口是另一份输入 `md` 的含义和来路。`run_evaluation` 本身只读取协议并转交，无法单独解释完整的评测输入。
- **停止位置：** 能分清“原始样本信息 → 整理后的任务字典 `md`”，并指出本例在哪个环境、哪个目录、用什么命令检查补丁即可。`grading` 是其中的一组评测配置；各评分分支随后再看。
- **保留的边界：** `Sample` 完整结构、数据集加载、`CONFIG` 构造、其他协议和沙箱内部暂不展开；新增 `eval_user` 先知道是命令执行用户，细节留到 `_run_eval_cmd`。
- **回到哪里：** 返回 scope 的评分入口 `run_evaluation`，继续核对 `md + diff_text → EvalResult`。本轮只提出入口建议，未开始这两个前置函数的逐段教学或建立新卡片，也未将输入缺口记为已经解决。

<details>
<summary>源码依据与核对范围</summary>

- [输入整理入口与 ScaleSWE 返回字典](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L86-L120)。
- [调用方与交接](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L296-L307)。
- [评测环境包装、协议分派与 ScaleSWE 编排](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L278-L340)。
- [后端选择](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sandbox.py#L8-L16)。
- [临时路径](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L62-L67)、[补丁应用](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L352-L366)、[命令评分](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L394-L418)。
- [E2B 进入与退出](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L298-L324)、[用户准备](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L409-L420)。
- 通过本地 Git 读取固定旧提交，与当前源码按函数比较；本次为静态核对，没有运行沙箱、应用补丁、执行评测或验证默认后端的实际部署环境。

</details>
