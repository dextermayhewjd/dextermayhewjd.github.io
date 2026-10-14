# Repository Guidelines

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
- Slime 已由用户确认使用 `/home/fredkeira/projects/slime`，核心包是其中的 `slime/`。2026-10-10 用户明确要求将这一选择持续保留，后续 Slime 阅读直接沿用，直到用户更改。
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
- 用户再次明确：本专题只考虑 Python 原生异步与并发，岗位仅是学习动机。按概念依赖安排先后，用 Slime、AReaL、verl 的相关用法和 API 次数辅助决定详略；不扩展为完整岗位准备、框架设计或通用工程化课程。具体路线与自查见学习规划第 4.3–4.5 节。
- 数据从 [资料总入口](python-async-reference/README.md) 查找；重点使用 [核心包 API 统计](python-async-reference/CORE-API-USAGE.md)、[官方文档目录](python-async-reference/OFFICIAL-DOCS.md) 和 `python-async-reference/repositories/<repo>/inventory.json`。调用、引用、语法和不确定候选遵循各自统计口径。
- `learning-plan.md` 中每库至少 3 处的高频筛选线是本轮工作口径，可根据讨论调整；必要前置与低频衔接接口要单独说明，不能冒称都是高频。具体讲解继续遵循 `.agents/skills/python-syntax-learning/SKILL.md`。
- 三库各约 70%–80% 的调用位置覆盖是阶段性选题核算，保留在学习规划第 4.2 节及 [覆盖与缺口核算](python-async-reference/learning-coverage.md)。显式 API 清单在 `python-async-reference/learning-scope.json`，用 `python3 python-async-reference/tools/build_learning_coverage.py --check` 核对；它不是完整岗位路线的覆盖分母。允许必要的仓库特有生命周期操作，不得把调用位置比例描述成实际场景覆盖率或学习完成度。
- 当前要学的具体 API 以 [82 项 API 清单](python-async-reference/current-api-plan.md)和 `current-api-plan.json` 为准；上面的 53 项保留作历史基线。新清单补齐对象的方法，固定快照调用覆盖为 Slime 79.5%、AReaL 83.6%、verl 78.2%，不为压低比例删除必要操作。用 `python3 python-async-reference/tools/build_current_api_plan.py --check` 复核，语法和异常引用不与调用数混算。
- 用户要求全课结束时包含全部 82 项 API。正式课程设置唯一数据为 `python-async-reference/curriculum.json`，说明与逐项映射为 [curriculum.md](python-async-reference/curriculum.md)：8 模块、40 个最小单元；01–05 沿用现有课，06–40 待拆分/补写。每个 API 恰有一个正式引入单元；82 项内不再以选读代替覆盖，清单外仍按需。新单元号与旧网页号分开，保留旧链接。改动后运行 `python3 python-async-reference/tools/build_curriculum.py --check`。
- 主线包括原生任务与结果、取消与超时、同步与队列、线程与执行器、进程、异步协议与上下文。测试、日志和诊断工具只辅助验证当前并发机制，不另设通用必学模块。01–05 继续保持最小递进，后续每次只引入一个新关系；公开入口见 `content/projects/python-async-concurrency/learning-route/index.md`。
- 保存规划不等于已经改写现有章节。后续改动应先核对规划、源码版本和 Python 文档版本；学习表格保存在独立文件中，刷新自动生成的统计报告时应保留它。

### 本专题的 Reference 入口

| 要查什么 | 文件 |
| --- | --- |
| 完整课程安排：8 模块、40 单元、前置、原子结论、自查和 API 对应 | [python-async-reference/curriculum.md](python-async-reference/curriculum.md) |
| 修改课程结构的唯一数据源 | [python-async-reference/curriculum.json](python-async-reference/curriculum.json) |
| 82 项 API、Python 官网入口、三库调用次数和覆盖比例 | [python-async-reference/current-api-plan.md](python-async-reference/current-api-plan.md) |
| 学习边界、选题依据与历史讨论结论 | [python-async-reference/learning-plan.md](python-async-reference/learning-plan.md) |

调整课程结构时修改 `curriculum.json`，运行 `python3 python-async-reference/tools/build_curriculum.py` 同步生成 Markdown 和网页课程表，再运行同一命令加 `--check` 核对 82 项 API、语法、异常和前置顺序。不要单独修改生成的 `curriculum.md` 或 `curriculum-web.md`。

## Testing Guidelines

Tests use Bash assertions and Python's standard-library `unittest`; no coverage threshold is configured. Name Python checks `tests/test_<feature>.py`. Add focused regression checks for changed navigation, diagrams, or interactions. Browser checks require Chrome; some source checks require local teaching repositories and skip when unavailable. Review skipped tests and manually verify desktop, narrow-screen, and keyboard behavior for UI changes.

## Commit & Pull Request Guidelines

History uses prefixes such as `docs:`, `feat:`, and `chore:` followed by a concise description. Keep commits focused. PRs should explain the change, identify affected pages, link relevant issues or design records, report validation and skips, and include screenshots for visual changes.

## Generated Files & Publishing

Keep generated `public/`, `resources/_gen/`, and Hugo lock files out of commits. Treat `bash deploy.sh` as an explicit publishing action: it rebuilds the site and force-pushes `gh-pages`.

## Slime Source Reading

For Slime source reading, route maintenance, or related learning notes, read `slime_photo/code-reading/AGENTS.md` and use `slime_photo/code-reading/repo-reading-route.md` as the current route. Keep published content focused on technical responsibilities and source evidence.
