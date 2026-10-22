# 启动到模型请求入口：本次增补的源码核对

本文件覆盖 2026-10-20 增补的“从 Harness.run 到 _run_turn”段落，以及 2026-10-21 增补的 `_run_turn` 逐段讲解。既有任务 walkthrough 其余部分继续保留原版本证据。

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

## 2026-10-21：一次模型请求的逐段处理

对应 [逐段讲解](walkthrough.md#run-turn-step-by-step)，固定提交仍为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。本次核对真实执行顺序和阶段输入输出，未运行 CLI、沙箱或模型；“你好。”为显式假设的模型生成结果。

| 编号 | 核对事实 | 调用处与定义处 |
| --- | --- | --- |
| RT1 | 请求 JSON、预处理、会话身份先于转换；Session 保存默认采样和上下文预算 | `adapters/common.py:34–42、325–338`；`adapters/anthropic.py:52–56、192–195` |
| RT2 | 转换返回两项；空工具列表返回 `None`，系统指令进入消息列表 | `adapters/common.py:341`；`adapters/anthropic.py:58–61、81–85、123–126` |
| RT3 | 消息和工具定义一同交给 tokenizer 模板，结果为 token ID 列表 | `adapters/common.py:58–74、342` |
| RT4 | 生成调用接收 prompt、Session、body、Adapter 和 sid，返回 TurnRecord | `adapters/common.py:344、442` 起的 `call_sglang_generate` |
| RT5 | 先解码，再解析，再构造 Reply；协议内容与轨迹消息分开 | `adapters/common.py:346–357`；`adapters/anthropic.py:63–69、147–185` |
| RT6 | `_respond` 正常返回后才进入 `record_turn`；非流式只是构造响应对象，流式在钩子里写出 SSE | `adapters/common.py:363–391`；`adapters/anthropic.py:71–75、198–238` |
| RT7 | 记录输入是 sid、turn、转换后消息与 manager_message；finally 移除当前请求登记 | `adapters/common.py:384–393` |

## 2026-10-21：`_render_token_ids` 的参数与返回值

对应[模板编码讲解](walkthrough.md#render-token-ids)，固定源码版本仍为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。

| 编号 | 结论 | 证据 |
| --- | --- | --- |
| RT8 | 调用处将 `translated / tok / tools_schema` 分别传给 `messages / tokenizer / tools`，`prompt_ids` 接收返回值 | `adapters/common.py:58–71、341–344` |
| RT9 | `apply_chat_template` 使用 `tokenize=True`；返回后取 `input_ids` 或直接使用序列，再转为列表 | `adapters/common.py:66–73` |
| RT10 | 测试替身按消息角色和文本产生 ID，并按 `add_generation_prompt` 追加助手开头；只记录工具定义，不编码它 | `tests/test_agent/_fakes.py:41–113` |

局部运行：从原文件按 AST 提取 `_render_token_ids`、`FakeTokenizer` 和其所需常量，执行[函数卡片](../../../../00-repo-reading/repositories/slime/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/_render_token_ids.md)中的两条消息及一个工具 schema，返回 `[1, 100, 5, 2, 101, 102, 5, 3]`；同时核对 `tok.rendered == [(translated, tools_schema)]`。此运行验证列表返回及参数交接，不验证真实模型的模板、工具编码、HTTP 或生成。字典类返回分支仅作静态核对。

`tokenize` 与助手前缀的语义参照 [Hugging Face 文档](https://huggingface.co/docs/transformers/chat_templating#add_generation_prompt)，工具参数参照[官方工具使用说明](https://huggingface.co/docs/transformers/chat_extras#passing-tools)；查阅日期为 2026-10-21。当前未固定具体运行时 Transformers 版本或模型模板，不据此宣称真实模板输出已经验证。

同日追问补充：[套模板与编码的区别](walkthrough.md#chat-template-two-actions)。`tokenize=False` 的观察用法来自上述官方文档；Slime 固定源码仍使用 `True`。正文方括号示意用于说明角色、边界和工具信息的组织，不是具体模板的实测输出，也没有执行真实 tokenizer。用户的“按照 tokenizer 内部的训练方式”是原话，助手将其澄清为“按模型所需的对话格式组织输入”；不将原话作为技术证据。

特别核对：`_run_turn` 的 docstring 写有 `append -> respond`，实现却先在第 363 行调用 `_respond`，再于第 384 行记录轨迹；讲解以实际代码为准。第 359 行的 flush 注释也不能推导出非流式客户端已确认收到数据：非流式钩子返回的是 `web.json_response` 构造的响应对象。

## 2026-10-21：响应编号怎样进入 `TurnRecord`

对应[单字段讲解](walkthrough.md#call-sglang-output-ids)，源码仍绑定 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。

| 编号 | 结论 | 证据 |
| --- | --- | --- |
| RT11 | HTTP 响应解析为 `data`，从 `meta_info.output_token_logprobs` 各项的第二个值取得 `output_ids` | `adapters/common.py:496–499` |
| RT12 | 函数在本地构造 `TurnRecord`，将提取的编号放进 `output_ids`；调用方随后读取 `turn.output_ids` 解码 | `adapters/common.py:509–514、344–346`；`trajectory.py:28–38` |
| RT13 | 教学响应采用仓库测试服务的字段形状，数值 `[-0.2, 701]`、`[-0.5, 702]` 是构造值 | `tests/test_agent/_fakes.py:156–168` |

局部例子用 Python 3.12.3 执行，三条提取语句与固定源码一致，得到 `[701, 702]`。本次只验证字段提取和静态数据交接；没有运行真实 tokenizer、HTTP 或模型，也不为这些编号指定解码文本。

## 2026-10-21：内部执行地图与第一段生成设置

对应[函数内部执行地图](walkthrough.md#call-sglang-internal-flow)，源码仍绑定 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。六段边界来自 `adapters/common.py:454–455、457–468、470–473、475–496、497–501、509–514`；失败支线来自 `:485–495、502–507`。`remaining_context <= 0` 的提前返回保留在第二段，不能当作普通日志省略。

第一段调用 `_sampling_params:416–439`，Anthropic 的参数名来自 `adapters/anthropic.py:45–46`。局部核对使用原函数、原 README 场景请求及构造的设置：会话默认 `max_new_tokens=256, temperature=0.7`，请求增加 `max_tokens=128, temperature=0.2`；结果为 `max_new_tokens=128, temperature=0.2`，其余三项固定设置仍保留。后续上下文检查可能进一步修改生成长度，本次未运行该段或任何网络请求。

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
