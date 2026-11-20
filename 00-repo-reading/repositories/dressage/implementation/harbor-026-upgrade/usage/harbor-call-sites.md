# Dressage 调用 Harbor 的逐处源码索引

固定 Dressage `3e3142f` 和 Harbor `3cb6273`。由 [扫描脚本](../tools/scan_harbor_surface.py) 从 Git 对象生成。接手审核时先看[交付物与验收表](../archive/integration-inventory.md#coverage)，在这里回查具体代码。

遍历 341 个跟踪文件，其中 238 个 Python 文件，生产包内 137 个。独立子模块 slime 按 Git 引用记录。

<a id="imports"></a>

## 1. 直接导入、包版本及动态导入

直接导入 12 句，分布在 8 个文件。另有 3 处读取 Harbor 发行包版本，找到 0 处以 Harbor 模块名字符串直接调用 import_module 或 __import__。

| 文件与行 | 源码原行 |
| --- | --- |
| [dressage/integrations/harbor/compat.py:52](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L52) | `harbor_version = importlib.metadata.version("harbor")` |
| [dressage/integrations/harbor/compat.py:105](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L105) | `from harbor.job import Job` |
| [dressage/integrations/harbor/data_source.py:538](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L538) | `from harbor.models.job.config import JobConfig` |
| [dressage/integrations/harbor/environment.py:23](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L23) | `from harbor.environments.base import BaseEnvironment, ExecResult` |
| [dressage/integrations/harbor/environment.py:24](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L24) | `from harbor.environments.capabilities import EnvironmentCapabilities` |
| [dressage/integrations/harbor/environment.py:25](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L25) | `from harbor.models.task.config import NetworkMode, NetworkPolicy, TaskOS` |
| [dressage/integrations/harbor/plugin.py:1134](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1134) | `from harbor.models.task.config import TaskConfig` |
| [dressage/integrations/harbor/rollout.py:105](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L105) | `from harbor.job import Job` |
| [examples/harbor/dataset_tools/dapo/prepare_dataset.py:553](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dataset_tools/dapo/prepare_dataset.py#L553) | `version = importlib.metadata.version("harbor")` |
| [tests/integrations/harbor/test_contracts.py:167](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_contracts.py#L167) | `from harbor.models.job.config import JobConfig` |
| [tests/integrations/harbor/test_contracts.py:169](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_contracts.py#L169) | `assert importlib.metadata.version("harbor") == "0.18.0"` |
| [tests/integrations/harbor/test_environment.py:13](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L13) | `from harbor.models.task.config import EnvironmentConfig, NetworkMode, NetworkPolicy` |
| [tests/integrations/harbor/test_environment.py:14](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L14) | `from harbor.models.trial.paths import TrialPaths` |
| [tests/integrations/harbor/test_gated_e2e.py:64](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_gated_e2e.py#L64) | `from harbor.models.job.config import JobConfig` |
| [tests/integrations/harbor/test_gated_e2e.py:65](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_gated_e2e.py#L65) | `from harbor.models.job.result import JobResult` |

### 通过配置字符串和 CLI 进入的源码原行

| 文件与行 | 源码原行 |
| --- | --- |
| [dressage/integrations/harbor/rollout.py:54](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L54) | `"dressage.integrations.harbor.environment:DressageEnvironment"` |
| [examples/harbor/dataset_tools/dapo/prepare_dataset.py:363](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dataset_tools/dapo/prepare_dataset.py#L363) | `"dressage.integrations.harbor.environment:DressageEnvironment"` |
| [examples/harbor/run_harbor_rollout_qwen3.5_4b.sh:109](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/run_harbor_rollout_qwen3.5_4b.sh#L109) | `harbor run \` |
| [examples/harbor/run_harbor_rollout_qwen3.5_4b.sh:111](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/run_harbor_rollout_qwen3.5_4b.sh#L111) | `--plugin dressage \` |
| [examples/harbor/run_harbor_training_qwen3.5_4b.sh:66](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/run_harbor_training_qwen3.5_4b.sh#L66) | `--data-source-path dressage.integrations.harbor.data_source.HarborDataSource` |
| [examples/harbor/run_harbor_training_qwen3.5_4b.sh:67](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/run_harbor_training_qwen3.5_4b.sh#L67) | `--rollout-function-path dressage.integrations.harbor.rollout.generate_rollout_harbor_sync` |
| [pyproject.toml:26](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/pyproject.toml#L26) | `[project.entry-points."harbor.plugins"]` |
| [pyproject.toml:27](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/pyproject.toml#L27) | `dressage = "dressage.integrations.harbor.plugin:DressageHarborPlugin"` |

<a id="overrides"></a>

## 2. Harbor 可调用的后端实现

对两个固定版本的类定义按同名方法逐个比对，得到 13 项。打开两边同行能查签名和返回值。

| 实现 | Dressage | Harbor 基类 |
| --- | --- | --- |
| `__init__` | [实现 262](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L262) | [基类 200](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L200) |
| `type` | [实现 289](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L289) | [基类 926](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L926) |
| `capabilities` | [实现 293](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L293) | [基类 968](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L968) |
| `preflight` | [实现 302](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L302) | [基类 1144](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1144) |
| `_validate_definition` | [实现 355](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L355) | [基类 1001](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1001) |
| `validate_network_policy_support` | [实现 373](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L373) | [基类 1040](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1040) |
| `start` | [实现 383](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L383) | [基类 1176](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1176) |
| `stop` | [实现 424](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L424) | [基类 1180](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1180) |
| `upload_file` | [实现 437](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L437) | [基类 1192](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1192) |
| `upload_dir` | [实现 445](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L445) | [基类 1202](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1202) |
| `download_file` | [实现 459](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L459) | [基类 1212](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1212) |
| `download_dir` | [实现 467](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L467) | [基类 1222](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1222) |
| `exec` | [实现 481](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L481) | [基类 1437](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1437) |

<a id="members"></a>

## 3. 配置、回调、对象字段和间接调用的位置

按已追踪的接收对象、getattr 等字段访问和已确认的间接入口找候选行。同一行只列一次，行号打开原文。通用变量名可能同时命中本仓库对象，变量别名和动态键还要结合交付物表里的完整函数判断。这部分适合查漏，行数不代表接口数量。

### `dressage/integrations/harbor/artifacts.py`

| 原行 | 位置 |
| --- | --- |
| `task_name=_string_attr(trial_result, "task_name"),` | [第 453 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L453) |
| `task_checksum=_string_attr(trial_result, "task_checksum"),` | [第 454 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L454) |
| `agent_name=_nested_string_attr(trial_result, "agent_info", "name"),` | [第 455 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L455) |
| `started_at=_datetime_attr(trial_result, "started_at"),` | [第 470 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L470) |
| `finished_at=_datetime_attr(trial_result, "finished_at"),` | [第 471 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L471) |
| `job_id = _string_attr(job_result, "id") or _job_id_from_keys(self._bundles, keys)` | [第 553 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L553) |
| `verifier_result = getattr(result, "verifier_result", None)` | [第 1057 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1057) |
| `rewards = getattr(verifier_result, "rewards", None)` | [第 1058 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1058) |
| `for step in reversed(getattr(result, "step_results", None) or []):` | [第 1060 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1060) |
| `step_verifier = getattr(step, "verifier_result", None)` | [第 1061 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1061) |
| `rewards = getattr(step_verifier, "rewards", None)` | [第 1062 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1062) |
| `top = getattr(result, "exception_info", None)` | [第 1074 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1074) |
| `for step in getattr(result, "step_results", None) or []:` | [第 1077 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1077) |
| `exception_info = getattr(step, "exception_info", None)` | [第 1078 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1078) |
| `step_name=_string_attr(step, "step_name"),` | [第 1083 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1083) |
| `exception_type = _string_attr(info, "exception_type") or "HarborException"` | [第 1090 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1090) |
| `message = _string_attr(info, "exception_message") or exception_type` | [第 1091 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1091) |
| `result.append(failure)` | [第 1129 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1129) |

### `dressage/integrations/harbor/compat.py`

| 原行 | 位置 |
| --- | --- |
| `if not hasattr(job, "_remaining_trial_configs"):` | [第 71 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L71) |
| `configs = job._remaining_trial_configs` | [第 75 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L75) |
| `not hasattr(config, "trial_name")` | [第 82 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L82) |
| `or not hasattr(config, "agent")` | [第 83 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L83) |
| `or not hasattr(config, "task")` | [第 84 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L84) |
| `if not hasattr(job, "_task_configs") or not isinstance(job._task_configs, list):` | [第 93 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L93) |
| `return tuple(job._task_configs)` | [第 97 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L97) |
| `resolver = getattr(Job, "_resolve_task_configs", None)` | [第 108 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L108) |
| `configs = await resolver(job_config)` | [第 113 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L113) |
| `if getattr(job, "is_resuming", False):` | [第 124 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L124) |
| `job_config = getattr(job, "config", None)` | [第 130 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L130) |
| `agents = getattr(job_config, "agents", None)` | [第 131 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L131) |
| `attempts = getattr(job_config, "n_attempts", None)` | [第 132 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L132) |
| `if config.task is not tasks[task_index]:` | [第 158 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L158) |
| `if config.agent is not agents[agent_index]:` | [第 162 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L162) |
| `trial_name = str(config.trial_name)` | [第 166 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L166) |
| `entry.config.trial_name = name` | [第 199 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L199) |
| `n_concurrent = getattr(agent, "n_concurrent", None)` | [第 206 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L206) |
| `existing = getattr(agent, "concurrency_group", None)` | [第 209 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L209) |
| `concurrency_key = getattr(agent, "concurrency_key", None)` | [第 212 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L212) |
| `dump = getattr(agent, "model_dump", None)` | [第 216 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L216) |

### `dressage/integrations/harbor/data_source.py`

| 原行 | 位置 |
| --- | --- |
| `self.job_config = _load_job_config(job_source, job_config_type)` | [第 182 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L182) |
| `tasks = _resolve_tasks(self.job_config)` | [第 183 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L183) |
| `agents=getattr(self.job_config, "agents", None),` | [第 186 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L186) |
| `self.eval_job_config: Any \| None = None` | [第 201 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L201) |
| `self.eval_job_config = _load_job_config(eval_source, job_config_type)` | [第 204 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L204) |
| `eval_tasks = _resolve_tasks(self.eval_job_config)` | [第 205 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L205) |
| `agents=getattr(self.eval_job_config, "agents", None),` | [第 208 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L208) |
| `self.job_config,` | [第 237 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L237) |
| `self.eval_job_config,` | [第 245 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L245) |
| `if self.eval_job_config is not None` | [第 250 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L250) |
| `copier = getattr(source, "model_copy", None)` | [第 564 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L564) |
| `return job_config_type.model_validate(dict(payload))` | [第 603 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L603) |
| `task_runtime = _dump_model(task, reveal_sensitive=True)` | [第 683 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L683) |
| `agent_runtime = _dump_model(agent, reveal_sensitive=True)` | [第 687 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L687) |
| `task_config=_deepcopy_model(task),` | [第 712 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L712) |
| `agent_config=_deepcopy_model(agent),` | [第 713 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L713) |
| `"job": _redact_public(_dump_model(job_config, reveal_sensitive=True)),` | [第 832 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L832) |

### `dressage/integrations/harbor/environment.py`

| 原行 | 位置 |
| --- | --- |
| `super().__init__(*args, **kwargs)` | [第 282 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L282) |
| `self.session_id, self._mounts` | [第 285 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L285) |
| `return EnvironmentCapabilities(` | [第 294 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L294) |
| `if self.task_env_config.os != TaskOS.LINUX:` | [第 356 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L356) |
| `if self.task_env_config.docker_image:` | [第 358 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L358) |
| `if (self.environment_dir / filename).exists():` | [第 361 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L361) |
| `workdir = _environment_path(self.task_env_config.workdir or "/app")` | [第 363 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L363) |
| `policy = network_policy or self.network_policy` | [第 376 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L376) |
| `super().validate_network_policy_support(policy)` | [第 377 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L377) |
| `if policy.network_mode == NetworkMode.ALLOWLIST and policy.allowed_hosts != [` | [第 378 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L378) |
| `workdir=self.task_env_config.workdir or "/app",` | [第 395 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L395) |
| `if not self.environment_dir.is_dir():` | [第 410 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L410) |
| `raise NotADirectoryError(self.environment_dir)` | [第 411 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L411) |
| `self.environment_dir,` | [第 414 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L414) |
| `effective_user = self._resolve_user(user)` | [第 491 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L491) |
| `cwd=cwd or self.task_env_config.workdir or "/app",` | [第 497 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L497) |
| `process_env.update(self._merge_env(env) or {})` | [第 500 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L500) |
| `callback = self._output_callback()` | [第 525 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L525) |
| `return ExecResult(` | [第 531 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L531) |
| `for mount in self._mounts:` | [第 539 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L539) |
| `if self.network_policy.network_mode != NetworkMode.PUBLIC:` | [第 601 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L601) |
| `if self.network_policy.network_mode == NetworkMode.ALLOWLIST:` | [第 633 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L633) |
| `if self.network_policy.network_mode != NetworkMode.ALLOWLIST:` | [第 651 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L651) |

### `dressage/integrations/harbor/plugin.py`

| 原行 | 位置 |
| --- | --- |
| `if bool(getattr(job, "is_resuming", False)):` | [第 266 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L266) |
| `self._job_id = str(getattr(job, "id"))` | [第 269 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L269) |
| `pending_names = {str(getattr(item, "trial_name")) for item in pending}` | [第 274 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L274) |
| `trial_name = str(getattr(trial_config, "trial_name"))` | [第 289 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L289) |
| `candidate_agent = getattr(trial_config, "agent")` | [第 290 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L290) |
| `task_dir = _existing_task_directory(getattr(trial_config, "task", None))` | [第 293 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L293) |
| `trial_name = str(getattr(trial_config, "trial_name"))` | [第 337 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L337) |
| `original_agent = getattr(trial_config, "agent")` | [第 344 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L344) |
| `getattr(original_agent, "concurrency_key", _stable_dump(original_agent))` | [第 346 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L346) |
| `agent = _deep_copy_model(original_agent)` | [第 348 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L348) |
| `getattr(agent, "n_concurrent", None) is not None` | [第 350 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L350) |
| `and getattr(agent, "concurrency_group", None) is None` | [第 351 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L351) |
| `agent.concurrency_group = (` | [第 353 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L353) |
| `task_fingerprint = _stable_dump(getattr(trial_config, "task", None))` | [第 359 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L359) |
| `trial_config.agent = agent` | [第 385 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L385) |
| `job.on_trial_started(self._safe(self._on_start, "START"))` | [第 407 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L407) |
| `job.on_agent_started(self._safe(self._on_agent_start, "AGENT_START"))` | [第 408 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L408) |
| `job.on_agent_ended(self._safe(self._on_agent_end, "AGENT_END"))` | [第 409 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L409) |
| `job.on_verification_started(` | [第 410 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L410) |
| `job.on_trial_cancelled(self._safe(self._on_cancel, "CANCEL"))` | [第 413 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L413) |
| `job.on_trial_ended(self._safe(self._on_end, "END"))` | [第 414 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L414) |
| `(str(getattr(result, "trial_name")), str(getattr(result, "id")))` | [第 424 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L424) |
| `for result in (getattr(job_result, "trial_results", None) or [])` | [第 425 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L425) |
| `getattr(event, "trial_name", "unknown"),` | [第 616 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L616) |
| `getattr(event, "trial_id", "unknown"),` | [第 617 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L617) |
| `trial_result=getattr(event, "result", None),` | [第 778 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L778) |
| `env = dict(getattr(agent, "env", {}) or {})` | [第 1037 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1037) |
| `agent.env = env` | [第 1064 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1064) |
| `hosts = list(getattr(agent, "extra_allowed_hosts", None) or [])` | [第 1066 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1066) |
| `agent.extra_allowed_hosts = hosts` | [第 1074 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1074) |
| `getter = getattr(task_reference, "get_local_path", None)` | [第 1082 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1082) |
| `path = Path(getter()).expanduser().resolve()` | [第 1086 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1086) |
| `environment = getattr(task_config, "environment", None)` | [第 1100 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1100) |
| `baseline = _network_mode(getattr(environment, "network_mode", "public"))` | [第 1101 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1101) |
| `phases: list[tuple[str, Any]] = [("agent", getattr(task_config, "agent", None))]` | [第 1108 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1108) |
| `for step in getattr(task_config, "steps", None) or []:` | [第 1109 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1109) |
| `phases.append((f"steps.{getattr(step, 'name', '?')}.agent", getattr(step, "agent", None)))` | [第 1110 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1110) |
| `explicit = _network_mode(getattr(phase, "network_mode", None))` | [第 1112 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1112) |
| `task_config = TaskConfig.model_validate_toml(config_path.read_text(encoding="utf-8"))` | [第 1136 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1136) |
| `payload = task_config.model_dump(mode="json", exclude_none=False)` | [第 1141 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1141) |
| `name = str(getattr(agent, "name", None) or "")` | [第 1154 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1154) |
| `import_path = str(getattr(agent, "import_path", None) or "")` | [第 1155 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1155) |
| `env = dict(getattr(agent, "env", {}) or {})` | [第 1197 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1197) |
| `return str(getattr(event, "trial_name")), str(getattr(event, "trial_id"))` | [第 1240 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1240) |
| `config = getattr(event, "config", None)` | [第 1244 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1244) |
| `trials_dir = getattr(config, "trials_dir", None)` | [第 1245 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1245) |
| `return Path(trials_dir) / str(getattr(event, "trial_name"))` | [第 1248 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1248) |

### `dressage/integrations/harbor/rollout.py`

| 原行 | 位置 |
| --- | --- |
| `return await Job.create(config)` | [第 107 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L107) |
| `name: _copy_model(getattr(model, name))` | [第 435 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L435) |
| `clone = _copy_model(model)` | [第 441 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L441) |
| `name = getattr(task, "name", None)` | [第 448 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L448) |
| `path = getattr(task, "path", None)` | [第 451 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L451) |
| `package = getattr(task, "task", None)` | [第 454 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L454) |
| `name = getattr(package, "name", None)` | [第 455 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L455) |
| `metadata = getattr(task, "metadata", None)` | [第 458 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L458) |
| `if list(getattr(job_config, "datasets", None) or []):` | [第 473 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L473) |
| `for index, task in enumerate(getattr(job_config, "tasks", None) or []):` | [第 475 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L475) |
| `source = getattr(task, "source", None)` | [第 476 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L476) |
| `agent = _copy_model(partition[0].spec.agent_config)` | [第 519 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L519) |
| `agent = _validated_model_update(agent, n_concurrent=None)` | [第 548 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L548) |
| `_validated_model_update(` | [第 550 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L550) |
| `_copy_model(item.spec.task_config),` | [第 551 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L551) |
| `source_environment = getattr(source_job_config, "environment", None)` | [第 567 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L567) |
| `updates["environment"] = _validated_model_update(` | [第 570 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L570) |
| `return _validated_model_update(` | [第 575 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L575) |
| `job = await _CREATE_JOB(job_config)` | [第 704 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L704) |
| `await plugin.on_job_start(job)` | [第 760 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L760) |
| `result = await job.run()` | [第 761 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L761) |
| `await plugin.on_job_end(result)` | [第 762 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L762) |
| `str(item.trial_name): item for item in (result.trial_results or [])` | [第 765 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L765) |
| `bundle = plugin.get_result(trial_name, str(final_result.id))` | [第 802 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L802) |
| `f"{trial_name}/{final_result.id}"` | [第 806 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L806) |
| `converted = _bundle_samples(` | [第 813 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L813) |
| `return RolloutFnEvalOutput(data=data, metrics=metrics)` | [第 1254 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1254) |
| `return _eval_output(groups, metrics)` | [第 1274 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1274) |
| `return RolloutFnTrainOutput(samples=groups, metrics=metrics)` | [第 1277 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1277) |


<a id="files"></a>

## 4. 全仓出现 Harbor 字样的文件

按正文大小写无关匹配，共 33 个文件。此处也保留文档、注释、随仓配置和集成测试目录以外的命中，便于复核统计边界。

| 用途 | 文件 |
| --- | --- |
| 文档 | [README.md](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/README.md) |
| 文档 | [docs/harbor.md](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/docs/harbor.md) |
| 集成实现 | [dressage/integrations/harbor/__init__.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/__init__.py) |
| 集成实现 | [dressage/integrations/harbor/artifacts.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py) |
| 集成实现 | [dressage/integrations/harbor/compat.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py) |
| 集成实现 | [dressage/integrations/harbor/config.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/config.py) |
| 集成实现 | [dressage/integrations/harbor/data_source.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py) |
| 集成实现 | [dressage/integrations/harbor/environment.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py) |
| 集成实现 | [dressage/integrations/harbor/gateway.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/gateway.py) |
| 集成实现 | [dressage/integrations/harbor/plugin.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py) |
| 集成实现 | [dressage/integrations/harbor/rollout.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py) |
| 源码注释提及 Harbor | [dressage/proxy/__init__.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/__init__.py) |
| 消费已转换 Sample 的奖励元数据 | [dressage/rollout/log_rollout.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/log_rollout.py) |
| 配置、启动脚本或任务生成工具 | [examples/harbor/dataset_tools/dapo/prepare_dataset.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dataset_tools/dapo/prepare_dataset.py) |
| 配置、启动脚本或任务生成工具 | [examples/harbor/dressage_profiles/rollout-bwrap.yaml](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dressage_profiles/rollout-bwrap.yaml) |
| 配置、启动脚本或任务生成工具 | [examples/harbor/dressage_profiles/rollout-native-local.yaml](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dressage_profiles/rollout-native-local.yaml) |
| 配置、启动脚本或任务生成工具 | [examples/harbor/dressage_profiles/rollout-native-remote.yaml](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dressage_profiles/rollout-native-remote.yaml) |
| 配置、启动脚本或任务生成工具 | [examples/harbor/dressage_profiles/training-bwrap.yaml](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dressage_profiles/training-bwrap.yaml) |
| 配置、启动脚本或任务生成工具 | [examples/harbor/dressage_profiles/training-native-local.yaml](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dressage_profiles/training-native-local.yaml) |
| 配置、启动脚本或任务生成工具 | [examples/harbor/dressage_profiles/training-native-remote.yaml](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dressage_profiles/training-native-remote.yaml) |
| 配置、启动脚本或任务生成工具 | [examples/harbor/harbor_job_configs/tau3-bench-e2b.yaml](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/harbor_job_configs/tau3-bench-e2b.yaml) |
| 配置、启动脚本或任务生成工具 | [examples/harbor/harbor_job_configs/terminal-bench-2-e2b.yaml](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/harbor_job_configs/terminal-bench-2-e2b.yaml) |
| 配置、启动脚本或任务生成工具 | [examples/harbor/run_harbor_rollout_qwen3.5_4b.sh](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/run_harbor_rollout_qwen3.5_4b.sh) |
| 配置、启动脚本或任务生成工具 | [examples/harbor/run_harbor_training_qwen3.5_4b.sh](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/run_harbor_training_qwen3.5_4b.sh) |
| 包依赖及插件登记 | [pyproject.toml](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/pyproject.toml) |
| 测试或夹具 | [tests/integrations/harbor/conftest.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/conftest.py) |
| 测试或夹具 | [tests/integrations/harbor/test_contracts.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_contracts.py) |
| 测试或夹具 | [tests/integrations/harbor/test_data_path.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_data_path.py) |
| 测试或夹具 | [tests/integrations/harbor/test_environment.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py) |
| 测试或夹具 | [tests/integrations/harbor/test_execution.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_execution.py) |
| 测试或夹具 | [tests/integrations/harbor/test_gated_e2e.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_gated_e2e.py) |
| 测试或夹具 | [tests/test_log_rollout_data.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/test_log_rollout_data.py) |
| 测试或夹具 | [tests/test_proxy_client.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/test_proxy_client.py) |
