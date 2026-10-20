# 04 · Step 1 的问题与澄清

## 从启动到请求入口

前一步已展示 `generate` 的七个核心环节；助手随后推荐从 `BaseHarness.run` 进入。用户明确把当前问题收敛为：

> 好的那么现在是否应该拆解一下这里的这个harness_cCLS().run了呢
> 但是这里的run 感觉内部细分就可以拆开成为非常多个步骤？
> 但是目前的问题是
>
> 这里是怎么从harness_cls().run到这里的baseAdapter._run_turn的呢？

本步据此只追踪启动到 HTTP 处理入口，不把所有内部调用各建为一个步骤。

助手核对当前固定源码：`HARNESS_CLS` 与 Adapter 成对选择；默认分支为 Claude Code / Anthropic。`BaseHarness.run` 委派具体 `launch_and_wait`；Claude Code 的启动环境带有 Adapter 地址；`AnthropicAdapter._register_routes` 将 `POST /v1/messages` 绑定到 `self._run_turn`。实现由 `BaseAdapter` 提供。

解释的关键关系是：Harness 启动外部 CLI 并等待，CLI 在此期间通过 HTTP 发出模型请求，Adapter 的路由调用 `_run_turn`。一次模型请求结束后可继续下一轮；CLI 整体结束后 `run` 才返回退出码，外层继续收集 diff。

