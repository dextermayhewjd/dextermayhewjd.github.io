# Dressage：按岗位目标逐步建立整体模型

[通用方法](../../README.md) · [工作流](../../workflow.md) · [岗位对照资料](job-and-repo-comparison.md)

阅读目标：为腾讯混元 Agent 强化学习框架岗位建立能力，围绕任务执行、模型与工具调用、上下文与轨迹、评测、训练数据交接及运行治理逐步阅读。官方文档作为资料索引；具体入口按当前问题、真实调用与必要前置选择。

## 源码与当前接续

- 源码仓库：`/Users/dextermayhew/projects/Dressage`。
- 本轮核对提交：`3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 当前接续：[Step 0 · 黑盒任务如何交回训练样本](steps/step-000-slime-bridge-and-interfaces/README.md)。用户于 2026-10-23 确认写入 scope；材料建立不表示已掌握或已运行。
- 当前学习内容在 Markdown 中预览；博客呈现另按用户明确要求处理。

## 步骤索引

| 步骤 | 本步问题 | 入口 |
| --- | --- | --- |
| 000 · 当前 | 一份黑盒 Agent 任务，怎样执行并交回可供后续训练处理的样本？ | [01-scope.md](steps/step-000-slime-bridge-and-interfaces/01-scope.md) |

Step 0 先建立 `blackbox_dispatch.generate()` 的正常路径骨架，定位回答与轨迹的两条结果通道，并保留环境回收时机。子函数内部留待后续问题展开，本步不创建函数卡片。下一步尚未确定；“执行期间怎样记录一次模型请求”保留为候选。

## 历史与证据边界

本轮落盘前，原 steps 目录已不存在。此前项目入口对 Step 1 的描述保存在[历史快照](steps/step-000-slime-bridge-and-interfaces/references/project-entry-before-step0.md)，不据此重建旧函数卡片或推断用户掌握状态。当前接续只在本页维护。

[认知阅读指南](cognitive-reading-guide.md)与岗位对照保留作既有参考；其中旧步骤安排不覆盖本轮确认的 scope。源码解释、个人理解和真实运行证据分别记录。
