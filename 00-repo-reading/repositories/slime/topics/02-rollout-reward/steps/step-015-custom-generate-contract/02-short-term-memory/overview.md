# 02 · Step 015 本步函数与类记录

[阅读范围与顺序](../01-scope.md#reading-order) · [前序累计记录](../03-long-term-memory/overview.md) · [理解过程](../04-flow.md)

| 函数／类 | 本步用途 | 来源与认识状态 |
| --- | --- | --- |
| [generate_and_rm](functions/slime/rollout/sglang_rollout.py/generate_and_rm.md#returned-sample-fields) | 调用方：传参、等待与接收结果；状态检查和奖励回填 | 从 03 完整调取。用户已初步表述路径加载、位置对应和生成后补分；reward 为 None 与样本不存在的区别、状态前置仍待校准。 |
| [coding_agent_rl.generate](functions/examples/coding_agent_rl/generate.py/generate.md#returned-samples) | 接入方：真实签名及正常返回来源 | 用户已表述位置对应；本轮从内层 finish_session 的交付处接续第二步，新增的是正常返回位置与数据来源说明，尚待理解反馈。 |
| [Sample](classes/slime/utils/types.py/Sample.md#step015-field-view) | 返回对象的字段视图，配合第二步阅读 | 从 03 完整调取。已补充字段分组和 status / reward 的区别；用户初步联系结果与补分，精确缺失条件仍待校准。 |
| [test_custom_generate_function_path_supports_user_override](functions/tests/plugin_contracts/test_plugin_generate_contracts.py/test_custom_generate_function_path_supports_user_override.md#minimal-generate) | 通过框架执行最小生成替身，并检查返回值 | 用户已初步区分签名检查与结果字段检查；当前校准“通过局部 contract”与完整数据有效性的区别，尚无 pytest 运行证据。 |
| [_run_server_abort_generate](functions/slime/rollout/sglang_rollout.py/_run_server_abort_generate.md#possible-server-abort) | 回看正常等待包装器与可能的服务端中止交接 | 从 03 完整调取。用户反馈已大致理解 counter 与后续可能中止的关系，已按要求记录条件分支；完整中止和接口错误反例仍待后续。旧局部验证保留，未新增运行。 |

测试文件本轮集中于上述正常路径用例，配套生成函数与短断言保留在这张父卡中；fixture 只说明用途。其他用例、错误／失败情形与实际运行仍待接续。更深的 Agent 与调度函数仍在 03，本步不递归调取全部依赖。

[调取来源清单](../references/active-retrieval.json)。复制卡片、补源码或填充历史空白，都不自动改变用户的认识更新时间。
