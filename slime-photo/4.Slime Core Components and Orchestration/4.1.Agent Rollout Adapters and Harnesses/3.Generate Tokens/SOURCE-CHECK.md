# Generate Tokens：源码出处与校验清单

本章已采用用户确认的第三版阅读稿。下面保留定稿过程中已核对的源码、图、示例与验证记录；本次采用没有重新运行模型或更新源码仓库。

本文件对应正式正文中的 C01–C09；原始图和示例继续保留。

## 固定依据

- 本轮确认仓库：`/home/fredkeira/projects/slime`；核心包为其中的 `slime/`。
- 阅读快照／源码链接：`22a89f96835969a47055a659c588f46151f8b07a`，分支 `main`。
- 原材料固定快照：`8c17b676cb57af1d17ee4402e91e9209af84b60b`。
- 已核对 `common.py`、`anthropic.py`、`trajectory.py`：两快照的文件内容相同；当前工作区这三个文件也与 HEAD 一致，因此原材料行号仍有效。
- 定稿核对时，官方 main 为 `58b0878679de339ec7844b45d884a87955a134be`，比本地领先 2 个提交，其中包含 Agent 源码变化。本轮不更新源码，候选绑定本地 HEAD；详见同目录 `upstream-check.json`。
- 本轮未运行模型、Agent、tokenizer 或 SGLang；原示例的编码与模拟响应保持原有性质。

## 逐步对应

### C01

**核对事实：** 共享 _run_turn 先转换、编码，再等待生成结果；turn 是返回值的接收变量。

| 位置 | 文件与行号 | 固定链接 |
| --- | --- | --- |
| 共享流程与输入准备 | `slime/agent/adapters/common.py:318` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L318-L344) |
| 下一步解码与解析 | `slime/agent/adapters/common.py:346` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L346-L354) |

**本轮结果：** 已静态读取对应文件与调用关系；这是源码核对，不是运行记录。

### C02

**核对事实：** tok 来自适配器；s 由 sid 取出或默认创建，Session 只保存默认采样和额外上下文上限。

| 位置 | 文件与行号 | 固定链接 |
| --- | --- | --- |
| 当前 tokenizer 与 Session | `slime/agent/adapters/common.py:335` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L335-L338) |
| Session 字段 | `slime/agent/adapters/common.py:33` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L33-L42) |
| Anthropic 的采样字段名 | `slime/agent/adapters/anthropic.py:45` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/anthropic.py#L45-L46) |

**本轮结果：** 已静态读取对应文件与调用关系；这是源码核对，不是运行记录。

### C03

**核对事实：** 一次 apply_chat_template(tokenize=True) 同时应用模板并编码，最后统一返回整数列表。

| 位置 | 文件与行号 | 固定链接 |
| --- | --- | --- |
| 模板编码函数 | `slime/agent/adapters/common.py:58` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L58-L73) |

**本轮结果：** 已静态读取对应文件与调用关系；这是源码核对，不是运行记录。

### C04

**核对事实：** 会话默认值覆盖基础值；请求长度与已有长度取 min，其他采样字段和 stop 按顺序映射。

| 位置 | 文件与行号 | 固定链接 |
| --- | --- | --- |
| 采样参数整理 | `slime/agent/adapters/common.py:416` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L416-L439) |
| 调用位置 | `slime/agent/adapters/common.py:455` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L455) |
| 协议字段配置 | `slime/agent/adapters/anthropic.py:45` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/anthropic.py#L45-L46) |

**本轮结果：** 已静态读取对应文件与调用关系；这是源码核对，不是运行记录。

### C05

**核对事实：** 上下文上限为正时启用预算；耗尽时直接返回空输出，否则再取较小的生成上限。

| 位置 | 文件与行号 | 固定链接 |
| --- | --- | --- |
| 额外上下文预算 | `slime/agent/adapters/common.py:457` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L457-L468) |

**本轮结果：** 已静态读取对应文件与调用关系；这是源码核对，不是运行记录。

### C06

**核对事实：** 生成请求通过 aiohttp POST 发出，rid 对应一次生成请求，会话标识按条件进入路由请求头。

| 位置 | 文件与行号 | 固定链接 |
| --- | --- | --- |
| 请求组装与发送 | `slime/agent/adapters/common.py:470` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L470-L496) |

**本轮结果：** 已静态读取对应文件与调用关系；这是源码核对，不是运行记录。

### C07

**核对事实：** 每项第 1 位进入 output_ids，第 0 位转 float 后进入 output_log_probs；结束原因读取 type。

| 位置 | 文件与行号 | 固定链接 |
| --- | --- | --- |
| 响应读取与提取 | `slime/agent/adapters/common.py:496` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L496-L501) |

**本轮结果：** 已静态读取对应文件与调用关系；这是源码核对，不是运行记录。

### C08

