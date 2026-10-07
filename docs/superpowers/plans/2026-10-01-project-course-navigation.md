# Project Course Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 Hugo 个人网站增加可复用的项目/课程方向入口、总览页和方向内侧边栏。

**Architecture:** 用 Hugo section 目录表达方向，用 `layouts/_default/` 覆盖方向列表与单页模板。导航 partial 从当前页面向上找到方向 section，递归渲染其子 section 和页面；CSS 在桌面端固定为左栏，在窄屏幕折叠。

**Tech Stack:** Hugo templates, Markdown front matter, CSS, shell build verification.

**Spec:** `docs/superpowers/specs/2026-10-01-project-course-navigation-design.md`

## Global Constraints

- 保留现有 PaperMod 顶部菜单、文章目录和感悟抽屉。
- 方向导航只显示当前方向的内容。
- 目录排序使用 front matter 的 `weight`。
- 不新增运行时依赖。

## Review Focus

- 普通 `posts` 页面不能误显示方向导航；由 `test-project-navigation.sh` 验证。
- 方向总览页必须列出子页面；由构建产物检查验证。
- 当前方向页面必须高亮当前链接；由构建产物检查验证。
- 移动端导航不能撑破正文；由 CSS 断点和构建检查验证。
- 现有 `/notes/` 模板必须继续生成；由完整 Hugo 构建验证。

### Task 1: Add build regression checks

**Files:**
- Create: `tests/test-project-navigation.sh`

- [x] 写检查脚本：构建到临时目录，检查课程首页、章节页、侧边导航、当前链接和普通文章隔离。
- [x] 运行脚本，确认在实现前因页面和模板不存在而失败。

### Task 2: Add reusable navigation partial and templates

**Files:**
- Create: `layouts/partials/project-nav.html`
- Create: `layouts/_default/section.html`
- Create: `layouts/_default/single.html`
- Modify: `assets/css/extended/notes.css` or create `assets/css/extended/project-nav.css`

- [x] 让 partial 从 `.CurrentSection` 生成当前方向导航，并按 `weight` 排序。
- [x] 在 section 和 single 模板中包装方向内容与导航。
- [x] 增加桌面侧栏、移动端折叠和当前项高亮样式。
- [x] 运行构建检查并修正模板错误。

### Task 3: Add a real course example and course index

**Files:**
- Create: `content/courses/_index.md`
- Create: `content/courses/mit-1806/_index.md`
- Create: `content/courses/mit-1806/01-systems.md`
- Create: `content/courses/mit-1806/02-elimination.md`
- Create: `content/courses/mit-1806/03-vector-spaces.md`
- Modify: `hugo.toml`

- [x] 增加课程入口和 MIT 18.06 示例内容。
- [x] 为页面设置 `weight`，确保导航顺序稳定。
- [x] 将课程入口加入顶部菜单。
- [x] 运行完整构建和回归检查。

### Task 4: Update contributor documentation

**Files:**
- Modify: `README.md`

- [x] 说明如何新增项目/课程方向、总览页和章节页。
- [x] 记录本地预览与构建命令。
