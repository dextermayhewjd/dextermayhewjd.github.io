# 完整输入输出参考：早期展开版

本例来自 Slime 的一次实际学习记录。原话保持原文；源码场景、输入输出及 LLM 模型由助手提供，不自动成为用户已经理解的内容。样本为既有教学数据，局部转换已经核对，范围见记录正文。

## 短期记录

文件位置：`step-01-translate-preview/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._translate.md`。

下面是完整格式示例；本独立文档将原项目的本地导航写成名称，实际使用时填写可访问的源记录链接。

````markdown
# BaseAdapter._translate

- 源码定位：[slime/agent/adapters/common.py:189](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L189)，由助手核对。
- 首次接触：Step 01。
- 最近认识更新：Step 01。

## 我的直接表述（原话）

Step 01 本轮对转换职责的复述：

> 这一轮是把传输进来的openai或者anthropic的请求body转换为对应的好处理的统一的格式
> 例如anthropic的messages 里面包括的system和和tool call和messages等内容
>
> 同时这里还要吧tools 中的内容转换为工具定义的schema 例如input type object name之类的（anthropic的形式）

被问到消息中有工具调用时是否会真正读取文件，我补充：

> 不会 这里的translate 只是作为一种格式的切换

原话及上下文见下方形成过程的问题四。原话中的字段层级仍待澄清，保留在未知中。

## 使用场景与调用代码

场景：Coding Agent 继续一次对话，请求模型概括已经读取的 README。Adapter 已拿到请求 `body`，其中同时有历史消息和当前可用工具。本例选用 Anthropic 协议。

调用者是 `BaseAdapter._run_turn()`；此时 `self` 为 `AnthropicAdapter`，因此实际转换由 `AnthropicAdapter._translate()` 完成。`BaseAdapter._translate()` 定义共同约定，其方法体本身会抛出 `NotImplementedError`；下面展示的是该约定在具体实现中的输入输出。

[真实调用位置：common.py:341–342](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L341)。以下连续两行摘自原仓库，省略外层会话检查和后续生成流程：

```python
translated, tools_schema = self._translate(body)
prompt_ids = _render_token_ids(translated, tok, tools=tools_schema, add_generation_prompt=True)
```

第二行是调用方对返回结果的使用，不属于 `_translate` 内部。

## 本场景的输入与输出

以下是助手核对的源码材料，不表示用户已经理解每个字段。输入沿用原页面的教学示例，其历史版本为 `8c17b676cb57af1d17ee4402e91e9209af84b60b`；本轮用当前固定版本 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 中提取出的真实 `_translate` 和四个纯辅助函数执行核对，两份输出与该示例一致。未运行 HTTP 服务、tokenizer、模型或完整 Agent。

### 输入

输入参数为下面的 `body`。它包含三条历史消息和一个可用工具定义，历史中已经发生过一次 `read_file` 调用并取得结果。

<details>
<summary>展开本例完整 body</summary>

```json
{
  "system": [
    {
      "type": "text",
      "text": "你是代码助手。"
    }
  ],
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "读取 README.md 并概括内容。"
        }
      ]
    },
    {
      "role": "assistant",
      "content": [
        {
          "type": "text",
          "text": "我先读取文件。"
        },
        {
          "type": "tool_use",
          "id": "toolu_demo",
          "name": "read_file",
          "input": {
            "path": "README.md"
          }
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "tool_result",
          "tool_use_id": "toolu_demo",
          "content": [
            {
              "type": "text",
              "text": "# Demo\n这是一个学习项目。"
            }
          ]
        },
        {
          "type": "text",
          "text": "请用一句话概括。"
        }
      ]
    }
  ],
  "tools": [
    {
      "name": "read_file",
      "description": "读取文件",
      "input_schema": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string"
          }
        },
        "required": [
          "path"
        ]
      }
    }
  ],
  "max_tokens": 128
}
```

</details>

### 当前函数的输出

实际返回值是二元组 `(translated, tools_schema)`。下面分别展示解包后的两个值，不另造返回对象：本例得到五条内部消息和一个工具定义。

