# Harbor 0.26 升级 · 审查记录写成什么样

这是一份供共同评阅的格式草案。先看一份记录的产出，再决定怎样生成它。目录名和编号沿用本项目，下面注明哪些字段来自社区实践、哪些是我们为了跨版本核查而增加的。执行顺序、复现命令和证据也在本升级目录里。[执行 SOP](tools/upgrade-sop.md) · [复跑命令](tools/reproduce.md#run-probes)

<a id="community-example"></a>

## Slime 社区怎样交付一次升级？跟着一个旧配置看

Slime 把 SGLang 升到 0.5.21 时，PR 正文承诺原有 YAML 配置继续生效。拿其中一个旧键就能看见维护者实际收到的东西。[已合并的 Slime PR #2476](https://github.com/THUDM/slime/pull/2476)

1. **在源码里保住旧写法。** 用户的配置写 `cuda-graph-max-bs: 8`。Slime 组装服务参数时，如果目标版本只认识新字段，就把这项传成 `cuda_graph_max_bs_decode=8`。[配置转换的源码](https://github.com/THUDM/slime/blob/4ac368bbb196bdb7637c8f36e2be91b56277b335/slime/backends/sglang_utils/sglang_engine.py#L631-L671)
2. **在测试里证明旧配置仍起作用。** 测试故意把新字段的初始值设成 `32`，再传入旧键和 `8`。它检查最终生成的参数确实是 `8`。如果代码只接受了旧键却忽略它，测试就会发现。[输入样例与最终断言](https://github.com/THUDM/slime/blob/4ac368bbb196bdb7637c8f36e2be91b56277b335/tests/utils/test_sglang_config.py#L289-L335)
3. **在 GitHub PR 里交给维护者评审。** 正文说明兼容目标和作者跑过的验证，`Files changed` 可对照实现与测试，`Checks` 展示自动检查。该 PR 页面显示 1 笔提交已合入 `main`。公开记录能核实交付内容，作者个人如何保存排查笔记则无法从中确认。[这份 PR 的改动](https://github.com/THUDM/slime/pull/2476/files) · [GitHub 对评审页面的说明](https://docs.github.com/en/pull-requests/reference/pull-requests#working-with-pull-requests)

<a id="example"></a>

## 对照 Dressage 的工厂预检记录

**U34 的问题是，Harbor 工厂调用 Dressage 环境预检时，后端有没有机会执行自己的检查？** 固定 Dressage `3e3142f`，给工厂同一个环境类路径，使用默认选项。用下面三行就能区分用法观察、调查决定和交付状态。

| 记录 | 打开后应能读到的实际内容 | 这条记录支持什么判断 |
| --- | --- | --- |
| 用法 U34 | Harbor 0.18 调 `env_class.preflight()`，探测到达 Dressage 的 bwrap 配置检查。Harbor 0.26 调 `env_class.preflight(kwargs=None)`，同一个后端在绑定参数时抛出 `TypeError`。 | 差异定位到工厂与后端的交接。观察停在预检入口。[两端原行与版本表](usage/环境构造与生命周期/U34-EnvironmentFactory%20调用%20DressageEnvironment.preflight.md#u34) |
| 调查 01 | 原测试直接调用后端可以通过。改从真实工厂进入后，0.26 的默认值、显式 `None`、空字典三例都失败。候选改法让基类解析选项，再执行后端检查。 | 有理由改实现并补工厂回归。从三例探测扩充到四例工厂回归，并保留直接调用用例。改写后的 C01 `8827b11` 加入上游签名快照，六例通过。[正式复验](investigations/01-environment-preflight/README.md#amended-check) · [修前输出](investigations/01-environment-preflight/factory-contract-results.txt#L16-L29) · [实验与改前上下文](investigations/01-environment-preflight/README.md#implementation) |
| PR-001 | 01 的候选修法会给基类传选项，Dressage 原依赖 0.18 的基类只接受 `cls`。评审草稿因此把该修复与 0.26 版本切换放在一起考虑。 | 可以说明为何一起评审。C01 已本地提交，最终版本上的完整 Trial 和训练入口仍待验。[候选改动](prs/001-harbor-026-compatibility/README.md#scope) · [交付验收](prs/001-harbor-026-compatibility/README.md#acceptance) |

<a id="impact-analysis"></a>

## 拆提交以前，先做一次变更影响分析

在调查页里沿着这次改动追一个实际结果。**旧实现顺手准备了什么？哪些调用方依赖这份状态？谁最先会因此失败？** 固定版本和任务，让真实调用方使用这份状态。特别检查测试是否提前帮它做了那一步，例如上传样本日志时顺手建了目录。原始输出留在调查页。

发现几个相关场景后，先用同一输入对照前一笔提交与当前候选，再决定如何交付。

| 实测看到什么？ | 怎么拆？ |
| --- | --- |
| 同一个改动能恢复多个输入下的同一行为 | 一笔提交，用多个输入验证。例如 C01 让后端接收并转交 `kwargs`，同一修改覆盖工厂传 `None` 和传 `{}`。[C01 的实现与回归](prs/001-harbor-026-compatibility/commits/01-environment-preflight.md) |
| 两处修改必须配合才产生这次要交付的行为，中间状态没有可独立验收的结果 | 将两处实现和证明该行为的测试放在同一笔。 |
| 第一笔修好一种配置，另一种配置仍能独立复现失败，且需要不同的修改 | 在同一主题下开第二笔，各自保留修前失败和修后结果。 |
| 前一笔能通过，当前候选让同一配置失败 | 在当前候选修复这次引入的回归，并保留该配置的测试。 |

对于可以脱离本次改动单独复现的问题，在调查页记下其触发条件和消费方，再判断是否属于本次 PR 的交付范围。尚缺版本对照时标为待验。

**父页和子卡都沿用①到⑤。** 父页开头用一句话点出用户任务和要追踪的结果。①先写各组都要满足的约定，如果分支来自可选配置，就在①末说明默认用法与主动选择另一项的理由。②给出同一修前版本上的实际表现，③解释哪项条件改变了行为，④决定改法并链接相应子卡，⑤用共同预期核对各组结果。[C05 父卡的阅读顺序](prs/001-harbor-026-compatibility/commits/05-log-directories/README.md#shared-analysis)

初读按父页顺序走完。审某笔时从④进入子卡，核对该笔的修前版本、故障、代码与断言，再回父页⑤。共同结论和跨组对照写在父页，只有一组才需要的实现细节和回归写在子卡。单笔改动沿用一个 Markdown 文件。

这里借用了两项实践。ISTQB 用影响分析确定哪些行为需要回归验证，Google 建议让一项可独立理解的逻辑变更连同相关测试一起评审。主题目录和五节提交卡是本项目的记录方式。[ISTQB CTFL §2.2.3、§2.3](https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf#page=31) · [Google Engineering Practices · Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html)

<a id="commit-card"></a>

## 提交卡模板

每笔跟一个具体输入或产物走到底。比如 C01 跟工厂传来的 `kwargs`，C05b 跟 Agent 要写的 `oracle.txt`。打开卡先读页首那句决定；想判断是否值得改，看②的修前结果；想判断是否修对，看④的选择能否通过⑤的断言。五节的编号和名称固定，标题后半句写本笔的具体行为。[C01 完整例子](prs/001-harbor-026-compatibility/commits/01-environment-preflight.md) · [C05b 简短例子](prs/001-harbor-026-compatibility/commits/05-log-directories/05b-mounted-output-directories.md)

复制下面的 Markdown 到 PR 的 `commits/` 目录，替换尖括号内的提示。简单的一节写一句话即可。

```markdown
# C<编号> · <本笔要恢复或保证的行为>

**本笔决策**　<谁改哪一步，让哪个下游得到什么结果。>
修前 <Dressage SHA> · Harbor <目标版本> · <待评审 / 已本地提交 SHA / 已推送 SHA>

## ① 上游约定 · <框架要求什么>

沿同一个入口，写清调用方交出什么、接收方应当做什么。需要时对照旧版和新版。

## ② 修前表现 · <用户或测试实际看到了什么>

固定一个输入。预期会得到什么？在准确的修前版本上实际得到什么？

## ③ 原因定位 · <哪一处最先偏离约定>

指出文件、函数或关键原行。把②的输入代入，解释这行为什么会产生那个结果。

## ④ 修复决策 · <在哪一侧恢复行为>

写最小改动及理由。指出一条原本能工作的相邻路径，以及它需要保住的结果。

## ⑤ 回归验证 · <哪个观察能判定修对>

旧测试从哪里进入，漏看了哪一步？新测试从哪里进入，在消费端断言什么？
写修前和修后观察、测试入口。尚未运行的用例写“待验”和通过条件。

## 证据索引

<链接到支撑上述判断的固定源码、调查或复跑记录。>
```

**认清②和③的区别。** C05b 的②是 Oracle 打开日志文件时发现目录不存在；③是更早的 `start()` 因父目录已挂载而跳过建子目录。只修测试夹具时也用同一套问题，比如 C03 的②是夹具在断言之前报错，③是夹具与真实 Trial 的传参不同。后续提交若沿用前一笔的上游约定，①可直接引用已有结论。

调查页保存排查顺序和完整实验，提交卡保存本笔决定及证据入口。Git 提交说明提炼④的改动和理由，PR 页汇总依赖与整体验收。正式提交后把真实 SHA 写回卡首。

<a id="formats"></a>

## 五个目录各交付什么

| 放在哪里 | 写入哪些字段 | 读者如何检查这份产出 |
| --- | --- | --- |
| `usage/` 一次交接一张表 | 调用方和被调用方的固定版本及原行、任务输入、各版本传参、返回值或副作用、消费方实际观察、证据范围。 | 给读者同一输入，能指出第一个行为差异或说明已观察到一致的范围。缺少运行证据时，写出要在下游观察的值、文件或状态。[日志回收用法与实际观察](investigations/02-output-mounts/README.md#mount-matrix) |
| `investigations/` 一个可独立裁定的问题一页 | 关联用法、环境与版本、最小复现、预期、实际、两边的源码依据、决定及验收条件。修改时追加修后结果和真实 SHA。 | 他人能复现问题，理解为什么修、沿用或继续调查。结论是“沿用”时也能找到实测边界。[05 的文件写入与读回](investigations/05-skills-upload/README.md#evidence) |
| `prs/` 一个合入目的一页 | 标题说明改什么，正文说明为什么、用户可见影响、关联调查、纳入的提交、可以一起合入的理由、测试结果及待验范围。 | 维护者可以从目标分支和公开复现命令评审这个 diff。正式 PR 创建后补链接，合并后补最终 SHA。[PR-001 的本地评审稿](prs/001-harbor-026-compatibility/README.md#scope) |
| `tools/` 一种核查方法一个可复跑入口 | 目的、输入仓库与固定提交、命令、如何筛选、输出文件、未覆盖的调用形式。 | 同一版本可重建清单。说明“命中一行”“确认一次交接”“运行验证通过”各自依据什么。[固定版本扫描器](tools/scan_harbor_surface.py) · [扫描产物](usage/harbor-call-sites.md) |
| `archive/` 一份历史材料一个出处 | 原件、来源与版本、冻结原因、当前接续位置。压缩包可附 SHA-256 供逐字节核对。 | 能回答“当时根据哪份材料作判断”和“现在应去哪里接着看”。本次旧工作树笔记包摘要为 `2bc2b813c79e21f90351703f1cfb90cf66cfd0298b1c371957ffd74bb3103c61`。[归档原件](archive/dressage-worktree-notes-3e3142f.tar.gz) · [材料迁移对照](tools/reproduce.md#provenance) |

<a id="sources"></a>

## 目录和字段各有什么社区依据？

这次升级按审查时要查找的产物分目录。Kubernetes 有按提案建目录的成例，Google AIP-180 说明怎样判断接口兼容，Google 的代码评审指南说明怎样拆分变更。这些资料各有适用范围，五个目录的组合是本次 Dressage 升级的本地约定。

| 社区原文中的观察点 | 本项目怎样采用 |
| --- | --- |
| Kubernetes 增强提案（KEP）模板明写 *Make a copy of this template directory*。目录用上游 enhancement issue 的编号和短标题命名。真实例子 `753-sidecar-containers/` 把提案正文 `README.md` 和状态等元数据 `kep.yaml` 放在一起。[KEP 模板原文](https://github.com/kubernetes/enhancements/blob/master/keps/NNNN-kep-template/README.md#L19-L27) · [753 的实际目录](https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/753-sidecar-containers) | 借用“一项可独立评审的事情有一个稳定入口”。调查 01 把判断、复现测试、失败输出放在同一目录。01 采用本地编号，若上游有对应 issue，再关联它的真实链接。[调查 01](investigations/01-environment-preflight/README.md#implementation) |
| Google AIP-180 区分源码、传输和语义兼容，其中 *Semantic compatibility* 关心已有调用方能否继续得到合理预期的行为。[Google AIP-180](https://google.aip.dev/180#guidance) | 把这个问题写成 `usage/` 的一列。例如回收日志后，宿主目录能否读到预期的文件字节？这次 Python 集成按实际调用方式选择断言，三版并排和 U 编号是本项目的做法。[实际读回结果](investigations/02-output-mounts/README.md#mount-matrix) |
| Slime 的 bug 表单分别填写 *Steps to Reproduce*、*Expected Behavior*、*Actual Behavior*、*Environment* 和 *Logs*。 | 调查页分开写复现条件、预期、实际和原始输出。额外写“这个差异在 Dressage 下游意味着什么”，将公开报错格式延伸到本地升级判断。[Slime 的实际表单](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/.github/ISSUE_TEMPLATE/bug_report.yml#L20-L83) |
| Slime 在同一份升级 PR 交付兼容实现、回归测试和验证说明。[旧 YAML 配置的实例](#community-example) | Dressage 的 PR 草稿先交代承诺保住的流程，再列各项验证。预检修复已有五例行为回归和一例上游签名快照，完整 Trial 和训练入口另列待验。[PR-001 的验收记录](prs/001-harbor-026-compatibility/README.md#acceptance) |
| Google 的变更说明要求解释改了什么和为什么。小变更指南要求改动能独立理解，带相关测试，并考虑合入后系统能否继续工作。Kubernetes 的实际 PR 模板还询问维护者应注意什么、是否有用户可见变化。 | PR 页首写改动和理由，再给合入边界、验证及用户影响。`tools/` 与 `archive/` 是本项目为复现和保存判断依据安排的目录。[Google 变更说明](https://google.github.io/eng-practices/review/developer/cl-descriptions.html) · [Google 小变更指南](https://google.github.io/eng-practices/review/developer/small-cls.html) · [Kubernetes PR 模板](https://github.com/kubernetes/kubernetes/blob/master/.github/PULL_REQUEST_TEMPLATE.md) |
