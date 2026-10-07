---
title: "S07.10 Appendix：一套完整的 Skills 示例"
weight: 100
summary: "用可下载的 review-diff 练习工程覆盖 S07.1–S07.9；每份文件标明位置、讲解章节和注意点。"
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
---

这份附录把前九节放进同一个 `review-diff` 场景：审查未提交改动，找出可验证的回归，并按证据报告。**主例走完整的 inline 路径，互斥配置用独立变体观察。** 一份 Skill 不能同时既 inline 又 fork，也不能同时验证“自动可调用”和“只许用户调用”。

[下载完整练习包 ZIP](/downloads/s07-skills-lab.zip)。博客仓库内的源码位于 `examples/s07-skills-lab/`。下方文件内容直接从这些源码生成，下载包与页面使用同一份文件。

示例面向 Linux/macOS，需要 Python 3.10+、Git、Bash；实际技能运行另需支持相应配置的 Claude Code。官网字段与行为核对日期：**2026-10-04**。项目、缺陷和评估格式是本教程自定义的，不是官方内置 Skill 或 eval 协议。

## 先知道所有内容在哪里对应

| 章节 | 附录中的落点 | 这次覆盖的内容 |
|---|---|---|
| [S07.1 结构]({{< relref "/projects/learn-claude-code/s07/01-structure.md" >}}) | 主 `SKILL.md`、references、scripts、assets | 元信息、正文、配套资源；标准结构与 Claude Code 扩展 |
| [S07.2 发现]({{< relref "/projects/learn-claude-code/s07/02-discovery.md" >}}) | project 与 discovery 模板 | 项目、个人、嵌套、管理、额外目录、插件、账号和云端；同名来源与 `/skills` |
| [S07.3 调用]({{< relref "/projects/learn-claude-code/s07/03-invocation.md" >}}) | inline、manual、model-only 变体及 eval 正反例 | 用户点名、模型选择、描述质量、调用开关、应用侧拒绝 |
| [S07.4 渐进披露]({{< relref "/projects/learn-claude-code/s07/04-context.md" >}}) | 两份参考资料、脚本、调用轨迹和生命周期实验 | 元信息／正文／资源；文件已读与模型可见不同；重复调用、内容变化与压缩 |
| [S07.5 渲染]({{< relref "/projects/learn-claude-code/s07/05-rendering.md" >}}) | 参数、Git 动态快照、inspect-diff 脚本、失败变体 | `$ARGUMENTS`、`$0`、`$1`、技能目录变量；预处理与普通工具调用；失效快照与渲染失败 |
| [S07.6 权限与 Hook]({{< relref "/projects/learn-claude-code/s07/06-permissions.md" >}}) | allowed/disallowed-tools、Hook 脚本、权限 profiles | 工作指令／工具可用性／执行授权；deny 与预授权；JSON 决策；正文、临时权限、持久 Hook 与 once |
| [S07.7 子 Agent]({{< relref "/projects/learn-claude-code/s07/07-subagents.md" >}}) | fork-wait、fork-background、preload、worktree | 接收上下文、同步／后台、非交互例外、共享目录、隔离工作树、反向预加载 |
| [S07.8 评估]({{< relref "/projects/learn-claude-code/s07/08-evaluation.md" >}}) | 两种真实回归、cases.json、结果模板、关闭 Skill profile | 正例／反例、显式运行、质量与触发分开、无 Skill 基线、重复观察、分阶段定位失败 |
| [S07.9 接回循环]({{< relref "/projects/learn-claude-code/s07/09-agent-loop.md" >}}) | trace_inline.py | 目录、调用、正文、按需资源与工具结果串接；与真实产品实现区分 |

## 文件夹结构与生成位置

下载包本身是源码模板。运行生成器之后，`project/` 内的内容会复制到指定的新目录；某个变体的 `SKILL.md` 会成为该目录中的 `.claude/skills/review-diff/SKILL.md`。

