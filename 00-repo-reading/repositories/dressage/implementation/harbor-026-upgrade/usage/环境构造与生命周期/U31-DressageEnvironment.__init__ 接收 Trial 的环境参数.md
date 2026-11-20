# U31 · DressageEnvironment.__init__ 接收 Trial 的环境参数

<a id="u31"></a>

[环境构造与生命周期目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[environment.py 282–286](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L282-L286)

```python
super().__init__(*args, **kwargs)
self._harbor_mounts = self._build_harbor_mounts()
self._separate_verifier = _is_separate_verifier_session(
    self.session_id, self._mounts
)
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor trial.py 1490–1501](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L1490-L1501) | 记下 `TrialPaths`、`session_id`、显式 mounts 和 Trial 添加的自动挂载。 |
| ② 结果　[Dressage environment.py 282–286](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L282-L286) | 看构造后的 `_harbor_mounts` 与 `_separate_verifier`，按 agent 和独立 verifier 两种会话分别核对。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L116-L220) | 题目环境目录、session、TrialPaths、task_env_config。Trial 的日志绑定走 `mounts` | 基线夹具可构造 | 得到环境实例以及本 Trial 的挂载和 Agent/verifier 会话标识 | 基线两类会话用例通过。原 Trial 构造的 agent 目录与实际绑定一致。 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L146-L336) | 同一基本输入。Trial 的日志绑定改走 `auto_mounts`，用户绑定仍走 `mounts` | 真实形状可构造。旧 verifier 夹具给错参数 | 得到环境实例以及本 Trial 的挂载和 Agent/verifier 会话标识 | 原 Trial 构造成功，agent 目录实际直挂。Harbor 回收时走了复制分支，见 U44。 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L200-L401) | 同 0.25，`auto_mounting` 默认 False | 真实形状可构造。旧 verifier 夹具给错参数 | 得到环境实例以及本 Trial 的挂载和 Agent/verifier 会话标识 | 对齐 verifier 夹具后四项通过。原 Trial 的 agent 目录实际直挂，回收时仍走复制分支，见 U44。 |

**独立 verifier 实测**　独立 verifier 的构造参数还包括环境定义目录。在无专用镜像的 DAPO 题中，0.18 传入 `tests/`，0.25、0.26 传入 `environment/`，之后由 Harbor 上传宿主测试。[问题 21 的三版原始调用](../../investigations/21-separate-verifier-input/README.md#evidence)

**接续**　分别验独立 verifier 会话形状与实际日志能否正确回收。构造成功只证明实例存在。 [environment.py 262-286](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L262-L286) · [基线套件的通过、失败和排除项](../../investigations/00-version-target/pytest-replay.txt) · [0.25/0.26 非空日志输出](../../investigations/02-output-mounts/log-recovery-output.txt) · [0.26 夹具的一行差异](../../investigations/03-verifier-fixture/auto-mounts.patch) · [对齐夹具后四项测试](../../investigations/03-verifier-fixture/fixture-pytest.txt) · [问题 02](../../investigations/02-output-mounts/README.md) · [问题 03](../../investigations/03-verifier-fixture/README.md) · [原 Trial 三版回放](../../investigations/02-output-mounts/trial-log-recovery.txt) · [回放代码](../../investigations/02-output-mounts/trial_log_recovery.py)
