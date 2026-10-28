# Scope 简写提案：阶段导航与当前展开点

[当前正式 scope](../01-scope.md) · [当前函数卡](../02-short-term-memory/functions/slime/rollout/sglang_rollout.py/_run_server_abort_generate.md)

2026-10-26，用户在补齐 evaluation 分支后提出：是否应该简写，不必详细展示每个函数。这份文件只保存表达方案，尚未替换正式 scope 或修改通用 skill。

**后续确认的限定**：用户明确现有主体很好，没有必要全部换掉。保留正式 scope 的三段结构、完整主流程、真实函数名、数据交接与控制范围；本提案仅供考虑 with 主体中参数适配和条件表达式的局部简写，不作为整体替换方案。下面的阶段导航是辅助对照，不取代现有主体代码。

## 1. 目前的问题

发现分支后把整段源码还原，虽然完整，却会使主骨架承担参数、接口适配和具体实现三种层次。之前“漏掉 evaluation”和现在“过于详细”可以同时成立：需要让这个选择可见，但不一定要把整个条件表达式和两套实参都放进总览。

## 2. 建议：总览说明阶段，当前节点再展开源码

针对当前 with 主体，可以用下面的**阶段导航**。中文行是阅读动作，不是新增 Python 函数或可运行代码；源码里的具体函数、参数及分支仍由局部说明和现有卡片承接。

```text
with state.dp_rank_context() as _:
    选择生成器          [自定义 / 默认]
    创建 generate_call  [支持时传入 evaluation]
    选择等待方式        [request / server]
        └─ 当前展开：_run_server_abort_generate
```

读到当前节点时，才显示两种等待包装的真实 if/else 和目标函数卡。需要查接口适配时，再打开 evaluation 的完整条件，不在整段主骨架中重复。

若保留当前自定义生成路径的代码骨架，可以使用下面的教学裁剪，同时紧邻保留其他路径的说明：

```python
with state.dp_rank_context() as _:
    generate_func = load_function(...)  # 本例选中 Coding Agent
    generate_call = generate_func(...)  # 支持该参数时传入 evaluation
    sample = await _run_server_abort_generate(state, generate_call)  # 当前路径
```

上述代码只展示当前路径：无自定义路径时用默认 generate；abort_mode 为 request 时改走 _run_request_abortable_generate。阶段导航保留这些选择，代码骨架不假装已经覆盖所有路径。

## 3. 哪些内容应该保留在哪里

| 内容 | 总览怎么写 | 详细内容放哪里 |
| --- | --- | --- |
| DP 上下文范围 | 保留 with 嵌套 | dp_rank_context 卡片 |
| 自定义或默认生成 | “选择生成器”旁注明两种来源 | 当前阶段的路径选择代码 |
| evaluation 参数支持检查 | “创建调用”旁注明支持时传入 | 当前阶段的接口条件与实参 |
| request/server 等待选择 | 保留分支存在，并标当前 server 路径 | 分派代码、对应方法卡 |
| 当前正在研究的方法 | 显示真实函数名与入口 | 方法卡的输入、输出和内部流程 |

这只是建议的阅读层次，不把所有参数条件永久判定为次要：当用户的问题就是 evaluation 或路径选择时，该项成为当前展开点。

## 4. 边界

- 正式 scope 仍保留现有全文，本提案未直接采用。
- 不删除已读来源、历史讨论或分支；只建议改变首屏呈现层次。
- 不新增函数记忆，不推进学习状态，不处理 Hugo。
- 源码依据仍为 Slime `18868a79` 的 `generate_and_rm:337–349`；参数支持检查与等待分派是依次执行的两个判断。
