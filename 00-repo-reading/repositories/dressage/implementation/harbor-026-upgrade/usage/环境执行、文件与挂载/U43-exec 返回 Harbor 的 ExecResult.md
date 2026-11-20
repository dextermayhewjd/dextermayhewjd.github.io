# U43 · exec 返回 Harbor 的 ExecResult

<a id="u43"></a>

[环境执行、文件与挂载目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[environment.py 531–535](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L531-L535)

```python
return ExecResult(
    stdout=stdout_text,
    stderr=stderr_text,
    return_code=int(process.returncode or 0),
)
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor oracle.py 136–141](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/agents/oracle.py#L136-L141) | 在 Oracle 调用环境 `exec` 时看实际命令、用户与 env，选一条有已知输出和退出码的命令。 |
| ② 结果　[Dressage environment.py 523–535](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L523-L535) · [Harbor oracle.py 154–158](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/agents/oracle.py#L154-L158) | 观察 `ExecResult` 的 stdout、stderr、return_code，再看 Oracle 是否按该退出码继续或报告失败。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L1119-L1138) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L78-L81) | 已启动环境中的 `command`，可传 cwd、env、timeout_sec、user。有效用户限 root/0 或默认值 | 基线真实 bwrap 用例通过 | `ExecResult` 含 stdout、stderr、return_code。超时或取消终止子进程并传播 | 持久工作区用例验证 return_code 与 stdout |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L1359-L1378) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L108-L111) | 已启动环境中的 `command`，可传 cwd、env、timeout_sec、user。有效用户限 root/0 或默认值 | 签名匹配。原 verifier 夹具在 exec 之前失败 | `ExecResult` 含 stdout、stderr、return_code。超时或取消终止子进程并传播 | 同一真实用例缺修正夹具结果 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1437-L1456) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L110-L113) | 已启动环境中的 `command`，可传 cwd、env、timeout_sec、user。有效用户限 root/0 或默认值 | 对齐 verifier 夹具后真实 bwrap 用例通过 | `ExecResult` 含 stdout、stderr、return_code。超时或取消终止子进程并传播 | 修正夹具后验证 return_code 与 stdout，超时/取消另验 |

**接续**　需承诺超时或取消时，单独检查进程退出、异常传播和宿主资源释放。 [environment.py 481-491](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L481-L491) · [environment.py 525-535](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L525-L535) · [基线套件的通过、失败和排除项](../../investigations/00-version-target/pytest-replay.txt) · [对齐夹具后四项测试](../../investigations/03-verifier-fixture/fixture-pytest.txt) · [问题 03](../../investigations/03-verifier-fixture/README.md) · [问题 14](../../investigations/14-phase-network-policy/README.md)
