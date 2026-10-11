# 第 4 章 Trace、结果分析、测试与复现

[阅读路线](../../repo-reading-route.md) · [总目录](../../README.md)

**目录 ID：** `04-trace-validation`
**产物状态：** planned
**学习状态：** 未开始

**问题：** 怎样把模型、工具、环境和评分的失败或延迟关联起来，并用测试与配置验证修改？

**前置：** 01–03；已能指出执行与评测的关键交接。

**图文对照：** 9、8.2、3.5；源码 tests/ 和复现文档。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 事件与 span 的组织 | [slime/observability/trace_utils.py · trace_span](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/trace_utils.py#L345) | trace | 自定义格式与跨边界 carrier；工具存在不表示所有示例已接好完整埋点。 |
| 实验日志与配置 | [slime/observability/logging_utils.py · configure_logger](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/logging_utils.py#L12) | locate | 继续读 init_tracking/finish_tracking；日志、指标与任务 Trace 分别定位。 |
| 正确率与结果统计 | [slime/observability/metric_utils.py · compute_pass_rate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/metric_utils.py#L14) | trace | 按题目分组和评分假设影响 pass@k 的解释。 |
| 轨迹时间线查看器 | [tools/trace_timeline_viewer.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tools/trace_timeline_viewer.py#L1) | locate | 输入适配、span 展示、离线分析；不当作现成的全链路在线监控。 |
| 扩展接口行为测试 | [tests/plugin_contracts/test_plugin_generate_contracts.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/plugin_contracts/test_plugin_generate_contracts.py#L1) | locate | 先读 fixture 与断言；测试未经本轮执行，不标为通过。 |

**章内顺序：**

1. 从 trace_span/trace_event 到 export_trace/import_trace，画父子 span 与跨进程关联。
2. 取一个评分失败或模型请求变慢的情景，决定应该记录的身份、阶段、尝试次数、耗时和错误。
3. 选 test_adapters、test_sandbox_exec_and_wait、test_eval_config 和 plugin_contracts，说明它们实际验证什么。
4. 读 docs/zh/advanced/reproducibility.md，记录代码 SHA、模型/tokenizer、数据集、采样、依赖和资源配置；固定随机种子不等于所有后端完全一致。
5. 第二遍再实践一项 fake 驱动的失败注入；需要模型或集群的验证另行准备环境。

**验收问题：** 一次任务失败，日志、Trace、样本状态和评分结果各回答什么？复现实验需要保存哪些配置与产物？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，学习状态尚未由用户复述确认。
