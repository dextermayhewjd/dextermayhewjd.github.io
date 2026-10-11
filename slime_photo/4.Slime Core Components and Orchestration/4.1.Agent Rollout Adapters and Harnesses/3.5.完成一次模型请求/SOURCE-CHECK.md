# 3.5 完成一次模型请求：源码与材料校验

本文件对应已采用正文中的 C01–C09。用户确认后，正式页与预览共用同一份正文；原材料仍保留。

## 固定依据

- 已确认并持续使用的仓库：`/home/fredkeira/projects/slime`；核心包为其中的 `slime/`。
- 本轮阅读快照：`22a89f96835969a47055a659c588f46151f8b07a`。
- 原材料快照：`8c17b676cb57af1d17ee4402e91e9209af84b60b`。本章四个相关文件逐字一致，工作区中相关文件也未改动。
- 本轮只做静态核对及隔离的函数／流程检查；未运行真实 tokenizer 解码、SGLang、外部 CLI 或网络服务。
- 原示例的 218 个输入 token、5 个输出 token 及概率仍沿用构造生成结果；原材料记录的 tokenizer 解码结果不冒充本轮重新计算。
- 定稿时官方 main 的查询结果与差异另见同目录 `upstream-check.json`；本轮不更新源码仓库。

## C01

**核对事实：** 共享流程先解码、解析、构造Reply，等待响应函数后记录轨迹，最后返回响应。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 共享处理器中的调用 | `slime/agent/adapters/common.py:344` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L344-L393) |

**状态：** 已读取调用与定义；模型、网络及外部工具未运行。

## C02

**核对事实：** 本章沿用turn、输入历史与请求；sid标识会话而非某一次请求。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 会话与输入准备 | `slime/agent/adapters/common.py:325` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L325-L344) |

**状态：** 已读取调用与定义；模型、网络及外部工具未运行。

## C03

**核对事实：** 保留特殊token进行解码；空输出时使用空字符串。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 解码调用 | `slime/agent/adapters/common.py:346` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L346-L346) |

**状态：** 已读取调用与定义；模型、网络及外部工具未运行。

## C04

**核对事实：** 主解析器返回结构化结果，工具调用识别后交给后续协议构造，不在这里执行工具。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 解析调用 | `slime/agent/adapters/common.py:347` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L347-L352) |
| 主解析器 | `slime/agent/parsing.py:25` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/parsing.py#L25-L56) |
| 工具与XML回退解析 | `slime/agent/parsing.py:59` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/parsing.py#L59-L114) |
| 解析结果字段 | `slime/agent/parsing.py:15` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/parsing.py#L15-L22) |

**状态：** 已读取调用与定义；模型、网络及外部工具未运行。

## C05

**核对事实：** Anthropic适配器构造Reply，wire供响应函数使用，manager_message供轨迹使用。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 共享调用 | `slime/agent/adapters/common.py:353` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L353-L354) |
| Reply数据合同 | `slime/agent/adapters/common.py:45` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L45-L55) |
| Anthropic协议适配入口 | `slime/agent/adapters/anthropic.py:63` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/anthropic.py#L63-L69) |
| 构造协议块和助手消息 | `slime/agent/adapters/anthropic.py:147` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/anthropic.py#L147-L186) |
| 冻结的生成记录 | `slime/agent/trajectory.py:28` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L28-L38) |

**状态：** 已读取调用与定义；模型、网络及外部工具未运行。

## C06

**核对事实：** 共享流程传入完整Reply；非流式分支构造JSON响应对象，流式分支在函数内部写事件。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 响应方式和调用 | `slime/agent/adapters/common.py:356` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L356-L374) |
| Anthropic响应入口 | `slime/agent/adapters/anthropic.py:71` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/anthropic.py#L71-L75) |
| 非流式协议字典 | `slime/agent/adapters/anthropic.py:198` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/anthropic.py#L198-L208) |
| 流式响应发送 | `slime/agent/adapters/anthropic.py:211` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/anthropic.py#L211-L274) |

**状态：** 已读取调用与定义；模型、网络及外部工具未运行。

## C07

**核对事实：** record_turn返回None，副作用是把输入历史和当前生成记录保存到会话树。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 可选回调与轨迹调用 | `slime/agent/adapters/common.py:376` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L376-L390) |
| 轨迹记录实现 | `slime/agent/trajectory.py:283` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L283-L305) |
| 挂载历史与本轮输出 | `slime/agent/trajectory.py:428` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L428-L454) |

**状态：** 已读取调用与定义；模型、网络及外部工具未运行。

## C08

**核对事实：** 返回先前构造的response；finally移除当前任务，但不销毁会话轨迹。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 返回与finally | `slime/agent/adapters/common.py:384` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L384-L393) |

**状态：** 已读取调用与定义；模型、网络及外部工具未运行。

## C09

**核对事实：** 响应函数断连或取消时不记录本轮，但finally仍移除任务。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 响应失败的处理 | `slime/agent/adapters/common.py:359` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L359-L374) |
| 最终清理 | `slime/agent/adapters/common.py:392` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L392-L393) |

**状态：** 已读取调用与定义；模型、网络及外部工具未运行。

## 关键解释边界

- `_respond()` 接收完整 Reply，Anthropic 实现在内部解包 wire。非流式分支构造 JSON 响应对象；流式分支才在函数内 prepare/write。两者都不能直接推出客户端已完成接收。
- 当前共享主线读取 reply.wire 和 reply.manager_message，没有读取 reply.finish_reason。轨迹的生成结束原因来自 turn。
- dataclasses.replace 新建记录，未深复制列表；record_turn 返回 None，结果保存在会话树。
- 输出中的 `<|im_end|>` 保留是这个固定示例在未配置专用解析器时的实际结果，不在讲解中手工删除。
- 一次请求完成、Agent 任务结束、会话轨迹导出是不同阶段。

## 图与示例

原 flow.svg、示例.json、README.md 和离线 index.html 均保持原样；保留哈希与正式入口变化记录在 adoption-manifest.json。正式页复用原图。

## 验证记录

- 从固定本地源码提取函数/类 AST 进行隔离验证：普通与 XML 工具解析、Reply、非流式协议 body、轨迹树均与原示例一致。
- HTTP 工厂、生成返回和 tokenizer 用显式替身；非流式路径没有 prepare/write，流式路径在示例中执行 prepare 和事件写入。两者退出后轨迹保留、当前任务不再在途。
- 15 段 JSON 与原材料值完全一致；8 段 Python 语法检查通过。
- 12 项章节测试通过，包括候选不进入生产输出、原页面/图/示例哈希保留、源码折叠与资源链接。
- 浏览器检查通过：原图一致、9 个源码组默认折叠、键盘可展开、资源返回 200、窄屏无页面横向溢出。

详细结果见同目录 `validation.json`。这些验证不包括真实模型、tokenizer 解码、SGLang 专用解析器或网络请求。


## 正式页采用验证

用户确认后，正式 3.5 与已采用预览共同读取本目录 reading.md。侧栏入口、9 个默认收起的源码组、键盘展开、资源链接与 Pre-4 链接均已检查；原讲解保留，窄屏无页面横向溢出。12 项章节检查通过。
