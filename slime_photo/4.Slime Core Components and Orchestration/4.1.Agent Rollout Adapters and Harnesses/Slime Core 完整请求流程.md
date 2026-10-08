# Slime Core (BaseAdapter, TrajectoryManager) 完整请求流程

[返回架构图与源码文件对应](README.md) · [返回动作 2 最小心智模型](<2.Translate & Forward/README.md>)

这篇延伸阅读展开共享处理流程中的模型输入准备、生成、输出解析、响应、轨迹记录和会话结束。动作 2 的转换与交接先从其入口文档阅读。

图中的 Slime Core 包含 `BaseAdapter` 和 `TrajectoryManager`。`BaseAdapter._run_turn()` 组织一次请求的处理流程，`TrajectoryManager` 保存会话轨迹。下面从适配器返回转换结果的位置开始，按正常请求的实际执行顺序展开；其中生成请求属于后续动作 3。

源码位置均相对于 Slime 仓库根目录。表中的“定义位置”是函数开始的行号，“调用位置”是本流程执行该函数的行号。

## 1 接收消息和工具定义

**执行逻辑：** `BaseAdapter._run_turn()` 调用 `self._translate(body)`。当前对象是 `AnthropicAdapter`，因此执行其 `_translate()`，把消息和工具定义转换后返回。共享流程用两个变量接收返回值，动作 2 在这里完成数据交接。

| 函数名 | 定义位置 | 调用位置 |
| --- | --- | --- |
| `AnthropicAdapter._translate()` | `slime/agent/adapters/anthropic.py:58` | `slime/agent/adapters/common.py:341` |

**输入 → 输出：** `body` → `translated` 和 `tools_schema`。

## 2 将消息编码为模型输入 Token

**执行逻辑：** `_render_token_ids()` 将规范化消息和工具定义传给当前模型的聊天模板，设置 `tokenize=True`、`add_generation_prompt=True`，最后整理为 Token ID 列表。

| 函数名 | 定义位置 | 调用位置 |
| --- | --- | --- |
| `_render_token_ids()` | `slime/agent/adapters/common.py:58` | `slime/agent/adapters/common.py:342` |

`tokenizer.apply_chat_template()` 的调用位于 `slime/agent/adapters/common.py:66`，其函数实现由外部 tokenizer 提供。

**输入 → 输出：** `translated`、`tools_schema` → `prompt_ids`。

## 3 整理本轮采样参数

**执行逻辑：** 共享流程进入 `call_sglang_generate()` 后，先调用 `_sampling_params()`。它合并默认参数和会话参数，再读取请求中的生成长度、温度及停止条件。Anthropic 请求的 `max_tokens` 转换为 `max_new_tokens` 的限制，`stop_sequences` 转换为 `stop`。

| 函数名 | 定义位置 | 调用位置 |
| --- | --- | --- |
| `_sampling_params()` | `slime/agent/adapters/common.py:416` | `slime/agent/adapters/common.py:455` |

**输入 → 输出：** 当前 `Session`、原始 `body`、适配器的参数键配置 → 采样参数字典 `sp`。

## 4 请求 SGLang 并整理生成记录

**执行逻辑：** `call_sglang_generate()` 检查上下文预算，再向 SGLang 的 `/generate` 发送 `input_ids`、`sampling_params`、请求标识 `rid` 和 `return_logprob=True`。正常响应返回后，从 `meta_info` 中提取输出 Token、对应的 log probability 和结束原因，构造 `TurnRecord`。

| 函数名 | 定义位置 | 调用位置 |
| --- | --- | --- |
| `call_sglang_generate()` | `slime/agent/adapters/common.py:442` | `slime/agent/adapters/common.py:344` |

| 具体执行点 | 源码位置 |
| --- | --- |
| 检查上下文预算 | `slime/agent/adapters/common.py:457` |
| 发出 POST 请求 | `slime/agent/adapters/common.py:475` |
| 读取响应 JSON | `slime/agent/adapters/common.py:496` |
| 提取 Token 与 log probability | `slime/agent/adapters/common.py:497` |
| 构造 `TurnRecord` | `slime/agent/adapters/common.py:509` |

上下文预算已耗尽时，函数在 `slime/agent/adapters/common.py:467` 直接返回结束原因为 `length` 的空输出记录。

**输入 → 输出：** `prompt_ids`、会话状态、请求参数 → `turn`，包含 `prompt_ids`、`output_ids`、`output_log_probs` 和 `finish_reason`。