<details>
<summary>展开 translated：转换后的消息列表</summary>

```json
[
  {
    "role": "system",
    "content": "你是代码助手。"
  },
  {
    "role": "user",
    "content": "读取 README.md 并概括内容。"
  },
  {
    "role": "assistant",
    "content": "我先读取文件。",
    "tool_calls": [
      {
        "type": "function",
        "function": {
          "name": "read_file",
          "arguments": {
            "path": "README.md"
          }
        }
      }
    ]
  },
  {
    "role": "tool",
    "content": "# Demo\n这是一个学习项目。"
  },
  {
    "role": "user",
    "content": "请用一句话概括。"
  }
]
```

</details>

<details>
<summary>展开 tools_schema：转换后的工具定义</summary>

```json
[
  {
    "type": "function",
    "function": {
      "name": "read_file",
      "description": "读取文件",
      "parameters": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string"
          }
        },
        "required": [
          "path"
        ]
      }
    }
  }
]
```

</details>

### 后续交接

`_run_turn()` 将两个返回值一起交给 `_render_token_ids()`。渲染器再使用 tokenizer 的 chat template 生成 `prompt_ids`，供后续模型生成使用；token IDs 是下一个函数的产物，不是 `_translate` 的返回值。本例没有运行具体 tokenizer，不提供推测的 token 数值。

## LLM 基于使用场景的心智模型

以下由助手根据固定版本调用处和相关实现归纳，属于源码解释。

**代码直接显示的关系：**

- `BaseAdapter._translate` 约定返回消息和工具定义；实际转换由相应协议的 Adapter 实现。
- 共同的 `_run_turn` 接住这两个值后，立即交给同一个 `_render_token_ids` 渲染入口。
- 本例中的具体转换不会执行历史里的 `read_file`，也不负责生成 token IDs。

**对职责的归纳：** 把 `_translate` 看作“外部协议请求到共同处理流程的适配接口”：前面允许请求格式不同，后面按照一致的消息和工具定义处理。它把协议差异收在具体 Adapter 中，让共同流程接着渲染模型输入。

**证据边界：** 这只验证了当前样本的局部转换。它不证明所有输入都被支持、所有字段都被无损保留，或完整 Agent 已运行。个人已经理解哪些关系，仍以下面的原话整理及未知为准。

## 当前心智模型

以下由助手依据用户在本步的原话整理：

- 这是请求转换的共同约定：输入是请求 `body`，输出包含整理后的对话历史与工具 schema。
- 一份结果保留历史内容，一份保留工具箱的工具定义。
- Anthropic 与 OpenAI 两个 Adapter 都需要交回约定的信息，具体转换由它们各自实现。
- 转换的目的是把传入的 OpenAI 或 Anthropic 协议请求，整理为后续便于处理的统一内部格式。
- 即使消息里包含工具调用，`_translate` 也只是转换它的表示格式，不会因此实际执行工具。

这份记录保存共同职责；Anthropic 示例对应的认识见具体实现记录。

## 尚不清楚

- 请求与返回结果的详细字段结构，以及具体转换规则。
- 运行时怎样选中某个 Adapter 的具体实现。
- Anthropic 和 OpenAI 两处实现内部有哪些差异。

目前知道共同职责，还不清楚这些实现细节。

## 形成过程

Step 01 · 共同约定与两个具体实现怎样分工。两份结果用途的讨论见同一文件的问题二，用户原话和源码核对保存在那里。

问题四保存本轮职责复述和追问：用户明确说明这里只转换格式，不执行消息中的工具调用。
````

## 下一步的长期记录

假设下一步尚未新增该函数的认识，将上面的完整记录合入：

`step-02-example/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._translate.md`

需要保留整份内容，包括用户原话、真实场景和代码、一对输入输出、LLM 模型、个人理解、未知、源码版本及形成来源。首次接触和最近认识更新仍为 Step 01；来源链接仍指向 Step 01。LLM 的解释继续标为 LLM 提供，不能因进入长期记忆而变成“用户已经掌握”。这是继承示例，不表示 Step 02 已经开始。
