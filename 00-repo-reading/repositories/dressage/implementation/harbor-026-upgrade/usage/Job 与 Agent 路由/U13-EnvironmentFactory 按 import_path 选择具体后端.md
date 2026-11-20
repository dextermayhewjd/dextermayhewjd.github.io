# U13 · EnvironmentFactory 按 import_path 选择具体后端

<a id="u13"></a>

[Job 与 Agent 路由目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[rollout.py 54](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L54)

```python
"dressage.integrations.harbor.environment:DressageEnvironment"
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor trial.py 1490–1499](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L1490-L1499) | 在 Trial 建环境时看 `config.environment.import_path`、题目目录和 `session_id`。 |
| ② 结果　[Harbor factory.py 401–409](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/factory.py#L401-L409) · [Harbor trial.py 1513–1515](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L1513-L1515) | 走过工厂的返回，核对 `type(trial.agent_environment)` 和 `context_id`，再看后续 start 是否用这个实例。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/factory.py#L297-L365) | bwrap 时传 `type=None` 与 `DressageEnvironment` 的模块路径。native 使用源 Job 环境设置 | 实测接受 bwrap 的 import path。native 配置以源码核对 | 工厂交回具体环境实例。实例随后接收 Trial 的 start、文件操作与 stop | 实测 `Trial.create` 得到 bwrap 实例，随后能 start 和进入日志回收。完整 Job 与 native 后端待测。 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/factory.py#L363-L437) | bwrap 时传 `type=None` 与 `DressageEnvironment` 的模块路径。native 使用源 Job 环境设置 | 实测接受 bwrap 的 import path。native 配置以源码核对 | 工厂交回具体环境实例。实例随后接收 Trial 的 start、文件操作与 stop | 实测 `Trial.create` 得到 bwrap 实例，随后能 start 和进入日志回收。完整 Job 与 native 后端待测。 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/factory.py#L413-L490) | bwrap 时传 `type=None` 与 `DressageEnvironment` 的模块路径。native 使用源 Job 环境设置 | 实测接受 bwrap 的 import path。native 配置以源码核对 | 工厂交回具体环境实例。实例随后接收 Trial 的 start、文件操作与 stop | 实测 `Trial.create` 得到 bwrap 实例，随后能 start 和进入日志回收。完整 Job 与 native 后端待测。 |

**接续**　分别追一题的 bwrap 与声明支持的 native 路径。U34 是独立的启动前预检。 [rollout.py 567-574](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L567-L574) · [prepare_dataset.py 363](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dataset_tools/dapo/prepare_dataset.py#L363) · [两份 YAML 和三版字段](../../investigations/18-example-configs/job-config-output.txt) · [问题 01](../../investigations/01-environment-preflight/README.md) · [问题 03](../../investigations/03-verifier-fixture/README.md) · [问题 16](../../investigations/16-e2b-template/README.md) · [原 Trial 三版回放](../../investigations/02-output-mounts/trial-log-recovery.txt) · [回放代码](../../investigations/02-output-mounts/trial_log_recovery.py)
