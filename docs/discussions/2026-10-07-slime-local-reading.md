# 最新 slime 第一章本地阅读原型

用户授权按当前机制拆解最新源码，停止旧版本内容与历史成长教学。网站采用可选 reading 模式，保留原 Learn Claude Code 阅读器行为；本轮不提交、推送或发布。

## 当前交付

本地地址：http://localhost:1326/projects/slime/01-agent-task/

页面位于 content/projects/slime/01-agent-task，保持 draft。来源为 THUDM/slime 的 2f2318653f6f794dddd321eff7c9d4b7b174643f；学习包由主线程从本轮 Git blob 和 AST 重新导出。原生目录共 645 文件，5 个纳入本章，640 个未纳入。本章 5 视图、25 个 trace 目标。

源包增加 canonical 定义后，共 41 条引用（39 可读、2 外部边界），20 个完整函数定义映射。文件图与函数图由主线程生成并接入；背景不作为函数节点。点击函数看完整定义，步骤按钮看实际调用处／实现处。

## 关键实现与边界

- reading-progress.js 处理源码身份、进度聚合与恢复；记录使用 progressKey，goalId 只作导航。
- reading-view.js 处理目录搜索、阶段、显式自检与双图焦点；文件或函数点击、搜索与换阶段不写记录。
- source-reference 与可选 architecture-explorer reading 参数读取 learning-pack v1；跨文件同名函数和无 def 调用片段均按引用 ID 取代码。
- 文件完成只表示本章 trace 范围自报；静态定义清单和未覆盖项仍显示，不宣称整函数、整文件或轨迹算法已掌握。
- 数据存在、hash 与范围有导出检查；接口绑定由课程作者对照当前代码，不宣称自动静态解析证明运行行为。
- 没有运行目标 Python、模型、CLI、沙箱或训练。本轮未发布网站，预览来自 /tmp 的构建产物。

## 已运行证据

范围与来源状态测试先出现预期缺失失败，随后通过。合成夹具不代表 slime，保存在 tests/fixtures 并只通过临时 Hugo mount 构建。

已运行整个网站 unittest 套件：80 项通过（137.438 秒），包括旧 LCC 回归。最新 canonical 定义包接入后，reading 专项 9 项通过，真实首章三屏、来源和实际刷新恢复 5 项通过（23.571 秒）。刷新验证使用同一临时 Chrome 档案再次打开页面，不仅测试内存模型 restore。Hugo --buildDrafts 构建通过，主线程独立确认本地页面 HTTP 200，并完成 SVG 结构与来源审阅。

独立 UI 审阅发现源码按钮被重复重建，导致弹窗锚点和 Escape 焦点丢失。已增加真实按钮点击的失败复现，再改为仅在目标切换时重建说明；三屏复验通过。面板状态改为限定名与路径，LCC 保留原文案；同页两图的 marker ID 已独立前缀，不改变几何。源端暗色对比与 data-goal-ids 修订已同步。

最终补跑 LCC S08 与 S17：各 4 项通过（12.453 秒、10.331 秒）；本地页面再次核对 HTTP 200，git diff --check 通过。现有其他会话的 CS285 文件未纳入本任务改动。

接续范围：本地首章审查与阅读反馈；保持当前 trace 目标，不扩展其他章节或增加动画。
