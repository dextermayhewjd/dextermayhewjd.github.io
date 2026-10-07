# dextermayhewjd.github.io

Hugo + PaperMod 个人博客：https://dextermayhewjd.github.io/

网站由本地构建后推送到 `gh-pages` 分支发布（`main` 只放源码）。

```bash
git clone --recurse-submodules https://github.com/dextermayhewjd/dextermayhewjd.github.io.git
hugo server -D                     # 本地预览 http://localhost:1313
hugo new content posts/xxx.md      # 新文章，写完把 draft 改为 false
hugo new content notes/xxx.md      # 新感悟（右下角灯泡抽屉 / /notes/ 页检索），写完把 draft 改为 false
git add -A && git commit -m "..." && git push   # 保存源码
./deploy.sh                        # 构建并发布网站
```

## 项目与课程方向

网站按“方向 → 总览 → 拆解页面”组织项目和课程。方向目录放在 `content/projects/` 或 `content/courses/` 下，每个方向用 `_index.md` 写总览，其他 Markdown 文件用 `weight` 控制侧边栏顺序：

```text
content/courses/my-course/
├── _index.md
├── 01-foundations.md
└── 02-practice.md
```

方向页面会自动显示左侧导航，移动端会折叠为“展开本方向导航”。新增方向后只需添加内容文件；模板会自动从 Hugo 的目录结构生成导航。

章节也可以有子章节，例如 `content/projects/learn-claude-code/s07/_index.md` 作为总览，同目录的 `01-structure.md` 到 `10-appendix.md` 作为子页面。侧边栏会递归读取层级，当前章节的分组自动展开；Learn Claude Code 的导航、卡片与文章共用标题，用 `weight` 控制同层顺序。

Learn Claude Code 主目录当前按新版 S01–S17 排列，S10 是 Task System，S16 是 Workflow Runtime，S17 是 Goal Loop。团队的协议、认领与 Worktree 主题放在 S13 子页面；System Prompt 与 Error Recovery 放在 S15 的子专题里。总览有旧编号迁移表，文章注明教学代码的版本范围。

旧 S18、S19、S20 地址用 Hugo `aliases` 分别跳转到 Worktree 子页面、MCP 与 Integrated Harness。旧 S10–S17 地址已被新主线同编号复用，不能同时作为旧主题的跳转地址；按总览中的主题映射查找。

## 架构图与代码讲解

Learn Claude Code 的完整写作约定见 [博客写作与架构图规则](docs/learn-claude-code-writing-rules.md)，后续章节以该文件为统一参考。

S01 所有功能节点统一蓝色。后续回顾图以蓝色建立已有基线，可以用 `modified="节点标识"` 将本轮要改造的旧模块标为橙色；框内仍是旧实现，第二张才展示改造结果。若某个旧细节在下一张图中合并展示，可用 `folded="节点标识"` 加灰色虚线框，并在图注说明去向；它表示画图粒度变化，功能没有删除。S03 已采用保留文件工具的画法：TOOLS 表示定义，文件工具实现仍明确关联到分发入口，并在 S04、S05 延续。

每张架构图旁自动显示带实际色块和线型的完整图例；未使用项标注“本图未用”。章节变化图使用 `legend="evolution"`，任务状态图使用 `legend="status"`。每次修改图，都同步核对图例文字、样本颜色与图中颜色；它们共用 CSS 变量，适配浅色和深色主题。

S06 沿用分发入口旁原来的工具小框，在 `read / write / edit / glob` 下只加 `TODO → S05` 的历史索引；不展开 Shell 或能力目录大区。本章的 Subagent 仍像 S05 的 TodoWrite 一样，在第二张图完整展开并接入整体流程，第三张再深入拆解。

S07 采用独立专题顺序：先看 Skills 自身的 A–F 机制图，按子章节拆解，S07.8 走完整案例，S07.9 最后接回 Agent Loop。默认路径与可选扩展分别显示，接入伪代码标为教学设计，不声称复刻 Claude Code 内部实现。