```text
s07-skills-lab/
  README.md
  manifest.json
  project/
    .gitignore
    .s07-skill-lab
    .claude/
      skills/
        review-diff/
          SKILL.md
          references/input-boundaries.md
          references/concurrency.md
          assets/report-template.md
          scripts/inspect-diff.sh
        origin-probe/SKILL.md
      hooks/skill-hook.py
    packages/api/
      example.py
      .claude/skills/origin-probe/SKILL.md
    src/__init__.py
    src/normalize.py
    src/counter.py
    tests/test_contracts.py
  variants/
    manual/SKILL.md
    model-only/SKILL.md
    fork-wait/SKILL.md
    fork-background/SKILL.md
    render-failure/SKILL.md
    preload/SKILL.md
    preload/review-worker.md
    worktree/review-worker.md
  discovery/
    personal/origin-probe/SKILL.md
    managed-template/.claude/skills/origin-probe/SKILL.md
    additional/.claude/skills/extra-probe/SKILL.md
    plugin/.claude-plugin/plugin.json
    plugin/skills/origin-probe/SKILL.md
    account-upload/account-probe/SKILL.md
  profiles/
    without-skill.json
    deny-snapshot.json
    no-dynamic-shell.json
  evals/
    cases.json
    result-template.json
  tools/
    new_case.py
    trace_inline.py
    verify_lab.py
```

生成后另外出现：

| 生成路径 | 用途 | 对应章节 |
|---|---|---|
| `<练习目录>/.git/` | 保存正常实现与配置的基线提交，让 diff 有明确比较对象 | S07.8 |
| `<练习目录>/untracked-note.txt` | 演示 git diff 不包含未跟踪文件正文；也用于观察 worktree 边界 | S07.2、S07.5、S07.7 |
| `<练习目录>/.claude/agents/review-worker.md` | 仅 preload/worktree 变体生成的子 Agent 定义 | S07.7 |
| `<练习目录>/.s07-trace/events.jsonl` | Hook 实际运行后的观察日志，初始不存在 | S07.6 |
| 手工填写的结果 JSON | 从 evals/result-template.json 复制，记录真实实验 | S07.8 |

管理、个人和账号来源不是复制工程就会生效；对应模板的目标位置见下面的发现实验。

## 每份文件对应哪一节

点击文件名可定位到下方源码；折叠项展开后可查看完整内容。每份文件旁都再次列出讲解章节与注意点。

{{< skill-lab mode="index" >}}

## 主例：从文件到一次实际审查

解压后在 `s07-skills-lab/` 运行：

```bash
S07_LAB_ROOT="$(pwd)"
python3 tools/verify_lab.py
python3 tools/new_case.py --destination /tmp/s07-inline-case --variant inline --case empty-list
cd /tmp/s07-inline-case
python3 -m unittest discover -s tests -v
claude
```

目标目录必须尚不存在。生成器只创建新练习目录，在其中提交正常基线，再制造选定回归；不会修改博客仓库。这里的测试**应因空列表回归失败**，保留它作为审查对象。

在 Claude Code 中先查看来源，再启动：

```text
/skills
/review-diff src 空输入
```

用这条链追踪：

1. 发现 `review-diff`；描述供选择，主正文尚未因“文件存在”自动全量加入模型。
2. 调用入口确定范围和重点，处理 `$ARGUMENTS`、`$0`、`$1`。
3. 应用执行正文中的 Git 动态命令，将快照放进将交付的内容。
4. 模型收到工作步骤，再请求工具读取代码、必要参考资料与输出模板。
5. 需要刷新快照时，通过普通 Bash 调用执行 `inspect-diff.sh`。
6. 按证据报告空列表触发 `items[0]` 的 `IndexError`，以及测试约定与实际行为的差异。

本工程用 Python 标准库复现 S07.8 的空输入契约，避免另装测试依赖；该节 JavaScript 的 `undefined.trim` 与这里的异常不是同一种语言错误，但验证方法相同。

## 关键字段、位置与注意点索引

`SKILL.md`、名称描述与资源组织对应开放标准；`disable-model-invocation`、`context: fork`、后台和 Hook 等行为按 Claude Code 扩展理解。迁移到其他 Agent 时逐项核对支持范围。

