# Dressage 使用 Harbor 的逐项兼容记录

每项用法的修后验收只针对 Harbor 0.26.0。三版表用 0.18.0 作升级前基线、0.25.0 作历史对照。按编号打开，就能查到**上游传了什么、Harbor 能否接受、下游实际拿到了什么**。Harbor 反向调用 Dressage 时也按这个顺序看。多个源码位置共同完成一次交接时共用编号。 [全部源码位置与编号](source-index.md#locations)

**第一次审核先看 U34 和 U44。** U34 在工厂传参时失败，后端第一行没有执行。U44 在旧版和目标版都返回 `None`、留下同一份日志，只有查看复制次数和 Trial 错误日志才发现分支改变。要看一次成功的文件交接，可以打开 U58，对照 `reward.json` 的 1 和 0。 [U34 工厂预检](环境构造与生命周期/U34-EnvironmentFactory%20调用%20DressageEnvironment.preflight.md#u34) · [U44 挂载查询](环境执行、文件与挂载/U44-Trial%20回收前查询挂载是否与宿主目录对应.md#u44) · [U58 奖励文件](题目文件与可选后端/U58-Harbor%20Verifier%20读取运行产生的%20reward.json.md#u58)

<a id="routes"></a>

## 按实际交接查表

核对本次检测的进度，可以直接看[已复现的问题与归属](#findings)和[七组用法还缺的运行证据](#remaining)。

| 用法 | 打开这一组 | 能查到什么 |
| --- | --- | --- |
| U01–U10 | [启动与配置](启动与配置/README.md) | Dressage 指定什么版本？两个入口加载什么？哪些 Job 字段用于恢复？ |
| U11–U22 | [Job 与 Agent 路由](Job%20与%20Agent%20路由/README.md) | Harbor 收到具体哪份配置？Dressage 取到的 Job、Trial 顺序和 Agent 路由是否对得上？ |
| U23–U30 | [Trial 事件与目录](Trial%20事件与目录/README.md) | 六个回调何时登记？运行中会拿到哪个 Trial 的 ID、结果和目录？ |
| U31–U38 | [环境构造与生命周期](环境构造与生命周期/README.md) | Harbor 怎样构造、预检、启动并停止 Dressage 后端？ |
| U39–U47 | [环境执行、文件与挂载](环境执行、文件与挂载/README.md) | 命令的返回值和日志、产物的实际落点正确吗？ |
| U48–U56 | [结果、样本与最终选择](结果、样本与最终选择/README.md) | Harbor 给出的分数和最终尝试，到了 bundle、训练样本与评测结果里是否仍一致？ |
| U57–U61 | [题目文件与可选后端](题目文件与可选后端/README.md) | Harbor 能读哪些生成的题目和分数文件？哪些后端行为还需要访问真实服务？ |

<a id="dependency-tests"></a>

## 哪些测试写出了 Dressage 对 Harbor 的依赖？

同一个 `TrialResult`，从 Harbor 看是产出，从 Dressage 的 `commit_attempt(trial_result=...)` 看就是输入。读测试时先找交给对方的对象，再找断言里实际检查的字段。

| 方向 | Dressage 原有测试写出了什么 | 升级时用真实 Harbor 核到了哪里 |
| --- | --- | --- |
| Dressage → Harbor，提交 Job 配置 | `test_temporary_job_contract` 用测试对象构造临时配置，断言并发数、各题的 `source is None`，以及 bwrap 环境类的 `import_path`。 [原测试的调用与断言](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_execution.py#L467-L482) | U12 的探测把 Dressage 生成的真实 `JobConfig` 交给 `await Job.create(config)`。三版都能用这道本地题创建 Job 和 lock，观察到此为止。 [调用处](../investigations/10-job-lock/probe.py#L32-L38) · [三版输出](../investigations/10-job-lock/job-lock-output.txt) |
| Harbor → Dressage，消费 Trial 的评分 | 测试夹具给出 `verifier_result.rewards={"reward": 1.0}`，插件测试断言末段样本的 `reward` 等于这份字典。 [夹具的输入](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/conftest.py#L80-L95) · [样本断言](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_execution.py#L104-L114) | U49 的探测用真实 Harbor 结果对象并指定评分。给 `reward=0.75` 和 `aux=0.25`，Dressage 选中 0.75。只给 `aux`，则记录 `REWARD_MISSING`，该次尝试不可训练。 [四组输入](../investigations/12-reward-validity/result_contract_probe.py#L56-L72) · [消费结果的断言](../investigations/12-reward-validity/result_contract_probe.py#L78-L109) · [0.26 输出](../investigations/12-reward-validity/result-contract-output.txt#L3-L7) |

评分探测验证 Dressage 怎样消费给定的结果。Harbor 队列实际重试后，最终 `JobResult` 里选中的 ID 是否一路对应到训练样本和 manifest，由问题 13 验收。上轮补的 U34 属于另一处交接，测的是 Harbor 工厂给 Dressage 后端传入的预检参数。[问题 13](../investigations/13-final-attempt/README.md) · [U34 工厂回归](../investigations/01-environment-preflight/test_factory_preflight.py)

升级前原套件由 pytest 收集到 74 个用例（含参数化展开），默认执行 66 个。两版复跑都记录了真实 Harbor 与 Dressage 方法分别被多少用例进入。按调查项反查时，可以看到哪些用法只有局部断言、哪些还缺完整链路的运行证据。[原套件的规模和实测](../investigations/original-test-audit.md#suite) · [逐问题反查表](../investigations/original-test-audit.md#issue-map)

<a id="replay"></a>

## 怎样在原调用中验证一项

1. **固定场景。** 选一项，从同一个业务入口，用相同的题目、配置和数据分别运行 0.18.0 与 0.26.0。0.25.0 的已有输出用于定位变化从哪版开始。每份记录注明实际经过的调用方，以及使用了哪些替身。
2. **只启用这项的两个观察点。** 在①看原调用方交出的参数。在②看下一方实际消费的值，或查看文件、异常、状态变化。页面列出的 Harbor 行号定位 0.26.0，旧版从版本表进入。一次运行内可以核对对象身份；跨版本对照时用题目名、尝试序号等稳定字段匹配，时间戳和运行时生成的 ID 可各自不同。
3. **让结论可以复验。** 单步调试适合定位第一个分歧。并发、取消、重试时，用 Trial ID 过滤日志或计数，保留事件顺序，避免暂停整个进程改变时序。把影响兼容性的观察写成可重复执行的断言，保存实际值和证据链接。没有执行到的下游注明“未到达”。

**怎样读证据。** 每项先给 Dressage 原行和两个观察点，再列三个版本的输入、输出及下游行为。观察点用于下次回放。“实测”对应列出的输入和调用路径，“源码吻合”表示此处尚待运行。“登记了回调”和“事件触发后回调收到结果”分别取证。 [一次原调用的三版输出](../investigations/02-output-mounts/trial-log-recovery.txt) · [复跑方式](../tools/reproduce.md#run-probes)

<a id="coverage"></a>

## 哪一种完整性已经核对过

| 核对的对象 | 本轮能确认什么 | 尚待取得的证据 |
| --- | --- | --- |
| 固定 Dressage 源码的扫描结果 | 扫查 341 个 Git 跟踪文件。33 个文本命中文件都有用途说明，归档的 191 个不同源码位置都有用法编号或排除理由。 | 配置动态指定的外部类、自定义任务和运行时事件还需具体输入。 [逐处对照](source-index.md) · [原始扫描及规则](harbor-call-sites.md) |
| 版本输入与下游输出 | 61 项用法都有三版表。同一组 TrialResult 在三版均已实测，Agent 非零退出时 Harbor 0.25 判分数无效、0.26 判有效，Dressage 两版都拒绝训练。 | 受控 Trial 正常和取消已验；真实 harness 请求、受限网络与完整分区仍待验。 [U50 结果与训练判定](结果、样本与最终选择/U50-从%20trial%20与%20step%20的%20exception_info%20生成训练失败记录.md#u50) · [U28 END 事件](Trial%20事件与目录/U28-Job.on_trial_ended%20登记%20END.md#u28) |
| 这次升级能否交付 | 原始基线的 0.26 默认集成套件为 63 通过、3 失败、8 项端到端测试排除。三版 DAPO 题目和奖励文件另有本地实测。 | 修后预检、独立 verifier、真实 CLI、完整分区及承诺支持的云端各有验收入口。 [基线输出](../investigations/00-version-target/pytest-replay.txt) · [文件交接输出](evidence/dapo-files.txt) · [PR 合并条件](../prs/001-harbor-026-compatibility/README.md#acceptance) |

<a id="findings"></a>

## usage 已经发现的问题都进调查项了吗？

本轮逐项读了 61 张用法表的三版结果和「接续」，对出现的失败、行为变化与限制逐项核实调查项的正文和运行输出。此前 U38 记录了停止后保留的疑问，关联的 02、03 分别验日志和夹具。补跑六次后已单列为 20。第二轮又从相同输入沿下游追出了四个独立问题，详见[复查结论与运行边界](../investigations/upgrade-audit-026.md)。[U 与调查项的逐项反查](../investigations/original-test-audit.md#issue-map)

| 用法中观察到什么 | 在哪个调查项作决定 |
| --- | --- |
| U34 的 0.26 工厂传入 `kwargs`，后端预检尚未执行便报错。 | [01 工厂预检](../investigations/01-environment-preflight/README.md#evidence) |
| U42、U44 的默认直挂日志在 0.26 被复制到自身，Trial 记录错误仍标记已下载。显式改绑到另一目录时，0.26 能交付，0.18 会漏交。 | [02 两种挂载的三版对照](../investigations/02-output-mounts/README.md#mount-matrix) |
| U31、U41 涉及的独立 verifier 夹具仍按旧方式传挂载。U01–U03 涉及的依赖声明、运行时门槛和 DAPO 工具仍选或要求 0.18。 | [03 夹具](../investigations/03-verifier-fixture/README.md#evidence) · [04 版本门槛](../investigations/04-version-checks/README.md#evidence) |
| U38 的 bwrap 会话在 `delete=False` 时仍丢失工作文件。旧版和目标版表现相同。 | [20 停止后保留](../investigations/20-bwrap-stop-delete/README.md#evidence) |
| U31、U37 的独立 verifier 取得环境材料目录，Dressage 仍把它作为测试目录。 | [21 启动输入](../investigations/21-separate-verifier-input/README.md) |
| U50、U53 涉及的物理尝试数随新版异常判定改变。 | [22 Harbor 重试](../investigations/22-retry-policy/README.md) |
| U11 的本地 dataset 按上限截取时会选到不同题目。 | [23 本地题目选择](../investigations/23-local-dataset-selection/README.md) |
| U21 显式连接设置会改变 Claude Code 最终启动地址或凭证；U10 在同输入上读取旧 checkpoint 会因摘要差异被拒绝。 | [07 命令启动环境](../investigations/07-agent-routing/README.md) · [19 五次恢复](../investigations/19-checkpoint-digests/README.md#checkpoint-replay) |
| U04、U22 还会产生宿主进程遥测；已实测 CLI 在发送前构造事件以及禁用分支。 | [24 宿主遥测](../investigations/24-host-telemetry/README.md) |

有些版本变化已能解释。U40 的新 skills 目录已读回文件，U18 在本地题上生成 v3 lock，U50 的 Harbor 分数有效性变化后 Dressage 的训练判定仍相同。U48 的 `Task.checksum` 弃用提示在旧版也出现，结果元数据的逐字段回读仍待验。[05 技能目录](../investigations/05-skills-upload/README.md) · [10 Job lock](../investigations/10-job-lock/README.md) · [12 评分和元数据](../investigations/12-reward-validity/README.md#evidence) · [19 摘要与恢复](../investigations/19-checkpoint-digests/README.md#evidence)

<a id="remaining"></a>

## 七组用法还缺哪些运行证据？

每组按 0.26 的实际观察划界。一条 U 可以同时有本地输入的结果和另一条待验分支。下面从每组指出下一处有价值的观察，单项的输入与实测结果仍在原用法表。

| 范围 | 已经看到的结果 | 还要从真实入口看到什么 |
| --- | --- | --- |
| U01–U10 启动与配置 | 旧运行时门槛拒绝目标版，两份示例 YAML 能解析，短名解析及两题的跨进程 checkpoint 读写已验。 | 干净安装后跑 CLI；从 Slime 加载数据源、rollout 并验证训练续跑。 [启动与配置](启动与配置/README.md) |
| U11–U22 Job 与路由 | 本地 Job、八份 Trial 配置的排列、Claude Code 命令启动时的连接选择、目录题集截取与本地 lock 均有观察。 | 真实 Agent 发第一条请求时命中哪个 Trial 的路由；并发键是否生效；远程 dataset 是否正确进入分区与 lock。 [Job 与路由](Job%20与%20Agent%20路由/README.md) |
| U23–U30 Trial 事件 | 真实 Job 与受控 Trial 已观察正常及取消时的回调、关闭次数和 END 文件状态。 | 让实际 harness 经过 Gateway，核对完整产物、路由清理及并发取消。 [Trial 事件](Trial%20事件与目录/README.md) |
| U31–U38 环境生命周期 | 本地 bwrap 能构造及启动，工厂预检失败已复现。两种停止配置的目录和工作文件均已核对。 | 修后从工厂重放预检；多步网络策略、非法题目输入和带活动进程的停止还有独立观察点。 [环境生命周期](环境构造与生命周期/README.md) |
| U39–U47 执行和文件 | 单文件、skills、日志挂载与 bwrap 独立评测有实测。即使 reward.json 已写入，Verifier 也会因挂载查询不匹配而回收失败。 | 修后重放两种日志挂载；命令超时或取消、显式用户、同名环境变量及输出订阅的实际值待验。 [执行和文件](环境执行、文件与挂载/README.md) |
| U48–U56 结果与训练 | 已验证四种评分输入，以及真实队列重试后的最终 Trial ID、manifest 与两段 Sample。 | 从完整分区走到 Slime 的训练和评测入口，核对分组、返回类型和 metrics。 [结果与最终选择](结果、样本与最终选择/README.md) |
| U57–U61 题目与可选后端 | 本地评分脚本对两种答案得到 1、0。E2B 模板资源键、续租调用和停止在 SDK 替身上已验。 | 完整 Trial 中的 verifier、受限网络下的实际工具选项待验；E2B 的启动、跨周期续租与回收需要云端运行。 [题目与可选后端](题目文件与可选后端/README.md) |

<a id="resume"></a>

## 下次怎样接着审

本次升级先从真实工厂预检和日志回收进入。PR 的测试表把关联 U 放在同一行，并列出已经跑到哪里、下一次要断言什么。默认直挂和显式改绑在三个版本下都返回 `None` 并标记完成，只有核对目标文件、复制次数和错误日志才能分清结果。[本次四组测试的执行顺序](../prs/001-harbor-026-compatibility/README.md#test-order) · [两种挂载的实测](../investigations/02-output-mounts/README.md#mount-matrix)

1. **相同版本、相同输入和路径**，按编号打开原始输出，读到该项的“接续”。只需新的观察时，把新输出存入关联调查项，更新这张表相应版本的输入或输出判断。健康用法的独立实验可存到 `usage/evidence/`。同一份输出可供多处引用。 [U58 实测与下一观察](题目文件与可选后端/U58-Harbor%20Verifier%20读取运行产生的%20reward.json.md#u58)
2. **代码、版本或场景变化**，先查两个固定提交之间与这项有关的差异，记录新提交、具体输入和观察到的值。旧版输出继续作对照。新发现的交接分配下一个空闲编号，补到对应主题和本页索引。例如第一组后来新增 U62，可写成 `U01–U10、U62`。沿调用链补查的入口也能登记发现来源。更新基线或发现规则时再复算整仓。 [补查入口](source-index.md#follow-up) · [扫描复算方式](../tools/reproduce.md#surface)
3. **交接记录与问题决定**各有固定入口。这里按用法查输入输出。遇到不匹配，把成因、修法和验收决定记到一个对应问题。PR 页只引用本次承诺的用法和证据。在升级目录运行 `python3 tools/check_docs.py` 即可检出遗漏的归档位置、缺失的版本行和失效的本地链接。 [问题审核入口](../investigations/README.md) · [PR-001](../prs/001-harbor-026-compatibility/README.md) · [复核命令](../tools/reproduce.md#provenance)

**版本依据**　2026-11-18。Dressage 固定 `3e3142f`，Harbor 0.18.0 为升级前基线，0.25.0 用于定位变化，0.26.0 为目标。新版 Job 探测在进程内临时放行旧版本检查。直接安装与正常启动的判定保留在 U01、U02。 [Dressage 提交](https://github.com/Accio-Lab/Dressage/commit/3e3142fe8ea07e4504c3b20a936a4c201a3de44c) · [U01 安装声明](启动与配置/U01-安装%20Dressage%20的%20Harbor%20extra.md#u01) · [U02 运行时检查](启动与配置/U02-require_harbor_runtime%20读取并检查发行包版本.md#u02) · [原始探测](../investigations/09-trial-plan/probe.py)