S07.10 是完整示例附录。`examples/s07-skills-lab/manifest.json` 维护每个文件的章节归属和注意点，附录通过 `skill-lab` shortcode 直接展示同一份源码。修改示例后运行 `PYTHONDONTWRITEBYTECODE=1 python3 examples/s07-skills-lab/tools/verify_lab.py`，再运行 `python3 scripts/build-s07-lab-archive.py` 更新下载包；本地脚本检查与真实模型评估分别记录。

S08 试用固定总览与局部交互。`s08/explorer.json` 定义七个模块的接口和正文来源；`architecture-explorer` shortcode 在点击节点附近打开一个浮动详情，复用正文图和代码，长内容在面板内滚动。图 1、图 3 保持固定，选择状态不会重排图 2 或改变变化颜色。S08 使用 `compactDiagramLegends: true` 保留短图例并默认收起完整说明。验证命令：`PYTHONDONTWRITEBYTECODE=1 python3 tests/test_s08_explorer.py`（需要本地 Hugo 与 Chrome）。默认总览下面的四个问题用于读者自检，学习效果须另外观察。

学习章节可以先用总图说明新模块插入原流程的位置，再用局部图说明职责和数据边界，随后逐步解释代码，最后用伪代码把流程串起来。图只保留理解机制需要的信息；教学策略和现代产品的公开行为在正文中区分。

S01–S09 统一使用紧凑布局：主流程从左到右，返回循环放在主线下方，分支就近展开。画布宽度为 760，正文显示最大宽度为 760px。S01 以全蓝色建立基础系统，后续机制图用蓝色标出已有流程、紫色标出本节核心机制；演化对照图按下面的对象变化规则着色。避免上下各绕一条返回线，也避免把每个函数细节都塞进总图。

后续章节沿用这套布局。任务依赖图可按状态着色：绿色表示已完成，蓝色表示正在进行，灰色表示待处理；同时写出状态，区分“尚待认领”和“被依赖阻塞”。

S02–S06 的三图对照：图 1 引用上一章总图的结构，保留节点、布局和连线，蓝色保留、橙色标出本轮将改造的旧对象；不补节点或提前画出新实现。图 2 展示改造结果，紫色新增，红色虚线／删除线表示移出；图 3 单独拆解核心机制。旧模块仅因本节展开而变得可见时，仍用蓝色并加灰色来源标签。颜色的参照是本轮变化，不是模块永久属性。优先保持主流程与模块的相对位置，必要的局部移位在正文解释。S06 的独立示例未带入 S05 的 TODO：回顾图用 `removed` 标记旧节点，本轮图将它们放在流程外作为历史对照，不假装仍在运行。

将 SVG 放在章节目录的 `images/` 下，通过可复用的 shortcode 插入：

```text
{{< architecture src="images/memory-loop.svg" label="Memory 在 Agent Loop 中的位置" caption="图 1：请求前召回，正常任务结束后提取与保存。" >}}
```

回顾上一章时通过 `from` 引用原资源，不复制另画：`{{< architecture from="/projects/learn-claude-code/s03" src="images/permission-flow.svg" mode="baseline" caption="回顾 S03 结构，已有功能统一蓝色。" >}}`。`mode="baseline"` 只调整回顾图的展示：统一功能配色、改成中性标题，并移除旧变化图例；原章节总图不变。当前文章的章节来源与图号放在图注中。

SVG 使用唯一的 `title`、`desc` 和箭头 ID，并以 `--diagram-text`、`--diagram-muted`、`--diagram-base-fill/stroke`、`--diagram-memory-fill/stroke`、`--diagram-modified-fill/stroke`、`--diagram-removed-fill/stroke`、`--diagram-storage-fill/stroke`、`--diagram-done-fill/stroke`、`--diagram-line` 设置颜色，提供默认色值。网站会随主题切换配色，窄屏可横向滚动，不依赖外部脚本。S04 的三图可作为演化对照示例，S09 的两张图可作为机制拆解示例。

`.github/workflows/hugo.yml` 是 Actions 自动部署方案，目前已停用；如需启用，把 Pages 来源改为 GitHub Actions 并 `gh workflow enable hugo.yml`。
