# 2026-10-21：修正前的格式选择证据

修正前保存，供核对本次生成为什么偏离 BaseAdapter._translate。以下内容是历史快照，不作为新记录的生成规则。

## 短期 skill 的正文规则

原路径：`.agents/skills/repo-reading-short-term-memory/SKILL.md`

````markdown
使用[短期函数模板](../repo-reading-memory/references/short-term-memory-template.md)，按以下顺序组织：

| 内容 | 记录要求 |
| --- | --- |
| 我的理解（原话） | 逐字保留用户对函数的表述，节选及多次回答分别标明；尚无直接表述时如实注明 |
| 使用场景与调用代码 | 简短说明当前任务、调用者与后续消费者，附几行真实调用 |
| Input → Output | 一组对应的小输入与当前函数的返回值或副作用，标明教学构造、缩减或输出节选 |
| LLM 补充模型 | 简短说明职责与边界，明确它是助手据源码提供的解释 |
| 尚不清楚 | 保留已经暴露的疑问与尚未展开的实现 |
| 来源 | 源码路径、符号、固定版本和行号，样例来源、验证方式及原始步骤的讨论链接 |

原话清楚时不再增加重复的归纳。源码解释不能代填个人理解；用户说“继续”、文件生成或静态核对成功，都不代表已经掌握。范围已确认后可以先建卡并注明尚无直接表述，不把复述作为保存记录的门槛。

默认使用短场景、少量调用代码和一组小输入输出；保留当前问题必需的字段及所有相关返回项，不为缩短而省掉一条输出。输入改变后重新核对输出。区分当前函数返回值与调用者的后续结果，区分静态推导与实际执行。基类接口的示例要注明实际使用的具体实现。

带读时提供局部材料，邀请用户说明当前理解，再根据回答聚焦一个关键区别。按实际发生的问答补充原话和未知；不要先给完整答案，再要求照着复述。完整问答和扩展讲解链接到原始 flow 或参考文件，不重复抄进函数记录。
````

## 短期模板

原路径：`.agents/skills/repo-reading-memory/references/short-term-memory-template.md`

````markdown
# 短期记忆：函数模板

用于本步新形成或修正的理解，存入 `02-short-term-memory/functions/<源码相对路径>/<完整函数名>.md`。替换下方占位内容；原话已清楚时不再重复归纳。同一函数有旧认识时，保留使本条独立可读的已有内容。[填写案例](translate-function-example.md)。

````markdown
# <完整函数名>

首次接触：<步骤>｜最近理解更新：<实际形成或修正理解的步骤>

**我的理解（原话）**

> <用户实际说过的直接表述；节选标明节选，多次回答分开引用。>

**使用场景与源码**

<1–2 句话说明当前任务、谁调用这里、结果交给谁。>

```python
# 几行原仓库真实调用代码；按实际语言替换代码块类型。
```

**Input → Output**

<一句说明本例观察什么，标明教学缩减或构造。>

```python
# Input：一组最小具体输入，保留真实字段。

# Output：与上述输入对应的函数返回值或副作用。
```

**LLM 根据调用处补充的模型**

<1–2 句话说明职责和边界；这是源码解释，未表达的关系不算用户已理解。>

**暂时不清楚**

<保留具体疑问与尚未展开的实现。>

**来源**

源码：<路径、符号、固定版本及行号>；样例：<来源与验证方式>；形成过程：<包含原始步骤名的 flow 段落链接>。
````
````

## 此前生成的函数卡片

原路径：`00-repo-reading/repositories/slime/steps/step-001-harness-to-adapter/02-short-term-memory/functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.apply_chat_template.md`

````markdown
# PreTrainedTokenizerBase.apply_chat_template

首次接触：Step 1 的 `_render_token_ids`｜最近认识更新：2026-10-21 提出疑问；本次单独整理不代表已掌握。

**我的理解（原话）**

用户上一轮的疑问（节选）：

> 但是我不理解的是这里的tokenizer的apply chat plate是在做什么

**使用场景与源码**

`_render_token_ids` 调用这个 Transformers 方法，将已整理的消息和工具定义交给聊天模板，取得编码结果。

```python
enc = tokenizer.apply_chat_template(
    messages,
    tools=tools,
    tokenize=True,
    add_generation_prompt=add_generation_prompt,
)
```

**Input → Output**

为看清“套模板”，本例显式使用最小教学模板和 `tokenize=False`，无工具、不追加助手开头。含工具的完整输入沿用 [`_render_token_ids` 的样例](../../../slime/agent/adapters/common.py/_render_token_ids.md)。

```python
template = "{{ messages[0]['role'] }}: {{ messages[0]['content'] }}"
text = tokenizer.apply_chat_template(
    [{"role": "user", "content": "你好"}],
    tools=None,
    chat_template=template,
    tokenize=False,
    add_generation_prompt=False,
)

# Output
"user: 你好"
```

这是教学模板的结果；真实模型使用自己的模板。模板字符串已用 Jinja2 渲染核对，未实际调用模型 tokenizer。

**LLM 根据调用处补充的模型**

> `apply_chat_template` 按聊天模板，把消息和可用工具定义组织成提示文本；工具呈现取决于模板是否支持。`tokenize=False` 返回文本，当前 Slime 使用 `True`，因此还会把文本编码成 token ID。

**暂时不清楚**

当前模型的具体模板和 token ID 尚未核对；用户尚未确认套模板与编码的区别。

**来源**

- Slime 调用：提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`，[`common.py:66–71`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L66-L71)。
- 库函数：Transformers [`v4.57.1 · tokenization_utils_base.py:1546–1721`](https://github.com/huggingface/transformers/blob/v4.57.1/src/transformers/tokenization_utils_base.py#L1546-L1721)，静态核对模板渲染与编码分支；这是接口参考版本，Slime 的 `requirements.txt` 未锁定 Transformers，本机当前解释器未安装该库，不能当作实际运行版本。
- 形成过程：[Step 1 · 套模板和编码](../../../../../../step-001-harness-to-adapter/04-flow.md#chat-template-two-actions)；[本次单独建卡](../../../../../../step-001-harness-to-adapter/04-flow.md#apply-chat-template-card)。
````
