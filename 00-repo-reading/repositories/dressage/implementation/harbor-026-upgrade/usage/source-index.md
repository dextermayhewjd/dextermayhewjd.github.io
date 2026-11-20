# Dressage 源码位置与用法编号

在 Dressage `3e3142f` 的已归档扫描内，191 个不同的“文件＋行号”均可查到用途或排除理由。同一行出现在导入、基类覆盖和对象成员多个表时只算一次。同一交接也可能分散在多行。下面保留具体行号，需要看原文时可按路径和行号查归档。 [扫描时的源码原行](harbor-call-sites.md) · [各版本的输入与产出](README.md)

<a id="locations"></a>

## 191 处归档位置

| Dressage 文件 | 固定提交的行号 | 对应用法或排除理由 |
| --- | --- | --- |
| `dressage/integrations/harbor/artifacts.py` | 453, 454, 455, 470, 471 | [U48](结果、样本与最终选择/U48-从%20TrialResult%20读取任务身份、Agent%20与时间.md#u48) |
| `dressage/integrations/harbor/artifacts.py` | 553 | [U53](结果、样本与最终选择/U53-get_result%20与%20write_job_manifest%20对齐最终物理尝试.md#u53) |
| `dressage/integrations/harbor/artifacts.py` | 1057, 1058, 1060, 1061, 1062 | [U49](结果、样本与最终选择/U49-从%20verifier_result%20或末尾%20step%20选择目标奖励.md#u49) |
| `dressage/integrations/harbor/artifacts.py` | 1074, 1077, 1078, 1083, 1090, 1091 | [U50](结果、样本与最终选择/U50-从%20trial%20与%20step%20的%20exception_info%20生成训练失败记录.md#u50) |
| `dressage/integrations/harbor/artifacts.py` | 1129 | 排除。`result.append(item)` 追加到 Dressage 自己的列表，变量名与 Harbor 结果相似。 |
| `dressage/integrations/harbor/compat.py` | 52 | [U02](启动与配置/U02-require_harbor_runtime%20读取并检查发行包版本.md#u02) |
| `dressage/integrations/harbor/compat.py` | 71, 75, 82, 83, 84 | [U16](Job%20与%20Agent%20路由/U16-Job._remaining_trial_configs%20提供待执行配置.md#u16) |
| `dressage/integrations/harbor/compat.py` | 93, 97 | [U15](Job%20与%20Agent%20路由/U15-Job._task_configs%20提供已经解析的任务对象.md#u15) |
| `dressage/integrations/harbor/compat.py` | 105, 108, 113 | [U11](Job%20与%20Agent%20路由/U11-Job._resolve_task_configs%20展开任务来源.md#u11) |
| `dressage/integrations/harbor/compat.py` | 124, 130, 131, 132, 158, 162, 166, 199 | [U17](Job%20与%20Agent%20路由/U17-build_trial_plan%20配对原对象并写回%20trial_name.md#u17) |
| `dressage/integrations/harbor/compat.py` | 206, 209, 212, 216 | [U20](Job%20与%20Agent%20路由/U20-复制%20AgentConfig%20时保留并发分组.md#u20) |
| `dressage/integrations/harbor/data_source.py` | 182, 204, 538, 564, 603 | [U06](启动与配置/U06-JobConfig.model_validate%20读取随仓%20Job%20YAML.md#u06) |
| `dressage/integrations/harbor/data_source.py` | 183, 205 | [U11](Job%20与%20Agent%20路由/U11-Job._resolve_task_configs%20展开任务来源.md#u11) |
| `dressage/integrations/harbor/data_source.py` | 186, 208, 683, 687, 712, 713 | [U09](启动与配置/U09-model_copy%20与%20model_dump%20建立题目及%20Agent%20注册表.md#u09) |
| `dressage/integrations/harbor/data_source.py` | 201 | 排除。这里把 Dressage 的可选 eval 配置初始化为 `None`，尚未调用 Harbor。 |
| `dressage/integrations/harbor/data_source.py` | 237, 245, 250, 832 | [U10](启动与配置/U10-Job%20配置摘要写入%20checkpoint%20并在%20load%20时比较.md#u10) |
| `dressage/integrations/harbor/environment.py` | 23 | [U31](环境构造与生命周期/U31-DressageEnvironment.__init__%20接收%20Trial%20的环境参数.md#u31) · [U43](环境执行、文件与挂载/U43-exec%20返回%20Harbor%20的%20ExecResult.md#u43) |
| `dressage/integrations/harbor/environment.py` | 24 | [U33](环境构造与生命周期/U33-Environment.capabilities%20给%20Harbor%20报告能力.md#u33) |
| `dressage/integrations/harbor/environment.py` | 25 | [U35](环境构造与生命周期/U35-BaseEnvironment%20构造时反向调用%20_validate_definition.md#u35) · [U36](环境构造与生命周期/U36-validate_network_policy_support%20接收%20Harbor%20的阶段网络策略.md#u36) |
| `dressage/integrations/harbor/environment.py` | 262, 282 | [U31](环境构造与生命周期/U31-DressageEnvironment.__init__%20接收%20Trial%20的环境参数.md#u31) |
| `dressage/integrations/harbor/environment.py` | 285, 539 | [U31](环境构造与生命周期/U31-DressageEnvironment.__init__%20接收%20Trial%20的环境参数.md#u31) · [U44](环境执行、文件与挂载/U44-Trial%20回收前查询挂载是否与宿主目录对应.md#u44) |
| `dressage/integrations/harbor/environment.py` | 289 | [U32](环境构造与生命周期/U32-Environment.type%20返回后端标识.md#u32) |
| `dressage/integrations/harbor/environment.py` | 293, 294 | [U33](环境构造与生命周期/U33-Environment.capabilities%20给%20Harbor%20报告能力.md#u33) |
| `dressage/integrations/harbor/environment.py` | 302 | [U34](环境构造与生命周期/U34-EnvironmentFactory%20调用%20DressageEnvironment.preflight.md#u34) |
| `dressage/integrations/harbor/environment.py` | 355, 356, 358, 361, 363 | [U35](环境构造与生命周期/U35-BaseEnvironment%20构造时反向调用%20_validate_definition.md#u35) |
| `dressage/integrations/harbor/environment.py` | 373, 376, 377, 378, 601, 633, 651 | [U36](环境构造与生命周期/U36-validate_network_policy_support%20接收%20Harbor%20的阶段网络策略.md#u36) |
| `dressage/integrations/harbor/environment.py` | 383, 395, 410, 411, 414 | [U37](环境构造与生命周期/U37-Environment.start%20把本次%20bwrap%20会话准备为可用.md#u37) |
| `dressage/integrations/harbor/environment.py` | 424 | [U38](环境构造与生命周期/U38-Environment.stop%20结束本次会话并释放资源.md#u38) |
| `dressage/integrations/harbor/environment.py` | 437 | [U39](环境执行、文件与挂载/U39-upload_file%20把一个宿主文件交给环境.md#u39) |
| `dressage/integrations/harbor/environment.py` | 445 | [U40](环境执行、文件与挂载/U40-upload_dir%20把一个目录交给环境.md#u40) |
| `dressage/integrations/harbor/environment.py` | 459 | [U41](环境执行、文件与挂载/U41-download_file%20把一个环境文件交回宿主.md#u41) |
| `dressage/integrations/harbor/environment.py` | 467 | [U42](环境执行、文件与挂载/U42-download_dir%20回收环境里的非空日志目录.md#u42) |
| `dressage/integrations/harbor/environment.py` | 481, 497, 531 | [U43](环境执行、文件与挂载/U43-exec%20返回%20Harbor%20的%20ExecResult.md#u43) |
| `dressage/integrations/harbor/environment.py` | 491 | [U45](环境执行、文件与挂载/U45-exec%20通过%20_resolve_user%20取得生效用户.md#u45) |
| `dressage/integrations/harbor/environment.py` | 500 | [U46](环境执行、文件与挂载/U46-exec%20通过%20_merge_env%20得到最终命令环境.md#u46) |
| `dressage/integrations/harbor/environment.py` | 525 | [U47](环境执行、文件与挂载/U47-exec%20通过%20_output_callback%20转发标准输出与错误输出.md#u47) |
| `dressage/integrations/harbor/plugin.py` | 266, 269, 274 | [U19](Job%20与%20Agent%20路由/U19-JobPlugin.on_job_start%20接收%20Job%20并登记路由与回调.md#u19) |
| `dressage/integrations/harbor/plugin.py` | 289, 337 | [U16](Job%20与%20Agent%20路由/U16-Job._remaining_trial_configs%20提供待执行配置.md#u16) · [U17](Job%20与%20Agent%20路由/U17-build_trial_plan%20配对原对象并写回%20trial_name.md#u17) · [U19](Job%20与%20Agent%20路由/U19-JobPlugin.on_job_start%20接收%20Job%20并登记路由与回调.md#u19) |
| `dressage/integrations/harbor/plugin.py` | 290, 344 | [U20](Job%20与%20Agent%20路由/U20-复制%20AgentConfig%20时保留并发分组.md#u20) · [U21](Job%20与%20Agent%20路由/U21-注入%20AgentConfig.env%20并设置%20extra_allowed_hosts.md#u21) |
| `dressage/integrations/harbor/plugin.py` | 293, 1082, 1086 | [U07](启动与配置/U07-TaskConfig.get_local_path%20定位题目目录.md#u07) |
| `dressage/integrations/harbor/plugin.py` | 346, 348, 350, 351, 353 | [U20](Job%20与%20Agent%20路由/U20-复制%20AgentConfig%20时保留并发分组.md#u20) |
| `dressage/integrations/harbor/plugin.py` | 359 | [U09](启动与配置/U09-model_copy%20与%20model_dump%20建立题目及%20Agent%20注册表.md#u09) · [U19](Job%20与%20Agent%20路由/U19-JobPlugin.on_job_start%20接收%20Job%20并登记路由与回调.md#u19) |
| `dressage/integrations/harbor/plugin.py` | 385, 1037, 1064, 1066, 1074, 1154, 1155, 1197 | [U21](Job%20与%20Agent%20路由/U21-注入%20AgentConfig.env%20并设置%20extra_allowed_hosts.md#u21) |
| `dressage/integrations/harbor/plugin.py` | 407 | [U23](Trial%20事件与目录/U23-Job.on_trial_started%20登记%20START.md#u23) |
| `dressage/integrations/harbor/plugin.py` | 408 | [U24](Trial%20事件与目录/U24-Job.on_agent_started%20登记%20AGENT_START.md#u24) |
| `dressage/integrations/harbor/plugin.py` | 409 | [U25](Trial%20事件与目录/U25-Job.on_agent_ended%20登记%20AGENT_END.md#u25) |
| `dressage/integrations/harbor/plugin.py` | 410 | [U26](Trial%20事件与目录/U26-Job.on_verification_started%20登记%20VERIFICATION_START.md#u26) |
| `dressage/integrations/harbor/plugin.py` | 413 | [U27](Trial%20事件与目录/U27-Job.on_trial_cancelled%20登记%20CANCEL.md#u27) |
| `dressage/integrations/harbor/plugin.py` | 414 | [U28](Trial%20事件与目录/U28-Job.on_trial_ended%20登记%20END.md#u28) |
| `dressage/integrations/harbor/plugin.py` | 424, 425 | [U52](结果、样本与最终选择/U52-JobPlugin.on_job_end%20从%20JobResult%20提取最终尝试.md#u52) |
| `dressage/integrations/harbor/plugin.py` | 616, 617, 1240, 1244, 1245, 1248 | [U29](Trial%20事件与目录/U29-TrialHookEvent%20的物理%20ID、结果对象与输出目录.md#u29) |
| `dressage/integrations/harbor/plugin.py` | 778 | [U29](Trial%20事件与目录/U29-TrialHookEvent%20的物理%20ID、结果对象与输出目录.md#u29) · [U51](结果、样本与最终选择/U51-commit_attempt%20将%20Harbor%20结果与%20Proxy%20轨迹持久化.md#u51) |
| `dressage/integrations/harbor/plugin.py` | 1100, 1101, 1108, 1109, 1110, 1112, 1134, 1136, 1141 | [U08](启动与配置/U08-TaskConfig.model_validate_toml%20解析题目与网络要求.md#u08) |
| `dressage/integrations/harbor/rollout.py` | 54, 567, 570 | [U13](Job%20与%20Agent%20路由/U13-EnvironmentFactory%20按%20import_path%20选择具体后端.md#u13) |
| `dressage/integrations/harbor/rollout.py` | 105, 107, 704 | [U14](Job%20与%20Agent%20路由/U14-Job.create%20在插件设置路由前创建%20Job.md#u14) |
| `dressage/integrations/harbor/rollout.py` | 435, 441, 448, 451, 454, 455, 458, 473, 475, 476, 519, 550, 551, 575 | [U12](Job%20与%20Agent%20路由/U12-model_validate%20重建每个分区的临时%20JobConfig.md#u12) |
| `dressage/integrations/harbor/rollout.py` | 548 | [U12](Job%20与%20Agent%20路由/U12-model_validate%20重建每个分区的临时%20JobConfig.md#u12) · [U20](Job%20与%20Agent%20路由/U20-复制%20AgentConfig%20时保留并发分组.md#u20) |
| `dressage/integrations/harbor/rollout.py` | 760 | [U19](Job%20与%20Agent%20路由/U19-JobPlugin.on_job_start%20接收%20Job%20并登记路由与回调.md#u19) |
| `dressage/integrations/harbor/rollout.py` | 761 | [U22](Job%20与%20Agent%20路由/U22-Job.run%20将本次%20Job%20的最终结果交给插件与分区.md#u22) |
| `dressage/integrations/harbor/rollout.py` | 762 | [U52](结果、样本与最终选择/U52-JobPlugin.on_job_end%20从%20JobResult%20提取最终尝试.md#u52) |
| `dressage/integrations/harbor/rollout.py` | 765, 802, 806 | [U53](结果、样本与最终选择/U53-get_result%20与%20write_job_manifest%20对齐最终物理尝试.md#u53) |
| `dressage/integrations/harbor/rollout.py` | 813 | [U54](结果、样本与最终选择/U54-_bundle_samples%20将一次尝试的分段奖励送入训练样本.md#u54) |
| `dressage/integrations/harbor/rollout.py` | 1254, 1274 | [U56](结果、样本与最终选择/U56-_eval_output%20返回按轨迹计数的评测结果.md#u56) |
| `dressage/integrations/harbor/rollout.py` | 1277 | [U55](结果、样本与最终选择/U55-generate_rollout_harbor_sync%20返回训练数据.md#u55) |
| `examples/harbor/dataset_tools/dapo/prepare_dataset.py` | 363 | [U13](Job%20与%20Agent%20路由/U13-EnvironmentFactory%20按%20import_path%20选择具体后端.md#u13) |
| `examples/harbor/dataset_tools/dapo/prepare_dataset.py` | 553 | [U03](启动与配置/U03-DAPO%20命令的%20check_runtime%20读取同一包版本.md#u03) |
| `examples/harbor/run_harbor_rollout_qwen3.5_4b.sh` | 109, 111 | [U04](启动与配置/U04-harbor%20run%20发现并挂接%20--plugin%20dressage.md#u04) |
| `examples/harbor/run_harbor_training_qwen3.5_4b.sh` | 66, 67 | [U05](启动与配置/U05-Slime%20按两个加载路径启动%20Dressage%20的训练入口.md#u05) |
| `pyproject.toml` | 26, 27 | [U04](启动与配置/U04-harbor%20run%20发现并挂接%20--plugin%20dressage.md#u04) |
| `tests/integrations/harbor/test_contracts.py` | 167 | [U06](启动与配置/U06-JobConfig.model_validate%20读取随仓%20Job%20YAML.md#u06) |
| `tests/integrations/harbor/test_contracts.py` | 169 | [U02](启动与配置/U02-require_harbor_runtime%20读取并检查发行包版本.md#u02) |
| `tests/integrations/harbor/test_environment.py` | 13 | [U31](环境构造与生命周期/U31-DressageEnvironment.__init__%20接收%20Trial%20的环境参数.md#u31) · [U36](环境构造与生命周期/U36-validate_network_policy_support%20接收%20Harbor%20的阶段网络策略.md#u36) |
| `tests/integrations/harbor/test_environment.py` | 14 | [U31](环境构造与生命周期/U31-DressageEnvironment.__init__%20接收%20Trial%20的环境参数.md#u31) · [U44](环境执行、文件与挂载/U44-Trial%20回收前查询挂载是否与宿主目录对应.md#u44) |
| `tests/integrations/harbor/test_gated_e2e.py` | 64 | [U06](启动与配置/U06-JobConfig.model_validate%20读取随仓%20Job%20YAML.md#u06) |
| `tests/integrations/harbor/test_gated_e2e.py` | 65 | [U22](Job%20与%20Agent%20路由/U22-Job.run%20将本次%20Job%20的最终结果交给插件与分区.md#u22) |

<a id="files"></a>

## 33 个全文命中文件

每个命中文件保留一个去向。文档、示例、夹具和下游日志均保留用途。同一条运行链经过多个文件时共用上面的用法编号。下表与扫描的文件名单逐项校对。 [固定版本的原始文件清单](harbor-call-sites.md#files)

| 文件 | 审核时怎样使用 |
| --- | --- |
| `README.md` | 仓库总说明中的文档入口。 |
| `docs/harbor.md` | 集成的使用说明与配置示例。 |
| `dressage/integrations/harbor/__init__.py` | 集成包导出 Dressage 自己的配置对象，保持 Harbor 延迟导入。 |
| `dressage/integrations/harbor/artifacts.py` | 消费 TrialResult、序列化结果与选择最终尝试。 [U48](结果、样本与最终选择/U48-从%20TrialResult%20读取任务身份、Agent%20与时间.md#u48) · [U49](结果、样本与最终选择/U49-从%20verifier_result%20或末尾%20step%20选择目标奖励.md#u49) · [U50](结果、样本与最终选择/U50-从%20trial%20与%20step%20的%20exception_info%20生成训练失败记录.md#u50) · [U51](结果、样本与最终选择/U51-commit_attempt%20将%20Harbor%20结果与%20Proxy%20轨迹持久化.md#u51) · [U53](结果、样本与最终选择/U53-get_result%20与%20write_job_manifest%20对齐最终物理尝试.md#u53) |
| `dressage/integrations/harbor/compat.py` | 读取包版本及私有 Job 成员，维持 Trial 排列和对象配对。 [U02](启动与配置/U02-require_harbor_runtime%20读取并检查发行包版本.md#u02) · [U11](Job%20与%20Agent%20路由/U11-Job._resolve_task_configs%20展开任务来源.md#u11) · [U15](Job%20与%20Agent%20路由/U15-Job._task_configs%20提供已经解析的任务对象.md#u15) · [U16](Job%20与%20Agent%20路由/U16-Job._remaining_trial_configs%20提供待执行配置.md#u16) · [U17](Job%20与%20Agent%20路由/U17-build_trial_plan%20配对原对象并写回%20trial_name.md#u17) · [U20](Job%20与%20Agent%20路由/U20-复制%20AgentConfig%20时保留并发分组.md#u20) |
| `dressage/integrations/harbor/config.py` | Dressage 的集成 profile 模型，配置由 Job 启动及插件消费。 [U13](Job%20与%20Agent%20路由/U13-EnvironmentFactory%20按%20import_path%20选择具体后端.md#u13) · [U19](Job%20与%20Agent%20路由/U19-JobPlugin.on_job_start%20接收%20Job%20并登记路由与回调.md#u19) · [U21](Job%20与%20Agent%20路由/U21-注入%20AgentConfig.env%20并设置%20extra_allowed_hosts.md#u21) |
| `dressage/integrations/harbor/data_source.py` | 读取 Harbor JobConfig、展开输入、登记和恢复数据源。 [U06](启动与配置/U06-JobConfig.model_validate%20读取随仓%20Job%20YAML.md#u06) · [U09](启动与配置/U09-model_copy%20与%20model_dump%20建立题目及%20Agent%20注册表.md#u09) · [U10](启动与配置/U10-Job%20配置摘要写入%20checkpoint%20并在%20load%20时比较.md#u10) · [U11](Job%20与%20Agent%20路由/U11-Job._resolve_task_configs%20展开任务来源.md#u11) |
| `dressage/integrations/harbor/environment.py` | Harbor 反向调用的 bwrap 后端。 [U31](环境构造与生命周期/U31-DressageEnvironment.__init__%20接收%20Trial%20的环境参数.md#u31) · [U34](环境构造与生命周期/U34-EnvironmentFactory%20调用%20DressageEnvironment.preflight.md#u34) · [U39](环境执行、文件与挂载/U39-upload_file%20把一个宿主文件交给环境.md#u39) · [U43](环境执行、文件与挂载/U43-exec%20返回%20Harbor%20的%20ExecResult.md#u43) · [U44](环境执行、文件与挂载/U44-Trial%20回收前查询挂载是否与宿主目录对应.md#u44) |
| `dressage/integrations/harbor/gateway.py` | Gateway 在启动处复用版本检查，运行时流量与插件注入关联。 [U02](启动与配置/U02-require_harbor_runtime%20读取并检查发行包版本.md#u02) · [U21](Job%20与%20Agent%20路由/U21-注入%20AgentConfig.env%20并设置%20extra_allowed_hosts.md#u21) |
| `dressage/integrations/harbor/plugin.py` | 消费 Job 和事件、注入 Agent 配置、交回最终结果。 [U19](Job%20与%20Agent%20路由/U19-JobPlugin.on_job_start%20接收%20Job%20并登记路由与回调.md#u19) · [U21](Job%20与%20Agent%20路由/U21-注入%20AgentConfig.env%20并设置%20extra_allowed_hosts.md#u21) · [U23](Trial%20事件与目录/U23-Job.on_trial_started%20登记%20START.md#u23) · [U28](Trial%20事件与目录/U28-Job.on_trial_ended%20登记%20END.md#u28) · [U29](Trial%20事件与目录/U29-TrialHookEvent%20的物理%20ID、结果对象与输出目录.md#u29) · [U52](结果、样本与最终选择/U52-JobPlugin.on_job_end%20从%20JobResult%20提取最终尝试.md#u52) |
| `dressage/integrations/harbor/rollout.py` | 创建 Job 与分区，取得最终结果并产出样本。 [U12](Job%20与%20Agent%20路由/U12-model_validate%20重建每个分区的临时%20JobConfig.md#u12) · [U14](Job%20与%20Agent%20路由/U14-Job.create%20在插件设置路由前创建%20Job.md#u14) · [U22](Job%20与%20Agent%20路由/U22-Job.run%20将本次%20Job%20的最终结果交给插件与分区.md#u22) · [U53](结果、样本与最终选择/U53-get_result%20与%20write_job_manifest%20对齐最终物理尝试.md#u53) · [U55](结果、样本与最终选择/U55-generate_rollout_harbor_sync%20返回训练数据.md#u55) · [U56](结果、样本与最终选择/U56-_eval_output%20返回按轨迹计数的评测结果.md#u56) |
| `dressage/proxy/__init__.py` | 源码注释提到 Harbor，此处没有跨项目调用。 |
| `dressage/rollout/log_rollout.py` | 下游日志消费已转换样本的元数据。 [U54](结果、样本与最终选择/U54-_bundle_samples%20将一次尝试的分段奖励送入训练样本.md#u54) · [U56](结果、样本与最终选择/U56-_eval_output%20返回按轨迹计数的评测结果.md#u56) |
| `examples/harbor/dataset_tools/dapo/prepare_dataset.py` | 生成题目和 verifier 并独立检查包版本。 [U03](启动与配置/U03-DAPO%20命令的%20check_runtime%20读取同一包版本.md#u03) · [U13](Job%20与%20Agent%20路由/U13-EnvironmentFactory%20按%20import_path%20选择具体后端.md#u13) · [U57](题目文件与可选后端/U57-Harbor%20Task%20读取%20Dressage%20生成的题目目录.md#u57) · [U58](题目文件与可选后端/U58-Harbor%20Verifier%20读取运行产生的%20reward.json.md#u58) |
| `examples/harbor/dressage_profiles/rollout-bwrap.yaml` | rollout 的 bwrap profile。 [U13](Job%20与%20Agent%20路由/U13-EnvironmentFactory%20按%20import_path%20选择具体后端.md#u13) · [U31](环境构造与生命周期/U31-DressageEnvironment.__init__%20接收%20Trial%20的环境参数.md#u31) |
| `examples/harbor/dressage_profiles/rollout-native-local.yaml` | rollout 的 native 本地 profile。 [U13](Job%20与%20Agent%20路由/U13-EnvironmentFactory%20按%20import_path%20选择具体后端.md#u13) · [U19](Job%20与%20Agent%20路由/U19-JobPlugin.on_job_start%20接收%20Job%20并登记路由与回调.md#u19) |
| `examples/harbor/dressage_profiles/rollout-native-remote.yaml` | rollout 的 native 远端 profile。 [U13](Job%20与%20Agent%20路由/U13-EnvironmentFactory%20按%20import_path%20选择具体后端.md#u13) · [U60](题目文件与可选后端/U60-native%20配置把模板和资源交给%20E2B%20启动沙箱.md#u60) · [U61](题目文件与可选后端/U61-E2B%20沙箱超时、续租和停止.md#u61) |
| `examples/harbor/dressage_profiles/training-bwrap.yaml` | 训练的 bwrap profile。 [U05](启动与配置/U05-Slime%20按两个加载路径启动%20Dressage%20的训练入口.md#u05) · [U13](Job%20与%20Agent%20路由/U13-EnvironmentFactory%20按%20import_path%20选择具体后端.md#u13) · [U31](环境构造与生命周期/U31-DressageEnvironment.__init__%20接收%20Trial%20的环境参数.md#u31) |
| `examples/harbor/dressage_profiles/training-native-local.yaml` | 训练的 native 本地 profile。 [U05](启动与配置/U05-Slime%20按两个加载路径启动%20Dressage%20的训练入口.md#u05) · [U13](Job%20与%20Agent%20路由/U13-EnvironmentFactory%20按%20import_path%20选择具体后端.md#u13) |
| `examples/harbor/dressage_profiles/training-native-remote.yaml` | 训练的 native 远端 profile。 [U05](启动与配置/U05-Slime%20按两个加载路径启动%20Dressage%20的训练入口.md#u05) · [U13](Job%20与%20Agent%20路由/U13-EnvironmentFactory%20按%20import_path%20选择具体后端.md#u13) · [U60](题目文件与可选后端/U60-native%20配置把模板和资源交给%20E2B%20启动沙箱.md#u60) · [U61](题目文件与可选后端/U61-E2B%20沙箱超时、续租和停止.md#u61) |
| `examples/harbor/harbor_job_configs/tau3-bench-e2b.yaml` | 随仓 τ³ Job YAML 的配置解析和 E2B 后端选择。 [U06](启动与配置/U06-JobConfig.model_validate%20读取随仓%20Job%20YAML.md#u06) · [U60](题目文件与可选后端/U60-native%20配置把模板和资源交给%20E2B%20启动沙箱.md#u60) · [U61](题目文件与可选后端/U61-E2B%20沙箱超时、续租和停止.md#u61) |
| `examples/harbor/harbor_job_configs/terminal-bench-2-e2b.yaml` | 随仓 Terminal-Bench Job YAML 的配置解析和 E2B 后端选择。 [U06](启动与配置/U06-JobConfig.model_validate%20读取随仓%20Job%20YAML.md#u06) · [U60](题目文件与可选后端/U60-native%20配置把模板和资源交给%20E2B%20启动沙箱.md#u60) · [U61](题目文件与可选后端/U61-E2B%20沙箱超时、续租和停止.md#u61) |
| `examples/harbor/run_harbor_rollout_qwen3.5_4b.sh` | 运行 Harbor CLI 并挂接 Dressage 插件。 [U04](启动与配置/U04-harbor%20run%20发现并挂接%20--plugin%20dressage.md#u04) |
| `examples/harbor/run_harbor_training_qwen3.5_4b.sh` | 给 Slime 的两个入口加载路径。 [U05](启动与配置/U05-Slime%20按两个加载路径启动%20Dressage%20的训练入口.md#u05) |
| `pyproject.toml` | Harbor 版本依赖及插件 entry point。 [U01](启动与配置/U01-安装%20Dressage%20的%20Harbor%20extra.md#u01) · [U04](启动与配置/U04-harbor%20run%20发现并挂接%20--plugin%20dressage.md#u04) |
| `tests/integrations/harbor/conftest.py` | 测试共用的替身、构造器和样本输入。 [U19](Job%20与%20Agent%20路由/U19-JobPlugin.on_job_start%20接收%20Job%20并登记路由与回调.md#u19) · [U29](Trial%20事件与目录/U29-TrialHookEvent%20的物理%20ID、结果对象与输出目录.md#u29) · [U54](结果、样本与最终选择/U54-_bundle_samples%20将一次尝试的分段奖励送入训练样本.md#u54) |
| `tests/integrations/harbor/test_contracts.py` | 配置及版本契约测试。 [U02](启动与配置/U02-require_harbor_runtime%20读取并检查发行包版本.md#u02) · [U06](启动与配置/U06-JobConfig.model_validate%20读取随仓%20Job%20YAML.md#u06) |
| `tests/integrations/harbor/test_data_path.py` | 数据源、题目、奖励与样本交接的测试。 [U10](启动与配置/U10-Job%20配置摘要写入%20checkpoint%20并在%20load%20时比较.md#u10) · [U49](结果、样本与最终选择/U49-从%20verifier_result%20或末尾%20step%20选择目标奖励.md#u49) · [U53](结果、样本与最终选择/U53-get_result%20与%20write_job_manifest%20对齐最终物理尝试.md#u53) · [U58](题目文件与可选后端/U58-Harbor%20Verifier%20读取运行产生的%20reward.json.md#u58) |
| `tests/integrations/harbor/test_environment.py` | 后端、文件交接、挂载与进程结果的测试。 [U31](环境构造与生命周期/U31-DressageEnvironment.__init__%20接收%20Trial%20的环境参数.md#u31) · [U39](环境执行、文件与挂载/U39-upload_file%20把一个宿主文件交给环境.md#u39) · [U41](环境执行、文件与挂载/U41-download_file%20把一个环境文件交回宿主.md#u41) · [U43](环境执行、文件与挂载/U43-exec%20返回%20Harbor%20的%20ExecResult.md#u43) · [U44](环境执行、文件与挂载/U44-Trial%20回收前查询挂载是否与宿主目录对应.md#u44) |
| `tests/integrations/harbor/test_execution.py` | 插件生命周期及网关行为的夹具测试。 [U19](Job%20与%20Agent%20路由/U19-JobPlugin.on_job_start%20接收%20Job%20并登记路由与回调.md#u19) · [U21](Job%20与%20Agent%20路由/U21-注入%20AgentConfig.env%20并设置%20extra_allowed_hosts.md#u21) · [U27](Trial%20事件与目录/U27-Job.on_trial_cancelled%20登记%20CANCEL.md#u27) · [U28](Trial%20事件与目录/U28-Job.on_trial_ended%20登记%20END.md#u28) · [U52](结果、样本与最终选择/U52-JobPlugin.on_job_end%20从%20JobResult%20提取最终尝试.md#u52) |
| `tests/integrations/harbor/test_gated_e2e.py` | 需显式启用的端到端测试。默认套件排除这组。 [U04](启动与配置/U04-harbor%20run%20发现并挂接%20--plugin%20dressage.md#u04) · [U22](Job%20与%20Agent%20路由/U22-Job.run%20将本次%20Job%20的最终结果交给插件与分区.md#u22) · [U53](结果、样本与最终选择/U53-get_result%20与%20write_job_manifest%20对齐最终物理尝试.md#u53) |
| `tests/test_log_rollout_data.py` | 样本夹具的 `parent_traj_id` 字符串包含 harbor，测试下游输出。 [U54](结果、样本与最终选择/U54-_bundle_samples%20将一次尝试的分段奖励送入训练样本.md#u54) |
| `tests/test_proxy_client.py` | HTTP 测试将 `harbor` 用作 X-Client 的示例值，没有调用 Harbor API。 |

<a id="follow-up"></a>

## 沿调用链补查的入口

比对源码行数之外，还要沿实际交付物寻找另一端。这些入口的三版位置随用法表维护。接手时可以直接打开相应证据。

| 从哪里发现 | 追到哪一方 | 三版用法 |
| --- | --- | --- |
| Dressage 在 END 读 Trial 目录并将 bundle 存在目录外 | Harbor 在哪个时点清理、脱敏并发出 END | [U30 Trial 目录](Trial%20事件与目录/U30-END%20前后的%20Trial%20目录及外部%20bundle%20路径.md#u30) |
| Dressage 的 DAPO 工具写题目目录与 verifier 脚本 | Harbor 的 Task 读题目，Verifier 读脚本写出的 reward.json | [U57 题目](题目文件与可选后端/U57-Harbor%20Task%20读取%20Dressage%20生成的题目目录.md#u57) · [U58 分数](题目文件与可选后端/U58-Harbor%20Verifier%20读取运行产生的%20reward.json.md#u58) |
| Job 配置选择 E2B，Dressage profile 选择 native | Harbor 使用的模板键、超时、续租和停止行为 | [U60 模板](题目文件与可选后端/U60-native%20配置把模板和资源交给%20E2B%20启动沙箱.md#u60) · [U61 续租](题目文件与可选后端/U61-E2B%20沙箱超时、续租和停止.md#u61) |

第二轮在上述源码边界内改变输入，并读到下游的题目身份、请求启动环境、重试次数、实际文件与游标。原 191 个扫描位置保留同一分母；新增问题 21–24 关联已有用法。每个新判断的证据入口见[0.26 复查](../investigations/upgrade-audit-026.md)。
