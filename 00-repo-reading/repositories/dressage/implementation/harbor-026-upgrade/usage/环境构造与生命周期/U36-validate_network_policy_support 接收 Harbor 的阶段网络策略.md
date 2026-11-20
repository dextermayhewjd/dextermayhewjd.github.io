# U36 · validate_network_policy_support 接收 Harbor 的阶段网络策略

<a id="u36"></a>

[环境构造与生命周期目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[environment.py 376–381](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L376-L381)

```python
policy = network_policy or self.network_policy
super().validate_network_policy_support(policy)
if policy.network_mode == NetworkMode.ALLOWLIST and policy.allowed_hosts != [
    "127.0.0.1"
]:
    raise ValueError("Dressage bwrap allowlist must contain only 127.0.0.1")
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor base.py 1105–1112](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1105-L1112) | 看 Harbor 传入的基线策略与阶段策略，记录 network mode 和允许的 hosts。 |
| ② 结果　[Dressage environment.py 376–381](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L376-L381) | 检查哪个阶段正常返回，哪个阶段触发拒绝。单步和多步的输入分别记录。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L759-L821) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L116-L220) | 基础 NetworkPolicy 和阶段策略。后端执行基类校验 | 形状可接收。具体多步组合待测 | 合规策略返回 `None`。Dressage 限定 allowlist 为单一 `127.0.0.1`。不符合时拒绝 | 基线夹具覆盖单步隔离，多步组合待验 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L975-L1037) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L146-L336) | 静态后端会推导可统一执行的策略，可能合并 allowlist 的主机 | 形状可接收。具体多步组合待测 | 合规策略返回 `None`。Dressage 限定 allowlist 为单一 `127.0.0.1`。不符合时拒绝 | 条件有源码，缺修正夹具或多步实测 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1040-L1102) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L200-L401) | 同 0.25，按推导结果交给后端校验 | 形状可接收。具体多步组合待测 | 合规策略返回 `None`。Dressage 限定 allowlist 为单一 `127.0.0.1`。不符合时拒绝 | 修正夹具覆盖单步隔离，多步组合待验 |

**接续**　用目标多步题的真实策略核对合并后的 allowed_hosts。 [environment.py 373-382](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L373-L382) · [对齐夹具后四项测试](../../investigations/03-verifier-fixture/fixture-pytest.txt) · [问题 14](../../investigations/14-phase-network-policy/README.md) · [问题 15](../../investigations/15-web-tools/README.md)
