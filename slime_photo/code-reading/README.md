# 源码阅读目录

## 每次开始前：确认源码与官方最新版本

1. 读取已确认的仓库记录：Slime 持续使用 `/home/fredkeira/projects/slime`，核心包是其中的 `slime/`。后续章节不再反复询问；只有用户更换路径、尚未确认仓库或候选有歧义时才确认。
2. 启动或确认本地 Hugo 预览，打开 [源码阅读顺序](http://localhost:1313/projects/slime/code-reading/)，供用户边读边看。
3. 检查本地分支、工作区与 HEAD，并直接查询 **THUDM/slime 官方 main**。本地 `origin` 可能是 fork，不能仅凭“与 origin/main 一致”判断是否官方最新。

```bash
git -C /home/fredkeira/projects/slime status --short --branch
git -C /home/fredkeira/projects/slime remote -v
git -C /home/fredkeira/projects/slime rev-parse HEAD
git ls-remote https://github.com/THUDM/slime.git HEAD refs/heads/main
```

4. 对比本地 SHA 和官方 `refs/heads/main` SHA：相同说明本地提交与核对时的官方 main 一致；还需检查工作区改动。不同则用官方比较页面或接口核对领先/落后、分叉和改动范围；网络查询失败时记录“未核实”，不能用缓存的远端引用宣称最新。
5. 记录核对时间、官方 SHA、本地 SHA 与差异。检查版本不会自动更新本地源码；需要更新时保留用户改动与阅读记录，并在更新后重新核对函数、行号和路线。正式阅读绑定一个明确的提交。

## 本次实际核对结果

核对时间：2026-10-10 UTC。详情与数据来源见 [upstream-check.json](upstream-check.json)。

| 项目 | 结果 |
| --- | --- |
| 本地路径与分支 | `/home/fredkeira/projects/slime`，`main` |
| 本地 `origin` | `git@github.com:dextermayhewjd/slime.git`，为 fork |
| 本地 HEAD / 阅读快照 | `22a89f96835969a47055a659c588f46151f8b07a` |
| 官方 main | `d06df4d77a1fbcf7bdc48e13071cf649e670133a` |
| 是否为核对时的官方最新 main | **否：官方领先 1 次提交，本地没有额外提交** |
| 差异内容 | `test: register Megatron bindings regression in CPU CI (#2458)`；仅 3 个 CI/测试文件，未修改本次阅读的核心源码 |
| 本地工作区 | 已跟踪文件无改动；存在未跟踪的 `.ua/`、旧 `docs/repo-reading-route.md` 和 `docs/repo-reading/` |
| 本轮处理 | 保留本地源码与旧阅读记录，阅读清单绑定本地 `22a89f9`，记录官方差异 |

[查看官方提交差异](https://github.com/THUDM/slime/compare/22a89f96835969a47055a659c588f46151f8b07a...d06df4d77a1fbcf7bdc48e13071cf649e670133a)。这是核对时的结果，新的阅读分析仍需重新查询。

## 阅读入口

每章先定位“正在跟随哪一层调用”，再打开所需源码。共用划分见 [4.1 各章语境与源码入口](action-contexts.md)，逐章文件/符号清单维护在 [action-contexts.json](action-contexts.json)；网页在各章的默认折叠入口中展示。

**当前先完成 4.1。** 直接打开[沿 generate 完成一次任务](chapters/01-task-execution/walkthrough.md)，沿主线进入各职责组件，讲完返回外层任务，把启动、模型请求循环、结果与清理连起来。阅读目标见[唯一路线中的当前主线](repo-reading-route.md#当前优先沿-generate-读完-41)。

Pre-4 的完整章节存档见 [Pre-4.启动前准备/README.md](../../slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/Pre-4.启动前准备/README.md)，包括 SVG、源码入口与来源说明。

本轮接续阅读：[Harness.run 主线](http://localhost:1313/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/4-launch-agent/harness-run/) → [动作5 Sandbox 的环境能力](http://localhost:1313/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/5-manage-sandbox/)，每次下钻后回到对应调用位置。

进入 Launch Agent 前，先读 [Pre-4：启动前准备](chapters/01-task-execution/pre-4-preparation.md)。它在页面目录中位于 3.5 后、4 前，解释进入 run 前的条件；实际执行顺序按完整任务主线理解。

完整任务读通后，用[代码阅读顺序名单](code-reading-list.md)继续定位和扩展：26 个条目列出真实文件/函数、阅读停止点与配套测试材料。该名单是[唯一阅读路线中的清单](repo-reading-route.md#最终代码阅读清单)的派生视图。

按[阅读路线](repo-reading-route.md)逐章推进。
各章 README 是范围与入口；walkthrough 和 review 在实际阅读该单元后生成。

开始一个单元时，先看[目标需求对照](job-alignment.md)中的相关行，用模块责任、扩展接口、失败情景和验证证据检查阅读重点。

部件和缺口见 [COVERAGE.md](COVERAGE.md)。目录存在不代表正文已完成或用户已掌握。

- [第 0 章 全局职责与三种运行粒度](chapters/00-overview/README.md)
- [第 1 章 完整任务、Harness 与执行环境](chapters/01-task-execution/README.md)
- [第 2 章 模型协议、上下文与训练轨迹](chapters/02-model-context/README.md)
- [第 3 章 策略接入、数据生成与评测合同](chapters/03-strategy-evaluation/README.md)
- [第 4 章 Trace、结果分析、测试与复现](chapters/04-trace-validation/README.md)
- [第 5 章 并发、任务数据、背压与恢复](chapters/05-concurrency-recovery/README.md)
- [第 6 章 模型服务、Ray 资源与容器边界](chapters/06-serving-resources/README.md)
- [第 7 章 训练交接、策略版本与权重更新](chapters/07-training-handoff/README.md)