这部分对应动作 3 **Slime Core → SGLang Backend**。

## 5 将生成 Token 解码为文本

**执行逻辑：** `BaseAdapter._run_turn()` 使用 `tokenizer.decode()` 解码 `turn.output_ids`，设置 `skip_special_tokens=False`。没有输出 Token 时，直接得到空字符串。

| 函数名 | 所在处理函数 | 调用位置 |
| --- | --- | --- |
| `tokenizer.decode()` | `BaseAdapter._run_turn()`，定义于 `slime/agent/adapters/common.py:318` | `slime/agent/adapters/common.py:346` |

**输入 → 输出：** `turn.output_ids` → `raw_output`。`tokenizer.decode()` 的实现由外部 tokenizer 提供。

## 6 分离正文 推理内容和工具调用

**执行逻辑：** `parse_model_output()` 根据配置解析推理内容，再调用 `parse_tool_uses()` 提取工具调用。配置了工具解析器且存在工具定义时，使用 SGLang 工具解析器；没有提取到工具调用且存在工具定义时，尝试 XML 格式的回退解析。

| 函数名 | 定义位置 | 调用位置 |
| --- | --- | --- |
| `parse_model_output()` | `slime/agent/parsing.py:25` | `slime/agent/adapters/common.py:347` |
| `parse_tool_uses()` | `slime/agent/parsing.py:59` | `slime/agent/parsing.py:50` |
| `parse_xml_tool_uses()` | `slime/agent/parsing.py:93` | `slime/agent/parsing.py:88` |

**输入 → 输出：** `raw_output`、`tools_schema`、解析器配置 → `ParsedModelOutput`，包含 `reasoning`、`text`、`tool_uses` 和 `ill_formed`。

## 7 构造协议响应内容和轨迹消息

**执行逻辑：** 共享流程调用 `self._build_reply()`，进入 `AnthropicAdapter._build_reply()`。它通过 `_build_reply_parts()` 构造 Anthropic 的 `thinking`、`text`、`tool_use` 内容块，同时构造给轨迹管理器使用的规范化 `manager_message`。

| 函数名 | 定义位置 | 调用位置 |
| --- | --- | --- |
| `AnthropicAdapter._build_reply()` | `slime/agent/adapters/anthropic.py:63` | `slime/agent/adapters/common.py:353` |
| `_build_reply_parts()` | `slime/agent/adapters/anthropic.py:147` | `slime/agent/adapters/anthropic.py:64` |
| `tool_call_dict()` | `slime/agent/adapters/common.py:110` | `slime/agent/adapters/anthropic.py:168` |
| `manager_finish_reason()` | `slime/agent/adapters/common.py:121` | `slime/agent/adapters/anthropic.py:67` |

**输入 → 输出：** `parsed`、生成结束原因 → `Reply`，包含协议内容 `wire`、轨迹消息 `manager_message` 和轨迹结束原因 `finish_reason`。

随后，`slime/agent/adapters/common.py:354` 将解析得到的 `ill_formed` 标记写入新的 `turn` 记录。

## 8 构造或发送客户端响应

**执行逻辑：** 共享流程计算输入和输出 Token 数量，并根据请求中的 `stream` 或 `Accept` 请求头选择响应方式，再调用 `AnthropicAdapter._respond()`。

| 函数名 | 定义位置 | 调用位置 |
| --- | --- | --- |
| `AnthropicAdapter._respond()` | `slime/agent/adapters/anthropic.py:71` | `slime/agent/adapters/common.py:363` |
| `_render_stream()` | `slime/agent/adapters/anthropic.py:211` | `slime/agent/adapters/anthropic.py:74` |
| `_render_response()` | `slime/agent/adapters/anthropic.py:198` | `slime/agent/adapters/anthropic.py:75` |

| 分支 | 具体处理 |
| --- | --- |
| 流式响应 | `_render_stream()` 创建 `web.StreamResponse`，写入 Anthropic Messages 格式的 SSE 事件 |
| 非流式响应 | `_render_response()` 生成协议响应字典，`_respond()` 使用 `web.json_response()` 构造响应对象 |

选择响应方式的执行点位于 `slime/agent/adapters/common.py:357`。

**输入 → 输出：** `Reply.wire`、Token 数量、响应方式 → `response` 对象。

## 9 执行可选调试回调

**执行逻辑：** `_run_debug_callback()` 将会话、输入消息、工具定义、轨迹消息和生成记录传给配置的调试回调。没有配置回调时直接返回。

