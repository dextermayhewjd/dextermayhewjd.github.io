# Learn Slime：从 Agent 基础自下向上

用户反馈覆盖上一版默认阅读方式：首屏太密集，改为小课，不在入口展示文件目录、大图、25 步控件或 trace 审计说明。旧单任务闭环保留为进阶串联；不发布。

## 页面

- 课程首页按 4 组列出 17 小课；每项只有课名与入口。
- 每页一个问题、2–3 段解释、一个例子、一段不超过 24 行的实际源码；复述答案、更多源码与版本信息折叠。
- 上下课链接与上下层依赖由课程提供，网页不另推断学习顺序。
- 一个页尾勾选记录该课自检（自报）。小课使用新 progressKey，不能把旧 25 步的完成当成这些小课已学。
- 首页模块图只生成明确勾选的小课；尚未勾选的模块不出现在图中。初始为空，引导进入第一课，不画全部未来模块再淡化。

## 数据接口

直接消费主线程当前源码重新编写的 agent-course.json：根含 repository、revision、groups、lessons。

lesson 含 id/title/group/question/explanation[]、example{language,code,explanation}、snippets[{path,symbol,line,endLine,text,url}]、check{question,answer}、prerequisites[]、next[]、files[]、progressKey。组 ID 与课 ID 稳定，来源仍为最新确认的 THUDM/slime。

页面位于 projects/slime/agent/{id}/，每页资源 lesson.json 保存其课程项与来源；页面不复制 645 文件目录。源码正文为实际摘录，不执行目标模块。引用版本和路径可折叠，但代码与解释不能隐藏。

## 实现边界与验收

使用简洁 agent-course 与 agent-lesson 页面组件，复用 Hugo Markdown、highlight 和现有导航；不把完整 architecture-explorer 强行放入小课。

本机记录只在用户勾选时改变，以 repository/revision/progressKey 分区；点击页、读源码、展开答案不计掌握。图仅反映自报小课，不能表示全文件覆盖。

验收：17 页正文齐全、4 组目录、真实来源与 ≤24 行摘要、不显示默认大图/审计目录、勾选与刷新恢复、已学图无未来节点、手机阅读、旧 LCC 与进阶页兼容。当前源码与课程解释由主线程负责，网站只呈现，不延续旧源码内容。
