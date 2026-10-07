# S15 Integrated Harness：从本地实现理解组装接点

用户要求重点看本地 S15，并考虑上一轮图、本轮整合图、核心组装图及上游配图。后续明确暂不考虑 Error 部分；本次最终范围是组装、工具执行与正常消息回流。固定源码 ce8f9f186058939da54c9d6fead78dfb5d0fd6c3，教学仓库只读。

上游 system-architecture.svg 用上方主循环、下方四个组件分组和工具池解释集成。保留原图作为可折叠图片对照及 MIT 许可；博客总图借鉴其分层，不继承上游主题颜色。图 1 直接复用 S14 默认图，不采用后加的 Tool Search 扩展；四个 MCP 细节标灰色虚线，组装与事件接口标橙色。

图 2 保留已有节点位置与主循环，将 MCP 实现合并到动态工具池与同步调用，右侧解释请求组装、工具池、异步事件桥和后台 Bash。Memory 由每用户回合的学习接口改成每个主 while 轮次刷新；压缩结束回到准备阶段，再组装 context、SYSTEM 与 tools。旧学习骨架的 Stop 反馈续轮没有在本地 S14／S15 实现，当前总图校正为正常统计与收尾；这是图示校正，不是删除实际能力。

图 3 分八个接点：事件与提醒、历史／context、配置／工具池、模型请求与判断、权限／分发、结果批次、正常收尾、宿主入口。完整函数来自源码，可点击就近阅读；原主函数可折叠，但阅读器能取到。正文分四组两级目录，代码先交代职责和输入输出，再用整体伪代码串联。

组装不是自动导入所有旧章节：多数机制直接定义在 S15/code.py，Memory 明确装载 S09 并共享 client、MODEL、workspace。SYSTEM / messages / tools 分工不同；active_teammates 虽收集到 context，当前 SYSTEM 函数没有渲染它。Skills 是简化 loader，MCP 仍为 mock，未集成 S14.3.6 的 Tool Search。

实际内置列表有 26 个 schema、25 个普通 handlers；compact 是单独控制分支，先回配对确认，本批全部结果交齐后摘要，不执行普通 Pre／Post。主线程每条 Bash 要确认，异步轮次拒绝交互；subagent 和 teammate 各有自己的工具集，不能说所有 Agent 都拥有主工具池。

用户与事件线程共用 agent_lock 和主 history。Team 在外层消费，Cron 与后台在内层注入；已完成后台工作能唤醒同一内核。后台先回占位，worker 真实结束才运行 Post 并发布通知，两个回传入口共用原子 collect。normal Stop 后才检查 Memory 和释放 completed assignment。

Error Recovery 本次不展开。当前本地还有 with_retry 等包装，保留函数完整源码便于复核，不再画独立恢复模块或展开状态算法；原 S15.2 子专题保留位置并说明暂不展开。S15.1 新增本地真实组装放在开头，旧版原型、缓存设计保留为明确对照。

验证记录：Hugo 构建和项目导航通过；S15 第一张图的几何／路径与 S14 保持一致，整体／核心图无穿框或共线重叠。六项源码、实际组装及三种宽度浏览器检查通过，覆盖主请求刷新、MCP 工具下一轮可见、26／25 计数、compact 批次时序、函数查看、连线悬停、完整折叠源码取用、键盘、ID 唯一和窄屏布局。上游原图复制逐字一致。

另运行教学仓库离线行为检查：agent_teams_runtime 64 项与 69 个子测试通过，agent_loop_boundaries / compaction_tool_pairs 合计 105 项与 22 个子测试通过。实际模型与外部服务未调用，教学源码未修改；截图核对总图与核心图排版。

## GitHub／本地／博客对照核验

用户再次询问博客是否也对照代码，而不只是 README。只读取得 GitHub main 的精确 SHA，仍为 ce8f9f186058939da54c9d6fead78dfb5d0fd6c3；按此 SHA 下载 code.py、README.zh.md、system-architecture.svg 到 /tmp，三份均与本地逐字一致。再次运行博客函数 AST 核对通过。

README 与博客的主线一致，讲解粒度不同。README 有 26／25 两种工具计数、压缩概览省略 fit_tool_results、Hooks 概述没有突出 compact 特判；博客按源码分清 schema 与 handlers，写出完整预算顺序和控制工具例外。Error 是用户要求暂不展开，并非上游实际删除。

覆盖检查发现 TODO／持久 Task 的区别、spawn 结束回合是提示约定、worktree 的后台使用检查及 Shell 生命周期在本章可更明确，已补充正文。保留阶段聚焦与旧章节来源，不重复全部内部代码；修正文案“主动态”为“主动”。

## S15.1 的最终分工：内容专题继续独立

用户指出主章已经覆盖运行时组装，同时认为原 System Prompt 笔记作为“有哪些内容”的专题仍清楚。采用分工：S15 解释如何运行与组装，S15.1 解释组成与用途；保留独立导航，不把它降成仅有历史稿的页面。

S15.1 更名为“System Prompt：模型需要哪些指令与背景”，按本地七类固定规则、五类动态背景和三份请求输入分类。移除重复的 update_context／assemble_system_prompt／主循环代码，只给 PROMPT_SECTIONS 的内容摘录与字段示意，并链接主章真实函数。原组成流程图改成内容来源图；Skills 图说明本地目录在 SYSTEM、正文在 messages 的边界，不再标作旧原型扩展。

旧全文保存为 static/examples/s15-repo/system-prompt-legacy.md，正文附录只保留简短说明与下载链接。保留旧 s15-local-assembly fragment 作为入口别名；主章卡片、交叉链接和项目总览同步更新名称与职责。新内容摘录通过源字典值 AST 核对。

原来的组装／Skills 两张图也分别冻结到静态历史资源。重整后 Hugo 构建、导航与源字典内容摘录核对、两张内容图路由检查通过；390／1180／1600 三种宽度的浏览器检查确认标题、目录、图中文字、完整图例、旧 fragment、ID 唯一与窄屏布局。本地父页、专题及历史稿／两张历史图均已返回 200。
