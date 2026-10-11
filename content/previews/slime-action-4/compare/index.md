---
title: "4. Launch Agent · 原讲解与已采用稿对比"
description: "左侧保留原有 Harness.run 主线讲解，右侧展示已采用到正式页的阅读稿。"
statusText: "右侧阅读稿已采用到正式页；左侧保留原有讲解供对照。"
chapterLabel: "Action 4 Launch Agent"
originalLabel: "原有 Harness.run 讲解"
candidateLabel: "已采用阅读稿"
layout: "slime-reading-comparison"
draft: true
originalPage: "/previews/slime-action-4/baseline/"
candidatePage: "/previews/slime-action-4/"
---

左侧完整保留采用前的 **Harness.run 主线**讲解；右侧阅读稿已采用到正式页，将同一段 `run()` 的局部图、实际交接数据、代码和解释接在一起。两侧可独立滚动，也可分别在新标签中阅读。

| 对比位置 | 原有讲解 | 已采用稿 |
| --- | --- | --- |
| 阅读入口 | 从公共 `run()` 的完整骨架进入 | 先看 `run()` 局部图，再说明输入与最小理解 |
| 正常路径 | 用下钻书签串起用户准备、上下文、配置与启动 | 保留同一主线，逐步连接关键代码、产物与接收者 |
| 上下文与参数 | 说明哪些字段进入 `HarnessContext` | 在使用处展开成员，保留独立传递的 Sandbox、提示词与预算 |
| 与其他动作的边界 | 集中说明动作 5、6、7 的关系 | 在实际委派处说明边界，读完返回 `run()` |
| 源码定位 | 文件和行号随正文显示 | 解释旁默认折叠，集中保存源码校验清单 |
| 阅读收口 | 追踪退出码返回调用方 | 保留返回链路，并补检查理解的复述问题 |

已采用稿的局部图只解释 `Harness.run()` 内的职责，原有包含启动前准备的图作为补充材料保留。
