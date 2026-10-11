# 全局职责回顾

[本章讲解](walkthrough.md) · [阅读路线](../../repo-reading-route.md)

当前证据：源码入口与固定 Git blob/AST 符号已静态核对。用户复述尚未记录；以下练习尚未执行。

## 闭卷复述

1. `agent/`、`rollout/`、`data/`、`ray/`、`backends/` 分别管理什么？它们在哪里发生数据或控制权交接？
2. 一次任务、一次模型请求和一份训练 Sample 为什么不是同一粒度？
3. 工具调用表示的解析、工具真正执行和执行环境操作分别由谁负责？
4. CLI 正常退出能否直接说明任务通过评分？Agent 的工作环境为什么与评分环境分开？
5. 新增策略、评分器、模型协议或沙箱后端，分别从哪个入口开始改？
6. 阅读 Ray、Docker 和 E2B 实现后，还缺哪些 Kubernetes 实践？

## 一个源码定位练习

建议：在 VS Code 中打开源码仓库，只用已定位的文件，不运行外部服务，画出代码任务骨架。每个节点写出输入、输出/副作用、调用者、返回位置和清理者。

```text
task -> sandbox + harness -> CLI
CLI -> HTTP adapter -> SGLang -> reply + turn record
task -> diff -> fresh evaluation -> reward
session -> trajectory export -> samples -> rollout result
rollout result -> training -> checkpoint + weight update
```

图中 CLI 内部工具循环、SGLang 内部生成和 E2B 服务操作都标为外部边界。再沿一次 wall-clock timeout 定位 aborted 结果、环境退出和 Session 清理。

验收证据应包括文件/符号位置、正常路径与失败分支的区别、仍未解释的实现。静态定位成功不记成 Agent 或训练运行成功。

## 学习记录

学习状态以唯一阅读路线为准，目前为“未开始”。材料已生成不等于用户未曾接触过相关概念，也不自动表示用户已经掌握。用户复述或明确报告结果后，再记录本章范围内的进展与缺口。
