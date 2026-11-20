# PR-001 · Dressage 适配 Harbor 0.26.0

<a id="scope"></a>

上游已发布 [Tracking Issue #44](https://github.com/Accio-Lab/Dressage/issues/44)，[第一条评论](https://github.com/Accio-Lab/Dressage/issues/44#issuecomment-7035038442) 按模块列出兼容性差异、处理方式和运行边界。发布原文见 [Issue 正文](tracking-issue.md) 和 [审计评论](compatibility-comment.md)。

**上游 [Draft PR #45](https://github.com/Accio-Lab/Dressage/pull/45) 已关闭，未合并。** 首版从公开 fork `dextermayhewjd/Dressage-contrib:compat/harbor-0.26` 向 `Accio-Lab/Dressage:main` 提交 C01–C04、C05a 和 C06，共 6 笔，基线为 `3e3142f`，首版提交为 `a1087bb`。目标是在 `harbor==0.26.0` 上交付现有 CLI rollout 和训练接入。当前先打通本地 Trial 的预检、独立评测与奖励交回。[版本决策](../../investigations/00-version-target/README.md)

<a id="review-order"></a>

## 这个 PR 准备拆成哪几笔 commit？

下表按实施顺序排列，正式提交后关联 Dressage 的 Git SHA。C04 后的完整 Trial 暴露了日志目录问题，单列为 C05，原定的版本声明顺延为 C06。每张卡都在②写修前现象，③定位原因，④说明改法，⑤给出验收。新卡直接复制五节模板。[提交卡模板](../../review-format.md#commit-card) · [Codex 评审入口](../../tools/upgrade-sop.md#codex-review-timeline)

| 计划提交 | 在哪个场景出了什么问题，这笔怎么改？ | 用什么结果验收 | 调查依据 |
| --- | --- | --- | --- |
| <a id="preflight"></a>[C01 · 环境预检](commits/01-environment-preflight.md) | Trial 排队前，0.26 工厂传 `kwargs`，旧后端在预检前报错。让后端接收选项、调用基类，再执行 bwrap 检查。 | 默认、显式 `None`、空字典和非空字典均原样到达基类，随后进入后端检查。 | [调查 01](../../investigations/01-environment-preflight/README.md#implementation) |
| <a id="mounts"></a>[C02 · 日志交付](commits/02-output-mounts.md) | Trial 回收日志时，0.26 会把已直挂的非空目录复制回自身。对齐 Harbor 查询到的宿主路径与 bwrap 的实际挂载。 | 直挂下载 0 次，改绑下载 1 次，两者都能在目标目录读回原文件字节。 | [调查 02](../../investigations/02-output-mounts/README.md#mount-matrix) |
| <a id="fixture"></a>[C03 · verifier 测试夹具](commits/03-verifier-fixture.md) | 夹具传 `mounts`，0.26 的真实 Trial 传 `auto_mounts`。夹具构造出的 verifier 多了日志挂载，改成与 Trial 相同的传参。 | 复跑原环境测试，确认独立 verifier 只取得预期目录。 | [调查 03](../../investigations/03-verifier-fixture/README.md) |
| <a id="verifier-start"></a>[C04 · 独立 verifier 启动](commits/04-verifier-start.md) | Harbor 准备从宿主上传测试，后端却先从 `environment/` 复制文件，缺目录就启动失败。让后端准备空的 `/tests`，交给 Verifier 上传。 | 缺少 `environment/` 仍能评出 reward 1。有环境材料时，启动时的 `/tests` 不混入这些材料。 | [调查 21](../../investigations/21-separate-verifier-input/README.md) |
| <a id="c05-log-directories"></a><a id="sandbox-log-dirs"></a>[C05a · Agent 第一次写日志](commits/05-log-directories/05a-sandbox-log-directories.md) | 关闭自动挂载且没有宿主挂载覆盖日志时，在沙箱中准备声明的可写输出目录。 | Oracle 执行解法，Harbor 收回含 `solved` 的 `agent/oracle.txt`，verifier 返回 1 分。 | [修前对照](../../investigations/02-output-mounts/c05-mount-experiments.md#first-write-probe) |
| <a id="versions"></a>[C06 · 声明支持 Harbor 0.26.0](commits/06-harbor-version.md) | 安装依赖仍锁定 0.18.0，两处运行时检查会拒绝 0.26.0。本笔一起切换依赖、版本检查、合同测试和安装说明。 | 干净环境安装得到 0.26.0，插件和 DAPO 的运行时检查接受该版本。 | [调查 04](../../investigations/04-version-checks/README.md) |
| [bwrap 回环初始化](validation.md#bwrap-loopback) | `b589289` 检查隔离命名空间的回环接口。已开启时直接启动 relay。 | 正式 CLI 跑一题，Gateway 转发请求，verifier 返回 1 分，manifest 指向该 trial。 | [修前与修后验收](validation.md#bwrap-loopback) |
| [C07 · 主 Agent 的 Gateway 连接](commits/07-main-agent-routing/README.md) | [07a · Gateway 地址与 Trial 凭证](commits/07-main-agent-routing/07a-claude-base-url.md) 原本地提交 `0b3d570` 已撤回；正式实现 `73347a1` 已推送至个人分支。[07b · Claude settings](commits/07-main-agent-routing/07b-claude-settings.md) 和 [07c · Codex profile](commits/07-main-agent-routing/07c-codex-profile.md) 的改动保存在备份工作树。 | 公共模型连接已在工作区完成配对验证，原生配置另见 07b、07c。 | [调查 07](../../investigations/07-agent-routing/README.md) |

### 当前进度

C01 至 C04 均已推送到个人 Dressage 的 `compat/harbor-0.26` 分支。C01 `8827b11` 的六例预检通过。C02 `8023acd` 的三种日志回归通过，独立评分和产物交付已复核。C03 `600b8cd` 复核了两种角色的挂载清单，整个环境测试文件 12 项全过。[C03 提交卡](commits/03-verifier-fixture.md) · [C02 提交卡](commits/02-output-mounts.md) · [C01 的远端复验](../../investigations/01-environment-preflight/README.md#amended-check)

<a id="current-status"></a>

个人 Dressage 仓库的 `compat/harbor-0.26` 分支已包含两笔独立修复：`b589289` 修复 bwrap 回环初始化，`73347a1` 绑定 Gateway 地址与 trial 凭证。后续训练验收需单独处理默认配置生成的 seed 超出有符号 64 位范围的问题。[本地入口验收](validation.md#entrypoint-experiments)

**C04 在私有开发仓库的提交为 `e6c0ce4`。** 具备权限的环境测试 15 项全过。公开 PR 首版还包含 C05a 和 C06。[C04 复评与实测结果](commits/04-verifier-start.md#formal-check)

**C05a 和 C06 均已本地提交，分别为 `8f51d19` 和 `a1087bb`。** bwrap Job 要沿用原版日志直挂流程，可在 Harbor Job 的 `environment.kwargs` 中设 `auto_mounting: true`，走 C02。默认关闭自动挂载时，日志可写在 C05a 准备的沙箱目录，由 Harbor 在 Trial 收尾时取回。[三种运行方式](commits/05-log-directories/README.md#mount-choice) · [C06 干净安装与回归结果](commits/06-harbor-version.md)

**C05b 暂停，移出第一轮必做项。** 手动把空宿主目录挂到 `/logs` 时，0.26 相对 0.18 有已知回归。这道 Oracle 题预建 `agent/` 和 `verifier/` 后可交付普通日志并得 1 分。若上游维护者确认宿主空目录初始化属于正式用法，再单独约定目录归属并提 CL。若上游要求随升级交付，则将 C05b 列为合并阻塞项。[已知回归](commits/05-log-directories/05b-mounted-output-directories.md) · [修前与候选对照](../../investigations/02-output-mounts/c05-mount-experiments.md#c05b-empty-mount)

**C06 从干净的 C05a 开始。** 临时评审目录撤下的是 45 行窄版候选。正式升级工作树另外留有通用挂载检查及其测试，分布在 `environment.py` 和 `test_environment.py`，共新增 732 行、删除 62 行。空宿主目录的归属与初始化权限仍待确认，保留这份实验代码会让 C06 的版本验收跑在第一轮 PR 范围之外。两处差异已从正式工作树撤下，核对 `HEAD` 为 `8f51d19`、工作树干净。归档补丁已在同一基线上重新应用，两个文件均与撤下前逐字节一致。[正式工作树旧实验补丁](../../archive/c05b-general-worktree.patch) · [45 行窄版候选](../../investigations/02-output-mounts/c05b-empty-log-mount.patch)

**为什么一起评审**　01 的实现调用 `super().preflight(kwargs)`；0.18 基类只接受 `cls`。决定合并边界时，要把后端行为和主分支声明的 Harbor 版本一起核对。候选修改的分组可随正式 diff 调整。[旧版基类](https://github.com/harbor-framework/harbor/blob/v0.18.0/src/harbor/environments/base.py#L863) · [合并与提交约定](../../tools/upgrade-sop.md)

<a id="acceptance"></a>
<a id="test-order"></a>

## 哪些入口还要验？

模型请求能否由插件接管，按 [C06 提交后评审](commits/06-harbor-version.md#post-commit-review) 的三项证据与待验条件跟进。

| 承诺的入口 | 评审人最终要见到什么 | 现有证据 |
| --- | --- | --- |
| 安装与发现 | 干净环境安装修后 wheel，得到 0.26.0，CLI 按短名找到插件。 | Python 3.12.3 中已通过，BlackboxServer 1.1.0 来自同仓 wheel。CLI 发现插件，DAPO 退出 0。[C06 验收](commits/06-harbor-version.md) |
| <a id="runtime"></a>CLI rollout | 正常 Trial 的请求抵达预期 Gateway，奖励和已提交的 manifest 可读；取消路径释放路由并排除该尝试。 | 真实 bwrap 与 Claude Code 的本地 CLI 正常路径已验，推理使用固定回答。取消路径仍待验。[运行验收](validation.md#test-order) |
| <a id="training"></a>Slime 训练接入 | 重试后，JobResult、manifest 和返回给 Slime 的样本均指向最终采用的尝试。 | Slime 训练 rollout 入口在 `seed_policy: agent` 下实际重试一次，三者都指向第二次尝试。默认 seed 策略仍有越界问题，GPU 权重更新待验。[训练验收](validation.md#training) |

<a id="handover"></a>

具体命令、各阶段观察点和此前判断见[四组验收顺序](validation.md#test-order)和[发布交接](validation.md#handover)。按需回查 <a id="skills"></a>[Skills](validation.md#skills)、<a id="job"></a>[Job 配置](validation.md#job)、<a id="network"></a>[网络](validation.md#network)、<a id="e2b"></a>[E2B](validation.md#e2b)与 <a id="checkpoint"></a>[旧 checkpoint](validation.md#checkpoint)。
