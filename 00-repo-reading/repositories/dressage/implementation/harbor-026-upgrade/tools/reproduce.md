# 从阅读仓库复查 Dressage 的 Harbor 升级依据

本次对照统一使用 Dressage `3e3142f`、Python 3.12 和 Harbor `0.18.0`、`0.25.0`、`0.26.0`。每个问题的 README 记录修改理由及验收边界。实验脚本和输出随对应问题保存，共用一次实验的条目链接到同一份输出。[问题索引](../README.md#investigations)

<a id="surface"></a>

## 复算接入点索引

日常接续时，在升级根目录 `harbor-026-upgrade/` 运行 `python3 tools/check_docs.py`。它只读取已经保存的索引、用法表和证据，对照文件与行号是否都有去向、每项是否有三个版本的输入和输出。需要更换固定提交、调整扫描规则或独立复核初次扫描时再运行下面的整树检查。 [逐项审核入口](../usage/README.md#resume)

在升级根目录运行。脚本读取两份固定提交里的文件与类定义，并逐行比较归档结果。运行此检查只需要 Python 标准库和两个包含指定 Git 对象的 checkout。[本次统计原行](../usage/harbor-call-sites.md) · [扫描脚本](scan_harbor_surface.py)

```bash
python3 tools/scan_harbor_surface.py --check --dressage-repo "$HOME/projects/Dressage-harbor-0.26" --harbor-repo "$HOME/projects/harbor"
```

<a id="setup"></a>
## 准备单个版本的复查环境

从升级根目录 `implementation/harbor-026-upgrade/` 目录开一个终端。`notes_dir` 指向本仓库的证据，`DRESSAGE_ROOT` 指向实际运行的 Dressage 工作树。示例采用当前机器的目录名，换机器时把第二行改成对应 checkout。每个 Harbor 版本使用一个 Python 环境。基线的 `.[harbor]` 固定 0.18.0。下面单独安装 0.26.0 以复现修前问题。要回放已归档的 0.25.0 对照时使用另一环境。

```bash
notes_dir="$(pwd -P)"
export DRESSAGE_ROOT="$HOME/projects/Dressage-harbor-0.26"
cd "$DRESSAGE_ROOT" || exit 1
harbor_version=0.26.0
env_dir="../.venvs/dressage-harbor-$harbor_version"
python3.12 -m venv "$env_dir"
. "$env_dir/bin/activate"
python -m pip install -e '.[test]' ./blackbox_server "harbor==$harbor_version"
export PYTHONPATH="$DRESSAGE_ROOT"
export LITELLM_LOCAL_MODEL_COST_MAP=True
export HF_HUB_OFFLINE=1
python -c 'import dressage; from pathlib import Path; from importlib.metadata import version; print(version("harbor"), dressage.__file__); assert Path(dressage.__file__).resolve().parent == Path.cwd().resolve() / "dressage"'
```

这些命令描述独立安装方式。本次本地复跑复用了已装的 Python 依赖和用发布标签构建的 Harbor 包，导入的是独立 Dressage 基线导出的源码。测试进程没有传入模型厂商凭证。LiteLLM 对 Qwen 的模型名给过识别警告，Job 仍创建成功。干净环境的安装验收属于[问题 04](../investigations/04-version-checks/README.md)。

<a id="c01-preflight-regression"></a>

## C01 · 下次升级 Harbor，怎样确认环境预检还能用？

使用包含 C01 回归测试的 Dressage 工作树（含签名快照的提交为 `8827b11`）。固定 Dressage 代码和测试，先用上次通过的 Harbor 版本跑一轮，再用候选版本跑一轮。两轮各自激活对应的 Python 环境。[准备单个版本的复查环境](#setup)

从 Dressage 工作树根目录执行。对照轮使用已知通过的 `0.26.0`，候选轮把 `expected_harbor` 改为待验证的版本。当前解释器查到的版本与预期一致才会运行 pytest。

```bash
expected_harbor=0.26.0
actual_harbor=$(python -c 'from importlib.metadata import version; print(version("harbor"))')
echo "Harbor 实际 $actual_harbor / 预期 $expected_harbor"
test_file=tests/integrations/harbor/test_environment.py
test "$actual_harbor" = "$expected_harbor" && \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -B -m pytest --confcutdir=tests/integrations/harbor \
    -p no:cacheprovider -p pytest_asyncio.plugin -o asyncio_default_fixture_loop_scope=function \
    -v --tb=short "$test_file::test_harbor_preflight_signature" \
    "$test_file::test_preflight_through_harbor_factory" \
    "$test_file::test_preflight_uses_container_compatible_proc"
```

**读结果时，先确认这六例都执行了。**

- **六例均通过。** 在 `8827b11` + Harbor `0.26.0` 上，一例上游签名快照、四组工厂输入和一次无参调用都通过。候选轮出现同样结果，说明这些输入下预检交接仍然成立。
- **用例被跳过或没有收集到。** 先核对解释器、Harbor 安装版本和 Dressage 工作树中是否有这三个测试函数。这一轮的兼容性仍待验证。
- **只有候选轮失败。** 签名快照单独失败时，复核新版接口及五例行为结果。若行为回归也失败，用第一条失败的异常或断言定位工厂传参、基类解析或后端入口。如果新版更换了 `parse_options` 这个观察点，先核实原始选项的交付行为，再决定改适配器还是改测试。[C01 提交卡 · 四种实现各在哪里失败](../prs/001-harbor-026-compatibility/commits/01-environment-preflight.md#preflight-tests)

C01 提交 `8827b11` 中的 GitHub Actions 工作流用于发布 Docker 镜像，这六例预检目前按上面的命令复跑。切换依赖版本的 PR 可增加自动检查，核对实际安装的 Harbor 版本，并确认六例全部执行通过。

C01 的端到端验收从本地 `harbor run` 加载指定 `DressageEnvironment` 的 Job 配置，观察 CLI 是否调用该类的 `preflight`。Harbor 0.26 的编程入口 `Job.create(config)` 另行调用 `EnvironmentFactory.validate_options` 校验环境选项，训练入口在 PR 中单独验收。[CLI 环境预检](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/cli/jobs.py#L113-L122) · [Job.create 的校验](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/job.py#L170-L185) · [PR-001 的整体验收入口](../prs/001-harbor-026-compatibility/README.md#acceptance)

<a id="second-pass"></a>

## 复跑第二轮的边界观察

独立 verifier、Job/Trial 重试和路由的复跑说明在各问题内。[21 独立 verifier](../investigations/21-separate-verifier-input/README.md) · [22 队列重试](../investigations/22-retry-policy/README.md) · [23 本地题单](../investigations/23-local-dataset-selection/README.md) · [07 命令启动环境](../investigations/07-agent-routing/README.md)

**数据源续跑。** 在同一工作目录执行，分别用含 0.18.0 和 0.26.0 的 Python 3.12 设置 `py018`、`py026`。两进程导入同一 Dressage 基线；探测用两项固定任务配置，只临时放行运行时版本检查。

```bash
probe="$notes_dir/investigations/19-checkpoint-digests/checkpoint_probe.py"
state_dir="$(mktemp -d)"
PYTHONHASHSEED=1 "$py018" "$probe" save "$state_dir/old"
PYTHONHASHSEED=1 "$py018" "$probe" load "$state_dir/old"
PYTHONHASHSEED=2 "$py018" "$probe" load "$state_dir/old"
PYTHONHASHSEED=1 "$py026" "$probe" load "$state_dir/old"
PYTHONHASHSEED=1 "$py026" "$probe" save "$state_dir/new"
PYTHONHASHSEED=1 "$py026" "$probe" load "$state_dir/new"
PYTHONHASHSEED=2 "$py026" "$probe" load "$state_dir/new"
```

**发行包和 CLI 收尾。** 下面从固定 Dressage 提交离线打包，准备工具需要 pip、setuptools 和 wheel。每个解释器已有对应 Harbor。脚本核对导入的 Dressage 模块及其发行元数据都来自临时安装目录，同时逐项核对当前 Harbor 的基础依赖，最后给写 manifest 模拟一次 I/O 失败。这里使用 `--no-deps` 专门观察发行包与调用边界；干净安装的问题仍按 04 验收。[两版输出](../investigations/04-version-checks/wheel-output.txt)

```bash
wheel_dir="$(mktemp -d)"
mkdir -p "$wheel_dir/source" "$wheel_dir/dist"
git -C "$DRESSAGE_ROOT" archive 3e3142fe8ea07e4504c3b20a936a4c201a3de44c | tar -xC "$wheel_dir/source"
python3 -m pip wheel --no-index --no-deps --no-build-isolation -w "$wheel_dir/dist" "$wheel_dir/source"
python3 -m pip install --no-index --no-deps --target "$wheel_dir/site" "$wheel_dir/dist/dressage-0.1.0-py3-none-any.whl"
for interpreter in "$py018" "$py026"; do
  PYTHONPATH="$wheel_dir/site" "$interpreter" "$notes_dir/investigations/04-version-checks/wheel_probe.py" "$wheel_dir/site"
done
```

<a id="run-probes"></a>
## 重跑一次观察

沿用上述终端。探测脚本和最小题目从本笔记目录读取，导入的是选定的 Dressage 工作树。右列是同一基线上已采集的实际 stdout，其中包含升级前的已知错误。

| 要查的证据 | 从已准备的终端执行 | 可对照的输出 |
| --- | --- | --- |
| 01 工厂是否进入 bwrap 预检 | `python "$notes_dir/investigations/01-environment-preflight/probe.py"` | [三个版本](../investigations/01-environment-preflight/preflight-output.txt) |
| U34 工厂能否原样转交选项并进入后端 | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest --noconftest -p no:cacheprovider --tb=line -q -r fs "$notes_dir/investigations/01-environment-preflight/test_factory_preflight.py"`。复跑历史三例时加 `-k 'not nonempty-options'`。 | [原三例的三版输出](../investigations/01-environment-preflight/factory-contract-results.txt) · [第四例抓到的错误](../investigations/01-environment-preflight/README.md#nonempty-options) |
| 02 非空目录是否触发重复复制 | `python "$notes_dir/investigations/02-output-mounts/probe.py" logs` | [0.25 和 0.26](../investigations/02-output-mounts/log-recovery-output.txt) |
| U42、U44 同一非空日志在原 Trial 回收方法里经过哪个分支 | `python "$notes_dir/investigations/02-output-mounts/trial_log_recovery.py"` | [三版的调用次数、返回值、文件内容比对和错误标记](../investigations/02-output-mounts/trial-log-recovery.txt) |
| U44 直挂日志有无冗余复制或复制错误 | `python "$notes_dir/investigations/02-output-mounts/trial_log_recovery.py" --check-compatible` | [0.18 退出 0，0.25 和 0.26 退出 1](../investigations/02-output-mounts/trial-log-recovery.txt#L16-L18) |
| U42、U44 显式改绑后，原本缺文件的 Trial 目录是否收到日志 | `python "$notes_dir/investigations/02-output-mounts/trial_log_recovery.py" --separate-source --check-compatible` | [0.18 漏收，0.25 和 0.26 各复制一次，与直挂场景对照](../investigations/02-output-mounts/trial-log-mount-matrix.txt) |
| 05 技能文件能否读回 | `python "$notes_dir/investigations/02-output-mounts/probe.py" skills` | [0.25 和 0.26](../investigations/05-skills-upload/skills-upload-output.txt) |
| 04、09、11 版本检查、Trial 排列和钩子注册 | `python "$notes_dir/investigations/09-trial-plan/probe.py"` | [三个版本](../investigations/09-trial-plan/trial-plan-output.txt) |
| 06、10 本地 Job 创建与 lock schema | `python "$notes_dir/investigations/10-job-lock/probe.py"` | [三个版本和三个 Agent 配置](../investigations/10-job-lock/job-lock-output.txt) |
| 18、19 两份 YAML 解析出的字段和 source 摘要 | `python "$notes_dir/investigations/18-example-configs/probe.py"` | [三个版本](../investigations/18-example-configs/job-config-output.txt) |
| U03 基线 DAPO 是否接受当前安装版本 | `python examples/harbor/dataset_tools/dapo/prepare_dataset.py --check-runtime`，紧接着运行 `echo "$?"` 查看退出码 | [三版退出码与 stderr](../investigations/04-version-checks/dapo-runtime-output.txt) |
| U57、U58 生成的本地题目与 reward.json 是否被 Harbor 原样读回 | `python "$notes_dir/usage/evidence/dapo_files.py"` | [三版的题目、正确与错误答案](../usage/evidence/dapo-files.txt) |

**12 的结果交接**　在三个版本各运行下面一条命令。脚本用本地 Oracle 题创建 Trial 并主动发一次 END，用相同的评分输入、Proxy 和样本夹具执行 Store、磁盘回读与两段样本的转换。DAPO 的文件探测另行执行题目生成代码、评分脚本和 Harbor 文件解析方法。两项探测的完整沙箱运行留给 Trial 验收。 [结果探测](../investigations/12-reward-validity/result_contract_probe.py) · [0.18.0](../investigations/12-reward-validity/result-contract-0.18.0.txt) · [0.25.0](../investigations/12-reward-validity/result-contract-0.25.0.txt) · [0.26.0](../investigations/12-reward-validity/result-contract-output.txt) · [文件探测](../usage/evidence/dapo_files.py)

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest --noconftest -p pytest_asyncio.plugin -p tests.integrations.harbor.conftest -p no:cacheprovider -o asyncio_default_fixture_loop_scope=function -q -s "$notes_dir/investigations/12-reward-validity/result_contract_probe.py"
```

Job 探测默认读取随仓两道最小本地题，只执行配置、计划、注册和 lock 操作。历史探测使用 Harbor 的 `hello-world` 和 `hello-alpine`。如要对照同一输入，计划探测接受 `--tasks <hello-world 目录> <hello-alpine 目录>`，lock 探测接受 `--task <hello-world 目录>`。模型名只作为构造 Job 的输入。[第一道输入](../investigations/09-trial-plan/tasks/first/task.toml) · [第二道输入](../investigations/09-trial-plan/tasks/second/task.toml)

问题 18 核对 dataset、Agent 模型和环境字段。问题 19 复用相同的输出，但评审的是摘要。旧版本的摘要还受 Python 哈希种子影响。要复查这项差异，在同一 Harbor 环境分别运行下列两行，再切换 Harbor 版本。[按种子保存的输出](../investigations/19-checkpoint-digests/hash-seed-output.txt)

```bash
PYTHONHASHSEED=1 python "$notes_dir/investigations/18-example-configs/probe.py"
PYTHONHASHSEED=2 python "$notes_dir/investigations/18-example-configs/probe.py"
```

<a id="stop-retention"></a>

**U38 的停止后保留行为。** 在同一 Dressage 工作树中分别选择 Harbor 0.18.0、0.25.0、0.26.0，运行下列两项本地用例。每项在 pytest 临时目录创建 Trial，用真实环境实例启动和停止。构造后端要能找到 `bwrap`、`python3`、`claude` 和 `curl`。测试只写本地工作文件。基线在每个版本均为删除用例通过、保留用例失败。[原始结果](../investigations/20-bwrap-stop-delete/stop-output.txt) · [界定保留范围](../investigations/20-bwrap-stop-delete/README.md#evidence)

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -B -m pytest --noconftest -p pytest_asyncio.plugin -p no:cacheprovider -o asyncio_default_fixture_loop_scope=function -q -s --tb=line "$notes_dir/investigations/20-bwrap-stop-delete/test_stop_retention.py"
```

<a id="suite"></a>
## 重跑默认套件与一行夹具对照

先在未修改的 `3e3142f` 运行默认 Harbor 套件。Linux 环境中 `bwrap`、`claude`、`curl` 和 `python3` 可用时，仓库的真实 bwrap 用例才会执行。pytest 会说明跳过和排除的用例。[原始 0.18 日志](../investigations/00-version-target/pytest-0.18.0.txt) · [原始 0.26 日志](../investigations/00-version-target/pytest-0.26.0.txt) · [本次三版复跑的失败项与计数](../investigations/00-version-target/pytest-replay.txt)

```bash
python -m pytest -p no:cacheprovider -m "not harbor_e2e" --tb=line -q -r f tests/integrations/harbor
```

<a id="original-suite"></a>

**单独统计升级前自带的测试。** 在同一固定 Dressage 工作树和选定的 Harbor 环境运行。第一条收集全部 74 个用例，含默认排除的 E2E。第二条执行默认 66 项，使用 Python 3.12 的 `sys.monitoring` 按用例观察两组函数入口。一组来自固定用法索引，覆盖六个实现文件中的 53 个函数。另一组是专门挑出的 16 个 Harbor 与 Dressage 交接方法，两组有交集。计数包含 pytest 主进程中每个用例的准备、执行和清理。脚本返回原 pytest 的退出码，故未修复的 0.26 基线会返回 1。[原始用例清单](../investigations/00-version-target/original-suite-collection.txt) · [53 个实现函数的计数](../investigations/00-version-target/original-suite-functions.txt) · [16 个方法入口的计数](../investigations/00-version-target/original-suite-calls.txt) · [按调查项对照](../investigations/original-test-audit.md#issue-map)

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -B -m pytest -p pytest_asyncio.plugin -p no:cacheprovider -o addopts= -o asyncio_default_fixture_loop_scope=function --collect-only -q tests/integrations/harbor
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -B "$notes_dir/investigations/00-version-target/observe_original_suite.py"
```

保持当前工作树的测试和后端原样，在单独导出的基线上应用问题 03 的夹具差异。运行此对照时选择 Harbor 0.26.0。补丁只将传给 verifier 的 `mounts` 换为 `auto_mounts`。[实际补丁](../investigations/03-verifier-fixture/auto-mounts.patch) · [应用补丁后的输出](../investigations/03-verifier-fixture/fixture-pytest.txt)

```bash
python_bin="$(python -c 'import sys; print(sys.executable)')"
fixture_dir="$(mktemp -d)"
git archive 3e3142f | tar -x -C "$fixture_dir"
(
    cd "$fixture_dir" || exit 1
    git apply --check "$notes_dir/investigations/03-verifier-fixture/auto-mounts.patch" &&
    git apply "$notes_dir/investigations/03-verifier-fixture/auto-mounts.patch" &&
    PYTHONPATH="$PWD" "$python_bin" -m pytest -p no:cacheprovider -q tests/integrations/harbor/test_environment.py
)
```

<a id="provenance"></a>
## 原临时材料现在在哪里

| 原材料 | 在本阅读仓库的位置 |
| --- | --- |
| `compare_versions.py` 与 `mounts.py` | 工厂调用在 [01](../investigations/01-environment-preflight/probe.py)。后端文件操作在 [02](../investigations/02-output-mounts/probe.py)，分为 `logs` 和 `skills` 两个独立观察。 |
| 两个版本的 `probe.py` | [09 的计划与钩子探测](../investigations/09-trial-plan/probe.py)保留原始版本检查、进程内临时放行和内存 Gateway。可直接从本仓库输入构造真实 Job。 |
| `audit.py` | [10 的 Job/lock 探测](../investigations/10-job-lock/probe.py)与 [18 的 YAML/摘要探测](../investigations/18-example-configs/probe.py)。工厂检查收在 01。 |
| `suite.log`、修改过的 verifier 夹具、`help018` 和 `help025` | 00 保存原始测试输出，去掉个人路径前缀及行尾空格。03 保存真正的一行差异和复跑结果。06 留存与插件加载、凭证模式有关的 [CLI 帮助摘录](../investigations/06-agent-credential-preflight/cli-help-excerpts.txt)。 |
| `new/` 的 20 个问题目录与 `check_docs.py` | 问题正文已迁入 [调查索引](../README.md#investigations)。[文档校验工具](check_docs.py)从自己的位置解析相对路径。 |

在升级根目录运行 `python3 tools/check_docs.py`，会核对主题目录、逐项输入与结果观察位置、本地链接和归档摘录。提供 checkout 后，还能按固定提交和行号校对源码。Slime 的三个接收位置按 Dressage 基线锁定的子模块提交 `aaf5c20` 校对，`--slime-repo` 可选。运行证据的适用范围见各项版本表。 [回到审核入口](../prs/001-harbor-026-compatibility/README.md#review-order)

```bash
python3 tools/check_docs.py --dressage-repo "$HOME/projects/Dressage-harbor-0.26" --harbor-repo "$HOME/projects/harbor" --slime-repo "$HOME/projects/slime"
```
