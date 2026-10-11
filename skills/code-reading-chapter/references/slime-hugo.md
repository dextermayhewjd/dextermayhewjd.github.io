# 当前 Slime/Hugo 项目的映射

仅在工作区为这个中文 Hugo 学习网站时使用本页；其他仓库遵循自己的目录与显示技术。

## 已采用的范例

相对于网站仓库根目录：

- `slime_photo/4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses/2.Translate & Forward/纵向数据流/reading.md`：Action 2 正式正文。看首图、调用骨架、连续示例、逐段出处与末尾复述，不照抄步骤数量。
- 同目录 `SOURCE-CHECK.md`：C 编号的证据清单；`SOURCE.md` 和 `adoption-manifest.json`：文件角色与保留资源的记录。
- `slime_photo/4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses/3.Generate Tokens/reading.md`：已采用的第三版正文，入口表先说明实际交接数据的最小理解，再在使用处展开成员；同目录 `SOURCE.md` 记录原稿与正式稿的分工。
- `slime_photo/code-reading/chapters/01-task-execution/pre-4-template.md`：对象组成较多时的补充模式。相关成员放在对应步骤开头，不先集中列完所有成员。
- `slime_photo/code-reading/AGENTS.md`、`repo-reading-route.md`：阅读边界、仓库确认、固定快照与学习状态的现有约定。

## 三种文件角色

| 角色 | 处理方式 |
| --- | --- |
| 原始材料与图 | 保留；是否重新绘图单独说明，不把旧图悄悄当成新源码证据 |
| 候选阅读稿 | 与正式稿分开存放，默认 draft；使用原文／候选对照入口供用户比较 |
| 已采用正文 | 一个维护来源，Hugo 与必要存档从它同步；采用后避免两份正文独立漂移 |

`README.md` 不天然等于旧稿或正式稿，应先检查实际角色。Action 2、Action 3 均由 `SOURCE.md` 明确分工；Action 3 已采用第三版 `reading.md`，原 `README.md` 与前两版保留为存档。

比较首图和阅读顺序时，必须同时读目标页的 `_index.md` 与所用 shortcode。当前 Action 3 正式页使用 `slime-photo-reading` 直接渲染已采用的 `reading.md`；第一版存档使用 `slime-action-reading` 的 `localDiagramAlt` 将局部图提前。不能根据原 README 的顺序推断正式页；模板未检查时只报告原文件结构。

## 入口表的最小理解对照

Action 3 原稿第 1 节与首版候选的差别，体现了入口表应保留的信息：

| 数据 | 原稿有效含义 | 候选变化与需要保留的内容 |
| --- | --- | --- |
| `translated` | 5 条按历史顺序排列的消息 | “局部变量、规范化消息”补充了身份，却丢失历史顺序；应保留顺序关系 |
| `tools_schema` | 1 个可用工具的定义 | 工具名 `read_file` 可以保留，但仍应说明它是可用工具定义；“局部变量”不能替代此含义 |
| 原始 `body` | 本例从请求读取 `max_tokens: 128`，整份请求交给采样函数 | 只列 `body["max_tokens"]` 会缩小交接对象；先保留原始请求，再解释读取哪个键 |
| 当前 `Session` | 同时提供默认采样参数和上下文预算，交给生成函数 | 拆为两个属性后，整体职责和真正接收者变弱；属性、空字典和 `0` 可放到采样步骤解释 |

这里保留的是任务含义和交接边界，不是单纯保留旧列名或追求更少字。类型、具体值与字段归属仍有用，在相应层次补充。对象组成章节可以详细展开成员，不受入口表行数限制。

## Hugo 接入

- 4.1 的八个当前章节统一在阅读问题后、首图前放 `<div class="reading-navigation" data-reading-navigation="…">`，其中是简短 Python 样式导航。`slime_photo/code-reading/action-navigations.json` 记录各章的文件与导航哈希；真实源码摘录校验排除该块。模型请求章要明确 HTTP 发生于 CLI 运行期间，不能按 Action 编号排成顺序调用。
- `slime_photo/code-reading/action-contexts.json` 是 4.1 各章的语境与主要源码入口映射；语义划分见同目录 `action-contexts.md`。`generate()` 是样本任务编排，2 → 3 → 3.5 在 `_run_turn()` 内展开一次请求，5/6 是环境能力与执行机制；不把这些层次压成同一条顺序步骤。
- `slime-photo-reading` 和 `slime-action-reading` 的可选 `context` 参数引用该映射，在原有图/简介之后、代码展开之前渲染共用块。直接编写的页使用 `slime-action-context key="…"`；总览使用 `slime-action-context-overview`。文件定位默认折叠、链接绑定提交，正文不显示版本号。
- 先按根 `AGENTS.md` 核对 `http://localhost:1313/` 服务和目标页。
- `layouts/shortcodes/slime-photo-reading.html` 支持 `source`、`document` 和 `guide`；适用于已有 Action 2 的正文资源组织，不可无检查地套用到其他深度的目录。
- `layouts/shortcodes/slime-action-reading.html` 默认渲染 `README.md`，可用 `document` 选择当前正文；Action 6、7 的正式页使用增加导航的 `reading.md`，原 README 和历史预览保留。`localDiagramAlt` 仅将原局部图提前、原位置段折叠，并改写链接。
- 图片、JSON、文本和校验文件通过 Hugo resource `.RelPermalink` 发布；不要仅拼接 `/slime-photo/...`，也不要发布依赖失效相对路径的旧离线 HTML。
- `assets/css/extended/reading-source.css`、`reading-object-tree.css` 提供现有折叠与对象树样式。
- 当前导航先于局部图；原组件图／完整生命周期图按需折叠。目录只保留一个章入口；已有兼容 URL 保留，可用 `hideInProjectNav` 隐藏重复子项。

当前 Action 2 页面由 `content/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/2-translate-forward/_index.md` 进入。Action 3 的同级目录为 `3-generate-tokens/`。

## 内容审阅边界与验证

使用已有材料进行格式审阅时，不需要读取新源码。Slime 已确认使用 `/home/fredkeira/projects/slime`，后续章节持续沿用，直到用户更换；不再逐章询问。新增代码解释或改语义前，按此仓库与固定提交核对调用处和实现处。需要更新阅读路线时，由既有 `repo-reading-workflow` 管理，不在这个模板里另建顺序或学习状态。

候选对比应列清哪些是显示变化、内容增补、事实纠正；原文和候选使用相同输入示例。未经确认，不改正式章节内容。用户只要求现有图文直接接入时，可以完成已授权的入口变化。

验证以实际改动为限：Hugo 构建、`python3 -m unittest discover -s tests -p 'test_slime_chapters.py'`，再检查真实侧栏点击、首图、默认折叠和键盘展开、下载资源与窄屏。记录原文件哈希，验证保留范围；页面通过不等于运行过 Agent 或模型服务。
