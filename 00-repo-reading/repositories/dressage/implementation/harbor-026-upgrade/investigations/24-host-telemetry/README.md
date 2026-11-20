# 24 · 本地运行 Harbor 时，宿主会向哪里提交遥测？

**当前判断**　从 0.18 升到 0.26 后，本地 CLI 默认在命令结束时准备一条发往 PostHog 的事件。程序直接调用 `Job.run` 也有独立的 Job 结束事件。需要离线运行时，在启动 Harbor 的宿主进程设置 `HARBOR_TELEMETRY=0`。Trial 网络策略约束的是沙箱，宿主的发送进程有单独的开关。[关闭条件](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/telemetry.py#L479-L480)

**对应的三版用法表**　[U04 随仓 CLI](../../usage/启动与配置/U04-harbor%20run%20发现并挂接%20--plugin%20dressage.md#u04) · [U22 执行 Job](../../usage/Job%20与%20Agent%20路由/U22-Job.run%20将本次%20Job%20的最终结果交给插件与分区.md#u22) · [原套件覆盖](../original-test-audit.md#i24)

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　示例脚本用 `harbor run --config … --plugin dressage --yes` 发起本地 Job。训练分区从 Python 直接调用 `job.run()`。[CLI 脚本](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/run_harbor_rollout_qwen3.5_4b.sh#L109-L112) · [训练分区](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L759-L762)

**Harbor 0.18.0**　CLI 顶层回调为空，该版本没有 `harbor.telemetry` 模块。[CLI 注册](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/cli/main.py#L43-L49)

**Harbor 0.26.0**　CLI 在命令关闭时生成 `harbor.command_finished`，把已知的命令选项名称写入事件。发送函数从允许的字段构造事件并交给独立 Python 进程向 `us.i.posthog.com` 发 POST。该路径与向 Harbor Hub 发布 Job 的 `--upload` 分开触发，`--yes` 也不控制遥测。[CLI 回调与参数](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/cli/main.py#L63-L91) · [发送地址和正文](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/telemetry.py#L395-L435) · [Hub 开关的默认值](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/cli/jobs.py#L1343-L1367)

**Harbor 0.26.0**　Job 写出最终结果后调度另一条事件。[job.py 第 1226 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L1226)

```python
capture_job_finished_async(self, self._job_result)
```

若运行抛出异常，已经建立 `JobResult` 且还没有结束时间时，也调度该事件。Job 事件定义包括 Job ID、Agent 和模型名称、并发数、结果状态、token 统计和平均 reward。此分支按源码核对，下面的 CLI 实验在建立 Job 前返回。[异常分支](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L1229-L1237) · [Job 事件字段](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/telemetry.py#L82-L160) · [Job 上报开关](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/telemetry.py#L334-L354)

<a id="evidence"></a>

## 证据与验证范围

在真实 CLI 的随仓命令后追加 `--print-config`，使用两份原版 E2B YAML。0.18 的两个输入都完成渲染。0.25、0.26 分别用未设置和取值为 `0` 的开关运行：默认情况下两份配置都构造了命令事件，指向 `us.i.posthog.com`；关闭后没有进入发送入口。探测给安装 ID 提供固定占位值，并以记录函数取代 `_spawn_sender`。记录到的是发包前的目标和载荷，没有创建发送进程、访问 PostHog 或请求 E2B。[探测脚本](cli_telemetry_probe.py) · [三版、两份配置的全部输出](cli-telemetry-output.txt)

**0.26 实测**　以同一份 τ³-bench 配置对照开关。[cli-telemetry-output.txt 第 9–10 行](cli-telemetry-output.txt#L9-L10)

```text
0.26.0 tau3-bench-e2b.yaml setting=unset event=harbor.command_finished host=us.i.posthog.com flags=--config,--plugin,--yes,--print-config
0.26.0 tau3-bench-e2b.yaml setting=0 event=none host=none flags=none
```

## 处理与验收

保留 Harbor 提供的宿主开关。复现命令为 `python cli_telemetry_probe.py <Dressage checkout>`，从本目录在装有相应版本 Harbor 的 Python 3.12 环境运行。离线 CLI 验收可在发送入口断言没有事件，若还需验证训练分区，则单独观察真实 `Job.run` 的完成和异常路径。[探测脚本](cli_telemetry_probe.py)

[返回问题索引](../../README.md#investigations)
