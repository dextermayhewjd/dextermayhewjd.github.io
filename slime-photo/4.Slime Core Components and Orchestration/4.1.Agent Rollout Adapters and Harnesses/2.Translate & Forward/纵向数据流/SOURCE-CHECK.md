# Action 2 源码出处与校验清单

本文件集中维护正式阅读页的源码定位与核对要点。网页中的 `查看源码出处与行号` 入口与下列编号一一对应，默认收起。

## 固定依据

- 源码快照：`8c17b676cb57af1d17ee4402e91e9209af84b60b`。
- 来源：原有 `2.Translate & Forward/2.主路径和源码函数.md` 与 `2.Translate & Forward/纵向数据流/README.md`。
- 下表是已有阅读材料的定位，不表示当前工作区行号相同，也不表示本次重新运行了 Agent、模型服务或工具。
- 校验时应查看固定快照中的文件，再对照说明、输入输出和调用关系。

## 逐项核对

### C01 · 共享流程接收转换结果

**应核对的事实：** 调用发生在同一个适配器实例中，接收 translated 与 tools_schema。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| _run_turn 定义 | `slime/agent/adapters/common.py:318` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/common.py#L318) |
| 调用 _translate 并接收返回值 | `slime/agent/adapters/common.py:341` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/common.py#L341) |

### C02 · 先消息、再工具、一起返回

**应核对的事实：** _translate 的四行实现按消息、工具定义的顺序执行。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| _translate 定义 | `slime/agent/adapters/anthropic.py:58` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L58) |
| 消息转换 | `slime/agent/adapters/anthropic.py:59` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L59) |
| 工具定义转换 | `slime/agent/adapters/anthropic.py:60` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L60) |
| 返回二元组 | `slime/agent/adapters/anthropic.py:61` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L61) |

### C03 · 入口 body 与后续采样字段

**应核对的事实：** 读取并预处理请求；max_tokens 留在 body 中供后续采样使用。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 读取请求 JSON | `slime/agent/adapters/common.py:325` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/common.py#L325) |
| 预处理 | `slime/agent/adapters/common.py:326` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/common.py#L326) |
| 本例预处理入口 | `slime/agent/adapters/anthropic.py:55` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L55) |
| 中途 system 消息处理 | `slime/agent/adapters/anthropic.py:291` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L291) |
| 生成长度字段配置 | `slime/agent/adapters/anthropic.py:45` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L45) |
| 后续采样读取 | `slime/agent/adapters/common.py:425` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/common.py#L425) |

### C04 · 消息列表的转换与返回

**应核对的事实：** system 与 messages 转换成规范化的消息列表。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| _translate_messages 定义 | `slime/agent/adapters/anthropic.py:81` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L81) |
| 返回消息列表 | `slime/agent/adapters/anthropic.py:120` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L120) |

### C05 · 系统文本块转成系统消息

**应核对的事实：** flatten_content 展开系统文本，结果进入 role=system 的消息。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| flatten_content 定义 | `slime/agent/adapters/common.py:76` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/common.py#L76) |
| 处理系统指令 | `slime/agent/adapters/anthropic.py:84` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L84) |
| 展开系统文本 | `slime/agent/adapters/anthropic.py:85` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L85) |

### C06 · 用户文本转成用户消息

**应核对的事实：** user 分支提取文本块，保留用户角色。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| user 分支 | `slime/agent/adapters/anthropic.py:90` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L90) |
| 普通文本处理 | `slime/agent/adapters/anthropic.py:95` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L95) |

### C07 · 助手正文与历史工具调用

**应核对的事实：** 助手内容进入 content；工具名称和参数进入 tool_calls，arguments 保持字典。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| assistant 分支 | `slime/agent/adapters/anthropic.py:99` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L99) |
| tool_call_dict 定义 | `slime/agent/adapters/common.py:110` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/common.py#L110) |
| 转换历史工具调用 | `slime/agent/adapters/anthropic.py:111` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L111) |
| 构造助手消息 | `slime/agent/adapters/anthropic.py:112` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L112) |

### C08 · 工具结果与后续用户文本

**应核对的事实：** tool_result 的内容展开成工具消息；其后的文本继续成为用户消息。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 工具结果分支 | `slime/agent/adapters/anthropic.py:93` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L93) |
| 调用 flatten_content | `slime/agent/adapters/anthropic.py:94` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L94) |
| flatten_content 定义 | `slime/agent/adapters/common.py:76` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/common.py#L76) |

### C09 · 可用工具定义转换

**应核对的事实：** input_schema 对应 function.parameters；没有有效工具定义时返回 None。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| _tools_to_chat_tools 定义 | `slime/agent/adapters/anthropic.py:123` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L123) |
| 组装 function 工具定义 | `slime/agent/adapters/anthropic.py:137` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L137) |
| 调用工具定义转换 | `slime/agent/adapters/anthropic.py:60` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L60) |

### C10 · 交回共享流程并准备模型输入

**应核对的事实：** 两份结果经 Python 返回值交接，再进入下一步模板渲染。

| 定位内容 | 文件与行号 | 固定源码 |
| --- | --- | --- |
| 返回两份结果 | `slime/agent/adapters/anthropic.py:61` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/anthropic.py#L61) |
| 共享流程接收 | `slime/agent/adapters/common.py:341` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/common.py#L341) |
| 调用 token 渲染 | `slime/agent/adapters/common.py:342` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/common.py#L342) |
| _render_token_ids 定义 | `slime/agent/adapters/common.py:58` | [打开](https://github.com/THUDM/slime/blob/8c17b676cb57af1d17ee4402e91e9209af84b60b/slime/agent/adapters/common.py#L58) |

## 图与示例的完整性

- Action 2 当前位置图、原纵向数据流图和原组件关系图均复用原文件。
- 原页与原图的 SHA-256 记录在本目录 `adoption-manifest.json` 的 `preservedAssets` 中。
- 完整 JSON 示例是同目录的 `示例.json`。
- 本次采用调整了阅读顺序与出处的显示方式，保留全部 Python 片段和 JSON 示例内容。

## 本地核对方法

在 Slime 仓库中读取固定快照，例如：

```sh
git show 8c17b676cb57af1d17ee4402e91e9209af84b60b:slime/agent/adapters/anthropic.py
git show 8c17b676cb57af1d17ee4402e91e9209af84b60b:slime/agent/adapters/common.py
```

按上面的定义位置、调用位置与核对事实检查。若本地缺少此快照，应先取得对应源码历史，再核对；不要直接用另一版本的行号替代。
