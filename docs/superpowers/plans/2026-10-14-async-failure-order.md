# Python 异步课程：失败处理顺序调整

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按用户确认的顺序重排已学课程，补齐 TaskGroup 失败处理的两个子课，并让课号、前置和导航一致。

**Architecture:** 继续使用 `curriculum.json` 作为唯一课程数据；保留页面 URL，以新课号显示标题和连接。共 41 个编号单元，其中 10、11 各有两个独立子课，17–41 自身编号保持不变。

**Tech Stack:** Hugo Extended 0.166.0、Markdown、Python 3.12.3、unittest。

**Spec:** 本轮用户确认的学习顺序与 `.agents/skills/python-syntax-learning/SKILL.md`；反方审阅由 `async_order_opposition` 独立完成。

## Global Constraints

- 保留已有 URL、下载与有效锚点，不提交或发布。
- 82 项 API 的正式引入不遗漏、不重复；语法与异常映射落在实际讲解的子课。
- 01–08 保持原顺序；先取消和失败处理，再按完成顺序取结果，最后超时。
- 原 Slime 课程证据继续绑定已有固定快照；新 TaskGroup 行为以官方 CPython 3.12.3 源码核对，不把框架吞掉的异常当作 TaskGroup 失败证据。

## 编号映射

| 原编号 | 新编号 | 内容 |
| --- | --- | --- |
| 10 | 09 | Task.cancel |
| 15.1、15.2 | 10.1、10.2 | gather 的失败与异常收集 |
| 16（待写） | 11.1、11.2 | TaskGroup 失败收尾、异常组 |
| 09 | 12 | as_completed |
| 11、12、13、14 | 13、14、15、16 | wait_for、时钟、timeout、shield |
| 17–41 | 不变 | 后续单元，前置引用同步映射 |

## Review Focus

- 不能只验证前置编号更小，必须验证仍指向同一概念。
- 10.2 不提前依赖 shield；各课“上一课”与实际顺序一致。
- 11.1 不把异常组当原始 ValueError；11.2 才正式引入 ExceptionGroup / except*。
- 小数编号来自课程数据，原 URL 数字和历史目录不作为新课号。
- 旧下载、浏览器导航、窄屏、键盘折叠与源码哈希都可复核。

## Tasks

- [x] 添加并观察新顺序、子课语法归属与新实验的失败测试。
- [x] 编写 11.1 与 11.2，各保留一个正常阅读的主实验及可选源码。
- [x] 按映射一次性更新课程、前置、页面标题、章节承接和 manifest；生成课程表。
- [x] 验证 API / 语法 / 异常归属、示例与源码、页面和下载，再跑本专题完整测试与站点导航检查。
- [x] 请独立审阅者检查最终结果，处理发现的问题，向用户提供新的学习入口。

## 验证结果

- 本专题 43 项测试、站点导航检查均通过。
- 课程、82 项 API 清单和覆盖报告的生成检查通过。
- 新课在桌面和窄屏下显示正常，导航顺序、下载示例和键盘展开源码均已检查。
- 独立反方审阅提出的隐性前置、子课语法归属及章节承接问题均已修正，最终未发现阻止交付的问题。
