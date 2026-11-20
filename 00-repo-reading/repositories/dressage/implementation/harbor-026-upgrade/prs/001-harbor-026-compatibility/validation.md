# PR-001 · 验收场景与评审记录

从[PR 首页](README.md#scope)查看候选修改、实际提交和交付目标。这里按场景保存运行输入、观察点、尚缺的证据和此前判断。

选测试时先确定哪个下游任务会观察到变化。每笔修复复跑受影响的行为，最终候选提交再验证下表的跨组件任务。[SOP 中的下游验收规则](../../tools/upgrade-sop.md#downstream)

<a id="review-order"></a>

## 当前审核顺序

**复查改变了四个评审项。** 独立 verifier 的启动输入需要生产修复，默认重试规则与本地 dataset 排序需要写明版本行为，离线配置还需明确宿主的遥测开关。[21 启动目录](../../investigations/21-separate-verifier-input/README.md) · [22 重试次数](../../investigations/22-retry-policy/README.md) · [23 题目选择](../../investigations/23-local-dataset-selection/README.md) · [24 宿主遥测](../../investigations/24-host-telemetry/README.md) · [复查摘要](../../investigations/upgrade-audit-026.md)

**按 U 核对交接，按实际场景执行测试。** 61 项 U 都有三版表和相关调查项入口。先选下表的一行，用同一份题目和配置跑该路径，沿涉及的 U 观察输入、分支、输出及下游副作用。一份运行记录可以回答多个 U。[用法和证据](../../usage/README.md#routes) · [源码位置反查](../../usage/source-index.md#locations)

<a id="test-order"></a>

| 顺序与涉及的用法 | 怎样测，在哪一刻判定 | 已有证据与下一步 |
| --- | --- | --- |
| ① 工厂预检 · U34 | 给 Harbor 工厂同一后端类路径，核对四种输入的原值到达基类且执行继续进入后端检查。 | 独立工作树已在 Harbor 0.26.0 实测，修前 4 失败、1 通过，修后 5 通过。改写后 `8827b11` 增加一例上游签名快照，六例通过。[运行记录](../../investigations/01-environment-preflight/README.md#amended-check) |
| ② 环境与日志 · U31、U42、U44 | 让原 Trial 回收一个非空文件。直挂时下载 0 次，另绑目录时下载 1 次且目标文件字节一致。独立 verifier 夹具另跑原有环境测试。 | 两种挂载各跑三版。0.26 的异目录交付已通过，直挂仍记错；只改 verifier 夹具后四项环境测试通过。**修 02、21 后重跑两种日志挂载，以及独立 verifier 在无环境目录时的启动、测试上传和评分返回，再复核 03。** [六次日志回收](../../investigations/02-output-mounts/README.md#mount-matrix) · [03 的测试输出](../../investigations/03-verifier-fixture/fixture-pytest.txt) |
| ③ 真实 Trial 正常和取消 · U19、U21、U23–U30 | 跑一次正常 Trial，再取消一次已开启路由的 Trial。正常时观察请求抵达 Gateway、END 提交 1 次；取消时按同一尝试观察 CANCEL 后的 END、训练提交 0 次。两者都核对路由释放。 | 受控 Job/Trial 已触发正常和取消的真实事件；还需在运行 harness 时捕获一次实际 Gateway 请求。[07 路由](../../investigations/07-agent-routing/README.md) · [11 正常与取消](../../investigations/11-trial-events/README.md) · [现有插件测试](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_execution.py#L64-L109) |
| ④ 真实重试进入训练 · U22、U50、U53、U54 | 用允许重试的错误让首轮失败、次轮成功。比对最终 `JobResult.trial_results` 的 ID、Sample 的 `harbor_trial_id` 和 manifest 选中的 ID，另核对旧尝试的训练标记。 | 受控失败经过真实 Job/队列，已核对物理次数、最终 ID、manifest 和 Sample。下次从完整训练分区和 Slime 入口复验。[12 评分交接](../../investigations/12-reward-validity/README.md#evidence) · [13 重试与最终选择](../../investigations/13-final-attempt/README.md) · [Sample 中的 ID](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L650-L660) |

**出现差异时怎样归档？** 找到第一个偏离预期的交接，把输入、应有行为和实际结果写回该 U。到关联调查项记录根因、受影响的下游、修前和修后的断言。同一根因补原调查项，新根因另开；一条用法只有静态依据时，保留待验标记。旧版也可能漏交数据，日志的异目录用例就是实证。[问题 02 的两种输入](../../investigations/02-output-mounts/README.md#mount-matrix) · [问题记录格式](../../investigations/README.md#handoff)

发布验收从干净环境安装 Dressage 的 Harbor extra，读取实际发行包版本，确认得到 0.26.0 后从正常入口复跑。可选云后端与 checkpoint 的证据见下表。[04 安装和运行声明](../../investigations/04-version-checks/README.md) · [最终验收](#acceptance)

给上游提交 01 和 02 时，将工厂调用和两种日志挂载的断言随修复加入 Dressage 的 `tests/integrations/harbor/test_environment.py`，让以后修改后端的人也能从默认集成套件跑到它们。阅读仓库保留三版证据，方便评审人对照修复前的行为。[Dressage 环境测试](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py) · [本地复现命令](../../tools/reproduce.md#run-probes)

## 哪些行为要在评审时核实

问题编号可以共用一份 PR。已经有运行证据的行为，只有新证据显示需要改动时才追加代码。待验的路径决定 PR 最终能承诺多大的支持范围。

| 范围 | 已有依据及还要观察什么 | 对应问题 |
| --- | --- | --- |
| <a id="skills"></a>Skills 文件 | 0.26.0 已能上传并读回技能文件，保留后端上传逻辑。 | [05 · Skills 上传](../../investigations/05-skills-upload/README.md) |
| <a id="job"></a>本地 Job 准备 | 已观察到 Job 创建、Trial 排列、钩子注册、lock 和 YAML 解析。源码改动后用同一批输入复查。 | [06 · 凭证预检](../../investigations/06-agent-credential-preflight/README.md) · [09 · Trial 计划](../../investigations/09-trial-plan/README.md) · [10 · Job lock](../../investigations/10-job-lock/README.md) · [18 · 示例配置](../../investigations/18-example-configs/README.md) |
| <a id="runtime"></a>CLI rollout | 短名发现、命令启动环境、受控 Trial 的正常/取消和脱敏已验。真实 CLI 要验请求落点、清理和最终已提交的 manifest。 | [07 · 请求路由](../../investigations/07-agent-routing/README.md) · [08 · 输出脱敏](../../investigations/08-trial-output-redaction/README.md) · [11 · Trial 事件](../../investigations/11-trial-events/README.md) |
| <a id="training"></a>训练接入 | 相同四组输入在三版得到相同的 Dressage 选分、失败码和训练标记。0.25 和 0.26 对 Agent 非零退出的评测有效性不同。真实队列的受控重试已核对最终 ID；完整训练分区、整组重试及 Slime 入口待验。 | [U50 三版判定](../../usage/结果、样本与最终选择/U50-从%20trial%20与%20step%20的%20exception_info%20生成训练失败记录.md#u50) · [12 · 结果原文](../../investigations/12-reward-validity/README.md#evidence) · [13 · 最终 attempt](../../investigations/13-final-attempt/README.md) |
| <a id="network"></a>受限网络与工具 | 在准备支持的任务阶段和 harness 上核实实际网络约束及 Web 工具开关。 | [14 · 阶段网络策略](../../investigations/14-phase-network-policy/README.md) · [15 · Web 工具](../../investigations/15-web-tools/README.md) |
| <a id="e2b"></a>E2B 云端 | 两份随仓 Job 已验配置解析。本机 E2B SDK 导入成功，Dockerfile 路径缺少 dockerfile-parse。云端复验前先安装完整 extra。评审若要确认 E2B rollout，先跑一题并观察 Gateway、奖励与回收。远端训练和跨周期续租分别按承诺补证据。 | [16 · 单题云端验收到哪里](../../investigations/16-e2b-template/README.md#cloud-review) · [17 · E2B 续租](../../investigations/17-e2b-renewal/README.md) |
| <a id="checkpoint"></a>已有 checkpoint | 两题的 0.26 同版恢复成功；同种子从 0.18 跨版被 source_digest 阻止。发布说明应明确这类旧 checkpoint 的处理。 | [19 · checkpoint 摘要与对照](../../investigations/19-checkpoint-digests/README.md) |

U38 另复现一个升级前已有的后端限制。Harbor 0.18、0.25、0.26 各跑一次停止后保留，三次均丢失会话工作文件。本 PR 的本地路径按正常清理验收，保留工作区的支持决定在问题 20 单列。[问题 20](../../investigations/20-bwrap-stop-delete/README.md#evidence)

<a id="acceptance"></a>

## 什么证据足以提交评审

1. **修复前后用相同输入。** 问题 01、02、21 分别附工厂、回收和独立 verifier 启动的修前修后结果。单列问题 03 的夹具验证。
2. **从干净环境安装并核对 `harbor==0.26.0`，再跑集成套件。** 记录通过、失败、跳过和排除项。已有三版修前记录使用同一 Dressage 基线，每版各排除 8 项端到端测试。[复现命令与历史输出](../../tools/reproduce.md#suite)
3. **附 0.26.0 上的入口运行结果。** CLI 路径看请求、事件和清理，训练路径看 Trial 结果、分组和最终采纳。云端或恢复用例尚未执行时，明确写出验证边界。

<a id="handover"></a>

### 交给维护者时还要写清楚什么

| 维护者要判断什么 | 这次 PR 怎么交代 |
| --- | --- |
| 哪份代码实际通过了测试？ | 在修后结果旁记录 Dressage 提交、实际安装的 Harbor 版本、命令和排除项。把本地工厂、日志和 verifier 回归随修复放进上游默认套件。固定基线的 GitHub workflow 在推送 main 或手动触发时发布镜像，默认 pytest 排除 8 项 Harbor E2E。评审时单列实际跑过的入口。[镜像工作流](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/.github/workflows/docker.yml#L1-L8) · [原套件执行范围](../../investigations/original-test-audit.md#suite) |
| 使用者拿到的安装包能否运行？ | 从修后提交构建 wheel，在干净的 Python 3.12 环境安装 Harbor extra，运行 `python -m pip check` 并由 CLI 按短名加载插件。仓库的 Dockerfile 安装 `.[transfer-queue]`。若 PR 承诺现成镜像能运行 Harbor，还需在对应镜像中核对实际安装步骤和版本。[修前 wheel 的实测](../../investigations/04-version-checks/wheel-output.txt) · [镜像安装步骤](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/docker/Dockerfile#L67-L68) |
| 已经在跑的实验怎样切换或退回？ | 建议 0.26 首次验证使用独立输出目录，保留旧环境、题目清单、哈希种子与原 checkpoint。已测两题样例在 0.18 同种子下可恢复，用 0.26 读取会被拒绝。发布说明写明已验证的组合。若承诺跨版续训，再核对恢复后的下一组题目、游标及训练状态。[恢复实验](../../investigations/19-checkpoint-digests/README.md#checkpoint-replay) · [题集选择差异](../../investigations/23-local-dataset-selection/README.md) |

逐条核对准备承诺的入口及其下游观察。DAPO 的题目读取与奖励文件解析已有三版输出，完整版 Trial 仍有独立验收。修复后把新提交与同输入的观察回写到对应用法。 [版本验收边界](../../usage/README.md#coverage) · [DAPO 奖励文件](../../usage/题目文件与可选后端/U58-Harbor%20Verifier%20读取运行产生的%20reward.json.md#u58)

## 本轮评审记录

- 2026-11-18　已对照 20 个问题所引的固定版本原文和现存实验材料。01 和 02 的修前失败、03 的夹具对照已有输出，修后端到端结果待取得。这三页是本轮建议的人审入口。[01 的版本对照](../../investigations/01-environment-preflight/README.md#evidence) · [02 的复制错误](../../investigations/02-output-mounts/README.md#evidence) · [03 的补丁与测试](../../investigations/03-verifier-fixture/README.md#evidence)
- 2026-11-18　收窄 11 的取消验收。正常 END 预期提交一次，已标记取消的 attempt 预期提交零次，两条路径都要观察路由关闭。依据是 Dressage 的取消分支与 `finally`，实测仍停在回调注册。[11 的改判及原文](../../investigations/11-trial-events/README.md#history)
- 2026-11-18　重新从两个 Git 版本反查接入点，补入构造期回调和上下游验收。问题 12 同输入双版本实测通过；问题 11 增加 END 对象身份的观察，正常与取消的实际时序继续待验。[源码与产出交接](../../archive/integration-inventory.md#coverage) · [12 的原始结果](../../investigations/12-reward-validity/README.md#evidence)

- 2026-11-18　归档的源码位置现可按稳定编号反查三个版本的输入与产出。已取得 DAPO 版本门槛、文件交接和中间版 TrialResult 的观察。非零退出的评测有效性存在版本差异，Dressage 的训练判断在此例保持一致。 [用法入口](../../usage/README.md) · [U03 版本检查](../../usage/启动与配置/U03-DAPO%20命令的%20check_runtime%20读取同一包版本.md#u03) · [U50 结果判断](../../usage/结果、样本与最终选择/U50-从%20trial%20与%20step%20的%20exception_info%20生成训练失败记录.md#u50) · [U58 奖励文件](../../usage/题目文件与可选后端/U58-Harbor%20Verifier%20读取运行产生的%20reward.json.md#u58)

创建上游 PR 后，在本页补 GitHub 链接、实际修复提交和修后测试结果。某项判断发生变化时，把新证据追加到对应问题的「判断记录」。[全部问题](../../README.md#investigations) · [GitHub 的评审说明](https://docs.github.com/en/pull-requests/concepts/helping-others-review-your-changes)
