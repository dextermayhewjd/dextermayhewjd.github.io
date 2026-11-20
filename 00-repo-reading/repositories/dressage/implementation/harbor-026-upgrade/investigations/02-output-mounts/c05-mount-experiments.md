# C05 挂载实验记录

第一轮由 C02 支持日志直挂，C05a 准备沙箱自有输出目录。手动挂载空宿主目录的 C05b 已暂停。本节保留普通日志用例和修前与候选对照，后面的历次实验供回查。[第一轮范围](../../prs/001-harbor-026-compatibility/README.md#current-status)

<a id="original-integration-parity"></a>
<a id="c05b-empty-mount"></a>

## 手动空 `/logs` · 普通 Oracle 日志的版本对照

相同输入为一个真实 bwrap 单步 Oracle Trial，唯一显式绑定是可写的 `host-logs/ → /logs`，使用各版默认挂载策略。题目在 `public` 网络模式下只做本地文件操作。解法在 `/logs/agent/run/` 写普通文件 `probe.log`，向 `/app/answer.txt` 写入 4，打印 `solved`。Verifier 检查答案后向 `/logs/verifier/reward.json` 写入奖励 1。[可复跑的 Oracle 用例](c05b_log_delivery.py)

| Harbor 与 Dressage | `host-logs/` 初始内容 | Trial 的 `agent/oracle.txt` | Trial 的 `agent/run/probe.log` | verifier 奖励及收尾结果 |
| --- | --- | --- | --- | --- |
| 0.18.0 原版 `3e3142f` | 空 | `b"solved\n"` | `b"fresh probe\n"` | 1 |
| 0.26.0 C05a `8f51d19` | 空 | 缺失 | 缺失 | 无奖励，`DownloadVerifierDirError` |
| 0.26.0 C05a `8f51d19` | 预建 `agent/`、`verifier/` | `b"solved\n"` | `b"fresh probe\n"` | 1 |
| 0.26.0 C05a 加空目录候选 | 空 | `b"solved\n"` | `b"fresh probe\n"` | 1 |

0.18 将三个自动输出子挂载和用户的 `/logs` 父挂载一起交给 Dressage。bwrap 先挂父目录、再挂子目录，日志直写 Trial 目录。0.26 默认关闭自动挂载，空宿主源遮住沙箱文件树，Oracle 首次打开日志时缺 `agent/`。表中比较的是 Trial 收尾后的文件字节。预建两目录的结果适用于这道普通日志题。[0.18 提供的挂载](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L1164-L1186) · [Dressage 原版的挂载顺序](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L620-L626) · [0.26 选择宿主挂载](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L329-L340)

**复跑普通日志用例。** 在有 bwrap 运行权限、Dressage 本地后端依赖和对应 Harbor 版本的 Linux 环境里，从阅读仓库根目录运行。下例使用 Harbor 0.26.0。基线应在 `DownloadVerifierDirError` 处失败，只在临时副本应用历史候选后应通过。核对原版时，使用 Harbor 0.18.0 和 `3e3142f` 的源码副本，运行同一个 pytest 用例即可。[历史候选补丁](c05b-empty-log-mount.patch)

```bash
evidence="$PWD/00-repo-reading/repositories/dressage/implementation/harbor-026-upgrade/investigations/02-output-mounts"
c05_work=$(mktemp -d)
git -C /home/hongshi/projects/Dressage-harbor-0.26 archive 8f51d19 dressage pyproject.toml | tar -x -C "$c05_work"
cd "$c05_work"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
python -m pytest -q --rootdir="$PWD" --confcutdir="$evidence" "$evidence/c05b_log_delivery.py"
git apply --check "$evidence/c05b-empty-log-mount.patch"
git apply "$evidence/c05b-empty-log-mount.patch"
python -m pytest -q --rootdir="$PWD" --confcutdir="$evidence" "$evidence/c05b_log_delivery.py"
```

<a id="runtime-agent-log-link"></a>

### 历史对照 · 运行时创建的跨目录链接

此前对照还记录了 Agent 在运行中创建 `run -> ../artifacts` 的结果。0.18 原版和空目录候选均得 1 分，探针字节均落在 `artifacts/logs/artifacts/probe.log`。两版回收的 `agent/run` 都是原相对链接，从 Trial 的 `agent/run/probe.log` 读取均失败。[Dressage 原有的目录下载](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L468-L479) · [Harbor 0.26 的发布产物落点](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/paths.py#L216-L243)

**插件职责另验。** 原版与 0.26 候选各复跑 Dressage 已有的三条用例，均为 3 过。它们分别检查同次轨迹和奖励组成可训练 Sample、取消后零提交、重试后选中最终尝试。这组使用受控 Job、Gateway runtime 和 Proxy。普通日志用例调用真实 `Trial.create()` 和 `Trial.run()`，直接指定 bwrap 后端。真实模型请求经过 Gateway/Proxy 再用于训练的端到端验收仍待进行。[原版训练交接用例](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_execution.py#L64-L122) · [取消与重试用例](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_execution.py#L168-L275)

<a id="c05b-plain-comparison"></a>

## 早期窄版对照 · 宿主已有空子目录时也尝试初始化

**当时用两条标准挑选候选。** ① 空的可写宿主目录挂到 `/logs` 时，真实 Oracle Trial 应交付日志和奖励。本笔在其他布局新建的输出也须能原样回收，否则在启动时报告错误。② 输入和题目相同时，基线原本正确交付的文件，升级后仍须逐字节正确交付。Oracle 会单独下载 `oracle.txt`，所以还要检查 Agent 自己写在日志树里的文件。

**三个版本用了同一份任务和隔离网络。** 基线为 `8f51d19`，现有候选为个人升级工作树的未提交快照，窄版从基线单独修改。均加载 Harbor 0.26.0，分别使用独立的宿主目录。主测试比较 Trial 目录和宿主目录中 `oracle.txt` 的 `solved\n` 与 `run/probe.log` 的 `fresh probe\n`，并确认回收的 `run` 是真实目录。准备空挂载时，还比较了 verifier 的奖励文件和发布的 `note.txt`。[窄版实现与六个 Oracle 回归](c05b-plain-log-mount.patch)

| Oracle 用例 | C05a 基线 | 现有候选 | 独立窄版 |
| --- | --- | --- | --- |
| 沙箱自有输出 | 两份日志正确，奖励 1 | 同基线 | 同基线 |
| 空的可写父挂载 | 两份都缺，无奖励 | 两份正确，奖励 1 | 两份正确，奖励 1 |
| 父挂载已有空 `verifier/` 和普通 `README` | 两份都缺，无奖励 | 两份正确，奖励 1 | 两份正确，奖励 1，原 README 字节不变 |
| ② 后挂的原目录遮住先前的子挂载 | 两份正确，奖励 1 | 启动报 `ValueError` | 两份正确，奖励 1 |
| ⑤ 先声明缺失的只读输入，后声明其可写子目录 | `NotADirectoryError`，未创建输入 | 输入被创建，奖励 1 | 与基线相同，输入仍缺失 |
| 已有 `agent/run → ../artifacts`，目标尚不存在 | 无法写入 probe，无奖励 | 宿主写出 probe，奖励 1，Trial 只收回链接 | 与基线相同；保留链接，未新建其目标 |

**窄版为什么能收住？** 保留 C05a 按声明顺序处理显式 bind 的逻辑。只在唯一宿主挂载是可写 `/logs`，且待准备输出均为直接子目录时，才尝试补建。这个前提下，Harbor 合并清单中的 `/logs` 是用户挂载，其余可写目标才是 Harbor 声明的输出。已有的输出若含文件、链接或无法检查，交还原流程；普通的无关 README 不妨碍初始化。新目录按宿主父目录描述符创建，验证读、写和进入权限。额外实测了空声明、仅 verifier、含模拟用户的四个声明，每个新目录均通过沙箱写入和整目录下载比对。把一个新建的必需目录限制为 `0333` 时，启动明确报错，解除限制后重试可原样回收。这组是环境接口测试，未调用模拟用户模型。[补充对照用例](c05b_plain_controls.py)

**三项既有缺陷单独跟踪。** ① 日志树内的链接指向树外，③ 宿主不能列举 `0333` 的日志目录，两者在基线和窄版都得了 1 分，但只收回 Oracle 日志，缺少 Agent 的 probe。④ 间接挂回自身的只读工作目录在两版都未能写出日志和奖励。记录启动前后宿主输出条目，窄版三例均未增加相关目录。这三个用例通过的是“观察到同一缺陷”的断言。[三项观察与启动记录](c05b_plain_controls.py)

**选择窄版要接受哪些差别？** 将现有候选原有的 12 个 Oracle 断言原样对照，基线通过 5 个，现有候选通过 12 个，窄版通过 6 个。窄版余下 6 个的实际结果与基线相同。其中 3 个是现有候选扩展的得分场景（额外的嵌套挂载点、`artifacts` 已是文件、`artifacts` 已是悬空链接且缺少必需目录），2 个是现有候选会更早拒绝的布局（不可访问的 Agent 目录、树外挂载经链接落入日志树），1 个是无关挂载仍然得到 1 分但没有额外创建 `artifacts/`。最后这一例单看通过数会误判为丢了评分。

**验证范围。** 六项主回归在窄版全部通过。另有四项声明及重试对照通过，三项既有缺陷复核通过。窄版完整环境测试 21 项通过，无跳过；Harbor 集成目录 82 项通过、1 项失败、8 项未选中，失败项仍断言安装了 0.18.0。整仓套件在收集时有六处导入错误，五处缺少 `torch`，一处缺少 `get_reward_context`。本轮没有运行真实模型或 Gateway 端到端任务。

复跑时在 `8f51d19` 的一次性副本中应用窄版补丁，使用已安装 Harbor 0.26.0 的解释器。在副本根目录运行以下命令，`evidence` 是本调查目录的绝对路径。比较现有候选时保留其代码，将同一份测试作为外部用例运行。实验开始和结束时，个人工作树的 `git diff --binary HEAD` SHA-256 均为 `eb1425660e50126618da6b01c26c34ba04686fee083ee2be90388ce444710ee7`。

```bash
git apply --check "$evidence/c05b-plain-log-mount.patch"
git apply "$evidence/c05b-plain-log-mount.patch"
python -m pytest --confcutdir=tests/integrations/harbor tests/integrations/harbor/test_environment.py -k test_oracle_trial_delivers_logs
PYTHONPATH="$PWD/tests/integrations/harbor:$PWD${PYTHONPATH:+:$PYTHONPATH}" python -m pytest --confcutdir="$evidence" "$evidence/c05b_plain_controls.py"
```

<a id="cli-mount-reachability"></a>

## 2026-11-20 · 用户能否通过真实配置遇到这两个问题？

用 Harbor 0.26.0 的 `harbor trials start --config trial.json` 指定 Oracle 和 `DressageEnvironment`。有显式挂载的两组再传 `--mounts` JSON 数组，自动挂载保持默认关闭。可写绑定省略 `read_only`，只读绑定使用 `read_only: true`。同一道题在断网沙箱写 `/app/answer.txt`，Verifier 检查答案并写 `reward.json`，题目没有声明 artifact。每种配置在各版本中分别使用独立空目录，验收终点为 Trial 的 `agent/oracle.txt` 和 `result.json`。

| 用户的显式挂载 | 第一笔 `8f51d19` | 第二笔修正可选目录前 | 第二笔修正后 |
| --- | --- | --- | --- |
| 无 | 收到 `solved`，奖励 1 | 收到 `solved`，奖励 1 | 收到 `solved`，奖励 1 |
| 空的可写宿主目录绑定 `/logs` | 没收回日志，没有奖励，最终报 verifier 目录下载失败 | 收到 `solved`，奖励 1 | 收到 `solved`，奖励 1 |
| `/logs` 只读，已有 `agent/` 和 `verifier/` 两个挂载点，各绑定可写宿主目录，没有 `artifacts/` | 收到 `solved`，奖励 1 | 启动时报 `EROFS: /logs/artifacts`，没有日志和奖励 | 收到 `solved`，奖励 1，`artifacts/` 仍缺失 |

修正后三组的 `result.json` 都记录了 `exception_info = null`。两组显式绑定还逐字节比较了实际宿主日志和 Trial 收回的 `agent/oracle.txt`，内容相同。

**自动挂载和手动挂载，最终交付是否一致？** 在同一修后工作树上，用上述 Oracle 题另跑两次 CLI。第一轮只开 `auto_mounting=True`，第二轮用 `auto_mounting=False` 并显式绑定空的 `host-logs/ → /logs`。两轮 Trial 收回的 `agent/oracle.txt` 逐字节相同，且与第二轮的 `host-logs/agent/oracle.txt` 一致。两轮均无异常，奖励均为 1。这次比较的是 Agent 日志与 Verifier 奖励。

检查了 Harbor `v0.26.0` 的 `examples/configs/` 下 39 份 YAML 和 Dressage `8f51d19` 的 `examples/harbor/` 下 8 份 YAML。解析后均没有显式 `mounts` 配置项。两种配置都可通过公开 CLI 实际执行，随仓配置没有提供使用频率的证据。只读父挂载的回归依据是相同输入在升级前后的实际结果。此处“升级前”特指 C05 第一笔，同样使用 Harbor 0.26.0。[CLI 的挂载选项](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/cli/trials.py#L512-L524) · [显式挂载与自动挂载的选择](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/base.py#L329-L340)

<a id="start-only-result"></a>

## 早期工作树候选 · 启动时准备输出目录

本轮使用 Harbor 0.26.0、C05 第一笔 `8f51d19` 和同一套 Linux bwrap。生产改动位于 `environment.py`，回归位于 `test_environment.py`。

| 检查 | 实测结果 |
| --- | --- |
| 同一份环境测试跑在固定基线和升级工作树 | 基线 **18 过、6 败**，工作树 **24 过**。基线上只读父挂载的完整 Trial 可以得分，空可写父挂载的 Trial 缺少 `agent/`。 |
| 先加测试，再修可选目录 | 在第二笔原候选上，三种 Oracle 配置和三种必需日志目录配置合计 **5 过、1 败**。唯一失败是只读父挂载的 Oracle Trial 在启动时收到 `EROFS: /logs/artifacts`。修正后六项均通过。 |
| 通过 Harbor CLI 交付日志和奖励 | 默认、空可写父挂载、只读父挂载三组均回收日志并得到奖励 1。宿主日志、可选目录和逐字节检查见[上表](#cli-mount-reachability)。 |
| 整套默认 Harbor 集成测试 | 一次性副本中 **85 过、1 败、8 项未选中**。失败的是 `test_official_jobs_validate_with_harbor_018` 仍断言版本为 0.18.0，归 C06。 |
| Dressage 全仓测试 | 一次性副本在收集阶段有六处导入失败。五个模块依赖当前测试环境缺少的 `torch`，另一个模块导入 `get_reward_context` 失败。全仓通过情况待验证。 |

小例子说明了修改的位置。`/logs` 已绑定时，`start()` 在实际挂载布局内批量创建 Harbor 声明的子目录，等待成功后才设置 `_started`。这一步不依赖 Gateway socket。[直接调用 Harbor ensure_dirs 的对照实验](#ensure-dirs-probe)

<a id="c05b-precommit-review"></a>

### C05b 提交前评审 · 三条意见分别有什么证据？

| 评审发现 | 核对结果 | 提交前怎样判断 |
| --- | --- | --- |
| ① 新建目录后可能收回旧文件 | 已有 `visible/hidden` 实验说明传输限制。评审者提供的 `alias/run` 修前修后对照说明新增影响：在 `8f51d19` 上因目录缺失而写入失败，本轮修复前的候选能写出 `fresh`，下载却得到 `stale`。[旧限制的传输对照](#mounted-namespace-result) | 只对本笔需要新建的目录检查创建与回收的实际落点。落点不同则在创建前明确拒绝，同一宿主目录则保留。接受的布局要核对新写入与收回的字节一致。 |
| ② 可选目录遇到 `EACCES` 阻断原本得分的 Trial | 此前已在普通用户下复现目录准备函数以 1 退出。评审者随后补跑完整 Harbor 0.26 Oracle Trial。父目录以读写方式绑定、权限为 `0555`，已有 `agent/`、`verifier/` 可写。基线收回 `solved`、奖励为 1，本轮修复前的候选在创建缺失的可选 `artifacts/` 时因 `EACCES` 启动失败，无日志和奖励。 | 把这组输入固化为完整 Trial 回归。仅在确认可选目录缺失且无法创建的权限分支跳过，必需目录创建失败仍报错。把“确认缺失”和“权限不足无法判断是否存在”区分开。 |
| ③ 检查与创建之间存在竞态 | 静态核对确认 `resolve()` 和 `mkdir()` 分别解析路径。用户可以让多个 Trial 使用同一宿主 bind 源，每个 Trial 有独立 rootfs 不能保证 bind 独占。尚无实际越界创建的复现。 | 对支持的共享 bind，将路径遍历和创建锚定到已经验证的目录句柄，保持约定的挂载边界。以稳定目录下创建成功、无法保证边界时安全失败作为行为要求。 |

**原有回归为什么没发现？** C05a 的 Oracle 用例验证默认的沙箱自有目录。C05b 后来验证普通可写父挂载和显式只读父挂载，后者产生 `EROFS`。这些用例覆盖了正常日志交付，却没有把“别名下新建后写入，再下载比较新字节”串成一次操作，也没有让读写 bind 的宿主目录权限独立产生 `EACCES`。各用例使用独立临时目录，不能据此推断共享 bind 上的并发安全。

<a id="c05b-reviewed-result"></a>

### 本轮 C05b 的修前与修后对照

基线是已提交的 C05a `8f51d19`。下表的“修前”特指该基线上上一版未提交的 C05b。运行使用 Harbor 0.26.0、Linux 普通用户及真实的 bwrap 隔离网络。

| 输入或检查 | 本轮修前 | 本轮修后 |
| --- | --- | --- |
| 读写父挂载权限为 `0555`，已有可写的 `agent/`、`verifier/`，Oracle 不发布产物 | 完整 Trial 在创建 `artifacts/` 时以 `EACCES` 终止 | 完整 Trial 收回含 `solved` 的日志，与宿主日志逐字节相同，奖励为 1 |
| 缺失的输出经别名进入嵌套挂载 | 同源配置能写回 `fresh`。异源且回收侧为空的配置意外通过启动 | 同源写入及下载的内容均为 `fresh`。异源的空目录和含旧日志的目录均被拒绝，内层没有新建 `run/` |
| 共享 bind 的路径检查 | 检查后会重新按原始路径创建。评审依据是静态源码 | 逐级用 `O_NOFOLLOW` 打开目录，核对父目录身份后通过 `dir_fd` 创建。未运行并发替换实验 |

实际升级工作树的 `test_environment.py` 为 **28 过**。一次性副本运行 Harbor 集成套件为 **89 过、1 败、8 项未选中**，失败项 `test_official_jobs_validate_with_harbor_018` 仍断言安装版本为 0.18.0。整仓 pytest 在收集时遇到 6 个错误。缺少 `torch` 影响 `test_engine_rebalancing`、`test_mopd_loss`、`test_mopd_metrics`、`test_proxy` 和 `test_tq_training_hydration`。另一个是 `test_reward_registry` 无法导入 `get_reward_context`。

<a id="c05b-final-location"></a>

### C05b 复核 · 从能启动一直检查到能下载

同一 Harbor 0.26.0 和 bwrap 环境，检查 `start → exec 写入 fresh → download_dir`。基线 `8f51d19` 和上一版 C05b 的三项对照使用各自的临时目录。新增的正式测试覆盖下表四项，修改前四项失败，修改后四项通过。

| 日志配置 | 上一版 C05b 的行为 | 修后验收 |
| --- | --- | --- |
| 别名下再进入嵌套 bind，祖先相同，实际父目录不同 | 成功写入，下载时报 `NotADirectoryError` | 启动明确拒绝，内层没有新建 `run/` |
| 前一个输出刚创建目录，后一个输出通过别名看到它 | 成功写入，下载时报 `NotADirectoryError` | 核对最终目录后拒绝该别名 |
| bind 目标本身是符号链接，已有日志目录 | 基线能下载 `fresh`。上一版 C05b 在启动时报 `ValueError` | 能下载 `fresh` |
| 同一 bind 目标，日志目录需要新建 | 上一版 C05b 在启动时报 `ValueError` | 能创建目录并下载 `fresh` |

环境文件 **32 过**。实际升级工作树的 Harbor 集成套件 **93 过、1 败、8 项未选中**。失败项仍是 `test_official_jobs_validate_with_harbor_018` 要求安装版本为 0.18.0。

<a id="c05b-runtime-compatibility"></a>

### C05b 核对原有的运行环境

| 新增回归 | 修改前 | 修改后 |
| --- | --- | --- |
| `/logs/shared` 经符号链接指向 `/dev/shm`，用户将宿主目录显式挂到 `/logs/shared` | 准备阶段建立这条 bind 时目标不存在 | 真实 bwrap 环境中的 Agent 写入 `fresh`，下载得到相同字节 |
| 通过 PATH 选择 `/run/user/<uid>/…/bin/python3`，手动挂载空父目录 | 准备进程覆盖整个 `/run`，启动解释器时报文件不存在 | 使用独立临时目录，解释器成功启动，宿主日志目录下出现 `agent/` |
| 目录创建返回 `EPERM` | 可选 `artifacts/` 和必需 `agent/` 均导致失败 | 仅缺失的可选目录跳过。必需目录仍报告原错误码及路径 |

前两项使用真实挂载和隔离网络。第三项在准备函数的 `os.mkdir` 调用上注入错误，检验错误处理范围；本轮没有设置文件系统的 immutable 属性。新增四例从 **3 败、1 过** 变为 **4 过**。完整环境文件 **36 过**。实际升级工作树的 Harbor 套件 **97 过、1 败、8 项未选中**，失败项仍是 `test_official_jobs_validate_with_harbor_018` 的旧版本断言。一次性副本的整仓 pytest 仍因缺少 `torch` 和无法导入 `get_reward_context` 在收集阶段停止（6 项）。

<a id="c05b-mountpoint-and-probe"></a>

### 挂载点建立与可选目录探测的完整 Trial

使用真实 bwrap 和 Harbor 0.26.0。前两项的基线 `8f51d19` 均收回日志并得到奖励 1。以下是上一版 C05b 与这次修改的对照。

| Oracle 配置 | 修前 | 修后 |
| --- | --- | --- |
| `/logs/link` 指向 `../app`，嵌套 bind 需要在 Trial 文件树中建立 `/app/data` | 准备函数启动前，bwrap 因根文件系统只读而失败 | bwrap 建立挂载点后才将根目录切为只读。Oracle 日志与宿主文件逐字节一致，奖励为 1 |
| 可选 `/logs/artifacts` 经符号链接进入不可遍历目录，必需日志目录可写 | 初次探测权限错误导致启动失败 | 跳过该可选目录，收回相同字节的 Oracle 日志，奖励为 1 |
| 同样的不可遍历路径用于必需的 `/logs/agent` | Trial 终止，得到包装后的 RuntimeError | Trial 仍终止，明确报告 `PermissionError` 和 `/logs/agent`，没有评分 |

实际升级工作树的环境测试 **39 过**；Harbor 集成套件 **100 过、1 败、8 项未选中**。失败项仍为旧版安装断言。一次性副本整仓 pytest 收集时仍有 6 项错误，涉及缺少 `torch` 和无法导入 `get_reward_context`。

<a id="c05b-acceptance-boundary"></a>

### C05b 提交边界的修前与修后对照

| 验收输入 | 上一版 C05b | 修后 |
| --- | --- | --- |
| 不改宿主目录，重新启动同一份别名冲突配置 | 第一次拒绝。第二次放行，写入后下载报 `NotADirectoryError` | 即使第一次留下了 `run/`，两次都在启动时报出冲突路径 |
| 白名单模式，显式日志 bind 实际落在 Gateway 保留目录 | 准备阶段未报告 Gateway 冲突 | 输出是该 bind 本身或其子目录时，均以明确的 Gateway 冲突结束。检查发生在输出创建前 |
| `artifacts` 是普通文件或悬空符号链接，题目不发布产物 | C05a 两组都得 1 分，上一版 C05b 两组都报 `FileExistsError` | 两组均收回含 `solved` 且与宿主日志字节相同的文件，奖励为 1。原文件字节或链接目标保持原样 |

本轮五个定向用例修前全部失败，修后全部通过。环境测试 **43 过**。升级工作树的 Harbor 集成套件 **104 过、1 败、8 项未选中**，失败项仍是要求安装 Harbor 0.18.0 的旧断言。

<a id="c05b-log-tree-and-access"></a>

### C05b 最后一轮评审 · 已有目录能否写入，整棵日志能否收回

| 评审问题 | 验证方式 | 结果 |
| --- | --- | --- |
| ① 必需目录存在但不可写 | 在 bwrap 中分别使用只读挂载和权限为 `0555` 的宿主目录，原样启动两次 | 两次都在启动阶段报告权限错误。 |
| ② 日志树的子目录被另一挂载覆盖 | Agent 在子目录写入新内容，Harbor 从父目录 `/logs/agent` 整体下载 | 子挂载与回收位置同源时字节一致。不同源时启动报错。也覆盖沙箱自有父目录下的子挂载。 |
| ③ Gateway 挂载位置与事后解析的路径不同 | 保留 bwrap 的 Gateway 冲突测试，另外用合成的内核挂载表隔离验证检查逻辑 | 检查使用已经生效的挂载点。合成用例没有启动实际 Gateway。 |
| ④ 创建可选目录遇到空间或配额限制 | 向创建操作注入 `ENOSPC`、`EDQUOT`、`EPERM`，分别观察可选和必需目录 | 可选目录允许跳过，必需目录保留错误。这是故障注入，未耗尽真实文件系统。 |
| ⑤ 已有自指的可选链接 | 预置 `artifacts -> artifacts`，运行环境启动并读回原链接 | 启动成功，原链接保留。Harbor 0.26 在后续产物收集时仍会遇到循环链接，验收止于启动。 |

固定修前提交 `8f51d19`、Harbor 0.26.0。修复前的定向测试为 10 项失败、6 项通过。修复后的环境测试为 54 项通过。整个 Harbor 集成目录为 115 项通过、1 项失败、8 项未选中。失败项 `test_official_jobs_validate_with_harbor_018` 仍断言安装了 Harbor 0.18.0。

<a id="c05b-declared-outputs"></a>

### C05b 收窄检查 · 哪些目录属于这次 Trial？

固定 Harbor 0.26.0。在以 `8f51d19` 为 HEAD 的升级工作树上，对照本轮修改前后的未提交代码。三组用例均运行了真实 Oracle Trial，使用隔离网络。

| 输入 | 收窄前 | 收窄后 |
| --- | --- | --- |
| 普通题额外挂了只读 `/logs/user-agent` | 启动时报权限错误 | 收回含 `solved` 的日志，奖励 1 |
| 用户在 `/logs/archived` 和 `/logs/active` 上的挂载互相覆盖，均在必需日志树之外 | 启动要求回收位置一致，拒绝配置 | 宿主与 Trial 的日志逐字节一致，奖励 1 |
| 配置写作 `/logs/view/out/run`，内核把独立目录挂到了沙箱自有的 `/logs/agent/run` | Trial 继续运行，没有报告子挂载冲突 | 启动指出 `/logs/agent/run` 无法随父目录回收，评分未开始 |

配套对照用例显式声明模拟用户日志。同一个只读 `/logs/user-agent` 仍会产生权限错误。环境测试 58 项通过。Harbor 集成套件 119 项通过、1 项失败、8 项未选中，失败项仍断言安装的是 0.18.0。

<a id="deferred-transfer"></a>

### 单独跟踪的嵌套挂载传输

此前将旧候选的 29 项测试用于只修改启动的版本，得到 **24 过、5 败**。下面是那次回放的传输失败项。`/logs/alias/run` 是人工构造的挂载示例，原测试保存在调查补丁中。当前启动回归使用真实 Trial 的标准目录。四个传输方法和 `_host_path()` 的源码已逐一对照 `8f51d19`。

| 失败测试 | 下游观察 |
| --- | --- |
| `test_log_symlink_resolves_through_nested_bind` 的相对、绝对链接两例 | 沙箱内能读的日志经过宿主机路径查找后，一例找不到文件，一例被判为越出挂载。 |
| `test_directory_transfer_uses_contents_of_nested_mount` 的新挂载点、遮住旧文件两例 | 下载整个目录时，一例缺少 `view/data`，一例收到父目录中的 `hidden`。Agent 在子挂载里读到 `visible`。 |
| `test_download_from_log_link_to_a_mounted_directory` 一例 | 下载通过日志目录链接访问的文件时报告找不到文件。 |

原候选已保存为相对于 `8f51d19` 的完整补丁。在基线临时副本中应用后，环境实现、测试文件和 `bwrap_files.py` 三个文件均与拆分前逐字节一致。独立处理传输时可直接复用其中的用例。[原候选补丁](../../archive/c05-combined-candidate.patch)

<a id="mounted-namespace-result"></a>

## 归档对照 · 同时改启动与传输的旧候选

以下是拆分前的测量，基线为 `8f51d19`，版本为 Harbor 0.26.0。旧候选当时同时修改了 `environment.py`、`test_environment.py` 并加入 `bwrap_files.py`。[当前启动修复](#start-only-result) · [原候选补丁](../../archive/c05-combined-candidate.patch)

| 验证对象 | 方法 | 观察结果 |
| --- | --- | --- |
| 先前的 bwrap 原型 | 复跑跨子挂载的相对链接、绝对链接和只读错误 | 两种下载找不到沙箱可读的文件，启动丢失只读错误类型，共三例失败。 |
| 原先在宿主机查找路径的候选 | 新回归对照沙箱中实际的读写行为 | 六例先失败，包括回收整个目录时读到了子挂载遮住的旧文件。 |
| 目录已建好时单独核对下载 | 在 `8f51d19` 和归档候选上预建三个输出目录，给 `/logs/agent/view` 加一个子挂载。沙箱内 `cat` 和宿主 `download_dir("/logs/agent", ...)` 分别读取 `view/data`。 | 两版均启动成功。第一笔在沙箱中读到 `visible`，下载却得到被遮住的 `hidden`。归档候选两处均为 `visible`。这个传输差异在输出目录已存在时仍可单独复现。 |
| 当时包含传输修改的工作树 | 运行整个 `test_environment.py`，包括四项专项评审、文件和目录的双向传输 | **29 过**。完整 Oracle Trial 分别用默认配置和空的显式父挂载运行，两者均收回含 `solved` 的 `agent/oracle.txt` 并得到 `{"reward": 1}`。挂载场景中宿主文件与 Trial 文件的字节相同。 |
| 拆分前保留的环境测试 | 在临时副本用同一实现运行历次保留的 27 项用例 | **27 过**。这批是历史对照，与工作树的 29 项有重叠。 |
| 文件系统本身返回 `EROFS` | 同一目录同时以只读和可写视图出现，两次交换输出声明顺序 | 两次均启动成功，两种视图最终均可见 `artifacts/`。只有只读入口时的失败路径另有工作树回归覆盖。 |
| 整个默认 Harbor 集成套件 | 从一次性副本运行 `tests/integrations/harbor` | **90 过、1 败、8 项未选中**。唯一失败为 `test_official_jobs_validate_with_harbor_018`，断言安装的是 0.18.0。版本切换归 C06。 |
| 整仓默认测试 | 从另一份一次性副本运行 | 收集时有 6 个模块报错。5 个依赖当前环境缺少的 `torch`，`test_reward_registry` 无法导入 `get_reward_context`。本轮整仓测试没有执行完。 |

**本机启动开销。** 两份实现均使用相同的解释器、Harbor 0.26.0 和断网沙箱。每种配置每次重新建 Trial 目录，预热 2 次后计时 20 次，只计 `start(False)`。显式父挂载预先放好三个子目录，让第一笔和第二笔从相同可用状态开始。

| `start(False)` 中位数 | 第一笔 `8f51d19` | 归档候选 |
| --- | ---: | ---: |
| 默认配置 | 0.54 ms | 0.60 ms |
| 显式绑定 `/logs` 父目录 | 0.53 ms | 22.65 ms |

多出的约 22 ms 是这台机器上显式父挂载的一次启动开销。传输吞吐与集群性能尚未测量。

**复跑当前环境回归。** 在 Linux 上使用能运行断网 bwrap 的测试环境，解释器应导入升级工作树和 Harbor 0.26.0。以下命令读取工作树中的测试。`--confcutdir` 避免加载仓库根部的 pytest 清理钩子。若本机临时 overlay 已清理，可改用已安装 Harbor 0.26.0 的等价环境。

```bash
cd /home/hongshi/projects/Dressage-harbor-0.26
env PYTHONPATH="$PWD:/tmp/harbor026-review.t62iId/overlay" \
  /home/hongshi/projects/agent-api-integration/.venv-harbor/bin/python -B -m pytest \
  -q --tb=line -p no:cacheprovider -o asyncio_default_fixture_loop_scope=function \
  --confcutdir=tests/integrations/harbor tests/integrations/harbor/test_environment.py
```

<a id="mounted-parent-trial"></a>

## 同一道 Oracle 题的版本对照

用同一道隔离网络 Oracle 题、同一条显式父挂载运行完整 Trial。前四行的宿主目录起初为空。

| Harbor / Dressage | bwrap 实际挂了什么？ | 收回 `solved` 日志 / 奖励 |
| --- | --- | --- |
| 0.18.0 / 原版 `3e3142f` | `/logs` 及 agent、verifier、artifacts 三个子目录均单独绑定 | 是 / 1 |
| 0.26.0 / C01 `8827b11` | 同样四个绑定。日志写出，verifier 目录下载失败 | 是 / 无 |
| 0.26.0 / C02 `8023acd`、C04 `e6c0ce4` | 按关闭自动挂载的配置，只绑定 `/logs` | 否 / 无 |
| 0.26.0 / C05 第一笔 `8f51d19` | 只绑定 `/logs`，第一笔跳过由这个挂载覆盖的目标 | 否 / 无 |
| 同一 C05 第一笔，先在宿主目录建好三个子目录 | 仍然只绑定 `/logs` | 是 / 1 |

<a id="first-write-probe"></a>

### 第一次写日志前，沙箱里究竟有没有 `agent/`？

固定 Harbor 0.26.0、断网 bwrap、同一道 Oracle 题和默认关闭的自动挂载。实际运行 `Trial.run()`，在 `DressageEnvironment.start()` 返回后额外执行只读的 `test -d /logs/agent`。第一笔的环境源文件已核对与 Git 提交 `8f51d19` 中的 blob 一致。

| Dressage | 启动前的输入 | 沙箱内有 `/logs/agent`？ | Trial 收回 `oracle.txt`？ | 奖励 |
| --- | --- | --- | --- | --- |
| C05 第一笔 | 默认配置，没有宿主绑定 | 有 | 有，含 `solved` | 1 |
| 同一份代码 | 空的 `host-logs/` 绑定到 `/logs` | 无 | 无 | 无 |
| 同一份代码 | 仍绑定到 `/logs`，宿主目录预先建好 `agent/`、`verifier/`、`artifacts/` | 有 | 有，含 `solved` | 1 |
| 当时的启动与传输候选 | 空的 `host-logs/` 绑定到 `/logs` | 有 | 有，含 `solved` | 1 |

第二行第一次打开日志时捕获到 `/bin/bash: line 1: /logs/agent/oracle.txt: No such file or directory`。第二、三行只改变宿主目录的初始内容，两次实际绑定的目标都是 `/logs`。

<a id="mounted-parent-result"></a>

### 早期候选在宿主机上查找路径时的验收

`start()` 先建可写绑定的宿主源，再调用 `_prepare_output_directories()` 准备 Trial 声明的输出。以 `host-logs/ → /logs` 为例，`/logs/agent` 缺失时就在可写的 `host-logs/` 下面创建 `agent/`。如果只读入口依赖另一个输出，就让其他目录先准备，再检查仍未就绪的目标。一轮都没有进展时，启动会报出失败的沙箱路径。

启动、上传和下载共用 `_host_path()`。已有用例能通过进入子挂载的链接读回日志。下面的实测记录了其余几种布局中，路径查找与沙箱实际行为发生分歧的位置。

- **完整 Trial。** 把第一笔的 Oracle 回归参数化。默认配置和空的可写宿主父挂载都得到奖励 1。挂载场景还比对宿主与 Trial 收回的 `oracle.txt` 字节。
- **已有目录与失败路径。** 相对和绝对沙箱链接都能从子挂载读回日志。写只读子挂载、访问挂载范围以外的宿主路径、只有只读入口却缺目录的场景均被拒绝。真实只读文件系统（`EROFS`）探测在两种声明顺序下均建出了可见目录。
- **四条专项评审之前的套件结果。** 正式工作树的环境测试 21 项通过。拆分前保留的 27 项环境测试也在临时副本通过。完整默认 Harbor 集成套件 82 过、1 败，8 项 E2E 未选中。唯一失败为 C06 待更新的 0.18 版本断言。

<a id="mounted-parent-review"></a>

## 四条评审意见如何复现

固定 Harbor 0.26.0、关闭自动挂载。以下记录对照的是第一笔 `8f51d19` 和当时在宿主机查找路径的候选。用相同的显式绑定另起一个断网 bwrap 沙箱，只将启动时声明的输出改为已经存在的挂载点。这样即使 Dressage 在启动阶段拒绝原配置，也能让 Linux 实际执行 `test -d`、`mkdir` 或 `cat`。工作树的启动结果见[当前回归](#start-only-result)，传输结果见[单独跟踪的五例](#deferred-transfer)。

| 场景 | 沙箱实测 | 第一笔 | 第二笔候选 |
| --- | --- | --- | --- |
| ① `agent → view/agent`。父挂载里有目录，覆盖 `view` 的子挂载里没有 | `test -d /logs/agent` 失败 | 启动成功，漏检 | 仍然漏检 |
| ② `/logs` 只读，`alias → writer`，`writer` 单独挂为可写 | `mkdir /logs/alias/run` 成功，从 `writer/run` 可见 | 启动成功，跳过建目录 | 启动报 `PermissionError` |
| ③ `alias → view/../agent-data`，`view` 是子挂载 | `cat /logs/alias/probe` 读到父挂载的文件 | 下载相同字节 | 下载报 `ValueError` |
| ④ `alias → missing/../view/agent`，分别让 `missing` 缺失或为普通文件 | `cat` 分别报路径不存在、不是目录 | 两次下载均失败 | 两次都下载到了沙箱读不到的文件 |

### 第二笔的历史候选与评审发现

**先只看普通可写父挂载。** 把第一笔提交卡中建目录循环的变量换成这次的实参：`target = /logs/agent`，`mount = /logs`。目标在挂载里面，因而第 411 行的 `if not any(...)` 为假，跳过第 412 行的建目录操作。这个配置中，已有的 `_host_path("/logs/agent")` 会找到 `host-logs/agent`。

在 `8f51d19` 的临时副本中加两行：对挂载覆盖且缺失的目录，先用 `_host_path(..., writable=True)` 查可写位置，再调用 `mkdir`。同一条空父挂载 Trial 从缺日志、无奖励变成宿主和 Trial 各自读到 `solved`、奖励为 1。另一个已有用例中，`/logs/agent` 是指向子挂载内目录的链接；原提交在沙箱内执行 `test -d /logs/agent` 成功，两行实验却在启动时报 `FileExistsError`。第二笔还需解决如何识别沙箱中已经可见的目录。

**为什么评审又提到顺序？** 假设宿主机有一个 `host-logs/`，里面还没有 `artifacts/`。用户给同一个宿主目录配了两个入口。

```text
沙箱 /logs/artifacts         → host-logs/artifacts   经 /logs，只读
沙箱 /logs/writer/artifacts  → host-logs/artifacts   经 /logs/writer，可写
```

这两个入口指向同一个 `artifacts/`。先遇到只读入口时，上一版当场报 `PermissionError`。把可写入口排在前面，同一份配置就能启动。另一个例子是宿主机已有符号链接 `agent → artifacts`。先遇到 `agent` 时，对它调用 `mkdir` 会报 `FileExistsError`。等 `artifacts/` 建好，原链接自然就能用。

```python
# DressageEnvironment.start() 中与目录准备有关的两步
for host_path, read_only in self._harbor_mounts.values():
    if not read_only:
        host_path.mkdir(parents=True, exist_ok=True)  # 先准备显式可写绑定或启用的自动绑定的宿主源
self._prepare_output_directories()                   # 再准备 Trial 声明的输出目录
```

`_prepare_output_directories()` 先使用已存在的目录，通过可写入口创建缺少的目录。遇到上述两种错误时，先记下路径，让其他输出继续准备。只复查尚未就绪的路径。一整轮都没有进展时，抛出原错误。最后 `start()` 核验只读绑定的宿主源，并准备沙箱挂载点。

**拆分前补充的测试。**

| 场景 | 操作 | 验收 |
| --- | --- | --- |
| 拆分前的候选 · Trial 多声明一个目录 | 让后端接收 `/logs/user-agent`，启动后直接下载该目录。这例分别跑「只用沙箱」和「用户显式绑定父目录」两次。 | 两次都能取得目录吗？自动挂载指定的宿主源是否仍未被创建？显式绑定父目录时，子目录是否落在它下面？ |

此前完整候选的挂载回归围绕以下两个行为，随第二笔保存。

| 验收问题 | 用哪个例子判断？ |
| --- | --- |
| **可以准备好的目录，换个声明顺序还能用吗？** | 交换上文只读入口与可写入口两个自动输出的顺序。两次都要能从可写入口写入、从只读入口读回相同字节。另测默认输出 `agent → artifacts`，启动后两个名字必须指向同一个目录，链接仍保留。先前回归也覆盖了两个显式入口共享宿主源，以及可写绑定的宿主源让另一个输出可读。 |
| **确实无法准备的目录还会报错吗？** | 只有只读入口且目录缺失时仍报权限错误。把 `agent` 的链接改指向缺失且未声明的目录，启动仍失败，目标没有被擅自创建。成功启动的配置也要检验经只读入口写入会被拒绝。 |

**拆分前的实验记录**

- **修前实测。** 同一道题默认关闭自动挂载时缺目录、无奖励。开启后，日志可读，奖励为 1。
- **临时补丁。** 在断网 bwrap 测试中，先只加 C05 回归，读取 `oracle.txt` 时失败。再固定创建三个默认目录，日志收到 `solved`，奖励为 1，整个环境测试文件 16 项通过。
- **拆分前的工作树。** 前三版环境测试分别为 18、22、23 项通过。对上一版加上四例后，两例失败（只读入口先声明、默认 `agent` 链接），两例符合预期（可写入口先声明、链接目标无法提供）。当时修正后四例全部通过，完整 `test_environment.py` 为 27 项通过，包含 Oracle 首次写日志并得到 1 分。
- **更大范围的复核。** 一次性副本的默认 Harbor 集成套件在 C04 基线上为 76 过、1 败，上一版 C05 为 84 过、1 败，本轮为 88 过、1 败。8 项 E2E 未选中。唯一失败均为 `test_official_jobs_validate_with_harbor_018` 的旧版本断言，版本切换归 C06。此前整仓 pytest 在此环境收集阶段就停下，涉及缺少 `torch` 和无法导入 `get_reward_context`。

<a id="mount-layout-review"></a>

**拆分前完整候选的复审实测。** 两次对照均使用 Harbor 0.26.0 和临时目录。

| 改变什么？ | 观察到什么？ | 哪个假设失效？ |
| --- | --- | --- |
| 固定挂载。父目录中有链接 `agent → view/agent`，另一个宿主目录挂在 `/logs/view` 并提供 `agent/`。切换 Dressage 版本。 | C04 启动成功，真实 bwrap 中 `test -d /logs/agent` 返回 0。C05 在启动阶段报 `FileExistsError`。 | 仅沿父挂载的宿主源跟随链接，会漏掉沙箱在 `/logs/view` 看到的子挂载。 |
| 固定 C05。在临时挂载空间里让同一宿主目录通过一个只读视图和一个可写视图出现，Dressage 的绑定配置没有标记只读。交换两个输出的声明顺序。 | 只读视图先声明时报 `OSError`（`EROFS`，errno 30）。可写视图先声明则启动成功，只读视图也能看到 `artifacts/`。 | 文件系统本身也能拒绝写入，当前循环只推迟处理 `PermissionError` 和 `FileExistsError`。 |

**能否把第一笔修复缩小？** 在 C04 的临时副本上加 7 行，只为没有宿主挂载覆盖的输出路径创建沙箱目录。C04 原有的 15 项环境测试和新增的完整 Oracle Trial 均通过，跨子挂载链接在真实 bwrap 中也仍可见。跑目前全部 27 项用例时为 20 过、7 败，缺口集中在宿主挂载，例如挂载整个 `/logs` 后缺少的 `user-agent/`。据此建议分两笔评审：第一笔解决沙箱自有输出，第二笔解决挂载覆盖的输出；完整升级仍须验收两者。

<a id="ensure-dirs-probe"></a>

另一个副本直接复用了 Harbor 的 `ensure_dirs(outputs, chmod=False)` 并检查返回码，27 项环境测试中 21 过、6 败。Dressage 的 `exec()` 在白名单网络模式下会先要求 Gateway socket 就绪，而原有启动流程允许稍后准备 socket。这个替代方案只在临时副本验证。选定的 7 行方案已在正式升级工作树复验。拆分前完整候选保存在本机 Dressage 的 Git stash `4a398d5`，可用于回查第二笔。

### 证据索引

- **定位错误。** [Dressage 创建目录的循环](https://github.com/dextermayhewjd/Dressage/blob/e6c0ce4912c3edaa1ead0a353419b399a3a3ca87/dressage/integrations/harbor/environment.py#L393-L405) · [Oracle 指定日志文件](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/oracle.py#L110-L116)
- **核对上游约定。** [两个参数的原文](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/base.py#L241-L246) · [Trial 提供的输出目录](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/trial/trial.py#L2089-L2122) · [Mosaic 后端按可写目标建目录](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/mosaic.py#L496)
- **复查测试。** [C02 旧测试写入日志的位置](https://github.com/dextermayhewjd/Dressage/blob/e6c0ce4912c3edaa1ead0a353419b399a3a3ca87/tests/integrations/harbor/test_environment.py#L216-L229) · [C02 的评审记录](./README.md#switch-review) · [完整 Trial 的两组实测](./README.md#oracle-log-start) · [固定三个目录的实验补丁](./c05-sandbox-log-directories.patch)
