# 000 · 从阅读目标建立最小整体模型

> 2026-10-21 已按用户要求移出当前步骤目录。以下保留当时内容；当前保留的步骤见 [Slime 项目入口](../../../../00-repo-reading/repositories/slime/README.md)，实时接续见[阅读路线](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。

2026-10-20：本页保留此前的框架启动方案。当前入口为 [Step 0 · Coding Agent 阅读准备](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-000-coding-agent/README.md)，具体主题须先由用户确认；下文关于 `train.py::main()` 的安排属于历史。

- 日期：2026-10-19。
- 前一步：无；从[Slime 阅读目标](../../../../00-repo-reading/repositories/slime/README.md)开始。
- 记忆来源：原 `000-initial-model.md`，按用户确认的目录格式迁入。
- 源码提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。
- 记录性质：助手定位与个人认知分开。先前的模型草案与静态源码分析移到 references，个人模型等待用户表述。

## 本步入口

1. [1.1 本步涉及范围](01-scope.md)：只看整体主线所需的代码。
2. [1.2 整体地图与完整记忆](02-memory/overview.md)：职责关系、已涉及源码与逐函数记录。
3. [1.3 初始定位与个人表述](03-flow.md)：定位后保留用户怎样描述运行过程。

## 本步新增或修正了什么

根据用户纠正，全景从阅读目标与框架基本职责建立；曾经读过 `generate()` 是历史记录，影响回顾深度。起点模型保留“任务与配置 → 生成评分 → 数据交接 → 训练 → 权重返回”，再逐步展开具体调用。

按用户对职责的纠正，原先助手写出的完整模型与三个源码分析移入 `references/`。`02-memory/` 中保留对应定位和未表述状态；只有用户自己的理解才能填入正文，具体实现允许留白。

## 下一问与证据边界

下一问仍是“谁启动工作，第一次怎样进入生成与训练循环？”后续实际展开 `train.py::main()` 时创建 step-001，先完整复制本步 `02-memory/`，再更新范围、函数理解与整体模型。

当前进度继续只在[阅读路线](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)维护。以上入口已静态核对；没有实际启动模型、Agent、训练或集群。
