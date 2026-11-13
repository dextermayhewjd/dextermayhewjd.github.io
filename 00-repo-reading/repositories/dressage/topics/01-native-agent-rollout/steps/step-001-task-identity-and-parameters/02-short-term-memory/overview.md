# Step 001 · 函数索引

| 函数 | 记录状态 |
| --- | --- |
| [blackbox_dispatch.generate](functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#sampling-seed) | 调取 Step 000 整体模型；本步补局部状态与采样配置，尚待理解反馈 |
| [ensure_blackbox_session_id](functions/dressage/rollout/prewarm/store.py/ensure_blackbox_session_id.md) | 用户概括为创建 ID；助手补充复用语义 |
| [instance_id](functions/dressage/rollout/artifacts/samples.py/instance_id.md) | 已展开取值优先级与返回；待用户表达理解 |
| [normalize_blackbox_type](functions/dressage/paddock/blackbox/common/defaults.py/normalize_blackbox_type.md) | 用户理解为返回 harness 名称；助手校准为格式规范化与缺省回退 |
| [paddock_env_args_from_metadata](functions/dressage/rollout/generate/runtime.py/paddock_env_args_from_metadata.md) | 用户已表述筛选与返回的理解；已补充配置、创建及缺失字段的区别 |
| [parse_blackbox_execute_cmds](functions/dressage/paddock/blackbox/execute_hooks.py/parse_blackbox_execute_cmds.md) | 用户已确认返回计划而非执行，包含运行前后两阶段 |
| [_backend_options_for_register](functions/dressage/rollout/generate/blackbox_dispatch.py/_backend_options_for_register.md) | 用户提出配置合并的理解；已补充类型选择和覆盖顺序 |
