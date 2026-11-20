# U45 · exec 通过 _resolve_user 取得生效用户

<a id="u45"></a>

[环境执行、文件与挂载目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[environment.py 491](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L491)

```python
effective_user = self._resolve_user(user)
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage environment.py 489–493](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L489-L493) | 在原 `exec` 调用里记下显式 `user` 与环境默认用户，可各取一个有默认值和有显式覆盖的样例。 |
| ② 结果　[Harbor base.py 625–634](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L625-L634) · [Dressage environment.py 491–496](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L491-L496) | 看返回的 `effective_user`，核对后端继续构造命令还是以该值拒绝执行。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L383-L392) | user 为字符串、整数或 None。None 时由 Harbor 决定默认用户 | 源码可接收 | 返回有效用户，Dressage 只接受 None、0、"0" 或 "root" | 默认用户在 exec 路径有间接证据。显式不同用户待测 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L560-L569) | user 为字符串、整数或 None。None 时由 Harbor 决定默认用户 | 源码可接收 | 返回有效用户，Dressage 只接受 None、0、"0" 或 "root" | 默认用户在 exec 路径有间接证据。显式不同用户待测 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L625-L634) | user 为字符串、整数或 None。None 时由 Harbor 决定默认用户 | 源码可接收 | 返回有效用户，Dressage 只接受 None、0、"0" 或 "root" | 默认用户在 exec 路径有间接证据。显式不同用户待测 |

**接续**　修改默认用户配置时核对传给 Dressage 的值。 [基线套件的通过、失败和排除项](../../investigations/00-version-target/pytest-replay.txt) · [对齐夹具后四项测试](../../investigations/03-verifier-fixture/fixture-pytest.txt) · [问题 03](../../investigations/03-verifier-fixture/README.md)
