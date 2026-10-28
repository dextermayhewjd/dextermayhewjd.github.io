# Trace 真实用法的具体数据案例

[短期记忆索引](../overview.md) · [scope 总览](../../01-scope.md#tool-catalog)

本目录只收录**在 Slime 业务源码中确实有调用的官方入口与其配套用法**。四个案例彼此独立，A–D 只是案例编号，不是新学习步骤，也不是一次执行的先后顺序。

| 案例 | 入口与配套用法 | 用具体数据看什么 |
| --- | --- | --- |
| [A · Agent 运行](trace-span-agent-run/README.md) | [trace_span 进入](trace-span-agent-run/README.md#use-enter) → [set](trace-span-agent-run/README.md#use-attrs) → [退出](trace-span-agent-run/README.md#use-exit) | 返回码 0 怎样进入 S1 结束事件；起止 10/12 秒 |
| [B · 函数调用](trace-function-generate-and-rm/README.md) | [trace_function 包装的调用](trace-function-generate-and-rm/README.md#trace-function-step) | 已完成且 reward=1.0 的真实分支仍留下 F1 记录，返回同一 Sample |
| [C · bind_trace](bind-trace/README.md) | [独立绑定的官方定位](bind-trace/README.md#official-basic-usage)；[Coding Agent 中的组合用法](bind-trace/README.md#bind-trace-step) | 基础绑定与本场景的 export/import 组合分开；具体数据展示“共享容器、带上父阶段”；[实际执行后续 span](bind-trace/README.md#actual-agent-model-turn)，事件从 1 条变为 5 条 |
| [D · 模型元信息](sglang-meta-update/README.md) | [build_sglang_meta_trace_attrs](sglang-meta-update/README.md#meta-transform-step) → [update](sglang-meta-update/README.md#update-step) → [退出](sglang-meta-update/README.md#span-exit-step) | 12 个输入 token、1 个输出 token 等如何变成结束属性 |

每个目录包含 README.md、input.json、expected.json。先看使用目的，再对照代码与数据变化；完整 JSON 可单独查看。案例 C 按“共享记录的前后结构 → 连续使用代码 → 后续请求怎样取用”组织，函数细节在同一段交接中解释。

**真实的是调用位置和执行规则；具体样本、返回值、编号与时钟是教学构造。** expected.json 是固定输入下的观察快照，按原实现做隔离核对；不是从真实 Agent/训练运行抓取的文件。核对边界见[verification.json](verification.json)。不把缺失业务环境的替身结果称为实际模型输出。

input.json 中 sample/base_sample 只节选与当前问题相关的真实字段；active_context、fixed_observation、assumed_* 描述观察环境及假设，不应写回 Sample。expected.json 的对象摘要和 identity 也属于观察格式，不是新增生产接口。

trace_event 当前没有找到实现文件之外的 Python 调用，因此不建立真实案例；trace_next_attempt 同样不收录。内部收尾方法继续在函数卡按需回查。

这里负责具体输入、连续变化和可对照的结果；函数卡保留职责与使用方法，scope 保留总览。后续继承本步 02 时一并继承这些样本、验证说明和来源。

[本轮确认](../../../step-014-agent-run-trace/04-flow.md#step014-concrete-examples) · [固定版本的真实调用证据](../../references/real-usage-evidence.json)