**核对事实：** 生成函数返回冻结 dataclass 实例；ill_formed 默认 False，后续解析通过 dataclasses.replace 产生替代记录。

| 位置 | 文件与行号 | 固定链接 |
| --- | --- | --- |
| TurnRecord 定义 | `slime/agent/trajectory.py:28` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L28-L38) |
| 封装返回 | `slime/agent/adapters/common.py:509` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L509-L514) |
| 接收记录与后续解析 | `slime/agent/adapters/common.py:344` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L344-L354) |

**本轮结果：** 已静态读取对应文件与调用关系；这是源码核对，不是运行记录。

### C09

**核对事实：** 预算耗尽直接返回；HTTP错误抛出；取消/客户端错误/超时会尝试abort后再抛出；共享finally解除在途登记。

| 位置 | 文件与行号 | 固定链接 |
| --- | --- | --- |
| 上下文用尽 | `slime/agent/adapters/common.py:457` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L457-L468) |
| HTTP 错误 | `slime/agent/adapters/common.py:485` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L485-L495) |
| 取消与网络错误 | `slime/agent/adapters/common.py:502` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L502-L507) |
| 中止请求函数 | `slime/agent/adapters/common.py:517` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L517-L554) |
| 共享流程的 finally | `slime/agent/adapters/common.py:392` | [查看](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L392-L393) |

**本轮结果：** 已静态读取对应文件与调用关系；这是源码核对，不是运行记录。

## 图与示例

- `flow.svg`、`示例.json`、`模型输入.txt` 均复用正式资料目录的原文件，未改内容。
- 图中的 `body.max_tokens` 为原图简写，候选正文解释为字典键。原图对 logprob 第三项的标签也保留；候选正文仅说明此实现不读取第三项。
- 原示例的 218 个输入 token 是原材料记录的 tokenizer 编码结果；本轮未重算。5 项输出 ID 是演示句子的编码，SGLang 响应与 logprob 为人为构造。
- 原始 JSON、模型输入文本仍完整可下载；正文中的短数组只用于快速阅读，折叠区保留完整数据。
- 模板编码函数保留原实现；采样与请求只摘出相应片段。请求片段省略外层 try 和响应处理，类定义省略原文档字符串，均在正文标明。
- 原材料和正式入口的保留哈希在 `comparison-manifest.json`。

## 核对方法与验证边界

固定版本比对与本地源码读取均为只读操作。可用以下命令复查：

```sh
git -C /home/fredkeira/projects/slime diff 8c17b676cb57af1d17ee4402e91e9209af84b60b HEAD -- slime/agent/adapters/common.py slime/agent/adapters/anthropic.py slime/agent/trajectory.py
git -C /home/fredkeira/projects/slime show HEAD:slime/agent/adapters/common.py
```

已完成：

- 3 个相关源码文件与固定旧快照逐字一致；9 个 Python 片段已按注明的省略范围与源码 AST 对照。
- 从源码 AST 独立提取 Session 与采样纯函数，执行 4 组上限用例，均符合预期；没有网络或模型调用。
- 7 个 JSON 代码块与原示例相应字段深比较一致；源码出处 C01–C09 均有对应正文入口。
- 11 项章节检查通过，包含候选不进入生产构建、对比两栏指向正确、沿用资源可访问及旧 Action 2 对比兼容。
- 浏览器验证两栏独立加载、原图一致、9 个源码折叠默认关闭、Enter 可展开、资源 HTTP 200、窄屏无页面横向溢出。
- 对比清单记录的 6 个原始文件哈希未变。

详细静态检查见同目录 `validation.json`。本轮未执行 Agent、模型服务、训练或集群。


## 第三版定稿时的核对记录

- 本轮只使用已核对的材料重排讲解，没有重新读取外部源码仓库。
- 与第二版逐字比较：17 个代码／数据围栏、20 个固定源码链接、9 个源码折叠均相同；第 4、5 步正文相同。
- 第二版正文、校验文件、入口和原对比页的保留哈希未变。
- Hugo 章节检查通过，覆盖第三版的独立预览、片段定位、原资源复用及未进入生产站点。
- 第三版输出是否更有助于理解，由用户实际对比判断；未据页面生成推断学习效果。

本轮一致性结果见同目录 `validation.json`。

- 浏览器已检查第二版／第三版两栏定位到同一节，三列均完整显示；源码折叠默认关闭、键盘可展开，资源返回 200，窄屏无页面横向溢出。


## 正式页采用检查

用户确认第三版后，正式第三章已切换为同目录 `reading.md`。正式入口与第三版预览共同使用该正文，第一版、第二版各自保留。

本次采用已验证：侧栏点击进入第三版；9 个源码折叠默认收起且可键盘展开；图、示例、模型输入和校验文件可访问；历史对比链接有效；窄屏无页面横向溢出。11 项章节检查通过。
