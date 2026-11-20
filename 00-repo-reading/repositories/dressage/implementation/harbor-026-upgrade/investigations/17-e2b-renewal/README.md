# 17 · 运行时间超过一个续租周期时，E2B 环境如何维持和回收？

**当前判断**　沿用 Harbor 的 E2B 续租和停止。已用 SDK 替身观察续租和停止调用，远端沙箱的续租与回收仍待实测。

**对应的三版用法表**　[U61 E2B 沙箱超时、续租和停止](../../usage/题目文件与可选后端/U61-E2B%20沙箱超时、续租和停止.md#u61) · [原套件在本问题测到了哪里](../original-test-audit.md#i17)

长 Trial 可能超过一次沙箱有效期，需要知道谁负责延长超时，以及结束后谁停止续租。

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　native profile 将环境生命周期交给 Harbor。[rollout-native-remote.yaml 第 4–5 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dressage_profiles/rollout-native-remote.yaml#L4-L5)

```yaml
environment:
  mode: native
```

**Harbor 0.26.0**　续租循环调用 SDK 的 `set_timeout` 并记录调用失败。[e2b.py 第 1609–1612 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/e2b.py#L1609-L1612)

```python
try:
    await sandbox.set_timeout(self._sandbox_timeout_sec)
except Exception as exc:
    self.logger.warning(f"E2B sandbox timeout renewal failed: {exc}")
```

**Harbor 0.26.0**　停止时取消续租任务、清除本地的续租任务句柄。[e2b.py 第 1641–1643 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/e2b.py#L1641-L1643)

```python
if self._renew_task is not None:
    self._renew_task.cancel()
    self._renew_task = None
```

**据此判断**　配置这条路径时，续租与停止均由 Harbor 负责。要评审实际行为，需要区分定时器发起 SDK 调用和服务端真正延长了该沙箱的有效期。

<a id="evidence"></a>

## 证据与验证范围

三版均执行 Harbor 自己的 E2B `start(False)` 和 `stop(delete=True)`；云端模板查询、SDK 的创建、文件读取、续租和终止使用本地替身。0.18、0.25 的默认创建调用都收到 86400 秒，停止时各收到一次 `kill()`。0.26 给定 9 秒有效期、0.015 秒续租周期，创建时收到 9 秒；真实续租循环向同一替身调用一次 `set_timeout(9)`，再停止并观察 0.035 秒。期间没有新续租，`kill()` 调用一次，Harbor 清除了本地句柄。这个实验覆盖调用参数、调度和终止顺序，未连接 E2B 服务。[脚本和断言](../16-e2b-template/e2b_offline.py) · [三版原始输出](../16-e2b-template/e2b-offline-output.txt)

## 处理与验收

**下一步**　云端验收时，用同一 sandbox ID 对上续租的实际响应、停止时刻和服务端资源状态。

**通过条件**　续租使用配置的有效期，停止后没有新的续租调用。云端验收以该沙箱的回收状态和观测时间为准。

<a id="history"></a>

## 判断记录

- 2026-11-18　已有证据是 Harbor 0.26 的选项与实现。默认有效期为一小时，每次续租的默认间隔为十分钟，本轮没有运行云端长任务。

### 复查入口

- 完整调用与配置　[rollout-native-remote.yaml](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dressage_profiles/rollout-native-remote.yaml) · [e2b.py:672](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/e2b.py#L672-L687) · [_renew_loop](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/e2b.py#L1603-L1613) · [stop](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/e2b.py#L1626-L1658)

[PR-001 如何审查此问题](../../prs/001-harbor-026-compatibility/README.md#e2b) · [返回问题索引](../../README.md#investigations)
