# Slime：按目标逐步建立整体模型

[通用方法](../../README.md) · [工作流](../../workflow.md)

用户的阅读目标是准备其提供的腾讯混元 Agent 强化学习框架工程师岗位。以理解框架为主，本地没有 GPU，希望用模型 API 辅助验证；按岗位责任取舍深度。完整目标和初始投入建议继续保存在[岗位对照](../../../slime_photo/code-reading/job-alignment.md)，不在这里复制一份。

整体起点由这个目标和 Slime 的基本任务决定。此前已读 `generate()` 是阅读历史，供重遇时简短提醒；不据此假定整体框架已经理解，也不把全景写成围绕该函数补外围知识。

## 源码与唯一记录入口

- 已确认的本地源码：`/home/hongshi/projects/slime`；本轮固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。历史材料保留各自版本。
- 当前进度与下一步：[阅读路线的当前接续](../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。
- 连贯技术正文：[00 全景 walkthrough](../../../slime_photo/code-reading/chapters/00-overview/walkthrough.md)，其 [Hugo 页面](http://localhost:1313/projects/slime/framework-walkthrough/)从同一文件渲染。
- 模块与函数资料：[现有源码索引](../../../slime_photo/code-reading/code-reading-list.md)。00–07 和 4.1 是资料分组；本目录步骤是理解形成的先后，两者不混用。

## 步骤索引

| 步骤 | 本步核心问题 | 记录 |
| --- | --- | --- |
| 000 | 从岗位目标出发，Slime 最基本的输入、职责与输出是什么？ | [初始模型文件夹](steps/step-000-initial-model/README.md) |

本次只建立真实的起点记录。以后实际展开新问题时再创建下一步，继承前一步模型；不把之前未保存的讨论补写成已完成的学习步骤。

新步骤按 `01-scope.md`、`02-short-term-memory/`、`03-long-term-memory/`、`04-flow.md` 保存范围、本步新认识、前序累计模型与理解过程。两层记忆都镜像 Slime 源码目录，例如 `functions/slime/ray/rollout.py/RolloutManager.generate.md`；字段见[统一规范](../../memory-format.md)。下一步合并上一份 `03` 与 `02`，旧步骤保留当时的理解和目录。
