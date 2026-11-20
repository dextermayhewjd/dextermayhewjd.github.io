# 14 · Harbor 合并各阶段网络策略后，bwrap 还能使用预期的 Gateway 吗？

**当前判断**　保留 bwrap 的回环 Gateway 约束。单步和多步 Trial 最终交给后端的网络策略需要实测。

**对应的三版用法表**　[U08 TaskConfig.model_validate_toml 解析题目与网络要求](../../usage/启动与配置/U08-TaskConfig.model_validate_toml%20解析题目与网络要求.md#u08) · [U36 validate_network_policy_support 接收 Harbor 的阶段网络策略](../../usage/环境构造与生命周期/U36-validate_network_policy_support%20接收%20Harbor%20的阶段网络策略.md#u36) · [原套件在本问题测到了哪里](../original-test-audit.md#i14)

Harbor 按任务阶段生成网络策略，Dressage 的静态 bwrap 环境却只能按一次配置启动。

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　`bwrap` 收到允许列表时，只接受单一回环地址。[environment.py 第 378–381 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L378-L381)

```python
if policy.network_mode == NetworkMode.ALLOWLIST and policy.allowed_hosts != [
    "127.0.0.1"
]:
    raise ValueError("Dressage bwrap allowlist must contain only 127.0.0.1")
```

**Harbor 0.26.0**　静态网络环境在允许列表分支汇集各阶段涉及的主机。[base.py 第 371–378 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L371-L378)

```python
allowed_hosts=(
    list(
        dict.fromkeys(
            host for p in policies for host in p.allowed_hosts
        )
    )
    if broadest.network_mode == NetworkMode.ALLOWLIST
    else []
```

**据此判断**　如果 Harbor 把不同阶段的主机合并，Dressage 最终收到的列表可能超过回环地址。有些策略组合会在 Harbor 先被拒绝，需按具体输入核对交给后端的策略。

<a id="evidence"></a>

## 证据与验证范围

**已有局部输出**　对齐夹具后的 0.26 环境测试文件，含 Agent／verifier 隔离用例。[fixture-pytest.txt 第 6 行](../03-verifier-fixture/fixture-pytest.txt#L6)

```text
4 passed in 0.12s
```

这次运行只覆盖夹具创建的环境。还要从真实单步及多步 Trial 取得合并后的 `network_mode`、`allowed_hosts` 和后端接受或拒绝的结果。

## 处理与验收

**下一步**　各用一份受限的单步和多步任务，记录阶段输入、合并结果和后端收到的策略。用测试 Gateway 验证一次本地模型请求，再用声明 public 的任务走 `enforced` 拒绝分支。

**通过条件**　受支持的 allowlist 只含回环主机，请求到达该 Gateway。public 任务按预期被拒绝。若某一阶段失败，按记录定位到策略合并或 Dressage 的校验入口。[已有配置拒绝测试](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_execution.py#L128)

<a id="history"></a>

## 判断记录

- 2026-11-18　0.18 已经存在阶段网络配置。0.26 源码仍能定位合并和校验入口。真实多步任务的最终策略尚待实测。

### 复查入口

- 复现与对照　[隔离用例](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L77) · [夹具实测](../03-verifier-fixture/fixture-pytest.txt)
- 完整调用与配置　[plugin.py:1099](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1099-L1150) · [附加允许主机](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1066-L1074) · [environment.py:373](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L373-L382) · [base.py:341](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/base.py#L341-L364) · [合并后的策略](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/base.py#L360-L386)

[PR-001 如何审查此问题](../../prs/001-harbor-026-compatibility/README.md#network) · [返回问题索引](../../README.md#investigations)