| 函数名 | 定义位置 | 调用位置 |
| --- | --- | --- |
| `BaseAdapter._run_debug_callback()` | `slime/agent/adapters/common.py:308` | `slime/agent/adapters/common.py:376` |

**输入 → 输出：** `sid`、`translated`、`tools_schema`、`reply.manager_message`、`turn` → 可选调试输出。

## 10 将本轮结果接入会话轨迹树

**执行逻辑：** 共享流程调用 `self.manager.record_turn()`。`TrajectoryManager` 根据 `sid` 取得或创建会话树，匹配已有历史、处理符合条件的助手消息重写、挂载剩余输入消息，再添加带生成记录的助手节点。

| 函数名 | 定义位置 | 调用位置 |
| --- | --- | --- |
| `TrajectoryManager.record_turn()` | `slime/agent/trajectory.py:283` | `slime/agent/adapters/common.py:384` |

`record_turn()` 内部按以下顺序执行：

| 顺序 | 函数名 | 执行逻辑 | 定义位置 | 调用位置 |
| --- | --- | --- | --- | --- |
| 1 | `_find_mount_point()` | 按消息角色和消息内容匹配已有路径，找到新消息的接入位置 | `slime/agent/trajectory.py:352` | `slime/agent/trajectory.py:302` |
| 2 | `_try_merge_assistant_rewrite()` | 阈值启用且当前输入为助手消息时，若唯一助手子节点是带生成记录的短叶节点，则合并客户端重写；否则保持原接入位置 | `slime/agent/trajectory.py:370` | `slime/agent/trajectory.py:303` |
| 3 | `_mount_prompt_messages()` | 将尚未匹配的输入消息逐个挂到树上 | `slime/agent/trajectory.py:428` | `slime/agent/trajectory.py:304` |
| 4 | `_attach_assistant_leaf()` | 创建本轮助手节点，保存 `response_message`、`turn`、元数据和轮次编号 | `slime/agent/trajectory.py:437` | `slime/agent/trajectory.py:305` |

**输入 → 输出：** `sid`、`prompt_messages=translated`、`response_message=reply.manager_message`、`turn`、元数据 → 更新会话轨迹树；`record_turn()` 返回 `None`。

源码先执行 `_respond()`，再执行调试回调和轨迹记录。这一步保存本轮轨迹，训练样本在会话结束阶段导出。

## 11 返回响应并清理本轮任务跟踪

**执行逻辑：** `BaseAdapter._run_turn()` 在轨迹记录完成后返回 `response`。其 `finally` 部分会在退出本轮处理时，把当前任务从 `self.inflight[sid]` 中移除。

| 函数名 | 定义位置 | 具体执行位置 |
| --- | --- | --- |
| `BaseAdapter._run_turn()` | `slime/agent/adapters/common.py:318` | 返回响应：`slime/agent/adapters/common.py:391`；移除任务：`slime/agent/adapters/common.py:393` |

**输入 → 输出：** 已构造的 `response` → HTTP 处理器返回值；当前任务退出进行中请求的跟踪集合。

## 会话结束阶段 导出训练样本

**执行逻辑：** 外层 rollout 在会话结束时调用 `BaseAdapter.finish_session()`。它先关闭会话并等待或取消进行中的请求，再调用 `TrajectoryManager.get_trajectory()` 将轨迹树的叶路径整理为 `Sample` 列表，附上奖励并移除该会话的轨迹状态。最后由适配器解码各样本的响应 Token，填充 `Sample.response`。

| 函数名 | 定义位置 | 调用位置 |
| --- | --- | --- |
| `BaseAdapter.finish_session()` | `slime/agent/adapters/common.py:245` | `examples/coding_agent_rl/generate.py:237` |
| `BaseAdapter.shutdown_session()` | `slime/agent/adapters/common.py:225` | `slime/agent/adapters/common.py:261` |
| `TrajectoryManager.get_trajectory()` | `slime/agent/trajectory.py:307` | `slime/agent/adapters/common.py:264` |

`get_trajectory()` 内部在 `slime/agent/trajectory.py:334` 调用 `_chain_to_samples()`，其定义位于 `slime/agent/trajectory.py:479`。适配器填充样本响应文本的执行点位于 `slime/agent/adapters/common.py:274`。

**输入 → 输出：** 完整会话轨迹、基础样本、奖励和元数据 → 可用于后续训练的 `Sample` 列表。

会话结束阶段由外层流程触发，不在每次 `_run_turn()` 中执行。