| 字段或文件位置 | 具体讲解 | 本例要注意什么 |
|---|---|---|
| `name`、`description` 与正文 | S07.1、S07.3 | 描述说明何时使用；正文规定工作步骤。来源探针带 SOURCE_TAG，便于观察同名覆盖 |
| `.claude/skills/<name>/SKILL.md` | S07.2 | 文件位置决定来源范围；目录存在不等于当前会话已发现 |
| `disable-model-invocation` | S07.3、S07.7 | manual 变体只供显式启动，不可拿它做预加载 |
| `user-invocable` | S07.3 | model-only 变体通过自然语言任务观察，不用斜杠命令验证 |
| `argument-hint`、`$ARGUMENTS`、`$0`、`$1` | S07.5 | hint 不是校验器；参数不直接拼进 Shell。缺失的位置参数可能仍保留为占位符 |
| `${CLAUDE_SKILL_DIR}` | S07.5 | 本例用在正文与 allowed-tools 的 Bash 规则里，定位同一个随技能分发的脚本 |
| Hook command 中的 `$CLAUDE_PROJECT_DIR` | S07.5、S07.6 | 这里使用 Hook 进程提供的项目目录变量；不要假设正文替换变量在所有 frontmatter 字段都适用 |
| `!` 动态命令与 `scripts/` | S07.4、S07.5 | 前者在正文交付前处理，后者在普通工具调用时执行；脚本不会因在文件夹里就自动运行 |
| `allowed-tools` 与 `disallowed-tools` | S07.6 | 前者预授权，后者移除工具；禁止 Write/Edit 不能证明 Bash 没有写能力 |
| `hooks.PreToolUse` | S07.6 | 在真正执行前返回允许或拒绝；不是把 JSON 放到正文就生效 |
| `hooks.PostToolUse` 与 `once` | S07.6 | once 由宿主管理；Hook 脚本日志不是官方自动执行次数的模拟器 |
| `context: fork`、`agent`、`background` | S07.7 | 决定正文交给谁及调度方式；任务应自包含，不依赖父聊天未传入的信息 |
| 子 Agent 的 `skills` | S07.7 | 全文预加载；不是工具白名单，也不是再次通过描述选择 |
| 子 Agent 的 `tools`、`disallowedTools` | S07.7 | 这是代理工具集合；字段采用 camelCase，不能照抄 Skill 的 `disallowed-tools` 拼法 |
| 子 Agent 的 `isolation: worktree` | S07.7 | 改变文件工作区；不自动复制父目录未提交修改 |
| `skillOverrides` | S07.8 | 对个人／项目技能做关闭对照；插件另按插件机制评估 |
| `evals/*.json` 与 trace_inline.py | S07.8、S07.9 | 前者记录真实结果；后者是无模型的教学模拟，不能替代模型评估 |

## 发现位置与同名来源实验

主工程已有根部和嵌套的 `origin-probe`。它只回复来源标记，避免把发现问题混入审查效果：

| 来源 | 本包文件 → 生效位置 | 操作与预期 |
|---|---|---|
| 项目 | project/.claude/skills/origin-probe/SKILL.md → 练习目录同路径 | `/origin-probe` 应指向项目根来源，前提是没有更高优先级同名来源 |
| 嵌套 | project/packages/api/.claude/skills/origin-probe/SKILL.md | 先让 Claude 读取 packages/api/example.py，再检查 `/skills`；可用 `/packages/api:origin-probe` 区分 |
| 个人 | discovery/personal/origin-probe/SKILL.md → `~/.claude/skills/origin-probe/SKILL.md` | 手工部署到空闲路径后做同名比较；若该路径已有内容，不覆盖。通常个人高于项目 |
| 管理 | discovery/managed-template/.claude/skills/origin-probe/SKILL.md → 管理配置根目录下同结构 | 需要管理员部署；管理来源高于个人与项目。本包只提供模板 |
| 额外目录 | discovery/additional/.claude/skills/extra-probe/SKILL.md | 从练习目录用 `claude --add-dir "$S07_LAB_ROOT/discovery/additional"` 启动，再查 `/extra-probe` |
| 插件 | discovery/plugin/ | 用 `claude --plugin-dir "$S07_LAB_ROOT/discovery/plugin"` 临时加载，调用 `/skills-lab:origin-probe` |
| 账号与云端 | discovery/account-upload/account-probe/SKILL.md | 通过产品支持的上传／启用入口操作；不要手写同步缓存。云端不会自动读取本机个人目录 |

如果目录里有文件但调用不到，按“来源 → 会话发现范围 → 调用可见性 → 权限 → 内容”排查。账号同步来源对动态命令的处理也不同，所以这个来源探针没有放命令。

