# dextermayhewjd 的学习笔记

这里记录我对项目、课程和工程实践的理解。按主题逐步拆解概念，把架构图、源码和自己的思考放在同一条阅读路径里。

**[进入网站 →](https://dextermayhewjd.github.io/)**

## 从这里开始

- **[00 · 仓库阅读与认知构建](00-repo-reading/README.md)**：适用于任意源码仓库。从阅读目标建立基本框架，每一步记录问题、目录/文件/函数和理解变化，下一步继承上一步的整体模型。
- **[Learn Claude Code](https://dextermayhewjd.github.io/projects/learn-claude-code/)**：目前的主要学习系列。从 S01 到 S17，逐步理解 Agent Loop、工具、Skills、上下文、Memory、任务系统、Workflow 与 Goal Loop。
- **[项目](https://dextermayhewjd.github.io/projects/)**：以项目为线索，记录系统结构、设计选择和实现过程。
- **[课程](https://dextermayhewjd.github.io/courses/)**：按课程组织学习内容，目前先保留课程目录和章节结构示例。

## 笔记怎样组织

Learn Claude Code 系列围绕“回顾已有系统 → 看清本轮改动 → 拆解核心机制”组织内容，配合分段源码和主循环伪代码理解。

部分架构图支持悬停追踪连线、点击函数查看实现。目的在于看清每个机制接在哪里、接收什么、返回什么，以及系统如何逐步演化。

这些内容是我的学习笔记；借鉴的教学实现和官方资料会在对应文章中注明来源与适用范围。

这套图形拆解方法也保留为一种[可复用的阅读笔记格式](docs/diagram-reading-method.md)，用于后续项目、课程或核心机制的学习；可以按需要选择两图对照或局部拆解。

## Codex Review 时间线

在功能分支对应的 worktree 里打开 Codex。选 `/review` 的哪一项，取决于此刻要审的是方案、手里的改动、一笔提交，还是整个 PR。

```text
只有方案卡          ④ Custom review instructions    指定文件，说明想核查的假设
    ↓ 写实现、补测试
代码已改，尚未提交  ② Review uncommitted changes    看本次工作树的改动
    ↓ git commit
取得本地 SHA        ③ Review a commit               看这一笔提交，推送前就能用
    ↓ 准备提 PR
选 PR 的目标分支    ① Review against a base branch  看整个分支要交付的差异
```

### Review 发现错误，修在哪一笔？

假设原计划依次做 C01、C02、C03，问题出在 C02。

```text
C02 还在写                C01 → C02（修正实现，补回归测试）→ C03
C02 已推送，C03 尚未做    C01 → C02 → 修复 C02 → C03
C03 也已推送              C01 → C02 → C03 → 修复 C02
```

**可以调整接下来先做什么。** 如果 C03 依赖 C02 的正确行为，先用一条测试复现错误，修好并验证，再继续 C03。如果只是同一笔尚未提交的实现没写对，就把修正和测试一起交付。

**已经发生的顺序看 Git 历史。** 普通 `git commit` 会接在这个 worktree 当前的 `HEAD` 后面，修复可以引用原提交的 SHA。若在尚未共享的个人分支上确实要把修复插到旧提交旁边，可以用交互式 rebase 重新排列，受影响的提交会获得新 SHA。已经推送并供别人评审时，追加修复最方便对照上轮意见。在 PR 记录里写清修了哪一笔、修复 SHA 和哪条回归测试通过即可。

## 本地预览

网站使用 Hugo 与 PaperMod。当前构建版本为 Hugo Extended 0.166.0。

```bash
git clone --recurse-submodules https://github.com/dextermayhewjd/dextermayhewjd.github.io.git
cd dextermayhewjd.github.io
./serve.sh
```

打开 [http://localhost:1313](http://localhost:1313)。脚本会同时显示草稿，修改文件后自动刷新；按 `Ctrl+C` 停止服务。

已克隆仓库时，在仓库根目录运行 `./serve.sh` 即可。如果缺少主题，先运行 `git submodule update --init --recursive`。

可以追加 Hugo 参数，例如端口已被占用时运行 `./serve.sh --port 1314`，然后访问 `http://localhost:1314`。也可以用 `HUGO=/path/to/hugo ./serve.sh` 指定 Hugo 程序。

`serve.sh` 用于本地预览。`deploy.sh` 用于正式发布，会构建网站并强制推送到远程 `gh-pages` 分支。

<details>
<summary>开发与维护</summary>

| 目录 | 用途 |
|---|---|
| `00-repo-reading/` | 通用源码阅读工作流、单步模板与各仓库的认知构建记录 |
| `content/` | 文章、项目章节与课程笔记 |
| `assets/`、`layouts/` | 页面样式、导航和图形交互 |
| `examples/`、`static/` | 示例源码与可下载资源 |
| `docs/` | 写作约定与设计记录 |
| `tests/` | 导航、图形和源码对照检查 |

生产构建：

```bash
hugo --gc --minify
```

源码保存在 `main`，开发分支为 `feature/project-course-navigation`。GitHub Pages 从 `gh-pages` 提供构建后的静态网站；仅推送源码不会更新线上页面。

进一步维护时可参考：

- [博客写作与架构图规则](docs/learn-claude-code-writing-rules.md)
- [图形交互设计记录](docs/discussions/2026-10-05-s08-interactive-diagram-pilot.md)
- [Skills 示例与验证说明](examples/s07-skills-lab/README.md)

</details>
