# Dressage 适配 Harbor 0.26.0

目标是把固定在 Harbor 0.18.0 的 Dressage `3e3142f` 升级到 **`harbor==0.26.0`**。0.25.0 用于历史对照。[版本决策](investigations/00-version-target/README.md)

**从上次停下的位置继续**，打开 [PR-001 当前进度与下一步](prs/001-harbor-026-compatibility/README.md#current-status)。

**第一次打开这个目录**　先看[Slime 的一次升级怎样交付](review-format.md#community-example)，再对照[Dressage 的工厂预检记录](review-format.md#example)。设计目录时，可核对[社区的原文与本项目的取舍](review-format.md#sources)和[五个目录各自的产出](review-format.md#formats)。实际修改沿用[修改与评审 SOP](tools/upgrade-sop.md)。

<a id="original-integration"></a>

## 升级要保住什么 · 跟一份题走完一次 Trial

**原版的交付是一次可追溯的 rollout。** Harbor 把题目交给选好的 Agent，运行 verifier 并返回这次尝试的奖励。Dressage 把这个奖励和**同一次尝试**的模型交互轨迹配在一起。训练入口再把合格结果转成 Slime 的 Sample。原来读过的总图在 Step 011 的第 2 节。那张图按 Harbor 0.25 带读，这次分别核对了原依赖 0.18 和目标 0.26 的普通单步路径。[Step 011 · 从准备到返回](../../topics/02-harbor-integration/steps/step-011-harbor-trial-lifecycle/05-task-flow.md) · [Dressage 原版职责说明](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/docs/harbor.md#L23-L39)

| 时刻 | 这一步把什么交给下一步？ | 对应的原笔记 |
| --- | --- | --- |
| Job 开始，Trial 发出 `START` | Dressage 配好 Agent 的模型地址并登记回调。收到 `START` 后，把本次物理尝试的 `trial_id` 用作 Proxy 的 `session_id`，登记对应路由。 | [Step 014 · 路由登记](../../topics/02-harbor-integration/steps/step-014-model-routing-and-api-contract/01-scope.md#reading-part-2) |
| Harbor `Trial._prepare()` | Trial 已持有选好的 Environment 对象。在它上面等待 `start()`，检查环境并准备 Agent。随后 `_run` 用**同一个环境**执行题目。在本地 bwrap 路线上，运行环境须让 Agent 能写第一份日志。C05 修的就是这一处。 | [Step 013 · 环境怎样启动](../../topics/02-harbor-integration/steps/step-013-harbor-kubernetes-environment/01-scope.md#reading-navigation) |
| Harbor `SingleStepTrial._run_agent()` | Harbor 把题目的 `instruction` 和刚准备好的环境交给 Agent。需要模型时，Agent 经 Gateway、Proxy 请求模型，Proxy 按本次会话记录 token 交互。工具命令在 Agent 的环境里执行。 | [Step 014 · 从 Agent 执行到模型请求](../../topics/02-harbor-integration/steps/step-014-model-routing-and-api-contract/01-scope.md#reading-part-1) |
| Harbor 收日志、收产物、跑 verifier | `_sync_agent_output` 先取回 Agent 日志并整理上下文。`_upload_agent_logs` 按需把本地整理的日志传回环境。`_collect_artifacts` 收集任务发布的文件，`_run_verifier` 把评分写进 `TrialResult.verifier_result`。 | [Step 015 · Agent 结束到取得评分](../../topics/02-harbor-integration/steps/step-015-harbor-results-and-samples/01-scope.md#reading-navigation) |
| Trial 收尾发出 `END`，Job 汇总 | 正常结束时 Dressage 读取该会话的 Proxy segments，从该 TrialResult 提取奖励，生成尝试的 bundle 并关闭路由。若一道题重试后第二次得 1，训练入口就按第二次的 ID 查 bundle，经资格与组检查交回 Sample。已标记取消时，插件跳过提交并清理路由。 | [Step 015 · bundle 交给谁](../../topics/02-harbor-integration/steps/step-015-harbor-results-and-samples/01-scope.md#bundle-handoff) |

**用什么界定这次适配？** 先用相同输入核对哪个调用方丢失了原版能交付的结果，再按上游支持的用法划定升级范围。bwrap 的直挂日志和沙箱自有日志纳入第一轮。手动空 `/logs` 已证实退化，初始化宿主目录的责任待上游确认，C05b 暂停。[第一轮范围](prs/001-harbor-026-compatibility/README.md#current-status) · [普通日志的同题对照](investigations/02-output-mounts/c05-mount-experiments.md#original-integration-parity)

例如，`trial/agent/run/probe.log` 是检查 Harbor 整目录回收的测试文件。Dressage 生成训练 bundle 时，实际读取的是 Proxy 轨迹和 Harbor 评分。这两处分别用文件字节和同一次尝试的轨迹、奖励来验证。[原版读取 Proxy 轨迹](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L389-L406) · [原版使用 Harbor 评分](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L431-L473)

## 按手头的问题选入口

| 手头的问题 | 记录放在哪里 | 以工厂预检为例 |
| --- | --- | --- |
| 谁调用谁，旧版和新版各传了什么？ | `usage/` 按交接编号记录调用、输入和下游结果。 | [U34 · Harbor 工厂怎样调用 Dressage](usage/环境构造与生命周期/U34-EnvironmentFactory%20调用%20DressageEnvironment.preflight.md#u34) |
| 这个行为在 0.26 下还成立吗？要改代码，还是已有证据足以沿用？ | `investigations/` 每个可以独立判断的问题一个目录，README 放结论与依据，旁边放复现脚本和原始输出。 | [01 · 复现、候选改法与验证](investigations/01-environment-preflight/README.md) |
| 哪几个修复一起提交，合并前还缺什么？ | `prs/` 每份 PR 一个目录，引用相关问题和验收证据。 | [PR-001 · 本地后端的验收顺序](prs/001-harbor-026-compatibility/README.md#test-order) |
| 下一笔 commit 具体改哪些文件、怎么验？ | 从所属 PR 的提交计划进入 `commits/`。 | [PR-001 的提交顺序](prs/001-harbor-026-compatibility/README.md#review-order) · [第一笔 C01](prs/001-harbor-026-compatibility/commits/01-environment-preflight.md) |

要看这次升级整体发现了什么，读[第二轮审核结论](investigations/upgrade-audit-026.md)。要查某个编号，直接跳到[调查索引](#investigations)或[七组用法](usage/README.md#routes)。

<a id="prs"></a>

## PR 索引

| 本地编号 | 审查目标 | 当前状态 |
| --- | --- | --- |
| [PR-001 · Dressage 适配 Harbor 0.26.0](prs/001-harbor-026-compatibility/README.md) | 核对后端修复、测试夹具、版本声明和两条运行入口 | [进度与合并前待办](prs/001-harbor-026-compatibility/README.md#current-status) |

独立 Dressage 工作树 `compat/harbor-0.26` 用于提交适配实现、默认套件中的回归测试，以及随行为变化需要同步的依赖声明和使用说明。源码对照、探测输出和 PR 草稿统一在本阅读仓库维护。创建 GitHub PR 后，将实际链接登记在对应评审页。

<a id="issues"></a>
<a id="investigations"></a>

## 调查索引

00–24 是本地调查编号。每项记录当前证据能支持的决定，例如 01 需要修复，05 在已测路径可以沿用，16 的云端启动仍待验证。发现新情况时，先按[新建调查的规则](investigations/README.md#new-investigation)判断归属。准备向维护者提交时，看[怎样写上游 PR](tools/upgrade-sop.md#upstream-pr)。

| 编号 | 打开一个问题 | 目前有何依据 |
| --- | --- | --- |
| 00 | [版本决策](investigations/00-version-target/README.md) | 已确定只交付 0.26.0 |
| 01 | [工厂预检的签名](investigations/01-environment-preflight/README.md) | 新版 C01 `8827b11` 已通过六例预检。 |
| 02 | [非空日志目录被复制回自身](investigations/02-output-mounts/README.md) | 默认直挂时日志复制回自身，独立 verifier 已写出奖励时仍可能在下载步骤失败。 |
| 03 | [独立 verifier 的测试夹具](investigations/03-verifier-fixture/README.md) | 已定位，对齐测试入参 |
| 04 | [安装依赖与版本检查](investigations/04-version-checks/README.md) | 适配验收后更新版本声明 |
| 05 | [技能目录上传](investigations/05-skills-upload/README.md) | 文件读写已过，暂保留 |
| 06 | [Job 创建时的凭证检查](investigations/06-agent-credential-preflight/README.md) | 随仓 Qwen 配置可以创建 Job；某些显式凭证配置会在插件挂接前拒绝。 |
| 07 | [实际请求到达的 Gateway](investigations/07-agent-routing/README.md) | 已观察 Claude Code 最终启动地址和凭证选择，第一条真实请求待验。 |
| 08 | [Trial 目录脱敏与 bundle 位置](investigations/08-trial-output-redaction/README.md) | 已观察受控 Trial 在 END 与返回时的文件脱敏差异。 |
| 09 | [Trial 排列与原模板配对](investigations/09-trial-plan/README.md) | 已有真实 Job 探测 |
| 10 | [临时 Job 生成 lock](investigations/10-job-lock/README.md) | 本地 lock 已验证 |
| 11 | [CANCEL 与 END 事件时序](investigations/11-trial-events/README.md) | 受控真实 Trial 已跑正常和取消，取消路径零次提交、一次关闭路由。 |
| 12 | [评测有效分数与训练采纳](investigations/12-reward-validity/README.md) | 三版同四组输入的 Dressage 采纳一致。Agent 非零退出时，Harbor 0.25 与 0.26 对分数有效性的判断相反。 |
| 13 | [重试后最终进入训练的尝试](investigations/13-final-attempt/README.md) | 真实队列的受控重试已对齐最终 Trial ID、manifest 和两段 Sample。完整训练分区待验。 |
| 14 | [bwrap 的阶段网络策略](investigations/14-phase-network-policy/README.md) | 多步任务待验 |
| 15 | [Agent 的 Web 工具开关](investigations/15-web-tools/README.md) | 目标 harness 待验 |
| 16 | [E2B 模板启动](investigations/16-e2b-template/README.md) | 离线观察到资源规格进入模板键，真实云端启动待验。 |
| 17 | [E2B 长任务续租](investigations/17-e2b-renewal/README.md) | SDK 替身已观察续租和停止后的回收次数，真实云端续租待验。 |
| 18 | [随仓 Job YAML 的含义](investigations/18-example-configs/README.md) | 两份 YAML 在三个版本均可解析 |
| 19 | [旧数据源 checkpoint 的识别](investigations/19-checkpoint-digests/README.md) | 两题同种子下，0.18 checkpoint 交给 0.26 会拒绝，0.26 同版可恢复游标。 |
| 20 | [bwrap 停止时能否保留工作目录](investigations/20-bwrap-stop-delete/README.md) | 三版实测均忽略 `delete=False`，属于升级前已有的限制。 |
| 21 | [独立 verifier 的启动目录](investigations/21-separate-verifier-input/README.md) | 省略空目录时 0.26 在上传 tests 前失败；非空目录的环境材料误入 /tests。 |
| 22 | [哪些失败触发 Harbor 重试](investigations/22-retry-policy/README.md) | 同一输入在 0.18 与 0.26 的物理尝试数有三个方向明确的差异。 |
| 23 | [本地 dataset 取前 N 题](investigations/23-local-dataset-selection/README.md) | 相同目录与上限会因排序改变选中的题目。 |
| 24 | [Harbor 宿主进程的默认遥测](investigations/24-host-telemetry/README.md) | 两份随仓 CLI 配置在 0.26 默认构造结束事件；禁用时不进入发送边界。 |

## 复跑和查证

`tools/` 收纳整个升级目录共用的工具。日常从本页所在目录运行 `python3 tools/check_docs.py`，它会调用 `check_usage.py` 校验用法表。需要从固定提交重建调用清单时，再运行 `tools/scan_harbor_surface.py`。[完整命令](tools/reproduce.md#provenance)

复现单个问题时，脚本和运行输出随对应调查项保存，例如 [01 的工厂预检实验](investigations/01-environment-preflight/probe.py)。跨用法共用的实验放在 `usage/evidence/`，例如 [U57 和 U58 共用的 DAPO 实验](usage/evidence/dapo_files.py)。

- 要自己运行实验，从[准备环境与复现命令](tools/reproduce.md#setup)进入。检查文档链接、用法映射和源码摘录的命令也在[校验说明](tools/reproduce.md#provenance)。
- 要查有没有漏审，从[191 处源码与用法的对应表](usage/source-index.md#locations)或[用法与问题反查表](investigations/original-test-audit.md#issue-map)进入。按文件核对原行时再开[固定提交的扫描结果](usage/harbor-call-sites.md)。
- `archive/` 保存首次调查的原始判断。要追溯当时的依据，看[首次接入点梳理](archive/integration-inventory.md#coverage)、[原七项升级建议及其核查](archive/decisions.md#gemini-review)或[Step 011 的版本对照](../../references/agent-sandbox-harbor-compatibility.md#harbor-version-upgrade-20261111)。
- 工作树最早的 `docs/harbor-026-upgrade/` 已完整保存为[原始笔记快照](archive/dressage-worktree-notes-3e3142f.tar.gz)。45 个文件已逐一核对，后续从上面的用法、问题和 PR 入口接续。

更多源码入口见 [Dressage 的 Harbor 集成说明](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/docs/harbor.md) · [接入实现](https://github.com/Accio-Lab/Dressage/tree/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor) · [测试套件](https://github.com/Accio-Lab/Dressage/tree/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor)。