同名规则与目录限定名称依据 [官方发现说明](https://code.claude.com/docs/en/skills#resolve-skills-that-share-a-name)，插件临时加载依据 [插件文档](https://code.claude.com/docs/en/plugins)。组织和账号实验受实际部署条件约束，不能把模板存在当成已经安装成功。

## 互斥变体怎样运行

从下载包根目录使用相同生成器，为每种变体选一个新目录，例如：

```bash
python3 tools/new_case.py --destination /tmp/s07-fork-case --variant fork-wait --case empty-list
```

| --variant | 最终放入练习项目的文件 | 如何调用／观察 |
|---|---|---|
| inline | 主 SKILL.md | 自然语言审查或 `/review-diff src 空输入`，正文进入当前会话 |
| manual | variants/manual/SKILL.md → 主 Skill 位置 | 显式调用；自然语言请求不能用来期待它自行启动 |
| model-only | variants/model-only/SKILL.md → 主 Skill 位置 | 用自然语言提出审查任务；用户命令入口被关闭 |
| fork-wait | variants/fork-wait/SKILL.md → 主 Skill 位置 | 显式调用，观察新子上下文和等待返回 |
| fork-background | variants/fork-background/SKILL.md → 主 Skill 位置 | 交互环境支持时可继续主会话，结果随后到达 |
| preload | variants/preload/SKILL.md + review-worker.md | 明确要求使用 review-worker；任务在委派消息中给出，方法全文预加载 |
| worktree | 复用 preload/SKILL.md + variants/worktree/review-worker.md | 明确要求该代理报告目录和文件可见性，观察隔离工作树 |
| render-failure | variants/render-failure/SKILL.md → 主 Skill 位置 | Git 引用不存在，观察正文交付前失败 |

**预加载例子：**

```text
请使用 review-worker 子 Agent，审查当前仓库的未提交改动，重点检查空输入。
返回文件位置、触发输入和证据，先说明你所在的工作目录。
```

新会话中加载自定义项目代理时，按客户端要求完成相应目录信任步骤。preload 版本没有动态快照与调用参数，因为这时它是方法材料，任务来自委派消息；也没有设置禁止模型调用的字段。

**worktree 例子：**

```text
请使用 review-worker 子 Agent，报告工作目录、Git 根目录，
以及是否看得到 untracked-note.txt。先只观察隔离边界，不做审查结论。
```

生成器先把代理和 Skill 配置提交进基线，再制造未提交改动。子工作树基于仓库基线，不能默认看到父目录的未提交回归；如果要审查那份改动，需要另外明确传递补丁或准备包含改动的分支。本例的目的先是验证“上下文隔离”与“文件隔离”的区别。

fork 的后台行为还有环境条件：`-p` / Agent SDK、禁用后台任务、同一技能已有运行中调用等情况下会等待。后台可用工具也可能更窄，观察时记录客户端版本和环境，不只看一个布尔字段。[fork 的官方条件](https://code.claude.com/docs/en/skills#run-skills-in-a-subagent)、[预加载与隔离](https://code.claude.com/docs/en/sub-agents#preload-skills-into-subagents)

## 内容、权限与 Hook 的生命周期实验

在一个全新的 inline 会话中：

1. 调用 `/review-diff src 空输入`，查看正文加载与工具执行。
2. 让模型再次读取项目文件，不重新调用 Skill。检查 `.s07-trace/events.jsonl`：成功匹配 Read 的 once 回调只应在该次注册中首次成功执行时出现。
3. 发送新的用户消息，要求用 Write 工具写一个测试文件，不允许改用 Bash 绕过。临时工具限制与授权已经进入新的 turn，但持久注册的 guard Hook 仍可拒绝 Write。
4. 保持工作区和参数不变，再次调用同一 Skill，观察是否避免重复注入相同正文；然后改变参数或实际 diff，观察渲染内容变化。
5. 长会话发生压缩时，观察已调用方法的延续，不假定所有文件全文都会永久保留。

正文、临时工具配置、Hook 注册是三个不同状态。once 不是脚本内的计数器；再次调用技能也可能涉及重新授权与注册，不能仅根据是否重复显示正文推断所有副作用。[内容与权限生命周期](https://code.claude.com/docs/en/skills#skill-content-lifecycle)、[Skill Hook 生命周期](https://code.claude.com/docs/en/hooks#hooks-in-skills-and-agents)

要单独验证 Hook 协议，可以在练习目录运行：

```bash
printf '%s\n' '{"hook_event_name":"PreToolUse","tool_name":"Write","session_id":"offline"}' |
  python3 .claude/hooks/skill-hook.py guard
```

它会返回拒绝 JSON，并写观察日志。这个离线调用验证的是脚本，不验证客户端是否正确注册、触发或移除 Hook。

## 故障路径与评估

| 实验 | 具体动作 | 应记录的区别 |
|---|---|---|
| 自动触发 | 新会话中使用 evals/cases.json 的正例与反例 | 显式启动成功不能代替自动触发评估 |
| 空输入回归 | --case empty-list | `normalize_first([])` 应失败，报告应定位表达式和契约 |
| 共享状态回归 | --case lost-update | 两次调用可能都读到旧值，最终为 1；按需读取 concurrency.md |
| 无 Skill 基线 | `claude --settings "$S07_LAB_ROOT/profiles/without-skill.json"` | 同一任务、工作区和模型，在新会话中比较 |
| 权限拒绝 | 使用 deny-snapshot.json profile | 预授权不能越过 deny，动态准备可能在正文加载前失败 |
| 命令失败 | render-failure 变体 | 即使命令获准，不存在的 Git 引用仍导致渲染失败 |
| 禁止动态 Shell | 使用 no-dynamic-shell.json profile | 按策略替换动态命令，不等于所有普通工具都被禁止 |
| 目录不可见 | 使用尚未发现的嵌套技能 | 先核对发现范围，不先改正文 |
| 上下文不完整 | fork 时省略任务范围 | 子 Agent 不能从没有收到的父聊天补全任务 |
| 格式正确但效果不好 | 文件通过格式／语法检查，报告仍无证据 | 单独记录任务质量与模型波动 |

无 Skill 对照记录模型、会话权限设置、耗时、上下文开销、证据质量和工具操作。主例本身包含临时授权与 Hook，因此整体收益也可能来自交互方式变化，不能全部归因为正文更好。结果模板默认没有成绩，要填入真实观察，必要时重复几次。

如果已安装标准参考工具，还可运行 `skills-ref validate .claude/skills/review-diff` 做格式检查；它不能替代上述任务评估。evals JSON 是本教程自己的记录格式。[标准格式验证](https://agentskills.io/specification#validation)

## 对应主循环的可运行教学轨迹

```bash
python3 "$S07_LAB_ROOT/tools/trace_inline.py" /tmp/s07-inline-case \
  --caller model --arguments "src empty-input" --resource input
```

它输出目录、调用、动态命令结果、正文交付、按需参考文件、普通工具结果，最后停在“可以再次请求模型”的位置。每条记录都有 `simulation: true`，没有生成虚构的审查报告。

脚本只支持本包固定格式、固定 Git 命令和 inline 路径；不实现完整 YAML、官方消息协议、权限引擎、Hook 注册器或 fork 调度。它负责把 [S07.9 的接口]({{< relref "/projects/learn-claude-code/s07/09-agent-loop.md" >}})变成可观察数据，真实产品行为仍按前面的客户端实验验证。

## 核心文件的完整内容

{{< skill-lab mode="files" group="核心文件" >}}

## 配置变体的完整内容

{{< skill-lab mode="files" group="配置变体" >}}

## 发现实验的完整内容

{{< skill-lab mode="files" group="发现实验" >}}

## 权限与对照文件的完整内容

{{< skill-lab mode="files" group="权限与对照" >}}

## 验证与追踪文件的完整内容

{{< skill-lab mode="files" group="验证与追踪" >}}

## 说明与索引文件的完整内容

{{< skill-lab mode="files" group="说明与索引" >}}

## 已验证什么

本附录的本地检查覆盖：正常基线通过、两个回归按预期失败、八个变体可生成、Hook JSON 与日志、inline 教学轨迹和动态失败分支，以及文件中的 Python、JSON、YAML 语法与博客链接。

这些检查不包含真实 Claude 模型调用。自动选择是否稳定、报告是否合格、客户端的权限生命周期与后台行为，按本页步骤观察并填写结果模板。

[上一节：接回 Agent Loop]({{< relref "/projects/learn-claude-code/s07/09-agent-loop.md" >}}) · [返回 S07 总览]({{< relref "/projects/learn-claude-code/s07/_index.md" >}})
