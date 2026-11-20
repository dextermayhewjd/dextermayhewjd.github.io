# 11 · 真实 Trial 正常结束或被取消时，插件何时提交并关闭路由？

**当前判断**　三版真实 Job 和 Trial 在夹具下发出正常 END 及取消后的 END。正常尝试由 Store 提交一次，已标记取消的尝试零次，两条路径的 route handle 均关闭一次。Gateway 使用记录对象，实际网络资源释放仍待联测。

**对应的三版用法表**　[U23 Job.on_trial_started 登记 START](../../usage/Trial%20事件与目录/U23-Job.on_trial_started%20登记%20START.md#u23) · [U27 Job.on_trial_cancelled 登记 CANCEL](../../usage/Trial%20事件与目录/U27-Job.on_trial_cancelled%20登记%20CANCEL.md#u27) · [U28 Job.on_trial_ended 登记 END](../../usage/Trial%20事件与目录/U28-Job.on_trial_ended%20登记%20END.md#u28) · [U29 TrialHookEvent 的物理 ID、结果对象与输出目录](../../usage/Trial%20事件与目录/U29-TrialHookEvent%20的物理%20ID、结果对象与输出目录.md#u29) · [原套件在本问题测到了哪里](../original-test-audit.md#i11)

同一份尝试的取消状态、产物提交和路由释放都依赖 Harbor 何时触发插件回调。

<a id="sources"></a>

## 两边的源码原文

**Harbor 0.26.0**　Trial 捕获取消后登记异常、发出 `CANCEL`，再恢复输出。[trial.py 第 619–622 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L619-L622)

```python
self._record_exception(exc)
await self._emit(TrialEvent.CANCEL)
await self._close_bridge()
await self._recover_outputs()
```

**Harbor 0.26.0**　收尾顺利时由 `_finalize` 发出 `END`。[trial.py 第 674–676 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L674-L676)

```python
# END hooks may upload trial files, so scrub them before hooks run.
self._scrub_jobs_dir()
await self._emit(TrialEvent.END)
```

**Dressage 3e3142f**　插件原注释说明取消后的 `END` 只负责收尾，此分支直接返回。[plugin.py 第 759–763 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L759-L763)

```python
if record.cancel_requested:
    # CANCEL is followed by END in Harbor.  END is still the sole
    # cleanup owner, but cancelled sessions are diagnostics-only
    # and must never be finalized/read into a training bundle.
    return None
```

**Dressage 3e3142f**　退出 `_finalize_attempt` 时由 `finally` 关闭路由。[plugin.py 第 802–803 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L802-L803)

```python
finally:
    closed = await self._close_attempt(record)
```

**据此判断**　正常 `END` 把结果交给 store。`CANCEL` 已给 attempt 作标记时，`END` 跳过训练 bundle 提交，随后仍进入 `finally`。两条路径的预期提交次数不同。

<a id="evidence"></a>

## 证据与验证范围

**已存输出**　0.26 的真实 Job 登记了下列回调，探测按名字排序打印。[trial-plan-output.txt 第 25 行](../09-trial-plan/trial-plan-output.txt#L25)

```text
registered: AGENT_END, AGENT_START, CANCEL, END, START, VERIFICATION_START
```

先前主动触发 END 的双版本实验核对了事件携带的对象、物理 ID 与目录。 [0.26 END 的对象与身份原始输出](../12-reward-validity/result-contract-output.txt#L1-L2) · [0.18 对照](../12-reward-validity/result-contract-0.18.0.txt#L1-L2)

新探测通过 `Job.run()` 让 Harbor 自己发事件。三版正常顺序均为 START → AGENT_START → AGENT_END → VERIFICATION_START → END，插件回调后依次为 ready、active、ready、ready、closed。单次取消时是 AGENT_END → CANCEL → END，记录带取消标记，Store 提交零次；正常和取消均记录一次 handle.close 与一次 lease.release。两步题每个 step 各打开、停接一个 turn。[三版各七例](../22-retry-policy/job-trial-output.txt) · [断言与替身](../22-retry-policy/probe.py)

## 处理与验收

**下一步**　在使用真实 Gateway、Proxy 与环境的联测中核对相同事件顺序，以及实际请求停接和资源释放。

**通过条件**　正常路径在 END 完成一次提交并关闭路由。取消路径能查到 CANCEL 的状态，收尾顺利时收到 END，commit_attempt 的调用次数为零，路由被释放。[现有端到端失败场景](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_gated_e2e.py#L168)

<a id="history"></a>

## 判断记录

- 2026-11-18　单题和八 Trial 的真实 Job 均能登记六个回调，探测停在注册阶段。0.18 与新版在取消和输出回收的先后关系上有差异，因此实际退出顺序单列验收。

- 2026-11-18　核对插件原注释与取消分支后，纠正旧验收文字“同一次尝试只提交一次”。正常 END 预期提交一次，已标记取消的 attempt 预期零次，两者都要核对关闭路由。现有输出止于注册。[两个分支的源码](#sources) · [注册输出](#evidence)

- 2026-11-18　主动触发 END 的结果探测补齐了事件携带对象的证据。它只观察一个指定时点，未运行含取消分支的生命周期。[探测及两版对照](../12-reward-validity/README.md#evidence)

### 复查入口

- 复现与对照　[注册探测](../09-trial-plan/probe.py) · [注册结果](../09-trial-plan/trial-plan-output.txt) · [已有插件用例](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_execution.py#L64)
- 完整调用与配置　[plugin.py:407](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L407-L414) · [plugin.py:731](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L731-L807) · [trial.py:608](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/trial/trial.py#L608-L634) · [trial.py:667](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/trial/trial.py#L667)

[PR-001 如何审查此问题](../../prs/001-harbor-026-compatibility/README.md#runtime) · [返回问题索引](../../README.md#investigations)
