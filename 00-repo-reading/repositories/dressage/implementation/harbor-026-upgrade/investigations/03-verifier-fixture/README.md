# 03 · 为什么两个独立 verifier 测试在构造环境时失败？

**当前判断**　改独立 verifier 的测试夹具。临时副本只改一个参数后，整个环境测试文件的 4 项都通过。

**对应的三版用法表**　[U31 DressageEnvironment.__init__ 接收 Trial 的环境参数](../../usage/环境构造与生命周期/U31-DressageEnvironment.__init__%20接收%20Trial%20的环境参数.md#u31) · [U41 download_file 把一个环境文件交回宿主](../../usage/环境执行、文件与挂载/U41-download_file%20把一个环境文件交回宿主.md#u41) · [原套件在本问题测到了哪里](../original-test-audit.md#i03)

两项测试在创建 verifier 环境时就报错，需要先核对夹具是否模拟了目标版 Trial 的调用。

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　夹具把 verifier 的日志绑定传给 `mounts`。[test_environment.py 第 71–73 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L71-L73)

```python
    network_policy=policy,
    mounts=mounts,
)
```

**Harbor 0.26.0**　独立 verifier 的真实构造调用传给 `auto_mounts`。[trial.py 第 1125–1127 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L1125-L1127)

```python
auto_mounts=self._verifier_env_mounts(env_config),
network_policy=plan.verifier_env_baseline,
phase_network_policies=[plan.verifier_phase],
```

**据此判断**　夹具省略 `auto_mounts` 时，基类补入默认日志目录，独立 verifier 收到多余的挂载。要区分夹具与后端故障，可以只改夹具的这个参数。

<a id="evidence"></a>

## 证据与验证范围

**实际补丁**　临时基线副本中唯一的改动。[auto-mounts.patch 第 5–6 行](auto-mounts.patch#L5-L6)

```diff
-        mounts=mounts,
+        auto_mounts=mounts,
```

**已存输出**　在 0.26.0 上只跑 test_environment.py。[fixture-pytest.txt 第 6 行](fixture-pytest.txt#L6)

```text
4 passed in 0.12s
```

这四项通过支持对齐挂载参数。原夹具还手工将 `task/tests` 传给独立 verifier，而真实 0.26 Trial 在宿主上传测试时传的是 `task/environment`。这一差异导致的启动错误和生产修复见[问题 21](../21-separate-verifier-input/README.md)。非空日志能否回收，需要用问题 02 的输入另验。[02 的非空目录输出](../02-output-mounts/log-recovery-output.txt#L7-L11)

## 处理与验收

**下一步**　让目标为 0.26 的夹具按真实 Trial 传 `auto_mounts`，继续检查 Agent 与 verifier 的目录和权限隔离。0.18 的基线保留其原来的调用方式。

**通过条件**　曾失败的两个环境用例与完整 `test_environment.py` 通过，独立 verifier 只取得预期目录。对具备 bwrap 的环境记录真实文件读写结果。[隔离用例](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L77) · [真实 bwrap 用例](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L193) · [复现命令](../../tools/reproduce.md#suite)

<a id="history"></a>

## 判断记录

- 2026-11-18　原始 0.26 默认套件共三项失败，其中两项共用该夹具。仅在临时副本对齐参数，整个环境文件四项通过。随后独立发现非空日志回收失败，两项修复各自验收。

### 复查入口

- 复现与对照　[原失败项](../00-version-target/pytest-replay.txt) · [一行补丁](auto-mounts.patch) · [四项测试输出](fixture-pytest.txt) · [问题 02](../02-output-mounts/README.md)
- 完整调用与配置　[test_environment.py:60](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L60) · [environment.py:238](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L238-L257) · [trial.py:1115](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/trial/trial.py#L1115-L1127) · [base.py:314](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/base.py#L314-L339)

[PR-001 的 C03 · verifier 测试夹具](../../prs/001-harbor-026-compatibility/README.md#fixture) · [返回问题索引](../../README.md#investigations)
