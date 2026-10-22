# Repository Guidelines

## 通用仓库阅读与认知记录

- 对任何源码仓库开展讲解、学习规划或阅读记录时，先读 [方法入口](00-repo-reading/README.md) 和 [工作流](00-repo-reading/workflow.md)，再接续 `00-repo-reading/repositories/<repo>/` 下的项目入口、最近步骤及该项目的唯一进度记录。此约定同时适用于聊天带读和文件修改。
- 开始或接续关于认知模型、记忆机制、阅读步骤或记录职责的讨论时，先读[源码阅读与认知制度 backlog](backlog/repo-reading/README.md)，再打开对应主题的最新讨论文件夹及其中的入口与记录，区分已确认约定和待讨论建议后再继续。
- 确定或修订本步阅读范围时，使用 [repo-reading-scope skill](.agents/skills/repo-reading-scope/SKILL.md)：明确阅读目标、定位指挥官函数、按五类过滤规则提取核心骨架；参数默认省略，保留必要业务分支和停止位置。
- 已有骨架后，选择下一处入口或解释为何优先读某个函数时，使用 [repo-reading-order skill](.agents/skills/repo-reading-order/SKILL.md)：按当前问题推荐核心动作，再按需回查最小前置；推荐与用户确认分开，不自动开启下一步。
- 创建或修订本步单函数短期记录时，使用 [repo-reading-short-term-memory skill](.agents/skills/repo-reading-short-term-memory/SKILL.md)；整体记忆分工与长期继承继续从 [repo-reading-memory skill](.agents/skills/repo-reading-memory/SKILL.md)进入。两者不替代各项目的阅读路线，也不自动将普通代码问答扩展为记录工作。
- 每个 step 开始前，先与用户讨论“这一步准备读哪个函数、围绕它要弄清什么、短期 memory 准备保留什么”。助手可以根据当前问题提出候选函数及理由，由用户确认后再展开源码、创建对应函数记忆和更新阅读进度。这里确认的是本步范围和记录重点，不要求预先给出答案。用户已明确指定时直接沿用，不重复询问；核心范围变化时重新讨论确认。不能把候选、目录顺序、旧阅读历史或已准备的材料当作确认。结构纠错和保存已发生讨论可继续在已授权范围内完成。
- 首轮源码阅读采用用户提供的[代码阅读指南：剪枝三步法](00-repo-reading/code-reading-guide.md)：先找组织主流程的函数，提取正常路径，暂时折叠配置、检查、日志、异常与失败包装；本轮调用下钻不超过两层，弄清输入输出后返回主线。按实际源码核对符号和接口，不把教学省略视为实际代码不存在或已掌握。
- 阅读时的记录参照指南的[第二条方法](00-repo-reading/code-reading-guide.md#方法二读代码时记录什么)，优先保存数据变化、当前追踪路径、设计疑问与依据；沿用既有函数记忆和过程记录，不逐行转述代码，也不因临时草稿可丢弃而删除正式历史。
- 全景从该项目的阅读目标与最小端到端职责建立；读过哪些函数属于历史记录，只影响回顾深度，不预设整体框架已理解。每次进入新模块都接回已有整体模型。
- 每个实质性阅读步骤记录前一步模型、当前问题、目录/文件/函数与版本、真实调用和输入输出、理解形成或修正、本步之后的整体模型及下一问。新问题实际展开时才创建下一份步骤，追问和纠正补在相关步骤；不预生成完成记录。
- 2026-10-19 确认的现行结构：每步包含 `01-scope.md`、`02-short-term-memory/`、`03-long-term-memory/` 和 `04-flow.md`。下一步的 `03` 合并前一步 `03` 与 `02`，新认识写入新的 `02`；保留完整模型、来源与未知。新模板已同步，旧步骤保留当时目录与快照，不因此重写学习历史。
- 两层 memory 遵循[统一格式](00-repo-reading/memory-format.md)。2026-10-20 用户再次明确：`02` 保存本步单个函数的记录，`03` 保存此前累计的同格式函数记录；`overview.md` 只做函数索引，任务主线与整体关系放在步骤 README / scope。`functions/<源码相对路径>/<完整函数名>.md` 保留源码定位、首次接触和最近认识更新。函数卡片以 [BaseAdapter._translate](.agents/skills/repo-reading-memory/references/base-adapter-translate.md) 为当前认可样例：开头定位、LLM 整理的四项、本场景的输入与输出、我的直接表述、尚不清楚、折叠来源；精简文字时保留当前调用场景与关键参数。尚无原话时如实注明，不能因此省略本步函数卡片或用整体图替代。校对从原讨论回查，个人原话不作为技术结论证据。整份记录和来源一起继承；只继承、补源码证据或改格式不算个人认识更新。
- Step 01 的 `01-scope.md` 按为什么读、核心问题、入口条件、源码范围、阅读边界五项组织；`04-flow.md` 按实际问题连接用户表述、源码材料、助手提示和后续修正。依据是用户已确认的[职责规范](backlog/repo-reading/2026-10-19-step-folder-format.md#scope-flow-conventions)。形成的认识写入 `02`，目录和模板调整留在格式讨论；不将讨论顺序当作函数执行顺序。
- 用户已要求持续保存认知构建过程。将实际问题与明确反馈、助手解释、静态源码证据、真实运行证据区分；不替用户虚构理解状态，不让用户反复提醒目标或保存讲解。
- 2026-10-20 最新澄清：Step 0 的单函数记录放入 `02-short-term-memory/`，`03-long-term-memory/` 初始为空，仅注明暂无前序继承；到下一步才把上一份 `03 + 02` 合并进新的 `03`。不要再把首步函数提前放入长期记忆。移动文件、补来源和 LLM 说明仍不代表个人新增理解或已经掌握。
- 个人认知由用户表达，助手先定位本步再提问、核对和整理。两层 memory 将个人已说清的关系、明确未知，与助手核对的场景代码、输入输出和 LLM 模型分开；“知道做什么、尚不清楚怎么做”是有效状态。扩展讲解放 `references/`，源码解释不能预填个人理解。此分工针对个人学习记录，完整教材仍按原出版约定维护。
- 带读需要助手主动选观察点、给局部材料并邀请用户解释，再核对和推进；不要退化成被动记录，也不要给完答案后机械要求复述。每次优先解决当前表述中的一个关键区别，机制细节可继续留白。
- 通用方法不另造课程顺序，不覆盖各专题已确认的学习边界。当前进度保持单一来源，Hugo 正文与步骤记录明确分工或引用同一正文；跨仓库使用须在目标仓库显式接入规则。

## Project Structure & Module Organization

This repository is a Chinese-language learning website built with Hugo and the PaperMod theme.

- `content/`: Markdown articles, project chapters, and course notes; page bundles keep JSON metadata and diagrams beside their pages.
- `layouts/`: Hugo templates, partials, and shortcodes that extend the theme.
- `assets/css/extended/` and `assets/js/`: custom styles and browser interactions.
- `examples/` and `static/`: teaching examples, downloadable archives, and directly served resources.
- `tests/`: navigation, diagram, source-excerpt, and browser checks.
- `docs/`: writing rules, design discussions, specifications, and plans.
- `themes/PaperMod/`: Git submodule. Keep site customizations in root-level layouts and assets.

## Build, Test, and Development Commands

Use Hugo Extended **0.166.0**.

- `git submodule update --init --recursive`: initialize PaperMod after cloning.
- `hugo server -D`: preview locally at `http://localhost:1313`, including drafts.
- `hugo --gc --minify`: generate the production site in `public/`.
- `bash tests/test-project-navigation.sh`: build into a temporary directory and check navigation and rendered content.
- `python3 -m unittest discover -s tests -p 'test_*.py'`: run Python checks.
- `python3 examples/s07-skills-lab/tools/verify_lab.py`: validate the Skills Lab.

## 开发前的本地预览

- 每次开始网站开发、页面修改或阅读材料开发时，先启动或确认本地 Hugo 预览，再进行改动，让用户能够随时查看正在开发的内容。
- 先检查 `http://localhost:1313/` 是否已经服务于当前项目；已有正确服务时复用，并验证本次相关页面可访问。仅发现端口占用不能当作预览验证成功。
- 没有可用服务时，在本仓库根目录运行 `hugo server -D --bind 127.0.0.1 --port 1313 --noHTTPCache --disableFastRender`。核对构建输出和 HTTP 响应后，向用户提供相关页面的本地链接，并保持服务运行供其查看。
- 端口由其他项目使用时先核对服务来源，再选可用端口，并告知实际预览地址。启动失败时说明具体原因，继续处理与预览无关的准备工作。

## 源码仓库选择

- 先读取用户已经确认的仓库记录。仓库一旦确定，后续任务与阅读章节持续沿用，不再逐章或逐轮重复询问；只有用户要求更换、尚无已确认仓库或存在多个有歧义的候选时才确认。
- Slime 的仓库选择持续沿用。2026-10-19 核对本机实际 checkout 为 `/home/hongshi/projects/slime`，核心包是其中的 `slime/`；历史记录中的 `/home/fredkeira/projects/slime` 在本机不存在。路径迁移不表示更换学习项目，旧材料的提交和源码证据仍保留原版本归属，不批量改成当前 HEAD。
- 用户明确给出新路径时采用该路径；多个候选无法从上下文确定时询问。分析其他仓库时，不把已确认的 Slime 路径误用于其他项目。
- 路径尚未确定时，可以启动预览或整理已有材料。路径确定后核对 Git 根目录、HEAD 和工作区差异，绑定源码证据；版本核对本身不需要再请求用户确认路径。

## 代码阅读顺序与讲解

- 先建立一条合理的端到端任务主线，再沿实际调用顺序进入各职责组件；每个主要职责的代码都走一遍，深度以能连贯说明交接为准。
- 进入组件时说明为什么到这里、输入是什么、实际行为与输出/副作用是什么；讲完返回任务主线，指出下一步。先走通正常路径，再补关键失败与清理分支。
- 整仓文件/函数清单用于定位和后续扩展；当前阅读单元围绕一个具体任务连续推进，避免在各文件之间失去调用上下文。
- 每个 Action 单独交代阅读语境：正在跟随哪一层调用、为何进入这里、本章展开什么、读完返回哪里。主要源码文件、入口符号和行号放在默认收起的入口；调用链与文件目录不能互相替代。Slime 4.1 的具体映射维护在 `slime_photo/code-reading/action-contexts.json`。

## Coding Style & Naming Conventions

Match surrounding formatting: generally two spaces in JavaScript, CSS, and templates, and four spaces in conventionally formatted Python. No repository-wide formatter or linter is configured.

Use lowercase, hyphenated content paths and descriptive asset names. Use `_index.md` for section pages and `index.md` for leaf bundles. Keep chapter numbering, titles, navigation labels, and front matter weights consistent. Follow `docs/learn-claude-code-writing-rules.md` for Learn Claude Code content and diagrams; retain source attribution and version boundaries.

## 学习文档的源码示例约定

- 编写最小实现前，先核对本地对应源码；本地没有时，查看用户指定的 GitHub 文档和对应版本的实现。
- 最小实现优先从真实源码裁剪，保留真实接口、函数名和输入输出字段。不要为了简化而另造包装函数，让读者随后还要重新映射到源码。
- 明确标注教学裁剪与原实现的差别，例如只保留一个审查维度、暂时改为顺序执行；后续在同一份示例上逐步还原完整机制。示意代码与原始源码摘录必须区分。

## Python 异步与并发学习规划

- 编写、续读或调整本专题前，先读 [完整课程规划](python-async-reference/curriculum.md)，确认当前单元、前置、新增问题和 API；需要核对选题理由时再读 [学习范围与顺序](python-async-reference/learning-plan.md)。不要从全部 API 清单重新推导一套课程顺序。
- 各学习单元标题沿用已有课的“编号 · API/语法：用途或问题”格式，让读者一眼看出“用什么机制、解决什么问题”。例如“gather：等待一组任务，收集一组结果”“asyncio.as_completed：按完成顺序取结果”；紧密配套的方法可并列，如“done、result、exception：读取 Task 的状态与结果”。页面、导航与课程表同步命名。
- 按理解难度选择展示方式，不把泳道图作为每课固定模板。简单流程优先使用代码、输出旁注或简短步骤；多个协程反复切换、等待关系难以跟踪时，再使用泳道图。若读者仍难以跟踪通知、挂起与恢复，即使流程较短也保留图解。
- 用户再次明确：本专题只考虑 Python 原生异步与并发，岗位仅是学习动机。按概念依赖安排先后，用 Slime、AReaL、verl 的相关用法和 API 次数辅助决定详略；不扩展为完整岗位准备、框架设计或通用工程化课程。具体路线与自查见学习规划第 4.3–4.5 节。
- 数据从 [资料总入口](python-async-reference/README.md) 查找；重点使用 [核心包 API 统计](python-async-reference/CORE-API-USAGE.md)、[官方文档目录](python-async-reference/OFFICIAL-DOCS.md) 和 `python-async-reference/repositories/<repo>/inventory.json`。调用、引用、语法和不确定候选遵循各自统计口径。
- `learning-plan.md` 中每库至少 3 处的高频筛选线是本轮工作口径，可根据讨论调整；必要前置与低频衔接接口要单独说明，不能冒称都是高频。具体讲解继续遵循 `.agents/skills/python-syntax-learning/SKILL.md`。
- 三库各约 70%–80% 的调用位置覆盖是阶段性选题核算，保留在学习规划第 4.2 节及 [覆盖与缺口核算](python-async-reference/learning-coverage.md)。显式 API 清单在 `python-async-reference/learning-scope.json`，用 `python3 python-async-reference/tools/build_learning_coverage.py --check` 核对；它不是完整岗位路线的覆盖分母。允许必要的仓库特有生命周期操作，不得把调用位置比例描述成实际场景覆盖率或学习完成度。
- 当前具体 API 以 [98 项 API 清单](python-async-reference/current-api-plan.md) 和 `current-api-plan.json` 为准：原 82 项加六组 11 项与 4 项必要配套，再按 2026-10-18 用户确认补入 threading.RLock 一项。原 82 项保留在 `api-plan-82.json`，53 项保留作历史基线。四库核心包总调用量加权覆盖为 1614/1899（85.0%），不是 API 种类比例或各库覆盖率平均。用 `python3 python-async-reference/tools/build_current_api_plan.py --check` 复核；语法与异常引用不混入调用数。
- 用户要求全课结束时包含全部 98 项 API。正式课程唯一数据为 `python-async-reference/curriculum.json`，逐项映射见 [curriculum.md](python-async-reference/curriculum.md)：8 模块、41 个主编号单元；01–22、24–38 已整理，23、39–41 待编写。10、11、20、21、23、24、28、31、33、35、36 用 `parts` 拆成子课，每个 API 恰有一个正式引入位置。21.1–21.6 保留资源三阶段、yield、装饰器、正常进入退出、异常和取消的顺序，`contextlib.asynccontextmanager` 正式引入在 21.4。2026-10-16 用户确认整合两版：Future 基础正式放在 20.2–20.5，承接 20.1 的 Event 通知，依次讲当前循环、结果对象、等待交付、状态与异常；第 33 单元保留远端 33.1–33.4 的当前循环复习、指定线程池、并发交接实验、循环时钟；35.1–35.2 保留为复习与源码应用，35.3 正式引入完成回调。第 24 单元拆为 24.1 的 ContextVar.set/get 与 24.2 的 token/reset，原 11-contextvars URL 和下载保留；当前继续 24.2，24.1 只记录为初步理解。第 36 单元的 36.1、36.2 均已整理。本轮先补 20.2–20.5，再回到第 33 单元。既有 URL 和主编号保留，不按 URL 历史数字推断现行单元号。改动后运行 `python3 python-async-reference/tools/build_curriculum.py --check`。
- 主线包括原生任务与结果、取消与超时、同步与队列、线程与执行器、进程、异步协议与上下文。测试、日志和诊断工具只辅助验证当前并发机制，不另设通用必学模块。01–06 继续保持最小递进，后续每次只引入一个新关系；公开入口见 `content/projects/python-async-concurrency/learning-route/index.md`。
- 保存规划不等于已经改写现有章节。后续改动应先核对规划、源码版本和 Python 文档版本；学习表格保存在独立文件中，刷新自动生成的统计报告时应保留它。
- 用户在 localhost 章节学习中追问的关键澄清，应同步补入对应教学正文，并提供本地页面锚点；不要只在聊天中解释后让网页内容停留在前一个问题。
- 当前学习记录：用户明确表示 36.2 `run_coroutine_threadsafe` 尚未读懂，要求暂时跳过，不计为已掌握。当前短补同一线程中的回调调度，完整教学分别在 `content/projects/python-async-concurrency/loop-call-soon/` 与 `loop-call-later/`；2026-10-17 用户表示已大致理解第 24 单元 ContextVar 的任务上下文与 set/get，当前继续 token/reset；整课尚未标为掌握；ContextVar 教学现已按第 24 单元加入主导航，教材 existing 状态不代表学习完成。待以后回访跨线程提交的动机与结果方向。当前阅读位置以学习记录为准，不因已有正文或 `existing` 状态推断掌握，也不自动跳回 20 或 31。

- 2026-10-17 用户澄清两个层级：补充教学负责问题、完整例子、输出和逐步解释，放在专题根目录，侧栏在第 38 课后直接显示且不编号；`content/projects/python-async-concurrency/comparisons/` 只保存函数关系摘要，供复习和以后画思维导图，写共同点、差别、选择条件与关系句，不复制长篇教学或完整可运行例子。关系摘要在侧栏中显示为独立、可展开的文件夹，教学页保持在该文件夹外；两个层级互相链接。当前摘要是 create_task 与 call_soon、call_soon 与 call_later；41 个主编号与 97 项正式 API 归属不变。

- 2026-10-18 用户确认把第 28 单元拆成 28.1 Lock 与 28.2 RLock，原 Lock URL 保留；RLock 正式加入范围，总数为 98 项。侧栏分组、课程表、频率表与 comparisons/lock-vs-rlock 同步。Slime ≥5 次（包含恰好 5 次）为当前重点；本轮先看 RLock，尚未确认掌握。此前日期记录中的 97 项保留历史语境。

### 本专题的 Reference 入口

| 要查什么 | 文件 |
| --- | --- |
| 完整课程安排：8 模块、41 单元、前置、原子结论、自查和 API 对应 | [python-async-reference/curriculum.md](python-async-reference/curriculum.md) |
| 修改课程结构的唯一数据源 | [python-async-reference/curriculum.json](python-async-reference/curriculum.json) |
| 98 项 API、Python 官网入口、四库调用次数和覆盖比例 | [python-async-reference/current-api-plan.md](python-async-reference/current-api-plan.md) |
| 学习边界、选题依据与历史讨论结论 | [python-async-reference/learning-plan.md](python-async-reference/learning-plan.md) |

调整课程结构时修改 `curriculum.json`，运行 `python3 python-async-reference/tools/build_curriculum.py` 同步生成 Markdown 和网页课程表，再运行同一命令加 `--check` 核对 98 项 API、语法、异常和前置顺序。不要单独修改生成的 `curriculum.md` 或 `curriculum-web.md`。

## Testing Guidelines

Tests use Bash assertions and Python's standard-library `unittest`; no coverage threshold is configured. Name Python checks `tests/test_<feature>.py`. Add focused regression checks for changed navigation, diagrams, or interactions. Browser checks require Chrome; some source checks require local teaching repositories and skip when unavailable. Review skipped tests and manually verify desktop, narrow-screen, and keyboard behavior for UI changes.

## Commit & Pull Request Guidelines

History uses prefixes such as `docs:`, `feat:`, and `chore:` followed by a concise description. Keep commits focused. PRs should explain the change, identify affected pages, link relevant issues or design records, report validation and skips, and include screenshots for visual changes.

## Generated Files & Publishing

Keep generated `public/`, `resources/_gen/`, and Hugo lock files out of commits. Treat `bash deploy.sh` as an explicit publishing action: it rebuilds the site and force-pushes `gh-pages`.

## Slime Source Reading

For any Slime explanation, study planning, source reading, or route maintenance, first read `slime_photo/code-reading/AGENTS.md`, the “当前接续” section of `slime_photo/code-reading/repo-reading-route.md`, and the current priorities in `slime_photo/code-reading/job-alignment.md`. This applies to chat-only teaching as well as file edits.

- Slime 学习按用户提供的腾讯混元 Agent 强化学习框架工程师 JD 决定投入重点；岗位对照保存能力与预算，阅读路线保存唯一进度，不把官网目录顺序当成平均投入要求。
- Slime 的认知步骤入口在 `00-repo-reading/repositories/slime/README.md`。全景从基本工作流开始，`generate()` 的已读历史仅用于按需提醒；本目录的步骤快照不另存一套实时进度。
- 阅读进度和当前入口只以路线的“当前接续”为准。保留用户已读事实，首次重遇时先短提醒职责、关键输入输出与主线位置；不假定已读内容仍能随时回忆，也不因需要提醒而清零进度或默认重讲内部全链。
- 带读同时交代全局位置与局部调用：框架中的当前位置 → 本轮源码与输入输出 → 回到调用方及下一次交接。具体协议与接续更新规则见 Slime 专属 `AGENTS.md`。
- 用户已要求在 Hugo 持续保存完整 Walkthrough：技术问题、关系如何建立、源码依据、解释与修正同步补入对应正文；有明确反馈才写成用户自己的理解，不替用户虚构心智状态。正文从一个维护来源渲染。
- 本专题规则不改写独立 Python 异步课程的范围和学习进度。公开内容聚焦技术问题、理解过程与源码证据；JD、时间预算、个人履历和进度状态保留在本地阅读记录中。
