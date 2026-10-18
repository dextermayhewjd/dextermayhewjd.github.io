# Future 基础与线程交接课程整合

> **For agentic workers:** 按已确认方案在当前会话执行；课程规则和生成检查是交付依据。

**Goal:** 按用户确认的比较结论，将本地 20.2–20.5 的小步 Future 基础接回远端课程，保留远端 33.1–33.4，并把 35.1–35.2 改为复习与源码应用。

**Architecture:** `curriculum.json` 继续是课程结构与 API 归属的唯一数据。恢复四个独立页面和例子，维护现有 URL、导航与示例清单，再由现有工具生成课程表及频率表。

**Tech Stack:** Hugo Extended 0.166.0、Markdown、Python 3.12.3、unittest。

**Spec:** 用户在本次会话批准的三项取舍：恢复本地第 20 单元基础顺序；保留远端第 33 单元拆分；第 35 单元保留复习、取消状态和源码对照，完成回调继续独立讲解。

## 约束与检查重点

- 保留 8 模块、41 主编号、97 项 API，每个 API 恰有一个正式引入位置。
- 恢复来源是 stash `9c164892a3460e6713155b8e9b6f0d31b5d936c2` 及其未跟踪文件父提交。
- 保留远端新增的第 25、34–38 单元及现有 URL，不恢复导航脚本等无关本地变更。
- 第 20 单元先区分对象与执行，再观察等待、交付与异常；第 35 单元不重复承担首次讲解。
- 第 33 单元继续分开当前循环、线程池提交、通知交接实验、循环时钟。
- 检查侧栏五节分组、20→21 和 33→34 的页间链接、35 的复习回链。
- 检查新页面主例子与下载文件一致，恢复的四个例子可运行。

## 执行步骤

- [x] 先更新课程归属与导航回归检查，确认当前版本不满足已批准的结构。
- [x] 恢复 20.2–20.5，补齐取消状态对照，调整 20.1、21.1、31.1 和 33 的前置说明。
- [x] 更新课程 JSON、示例清单、学习路线和项目记录；保留 33 的四节结构。
- [x] 精简 35.1–35.2 为复习与源码应用，35.3 承接第 20 单元基础。
- [x] 生成课程表与频率表，运行课程检查、页面检查与相关示例。
- [x] 核对 Hugo 预览的页面、导航与已有 URL，最后审阅差异。

## 验证命令

```bash
python3 python-async-reference/tools/build_curriculum.py --check
python3 python-async-reference/tools/build_lesson_api_frequency.py --check
python3 -m unittest discover -s tests -p 'test_python_async_curriculum.py'
python3 -m unittest discover -s tests -p 'test_python_async_project.py'
python3 -m unittest discover -s tests -p 'test_python_async_api_frequency.py'
```

示例涉及线程唤醒时在正常本机环境验证，避免沙箱限制被误判为代码问题。

## 完成记录

- 课程检查 17 项、API 频率检查 17 项、页面与示例检查 53 项全部通过；后者运行并验证 68 份主示例。
- `build_curriculum.py --check` 验证 41 单元、97/97 API、语法与异常映射；频率表生成检查通过。
- 本地预览逐页核对 20.2–20.5、35.1–35.3 及学习路线，首页从 20.1 到 21.1 的链接顺序连续。
- 独立审阅发现的示例计数、首页旧路线与旧版首次讲解话术均已修正。
- 35.3 直接以前面 Task 与第 20 单元为前置，两个复习页不构成强制阅读门槛。
- 原本地快照保留；修改留在当前工作区。
