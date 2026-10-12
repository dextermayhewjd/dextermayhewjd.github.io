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

## Testing Guidelines

Tests use Bash assertions and Python's standard-library `unittest`; no coverage threshold is configured. Name Python checks `tests/test_<feature>.py`. Add focused regression checks for changed navigation, diagrams, or interactions. Browser checks require Chrome; some source checks require local teaching repositories and skip when unavailable. Review skipped tests and manually verify desktop, narrow-screen, and keyboard behavior for UI changes.

## Commit & Pull Request Guidelines

History uses prefixes such as `docs:`, `feat:`, and `chore:` followed by a concise description. Keep commits focused. PRs should explain the change, identify affected pages, link relevant issues or design records, report validation and skips, and include screenshots for visual changes.

## Generated Files & Publishing

Keep generated `public/`, `resources/_gen/`, and Hugo lock files out of commits. Treat `bash deploy.sh` as an explicit publishing action: it rebuilds the site and force-pushes `gh-pages`.

## Slime Source Reading

For Slime source reading, route maintenance, or related learning notes, read `slime_photo/code-reading/AGENTS.md` and use `slime_photo/code-reading/repo-reading-route.md` as the current route. Keep published content focused on technical responsibilities and source evidence.
