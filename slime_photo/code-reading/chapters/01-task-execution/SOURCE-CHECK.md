# 启动到模型请求入口：本次增补的源码核对

本文件只覆盖 2026-10-20 增补的“从 Harness.run 到 _run_turn”段落。既有任务 walkthrough 其余部分继续保留原版本证据。

当前源码根目录：`/home/hongshi/projects/slime`；固定提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。以下均为静态阅读，没有运行 CLI、沙箱或模型服务。

| 编号 | 核对事实 | 调用处与定义处 |
| --- | --- | --- |
| C01 | 当前选择的 Harness 与 Adapter 配套；默认 Claude Code / Anthropic 分支 | `examples/coding_agent_rl/generate.py:43–51` |
| C02 | `generate` 调用 Harness；`BaseHarness.run` 组织上下文并委派具体启动等待 | `generate.py:205`；`slime/agent/harness/common.py:81–104` |
| C03 | 具体启动器把 Adapter 地址放入 CLI 环境，随后运行外部 Claude CLI | `slime/agent/harness/claude_code.py:57–73`；`harness/common.py:107–123` |
| C04 | Adapter 服务已创建并监听；`POST /v1/messages` 绑定 `_run_turn` | `generate.py:138–172`；`adapters/common.py:156–178`；`adapters/anthropic.py:38–50` |
| C05 | `_run_turn` 接收 HTTP 请求并读取 JSON，再进入一次模型请求处理 | `slime/agent/adapters/common.py:318–344` |
| C06 | `_translate(body)` 位于 `_run_turn` 内，请求内容经 `request.json()` 取得；具体 Anthropic 转换实现在子类中 | `slime/agent/adapters/common.py:325、341`；`adapters/anthropic.py:58–61` |
| C07 | `ClaudeCodeHarness` 未定义 `run`，继承 `BaseHarness.run`；定义了 `launch_and_wait` | `harness/claude_code.py:15、57`；`harness/common.py:81、104` |
| C08 | `AnthropicAdapter` 未定义 `_run_turn`，继承父类处理器；定义了 `_translate` | `adapters/anthropic.py:39、48、58`；`adapters/common.py:318、341` |
| C09 | CLI 来自安装包；本地启动方法准备命令和环境，交给沙箱执行 | `harness/claude_code.py:36–42、57–71`；`harness/common.py:107–122`；`sandbox.py:107–139` |
| C10 | 路由注册与服务启动在 CLI 执行前完成；Adapter 服务使用单独线程 | `adapters/common.py:175`；`generate.py:150–171、184、205` |
| C11 | `run` 顺序准备用户、构造上下文、写配置，随后等待启动方法；配置写入来自具体 Harness | `harness/common.py:97–104`；`harness/claude_code.py:44–55` |
| C12 | `run_agent` 准备输出目录后委派 `exec_and_wait`；后者写启动脚本、后台启动，再轮询退出标记 | `harness/common.py:107–122`；`sandbox.py:65–79、107–139` |
| C13 | 正常结束时，脚本在 Claude 命令退出后写退出码；等待逻辑取得退出码，经调用链返回后 `generate` 才收集 diff | `sandbox.py:112、139–145`；`harness/common.py:104、111–122`；`harness/claude_code.py:71`；`generate.py:205–213` |
| C14 | 源码导航的范围由定义与调用行共同核对；两个 `common.py` 分属 Harness 与 Adapter | `harness/common.py:81–104、107–122`；`harness/claude_code.py:44–55、57–71`；`adapters/anthropic.py:48–50`；`adapters/common.py:318、325、341`；`sandbox.py:65–79、82–145、390–399` |
| C15 | Web 应用先创建、注册路由，再交给独立线程运行；`TCPSite.start` 开始监听 | `adapters/common.py:159、175`；`adapters/anthropic.py:49`；`generate.py:161–170`；`aiohttp_threaded.py:69–72、87–88` |
| C16 | 对外访问主机与监听主机分别配置；对外地址传入 CLI 环境 | `generate.py:144–148、163–171、209`；`harness/claude_code.py:63` |
| C17 | 请求经 JSON 解析后进入业务处理；结果通过 JSON 或 SSE 响应交回客户端 | `adapters/common.py:325、344、357、363、391`；`adapters/anthropic.py:71–75、198–208、211–238` |

CLI 发起请求的内部实现不在这几处 Python 函数中；这里核对的是启动配置、服务路由和请求处理端的连接合同。

## 外部客户端与 HTTP 时序核对

针对“为什么突然 POST、运行顺序是什么”的追问，本轮补查 Claude Code 官方文档：

- [环境变量](https://code.claude.com/docs/en/env-vars)：`ANTHROPIC_BASE_URL` 改变 API 请求地址；赋值本身不是发送请求。
- [网关协议](https://code.claude.com/docs/en/llm-gateway-protocol#api-formats)：该变量对应 Anthropic Messages 格式，模型推理请求使用 `/v1/messages` 路径。
- [CLI 参数](https://code.claude.com/docs/en/cli-reference)：`-p` 是非交互运行入口。

文档查阅日期为 2026-10-20，用于核对协议边界；不据当前在线文档推断历史 CLI 安装包的内部函数名或完整请求字段。安装包的具体版本、发送函数和真实网络流量本轮未核对。教学时序是依据本地启动、路由代码和外部协议整理的正常路径，不是抓包或运行日志，也未枚举 CLI 可能发出的其他启动请求。

本轮“HTTP 服务与信息往返”另外核对了 aiohttp 的[服务端入门](https://docs.aiohttp.org/en/stable/web_quickstart.html#handler)与[服务端接口](https://docs.aiohttp.org/en/stable/web_reference.html#streamresponse)：处理器接收 `Request`、返回响应；JSON 与流式写入由框架负责对应的协议处理。查阅的 stable 页面标为 3.14.5，仅用于这些接口语义，不据此断言本地 Slime 实际安装的 aiohttp 版本。教学请求只展示构造的 `messages` 字段片段，不是完整请求或真实运行记录。

## Python 语言机制核对

书上怎么说：第 14 章的 `Leaf` 实例调用继承的 `pong` 时，示例输出显示对象仍是 `Leaf`，执行的方法来自 `A`。

- 版本：《Fluent Python》第 2 版（2022），基于 Python 3.10；本机 Python 3.12.3。
- 英文小节：`Multiple Inheritance and Method Resolution Order`，本地镜像 `corpus/en/ch14.md:232–418`，锚点 `multiple-inheritance-and-method-resolution-order`。
- 中文小节：`14.4 多重继承和方法解析顺序`，本地镜像 `corpus/zh/ch14.md:227–404`，相同锚点。
- 原文示例输出：`<instance of Leaf>.pong() in A`。
- 中文对照示例输出：`<instance of Leaf>.pong() in A`。

当前源码判断：两个具体类均未重定义上述入口方法，分别实现启动方法和转换方法。已用 AST 静态检查类的基类与方法定义；不把 `BaseHarness`、`BaseAdapter` 当作调用途中额外创建的对象。书中多重继承示例用来核对“实例类型与执行体位置分开”这一关系，本步不展开 MRO 算法，也未运行外部服务。
