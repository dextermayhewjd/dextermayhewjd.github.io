# Harbor 0.26 升级 · 从一个问题到一个 PR

每种记录应写哪些字段、产出由谁检查，以及字段对应的社区原文，见[审查记录格式草案](../review-format.md#formats)。

从 [usage 的调用表](../usage/README.md#routes) 找到发生差异的位置，再打开相应调查项。要亲自走一遍，先看 [01 的改前上下文与提交记录](../investigations/01-environment-preflight/README.md#implementation)，再看 [PR-001 怎样决定交付范围](../prs/001-harbor-026-compatibility/README.md#scope)。

## 检查一次跨库调用的三问

其他仓库遇到类似的升级，可以按受影响的行为选择测试范围，再从使用者约定推导断言。

先写清谁在什么时候调用谁。C01 的方向是 `Harbor CLI → 环境工厂 → DressageEnvironment.preflight`。对同一份任务配置，从真实调用入口依次检查三件事。

| 检查什么 | C01 怎么判断 |
| --- | --- |
| ① 原入口还能找到吗？ | 用原来的 `environment.import_path` 让工厂解析。0.26 仍能取到 Dressage 提供的类和它的 `preflight` 方法。 |
| ② 调用方实际传什么，接收方还能接住吗？ | 0.18 调 `preflight()`。0.26 调 `preflight(kwargs=kwargs)`，这份 CLI 配置下传的是空字典。旧签名在进入方法体前就报错。 |
| ③ 下游依赖的结果或效果还成立吗？ | 预检成功时返回 `None`。C01 测试观察基类是否收到选项原值、Dressage 是否开始检查 bwrap。本次回归验证到这里，完整环境启动另有验收入口。 |

下次升级，保留同一份任务输入，从旧版和候选版的真实调用方各走一次。第一个不符合预期的位置给出适配起点，下游实际依赖的行为给出回归断言。新版多出的字段若不影响消费方，可以直接沿用现有实现。[C01 的调用与回归证据](../prs/001-harbor-026-compatibility/commits/01-environment-preflight.md)

### 测试失败后，怎样决定改哪一侧？

写用例时保留这次交接的真实双方。Dressage 调外部库时，从 Dressage 的调用入口进。Harbor 回调 Dressage 时，从 Harbor 的工厂进。把慢的系统操作放在交接之后替代，例如记录将要执行的 bwrap 命令。先断言下游能观察到的效果，需要区分两种根因时再加局部断言。[Google 工程手册 · 通过公开接口测试](https://abseil.io/resources/swe-book/html/ch12.html) · [选择真实实现与测试替身](https://abseil.io/resources/swe-book/html/ch13.html)

| 同一份 Dressage 与输入，旧版通过、候选版失败 | 首先核对什么，再决定改哪里 |
| --- | --- |
| 函数还没进入，报 `unexpected keyword argument` | 对照调用行和接收方签名。C01 是 Harbor 按新版约定传 `kwargs`，接收方属于 Dressage，因此改 Dressage 的方法签名并按新版要求转交选项。 |
| 调用成功，消费方拿到的内容不对 | 用一个可辨认的输入追踪实际值。例如传 `{"test_marker": "keep"}`，在首个丢失内容的位置检查转换或转交。 |
| 只看到内部方法的调用次数变了 | 用真实入口核对公开行为。如果选项仍被正确处理、后端仍能预检，更新测试的观察点。如果行为也变了，再定位实现。 |

<a id="codex-review-timeline"></a>

## 看手里的材料，选 Codex 的 /review 入口

从上往下找当前状态，只选那一行。图中标出 2026-11-19 的 C01、C02 位置，操作目录为 `Dressage-harbor-0.26`。

```text
手里只有方案卡 ────────── ④ Custom review instructions（指定卡片和疑问）
       │
       ▼
开始写实现、补测试 ────── 普通对话     ◀ C02 在这里，方案已审
       │
       ▼
有代码改动，还没 commit ── ② Review uncommitted changes
       │
       ▼ git commit
已有提交 ─┬─ 只查一笔 ─── ③ Review a commit（选择 SHA，例如 C01 的 8827b11）
          └─ 准备提 PR ── ① Review against a base branch（选择 main，看累计改动）
```

C01 在北京时间 11:38 创建提交，11:43 本地 Git 记下推送。③ 从取得本地 SHA 时就可用。C02 的下一次代码 review 在正式改动写入工作树后，用②。[C01 的提交与复验](../prs/001-harbor-026-compatibility/commits/01-environment-preflight.md) · [C02 的方案审查结论](../prs/001-harbor-026-compatibility/commits/02-output-mounts.md)

## 怎样用目录拆问题和交付

| 要做的决定 | 记录的位置 | 什么时候另开目录 |
| --- | --- | --- |
| 这个问题如何复现、怎样才算修好？ | `investigations/<编号>-<问题>/README.md` 放改前上下文、根因、通过条件和修复提交。实验脚本和输出与问题页放在一起。 | 同一根因的新输入、同一修复的补充证据写回原页。需要独立决定怎么修、且通过条件不同的，另开调查项。例如 02 验真实日志交付，03 验 verifier 测试夹具。[02 与 03 的拆分依据](../investigations/README.md) |
| 下一笔 commit 交付哪个行为？ | 在所属 PR 首页列候选顺序。轮到修改时，在 `prs/<PR>/commits/` 按[提交卡模板](../review-format.md#commit-card)写卡。单笔用一个文件，同一问题拆出的多笔归入一个主题目录，由目录 README 对照。 | 一项新的行为需要它自己的修改和断言时再拆一笔。同一行为的实现与回归放在一起。修前输出引用调查页，正式提交用 Git SHA 查实际 diff。[完整的 C01](../prs/001-harbor-026-compatibility/commits/01-environment-preflight.md) |
| 哪些改动请求维护者一起合并？ | `prs/<编号>-<目的>/README.md` 是评审首页，链接所含调查项和提交。验收较长时，在同一目录放具体场景、结果和评审记录。 | 有独立交付目的、单独合并后仍能满足主分支版本契约的改动，可以另开 PR。必须一起生效的提交留在同一个 PR，说明依赖。 |

## 每次修改怎样走

| 时刻 | 动作和完成条件 |
| --- | --- |
| ① 选问题 | 从一个用户可见的结果往回找。用固定基线、目标版本和相同输入定位首个差异。把复现命令、预期、实际和下游影响放进调查项。上游已有相关报告时记下链接。若改动影响多个场景，先核对它们依赖的状态，再决定拆几笔。[变更影响分析与提交拆分](../review-format.md#impact-analysis) |
| ② 给改前上下文 | 复制[提交卡模板](../review-format.md#commit-card)。固定一个输入，写清约定、修前表现和原因，再列候选修法与消费端的验收条件。未运行的用例标为待验。读者确认后进入这笔修改，范围变化时重新交代。 |
| ③ 形成小 commit | 在 Dressage 工作树里用同一输入复现、修复并复验。一笔提交解释一个逻辑变化，带上证明该行为的回归测试。几项调查指向同一改动时，可以引用同一个 SHA。 |
| ④ 登记证据 | 正式提交后，把 Dressage 修复 SHA、该提交上的命令和结果追加到调查项的判断记录；在页首指向这条记录和关联 PR。若需多笔提交，逐笔标明作用。决定沿用现状时写依据及验证边界即可。 |
| ⑤ 组 PR、验交付 | 在 PR 首页列目标、关联问题、实际提交和一起合并的理由。从承诺的入口验证最终输出；写清已经跑过和仍待验的场景。检查命令见[复跑说明](reproduce.md#provenance)。 |
| ⑥ 合并后可追溯 | 本地 PR 页登记真实上游 PR 链接和最终合并 SHA。若 squash 或 rebase 改写了 SHA，保留分支提交与最终 SHA 的对应。问题页指向 PR 页即可追到最终版本。 |

**讨论怎样存。** 改变根因、修法或验收条件的讨论，带上日期和依据写回相应调查项。影响哪些改动一起交付的决定写到该 PR 的评审记录。`archive/` 保存已被后续材料替代的历史快照。

<a id="downstream"></a>

## 怎样确认原来的下游任务仍然正确？

带着一个具体用法做下一次评审时，可调用 `$dependency-upgrade-review`。新项目可用它从固定提交生成 `usage/` 等五类目录、登记交接和归档原件。每个动作都可先预览。当前 Dressage 审查已有 61 项用法和专用校验，继续沿用现有编号。

Google 的代码评审指南要求审查组件交互、用户实际得到的行为，以及实现出错时测试能否发现。Google 的 API 指南把“调用方还能得到合理预期的行为”称为**语义兼容**。本次升级借用这个判断来检查 Dressage。Harbor 各版本实际提供的行为，以本项目的源码和运行结果为准。[Google 代码评审指南](https://google.github.io/eng-practices/review/reviewer/looking-for.html) · [Google AIP-180](https://google.aip.dev/180#semantic-changes)

| 什么时候 | 怎么选验证 | 证据写在哪里 |
| --- | --- | --- |
| 改前 | 从相关 U 找到实际消费方，写一句可验证的预期，例如“Trial 收尾后，宿主目录能读回同一份非空日志”。固定输入和配置，区分原流程应保留的结果、此次有意改变的行为和待确认的差异。 | 在已有调查页的“处理与验收”记录预期和修前证据。 |
| 每笔修复 | 用相同输入复跑触发故障的路径，再跑受同一改动影响、原本正常的分支。在消费方断言它读到的值、文件或状态。 | 调查页记录修复 SHA、测试命令和两条路径的实际结果。 |
| 合并前 | 在最终候选提交上跑多笔修改共同影响的任务。一份运行可覆盖多个 U。若承诺训练接入，重试后检查 Job 选择的尝试、manifest 采用的尝试和 Slime 收到的 Sample 三者身份一致。关键结果仍待验证时，在 PR 保留待验状态。 | PR 的验收页汇总任务结果、运行版本和未覆盖范围。[已有四组场景](../prs/001-harbor-026-compatibility/validation.md#test-order) |

**调查 02 示范了为什么要在消费端断言。** 现有 0.18 基线在日志另绑目录时标记“已下载”，但宿主目录缺文件。0.26 基线在另绑时能正确交付文件，在直挂时却尝试复制回自身并记录错误。修后验收用同一个非空文件检查两个分支，直挂时零次下载且无复制错误，另绑时一次下载，最终都能读回原字节。这两条断言既能发现旧缺陷，也能保护目标版本原本正常的分支。[六次修前运行的原始输出](../investigations/02-output-mounts/trial-log-mount-matrix.txt)

<a id="upstream-pr"></a>

## 从调查 01 到一份维护者能评审的 PR

**这次升级统一用四项写 PR 正文。** ① 原来从哪里进入，升级影响谁。② 交付哪些行为修复或有意变化。③ 用哪些输入验证，消费端实际得到什么。④ 哪些场景还待验。前三项给出能公开复核的代码、命令或 CI 结果，第四项说明结论边界。上游已有 PR 模板时，将这些内容填写到对应栏目。[Google 的变更说明](https://google.github.io/eng-practices/review/developer/cl-descriptions.html)

1. **先切一笔能验证的提交。** 01 对应的行为是“0.26 工厂传入选项后，Dressage 能校验选项并继续 bwrap 预检”。初版提交 `435e9f2` 的标题是 `fix(harbor): validate environment options during preflight`。这笔提交包含后端修改和从真实工厂进入的回归测试。提交后，SHA、命令和五例结果已写回调查 01。[提交上的实际运行](../investigations/01-environment-preflight/README.md#worktree-check)
2. **再决定它能否单独合入。** 01 的实现调用 `super().preflight(kwargs)`，主分支固定的 0.18 基类只接受 `cls`。按当前方案，01 可以独立提交，进入上游时要与 0.26 版本切换及其必要修复共同验收。出现可以在主分支独立合入的行为时，再建新的 `prs/NNN-交付目的/`。[PR-001 的边界](../prs/001-harbor-026-compatibility/README.md#scope)
3. **用公开证据写 PR 正文。** 在 Dressage 升级分支核对相对上游目标分支的 diff，推送贡献分支，再向 Dressage 打开 PR。用四小段写明**影响、修改、验证、尚待验证**。例如预检段直接给出工厂调用、基线的 `unexpected keyword argument 'kwargs'`、修后测试命令和实际结果。维护者应能在 Dressage checkout 复现，公开正文使用上游路径和可访问的证据。若有对应 GitHub issue，引用其真实编号。[GitHub 的关联规则](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue)
4. **把上游反馈接回本地。** 在本地 PR 页登记上游链接。评审意见改变某项验收时，更新该调查页并在 PR 记录对应的新提交和复验结果。合并后登记最终 SHA。当前 PR-001 处于准备阶段，C01 已登记本地修复 SHA，完整入口待验。[PR-001 的验收页](../prs/001-harbor-026-compatibility/README.md#acceptance)

## 这些约定从哪里来

| 参考 | 在本次升级中怎样用 |
| --- | --- |
| [Slime Bug 表单](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/.github/ISSUE_TEMPLATE/bug_report.yml#L14-L74) · [贡献范围](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/CONTRIBUTING.md#L63-L79) | 让另一位工程师能够凭版本、输入、命令和预期复现同一问题。准备公开报告时先查重。 |
| [Slime 升级 SGLang 的 PR #2476](https://github.com/THUDM/slime/pull/2476) · [Slime CI](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/docs/zh/developer_guide/ci.md#L3-L18) | 先说升级要保住哪些调用，再按承诺选择验证。工厂回归能验预检，完整 Trial 才能验奖励、产物和清理。 |
| [Linux 补丁拆分指南](https://docs.kernel.org/process/submitting-patches.html#separate-your-changes) · [Google 小变更评审指南](https://google.github.io/eng-practices/review/developer/small-cls.html) | 按逻辑行为切 commit，按可安全合并的边界切 PR。比如 01 的修法要调用基类预检；如另开 PR，需核对合入时仍声明支持的 Harbor 版本。[0.18 基类签名](https://github.com/harbor-framework/harbor/blob/v0.18.0/src/harbor/environments/base.py#L863) |
| [GitHub 的 issue 与 PR 关联](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue) · [Dressage PR #38 的三笔提交](https://github.com/Accio-Lab/Dressage/pull/38/commits) | 本地用问题编号关联 Dressage SHA。向默认分支提交 PR 时，只有实际解决了对应上游 issue 才使用 `Closes #<上游编号>`。本地的 01 和 PR-001 各有自己的编号空间。 |
