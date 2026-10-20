# Slime：按目标逐步建立整体模型

[通用方法](../../README.md) · [工作流](../../workflow.md)

用户的阅读目标是准备其提供的腾讯混元 Agent 强化学习框架工程师岗位。以理解框架为主，本地没有 GPU，希望用模型 API 辅助验证；按岗位责任取舍深度。完整目标和初始投入建议继续保存在[岗位对照](../../../slime_photo/code-reading/job-alignment.md)，不在这里复制一份。

本轮已确认阅读方向是 Coding Agent。Step 0 以阅读目标、指挥官函数和核心骨架建立整体轮廓；用户现在明确追问 Harness 怎样接到 Adapter 请求入口，当前进入 Step 1。每个后续 step 仍先一起确认具体问题与函数范围。此前已读记录继续保留，不据此推断当前掌握状态。

## 源码与唯一记录入口

- 已确认的本地源码：`/home/hongshi/projects/slime`；本轮固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。历史材料保留各自版本。
- 当前进度与下一步：[阅读路线的当前接续](../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。
- 连贯技术正文：[00 全景 walkthrough](../../../slime_photo/code-reading/chapters/00-overview/walkthrough.md)，其 [Hugo 页面](http://localhost:1313/projects/slime/framework-walkthrough/)从同一文件渲染。
- 模块与函数资料：[现有源码索引](../../../slime_photo/code-reading/code-reading-list.md)。00–07 和 4.1 是资料分组；本目录步骤是理解形成的先后，两者不混用。

## 步骤索引

| 步骤 | 本步核心问题 | 记录 |
| --- | --- | --- |
| 001 · 当前 | Harness 怎样启动 CLI，CLI 怎样经 HTTP 进入 Adapter？ | [步骤入口](steps/step-001-harness-to-adapter/README.md) |
| 000 · 前序 | 理解 Coding Agent，定位指挥官函数并提取核心骨架 | [步骤入口](steps/step-000-coding-agent/README.md) |
| 000 · 历史 | 此前从框架启动定位整体模型的方案 | [旧初始模型](steps/step-000-initial-model/README.md)，保留历史，不作为当前起点 |

Step 0 的三项 scope 见[原阅读范围](steps/step-000-coding-agent/01-scope.md)。Step 1 的范围见[当前阅读范围](steps/step-001-harness-to-adapter/01-scope.md)，`03` 已继承 Step 0 的转换函数记录，`02` 保存本步的 Harness 函数记录；助手给出连接解释不等于用户已掌握全部实现。

新步骤按 `01-scope.md`、`02-short-term-memory/`、`03-long-term-memory/`、`04-flow.md` 保存范围、本步新认识、前序累计模型与理解过程。两层记忆都镜像 Slime 源码目录，例如 `functions/slime/ray/rollout.py/RolloutManager.generate.md`；字段见[统一规范](../../memory-format.md)。下一步合并上一份 `03` 与 `02`，旧步骤保留当时的理解和目录。
