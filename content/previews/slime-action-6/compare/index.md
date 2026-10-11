---
title: "6. Exec Commands · 新旧阅读稿对比"
description: "左侧保留原讲解，右侧沿同一 CLI 任务展开代码与交接。"
statusText: "右侧为候选稿，正式页尚未替换。"
chapterLabel: "Action 6 Exec Commands"
originalLabel: "原有讲解"
candidateLabel: "新版阅读候选稿"
layout: "slime-reading-comparison"
draft: true
originalPage: "/previews/slime-action-6/baseline/"
candidatePage: "/previews/slime-action-6/"
---

两边都解释同一套后台执行机制。新版先走完正常返回，再展开防重、预算和失败边界。

| 对比位置 | 原有讲解 | 新版候选 |
| --- | --- | --- |
| 首图 | 任务生命周期图 | 本章启动与等待局部图，生命周期按需展开 |
| 入口 | 参数用途清单 | 真实 run_agent 调用，加上输入、接收者与最小理解 |
| 上层定位 | 从执行机制开始讲解 | 局部图之前先用短伪代码标出当前入口，具体实现在图后展开 |
| 过程 | 文字流程与启动片段 | 脚本、清理、启动、轮询、输出六段真实代码，沿同一示例推进 |
| 状态 | 说明退出码返回 | 区分启动提交状态、标记检查状态、CLI退出状态和预算状态 |
| 出处 | 路径与行号直接出现在正文 | 解释旁默认折叠，另存源码校验清单 |
| 例子 | 静态讲解 | 用记录型依赖执行原函数；SDK和CLI仍未运行 |
