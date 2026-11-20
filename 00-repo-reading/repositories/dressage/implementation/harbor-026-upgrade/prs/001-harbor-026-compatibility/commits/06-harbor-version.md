# C06 · 让 Dressage 安装并接受 Harbor 0.26.0

**本笔决策**　用户安装 Dressage 的 `[harbor]` 可选依赖后，应该得到 Harbor 0.26.0。同一环境要能启动 Dressage 的 Harbor 接入，也要能通过 DAPO 数据准备工具的版本检查。

实施基线 `8f51d19`（C05a） · 目标 `harbor==0.26.0` · 已本地提交 `a1087bb`。提交正文记录了手动空日志挂载的已知回归与延期原因，提交前默认集成套件复验通过。

## ① 上游约定 · Harbor 0.26.0 要求 Python 3.12 或更高版本

Harbor 在自己的发行包中声明版本 `0.26.0` 和 `requires-python = ">=3.12"`。Dressage 则决定自己的可选集成支持哪一版 Harbor。这次升级选择精确支持 `0.26.0`。用户从 Dressage 仓库执行 `python -m pip install '.[harbor]'`，安装器首先读取的是 Dressage 的依赖声明。[两边的版本声明](../../../investigations/04-version-checks/README.md#sources)

## ② 修前表现 · 正常安装选中旧版，手动装新版又被拒绝

原版 Dressage wheel 的元数据要求 `harbor==0.18.0`。研究时把 Harbor 0.26.0 单独放进实验环境，用原来的运行时检查得到下面的结果。DAPO 命令在同一版本上也退出，退出码为 2。

```text
unsupported Harbor version '0.26.0'; expected exactly '0.18.0'
```

以上是原版 `3e3142f` 的归档实测。在本笔起点 `8f51d19` 核对源码，安装声明和两处检查仍要求 0.18.0。[wheel 元数据](../../../investigations/04-version-checks/wheel-output.txt) · [运行时检查原始输出](../../../investigations/09-trial-plan/trial-plan-output.txt) · [DAPO 三版退出码](../../../investigations/04-version-checks/dapo-runtime-output.txt)

## ③ 原因定位 · 一个安装声明，两个独立的启动入口

| 用户执行什么 | 哪段代码决定结果 | 当前行为 |
|---|---|---|
| 安装 `.[harbor]` | `pyproject.toml` 的 `harbor` extra | 安装器按 `harbor==0.18.0` 解析依赖。 |
| 启动 Harbor rollout | `dressage/integrations/harbor/compat.py` 的 `require_harbor_runtime()` | 读取已安装的包版本，和本模块的 `SUPPORTED_HARBOR_VERSION` 比较。 |
| 准备 DAPO 数据 | `examples/harbor/dataset_tools/dapo/prepare_dataset.py` 的 `check_runtime()` | 脚本读取包版本，与脚本自己的常量比较。 |

只改安装声明，用户会装到新版，两个入口仍会拒绝它。只改运行时检查，用户照文档安装仍会得到旧版。三处要在同一笔提交中对齐。

## ④ 修复决策 · 把三个接触点一起切到 0.26.0

extra 和两处 `SUPPORTED_HARBOR_VERSION` 已同步为 0.26.0。沿用现有精确比较和 Python 最低版本检查，Harbor 继续按需安装。合同测试新增真实发行包版本检查和 DAPO 子进程调用，诊断文字同步更新。本次使用的包索引找不到原已固定的 `dressage-blackbox-server==1.1.0`。干净安装验证使用同仓 `blackbox_server/` 构建的 1.1.0 wheel；安装说明已明确指定这个同仓依赖来源。

## ⑤ 回归验证 · 从干净安装走到两个真实入口

**旧测试测到了什么？** 现有运行时合同用例会拒绝过低的 Python 和错误的 Harbor 版本，随后临时替换版本检查来测试 Trial 排序。另一条用例在解析两份官方 Job YAML 前先断言已经安装 `0.18.0`。前者无法证明新版可以启动，后者在 0.26 上还没读到 YAML 就会失败。[原套件与修前记录](../../../investigations/04-version-checks/README.md#history)

| 修后怎么验 | 通过条件 | 能抓住哪种遗漏 |
|---|---|---|
| 在干净 Python 3.12 环境构建并安装带 `[harbor]` 的 Dressage wheel | `importlib.metadata.version("harbor")` 得到 `"0.26.0"`；Harbor 能按短名 `dressage` 找到插件。 | 源码环境碰巧装了新版，发行包却仍要求旧版。 |
| 在上述环境调用 `require_harbor_runtime()`，再运行 DAPO 的 `--check-runtime` | 前者返回的 `harbor_version` 为 `"0.26.0"`，后者退出码为 0。 | 只更新了其中一个入口。 |
| 给合同测试传 Python 3.12 与 Harbor 0.25.0，再单独传过低的 Python 与 Harbor 0.26.0 | 分别得到版本不匹配、Python 版本过低的错误。 | 切换版本时意外放宽检查。 |
| 用真实的 Harbor 0.26 `JobConfig.model_validate()` 解析 Terminal-Bench 2 和 τ³-bench 的 E2B YAML | 两份配置通过，原测试对数据集、模型和环境类型的断言继续成立。 | 版本检查通过后，用户提供的 Job 配置仍无法加载。 |

**本次实测。** 修前同一个 0.26.0 环境里，新增合同测试在 Dressage 版本检查处失败，独立 DAPO 命令退出 2。修后在全新 Python 3.12.3 环境安装 Dressage wheel 的 Harbor 和测试依赖，同仓提供 BlackboxServer wheel，Harbor 从包索引安装。`uv pip check` 核对 139 个已安装包，依赖全部相容。Dressage 从该环境的 `site-packages` 加载，`require_harbor_runtime()` 返回 0.26.0，`harbor plugins list` 列出 `dressage`，DAPO 检查退出 0。

同一环境的合同文件 18 项通过，涵盖两份官方 Job YAML。默认 Harbor 集成套件共 79 项通过（含上述 18 项和宿主 bwrap Oracle），8 项 `harbor_e2e` 按默认配置排除。套件从源码副本读取 `examples/` 测试材料，Dressage 与 Harbor 均使用安装包。真实模型 rollout、远端沙箱和训练入口仍按 PR 级验收跟进。[修前安装记录](../../../investigations/04-version-checks/README.md#evidence) · [PR-001 验收入口](../README.md#acceptance)

<a id="post-commit-review"></a>

### 提交后评审 · 放行 0.26 后，模型请求是否仍由 Dressage 接管？

`a1087bb` 已验证安装与版本检查。下面三项是 PR-001 合入前的评审记录。主 Agent 的修复和验收已记入 C07。

| 评审意见 | 已有证据 | 如何决定和验收 |
|---|---|---|
| P1 · 主 Agent 的连接覆盖 | 已在 `a1087bb` 用同一 Claude Code + Qwen Job 复现。常规配置得到 Gateway 和 Trial 凭证；只改 `base_url` 会改变地址而保留 Trial 凭证；只改 `model_api_key_name` 会保留 Gateway 而改变密钥。离线截获启动参数。[三组实测](../../../investigations/07-agent-routing/README.md#c06-main-agent) | 本地 `0b3d570` 已撤回。正式实现 `73347a1` 已推送至个人 Dressage 分支，标准配置的最终地址和凭证已通过同一组断言。[07a · Gateway 地址与 Trial 凭证](07-main-agent-routing/07a-claude-base-url.md) |
| P1 · 模拟用户的角色归属 | Harbor 可从 `user_agent` 创建第二个 Agent；Dressage 启动插件时只为主 Agent 配置路由。这里的依据是源码，双角色 Trial 的实际请求和轨迹尚待验证。 | 若只训练主 Agent，模拟用户的回复应进入主 Agent 的输入上下文，其自身采样是否收集需另定。先确定是否支持这种 Job；若暂不支持，验证插件在分配路由前明确拒绝。 |
| P2 · 凭证预检早于插件注入 | 既有对照确认部分模型配置在 `Job.create()` 阶段因缺少厂商凭证失败；评审另外报告了 Terminus-2 用例。[调查 06](../../../investigations/06-agent-credential-preflight/README.md#evidence) | 分别从 CLI runner 和训练临时 Job 验证。若确认阻断，由 Gateway 管理的 Job 可使用 Harbor 的 `skip_credential_checks`，并验证 Dressage 自身的后端凭证检查仍生效。 |
