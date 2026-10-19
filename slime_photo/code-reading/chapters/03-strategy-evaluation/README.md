# 第 3 章 策略接入、数据生成与评测合同

[阅读路线](../../repo-reading-route.md) · [总目录](../../README.md)

**目录 ID：** `03-strategy-evaluation`
**产物状态：** planned
**学习状态：** 统一见[阅读路线的当前接续](../../repo-reading-route.md#当前接续)。

**问题：** 新增 Agent 策略、评分器、数据集或样本处理逻辑时，应该接在哪个扩展点？

**前置：** 00–02；知道 Sample 与一次任务的返回边界。

**图文对照：** 4.5、3.4、3.3、3.2、3.1；7.5/7.6/7.10 作为对照。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 单样本生成与评分组合 | [slime/rollout/sglang_rollout.py · generate_and_rm](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L289) | trace | custom generate、异步等待、样本 hook 和 group_rm 分支；自定义函数可能扇出多个 Sample。 |
| 整批 rollout 返回合同 | [slime/rollout/base_types.py · call_rollout_fn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/base_types.py#L28) | trace | 训练/评估输出不同；本版本支持数据引用，不能只记成 Python Sample 列表。 |
| 可替换评分器 | [slime/rollout/rm_hub/__init__.py · async_rm](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/rm_hub/__init__.py#L55) | trace | 按样本、全局路径或远端评分分发；分组评分另看 batched_async_rm。 |
| 评测数据与参数 | [slime/utils/eval_config.py · EvalDatasetConfig](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/eval_config.py#L135) | trace | 先核对 eval_rollout_single_dataset 实际消费字段和结果合同；类中 timeout/early-stop/app_service 字段不能直接当作默认 runner 已实现的行为。 |
| 样本处理扩展点 | [slime/rollout/sample_hooks.py · apply_rollout_sample_hooks](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sample_hooks.py#L52) | trace | 同步/异步 hook 与样本身份传递；动态过滤和批次 hook 有不同位置。 |

**章内顺序：**

1. 标出 --custom-generate-function-path、--custom-rm-path、--data-source-path 和 --rollout-function-path 的不同作用范围。
2. 追踪 generate_and_rm 的生成、Sample 上下文继承、hook、奖励和返回；看 generate_and_rm_group 的组级处理。
3. 读 EvalDatasetConfig 与 eval_rollout_single_dataset，画一次固定数据集评测的结果合同。
4. 选 Search-R1 或 multi_agent 的入口，与 Coding Agent 对照如何替换单样本生成；Tau-bench 作为后续环境适配例子。
5. 读 tests/plugin_contracts 与 test_rollout_sample_hooks，列出新策略需要维持的输入、输出、身份和错误约定。

**验收问题：** 新增搜索工具策略和新增评分方法分别改哪里？什么时候需要替换整个 rollout？过滤样本后身份与完成确认由谁处理？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](../../repo-reading-route.md#当前接续)。
