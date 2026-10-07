---
name: review-diff
description: 提供 review-worker 使用的审查准则；任务范围由委派消息给出。
user-invocable: false
---

# 预加载的审查方法
SOURCE_TAG: preloaded-method

这是方法，不是任务。根据委派消息确定文件范围和输出要求。
需要时读取项目中的下列资源：
- .claude/skills/review-diff/references/input-boundaries.md
- .claude/skills/review-diff/references/concurrency.md
输出格式见 .claude/skills/review-diff/assets/report-template.md。

先核对代码约定，再收集触发条件和证据；没有足够证据时说明不确定性。
预加载会直接交付本文件全文，不需要先让模型按描述选择它。
