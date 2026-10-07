# S16 Workflow Runtime：编排、同步等待与单步续跑

按用户已确定的博客体例继续 S16，以本地 ce8f9f186058939da54c9d6fead78dfb5d0fd6c3 的 code.py／README.zh.md／上游图为依据。保留 S15 的错误恢复暂不展开范围；本章解释自身结构校验和 failed 任务状态。

S16 默认 CLI 实际装载 S15，包装其 assemble_tool_pool，追加 Workflow schema 与 run_workflow_sync；无 MCP 时变为 27 schema／26 普通 handlers，compact 特判不变。模型提供名称、args、可选 run ID，宿主 registry 提供可信 meta 与 script_fn。当前没有把 WORKFLOWS 目录自动提供给模型，SYSTEM 的静态工具说明也没追加 Workflow；入口由 tools schema 可见。

一次 Workflow 工具调用等待整套脚本结束。async_launched 是调用期间的本地事件，不是已向父循环先回启动结果。phase／agent／log 主要打印并维护 progress，最终持久化、task_notification 后一次返回 launched／result／task。原 PostToolUse 在同步 handler 返回后运行，workflow 事件不进 S15 后台通知／Lead 邮箱。

图 1 直接复用 S15，几何和路由不变，只标记真实扩展的三个工具池接口。图 2 向下新增四个 runtime 接口，1200×1420，主结果回线移到新增模块下方；已有模块位置不变。图 3 挂真实内部方法，区分 registry 运行、脚本、单步缓存、runner／schema、资源与收尾，类名与角色标明 owner。完整上游图原样保存为折叠对照，许可随资源保留。

parallel 等齐输入的一组协程结果；pipeline 对每个 item 顺序执行 stages，不同 item 可同时在不同阶段，最后才等全部返回。结果列表对应输入顺序，gather 的异常传播不保证自动取消其他 awaitable。本地单步真实 runner 只用传入文本并请求一个回答，没有 tools；注册 Python 脚本可信但不是沙箱。

journal 使用 prompt／schema／label 等内容产生稳定 key，恢复时重新走脚本，每步命中复用，未命中运行。原 args 不一致拒绝；没有 Python 执行现场恢复或独立依赖失效图。key 不含模型或代码版本，截为十位十进制，不宣称无碰撞。新 run 排他预留 ID、整次执行持线程／文件锁，快照和输出原子替换，journal 逐条 flush。

schema 检查只支持小集合，integer 的检查也接受 float；不是 API 强制输出解码。预算在 runner 后记账，cache 也计 agent 上限；初次 runner 受并发信号量控制，JSON 修正调用在块外。因此不会把代码描述成严格的所有请求并发／费用预留器。样例汇总并排序 confirmed，未实现去重。

## Python 并发依据

沿用 fluent-python-kb:check-fluent-python-first 的语言机制核对，并核对 [Python 3.12 gather 文档](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.gather)。

### 书上怎么说

书中展示将需要限制并发的 await 操作放在 semaphore 的异步上下文里。依据 A。

### 我的判断（本书未覆盖）

本仓库的 semaphore 只包住初次 runner 调用，输出纠正调用在外。这个限制范围依据本地代码，而非把书的示例直接套成整个 runtime 的保证；父同步工具的等待边界则依据 run_workflow_sync 的 asyncio.run 和主分发。

### 依据

A：Fluent Python, 2nd Edition，第 21 章，Throttling Requests with a Semaphore／21.7.2 使用信号量限制请求。

- 英文：corpus/en/ch21.md:483–606，anchor throttling-requests-with-a-semaphore。
- 中文：corpus/zh/ch21.md:445–571，同一 anchor。
- 镜像根目录：/home/fredkeira/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local。
- 版本：本书基于 Python 3.10；当前环境 Python 3.12.3。
- 原文代码：`async with semaphore:`，内部执行 `image = await get_flag(client, base_url, cc)`。
- 对照代码：`async with semaphore:`，内部执行 `image = await get_flag(client, base_url, cc)`。

两侧区间与 anchor 已按 section map 核对，示例代码在两侧正文逐字出现。

## 验证与环境边界

Hugo 与项目导航通过；总图／核心图路径不穿框或共线重合，源码 AST 核对包括 async 方法，类方法摘录只规范化多行 docstring 因取消类缩进产生的空白差异。代码逻辑和其他字符串必须一致。原图资源逐字一致；浏览器验证 S15 回顾隔离、可点击内部方法、悬停缓存关系、完整调用而非异步唤醒路径、键盘、函数标签边界、ID 与窄屏。

普通沙箱下内部并发测试超时，解除该执行限制后，教学仓库 16 项 workflow 测试直接通过。唯一的真实 S15 宿主装载测试因缺少 anthropic SDK 无法直接执行；采用明确禁止 API 请求的 SDK／dotenv 替身单独验证通过，未安装依赖或调用真实模型。博客额外测试用 /tmp 和 MockAgentRunner 核验单次最终回传、同参数续跑全部命中与不一致 args 不覆盖成功产物。

## 图 3 的悬停连线预览

用户要求 S16 图 3 同样支持悬停高亮。核心 figure 通过 trace=true 显式启用，与总图的选择状态分离。按 SVG 中 data-from／data-to／data-kind 查直接关系，用整块节点坐标命中，覆盖函数文字和空白；相关线加粗，其他线淡化，节点颜色与几何不变。引用关系补方向头，选中头固定为 12px。

鼠标移开、画布滚动、窗口滚动／缩放恢复；触摸滚动不切换预览。键盘聚焦函数名能看关系，点击或 Enter／Space 在原源码阅读动作前清除临时状态，避免副本带入悬停。详情中的图 3 副本重新绑定自己的预览，引用 ID 继续按现有规则独立命名。

先添加真实浏览器用例，确认原实现因缺少 core hover 失败，再实现；桌面、手机、宽屏检查覆盖可见线宽／淡化、移开恢复、引用、箭头大小、颜色／坐标与页面滚动稳定、触摸忽略、焦点与原代码点击。

共享脚本回归：仓库 60 项 unittest 全部通过，另加入详情副本独立悬停后，S16 三种宽度再次通过。Hugo、导航和所有图形路由检查通过，本地预览已加载新 fingerprint；图 1 与其他未启用章节保持原行为。环境没有 node 命令，JavaScript 由 Hugo minifier 构建并通过真实浏览器执行验证。
