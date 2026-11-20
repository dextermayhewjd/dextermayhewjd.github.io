# U46 · exec 通过 _merge_env 得到最终命令环境

<a id="u46"></a>

[环境执行、文件与挂载目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[environment.py 500](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L500)

```python
process_env.update(self._merge_env(env) or {})
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage environment.py 499–505](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L499-L505) | 让持久环境、单次命令和作用域对同一个测试键赋不同值，观察 `_merge_env` 的输入。 |
| ② 结果　[Harbor base.py 649–665](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L649-L665) · [Dressage environment.py 500–505](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L500-L505) | 看传给子进程的 `process_env`。从运行中的命令打印并读回这个测试键，核对最终优先级。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L407-L423) | 本次命令环境或 None，结合 Harbor 保存的持久环境和当前作用域环境 | 源码可接收 | 返回 dict 或 None。同名键按持久环境 → 单次命令 → 作用域覆盖 | 三版源码的优先级吻合。针对同名键的进程读回待测 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L584-L600) | 本次命令环境或 None，结合 Harbor 保存的持久环境和当前作用域环境 | 源码可接收 | 返回 dict 或 None。同名键按持久环境 → 单次命令 → 作用域覆盖 | 三版源码的优先级吻合。针对同名键的进程读回待测 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L649-L665) | 本次命令环境或 None，结合 Harbor 保存的持久环境和当前作用域环境 | 源码可接收 | 返回 dict 或 None。同名键按持久环境 → 单次命令 → 作用域覆盖 | 三版源码的优先级吻合。针对同名键的进程读回待测 |

**接续**　模型路由配置变化时，用合成值在目标进程核对最终生效的变量。 [问题 07](../../investigations/07-agent-routing/README.md) · [问题 14](../../investigations/14-phase-network-policy/README.md)