连贯讲解与局部导航统一保存在[任务 walkthrough 的补充段落](../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#harness-to-adapter)，静态证据见[本次源码核对](../../../../../slime_photo/code-reading/chapters/01-task-execution/SOURCE-CHECK.md)。没有运行 CLI、沙箱或模型服务。

当前尚无用户对这项连接的复述或修正。后续按实际反馈判断先澄清地址与路由，还是继续进入一次请求处理；不预填用户已经理解。

## 后续反馈：详略控制仍不明白

用户明确表示仍不理解从什么方向读，以及阅读链路的详略怎样控制。本轮停在原有连接问题，先将各处代码区分为辨认职责、追踪关键连接和后续问题；没有据此进入 `_translate` 的新一轮细读。完整表述与方法讨论见[讨论记录](../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#用户仍不清楚阅读方向与详略控制)。

用户继续指出此前设计主要给出函数作用，追问如何一步步读清实现。助手补充了“展开函数主体 → 追踪具体中间值 → 展开一个子调用 → 返回补全模型”的安排，示例为 `run` 内的上下文构造及地址传递。完整讨论见[从作用走到实现](../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#从函数作用继续走到实现)；仍未记录用户已经掌握。

## 多个函数的连接仍然不清楚

用户明确指出现有模块缺少对多函数调用关系的处理，自己仍不清楚这些函数怎样连接。本轮核对了两个具体对象的方法：`ClaudeCodeHarness` 的 `run` 来自父类、启动方法由自身实现；`AnthropicAdapter` 的请求处理器来自父类、转换方法由自身实现。另行区分普通函数调用与 CLI 发起的 HTTP 请求。

对应表格补入[调用位置与实际实现](../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#call-sites-and-implementations)。它是助手据源码给出的关系说明，不能据此写成用户已经理解了继承或完整调用链。

## HTTP 请求为什么会发生，先后顺序仍不清楚

用户进一步指出：

> 主要的问题是这里是怎么就突然通过http 来吧信息post出去的呢？ 这里的运行顺序是什么我还是没有理解

这次卡点在“启动外部程序”与“外部程序发送请求”之间。先前的调用树只标了 HTTP 箭头，没有说明设置环境变量不发送请求、执行 CLI 命令才启动另一个程序，以及 `add_post` 属于接收端注册。

助手据当前源码核对：Adapter 的路由先注册、服务先启动；Harness 准备命令与环境，经沙箱执行接口启动 Claude CLI 并等待；CLI 在此期间发出模型请求，Adapter 收到后才调用 `_run_turn`。Claude Code 官方环境变量与网关协议文档用于核对外部客户端行为；CLI 安装包中的具体发送函数及实际网络请求未检查或运行。

按时间排列的解释保存在[任务链路](../step-001-harness-to-adapter/05-task-flow.md#http-request-order)，同源内容同步到[教学正文](../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#http-request-order)。此处记录疑问和助手澄清，尚无用户对这次解释的后续反馈。

<a id="run-execution-still-unclear"></a>

## 再次反馈：仍然跟不上 run 如何往下执行

用户随后明确表示：

> 重新讲一下这里吧 我感觉根本不清楚
> 我完全不能够理解这里是怎么从run走下去的
> 我觉得这里的流程极度的不清晰
> 我完全不能够理解每一步到底是怎么走的

这条反馈说明上一轮的时序表和调用树仍不足以帮助用户跟踪执行。它不表示用户已接受或掌握上面的解释，本步也没有推进到新的函数学习主题。

助手这次从 `BaseHarness.run` 的四项操作重新展开：准备运行用户、构造上下文、写配置、进入启动等待。每个子调用都交代返回位置；进入 `launch_and_wait` 后先解释命令和环境只是数据，再跟到 `run_agent`、`exec_and_wait` 的脚本启动与退出标记等待。

此次重点补充两个不同的完成时刻：后台启动命令返回时，Claude 进程已经开始运行；只有 Claude 整体退出、启动脚本写下退出码后，等待它的调用链才返回。CLI 与 Adapter 的 HTTP 请求发生在这段等待期间。`run` 的退出码与一轮模型请求的 HTTP 响应分别交回不同的调用方。

完整逐句讲解保存在[本步任务链路](../step-001-harness-to-adapter/05-task-flow.md#run-execution-order)，从同一来源同步到[教学正文](../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#run-execution-order)。依据是固定版本源码的静态核对和前轮已查阅的 CLI 接口文档；没有运行 CLI、沙箱或模型服务，也没有核对外部 CLI 的内部发送函数。

本条只保存用户的困难和助手本次解释，不预填解释之后的理解状态；函数记忆仍保留原有内容。

<a id="document-organization-feedback"></a>

## 文档结构反馈：逐句解释后仍然混乱

用户随后反馈：

> 我感觉这里的内容好乱
> 科技大厂程序员会如何写这里的文档呢？
> 这里的文档也太乱了根本看不懂

本轮转为审阅讲解的组织：现有主文重复讲同一条链，混合任务阶段与辅助实现；逐句增加信息尚未解决阅读困难。结构对照、公开工程写作依据和短版候选保存在[文档审阅讨论](../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#task-flow-document-review)。候选按启动、模型请求、退出返回组织，先辨认参与者，再在各阶段连接短代码。

本轮未替换正式 task-flow 或 Hugo 正文，未新增步骤或函数记忆。用户是否认可候选，以及是否理解运行关系，仍待其实际反馈。

<a id="source-location-and-return-feedback"></a>

## 流程还需明确具体实现、行号和嵌套后的返回位置

用户进一步指出：

> 这里还需要看到底是看哪一个harness的代码 是anthropic的harness还是common的
> 我觉得这里代码特别难读懂
> 我觉得这个图也需要具体的代码是在多少行吧
> 我总觉得这里缺了点东西
>
> 哪一段代码做了什么事情我觉得这里的flow就是没有讲清楚让我觉得很痛苦
> 特别是一个链条调用了太多内容 一层一层嵌套的时候

助手据固定版本重新核对选型、类定义和方法范围：本篇使用 `ClaudeCodeHarness`，其 `run` 在 `harness/common.py:81–104`，具体启动方法在 `harness/claude_code.py:57–71`；`AnthropicAdapter` 在 `adapters/anthropic.py:49` 登记路由，处理器实现在另一个文件 `adapters/common.py:318`。

此次将原有调用导航替换为带文件、阅读范围和调用行的导航，并在 task-flow 中放到逐句说明之前。第一处明确跳转是 `harness/common.py:104 → harness/claude_code.py:57`；进一步进入子调用时保留当前等待行，返回时按退出码的实际接收与返回位置回到调用方。运行用户、上下文和配置的短调用另列完成后的继续行。HTTP 边界继续标明，外部 CLI 的内部发送函数没有伪造行号。

同源导航见[本步 task-flow](../step-001-harness-to-adapter/05-task-flow.md#source-jump-map)和[教学正文](../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#source-jump-map)。既有逐句解释保留为可展开回查；这次未修改函数记忆，也未将文档补齐写成用户已经理解。

<a id="http-service-and-round-trip"></a>

## 调用链得到确认，接着解释 HTTP 服务与信息往返

用户明确反馈并提出下一问：

> 好的这么函数调用的链条没有问题了
> 现在的问题是
> 为什么这里有http的服务
> 以及这里的http的服务是怎么做到把信息传来传去的

这次明确确认的是前一轮函数调用链；不能扩展为用户已经掌握 HTTP、线程或各函数内部实现。本轮沿同一个 Step 1 继续解释服务与通信，不重新讲整条 Harness 调用链。

助手核对：`generate.py:150–171` 创建 Adapter、启动其 Web 应用并形成访问地址；`aiohttp_threaded.py:69–72` 用 `TCPSite` 开始监听。地址传入 Claude 的环境配置后，外部 CLI 发出模型请求；aiohttp 按已注册的路由进入 `_run_turn`，第 325 行读取 JSON。模型处理后，第 363 行调用 `_respond`；`anthropic.py:71–75` 分为 JSON 和流式响应，响应回到发起这次请求的客户端。

解释重点是两端独立程序通过请求与响应交换数据，HTTP 框架负责监听、解析、分派与发送；Python 处理器负责请求内容与业务结果。用户关注的往返不要求 Adapter 再向 Claude 的另一个服务地址发送 POST。流式响应也是同次请求的响应，不能混作多次模型调用。

正文与源码位置保存在[HTTP 往返讲解](../step-001-harness-to-adapter/05-task-flow.md#http-round-trip)，同源同步到[教学正文](../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#http-round-trip)。其中请求 JSON 是教学构造的字段节选，没有运行 CLI、沙箱或模型服务。HTTP 这部分是否理解，等待用户后续实际反馈；函数记忆未新增或改写。

<a id="core-first-and-handoff-depth"></a>

## 整体讲解仍不清楚，回到重要函数与展开深度的分工

用户继续表示链条和文档仍不清晰，询问怎样修改，以及之前“先看重要函数”的方法是否适用。完整原话、对照和短版候选保存在[本轮文档与方法讨论](../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#core-first-and-handoff-depth)。

助手建议保留核心函数优先的方法，按当前问题判断哪些代码必须展开：HTTP 地址和路由虽然属于配置，却是此处的必要连接证据。已认可的启动调用图保留作回查；当前正文从运行中的 CLI 接续，只跟随一次请求到 `_run_turn` 再返回 CLI。区分按问题回查代码的阅读顺序与先准备、后请求的实际执行顺序。

本轮只保存结构对照与候选，未改写已采用正文、函数记忆或 scope，也未新增步骤。前一轮对函数调用链的确认仍保留；HTTP 机制及候选结构是否清楚，尚无用户后续反馈。验证限于静态源码、文档及现有预览，没有执行 CLI 或模型服务。
