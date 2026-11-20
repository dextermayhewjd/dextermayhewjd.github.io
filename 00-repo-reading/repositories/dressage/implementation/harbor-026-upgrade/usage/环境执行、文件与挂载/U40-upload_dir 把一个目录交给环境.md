# U40 · upload_dir 把一个目录交给环境

<a id="u40"></a>

[环境执行、文件与挂载目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[environment.py 445](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L445)

```python
async def upload_dir(self, source_dir: Path | str, target_dir: str) -> None:
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor trial.py 1853–1859](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L1853-L1859) | 以一个只含 `SKILL.md` 的 skill 进入上传，记录源目录与最终的 skills 目标目录。 |
| ② 结果　[Dressage environment.py 449–457](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L449-L457) | 等目录复制返回，读回目标下的 `SKILL.md` 并比较内容，保留实际使用的目录前缀。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L918-L925) | `source_dir` 是宿主目录，`target_dir` 是环境可写目录 | 源码可接收，未见同一技能目录对照 | 正常返回 `None`，目标目录包含源文件 | 技能目录用例待验 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L1134-L1141) | `source_dir` 是宿主目录，`target_dir` 是环境可写目录 | 实测接受 /runtime/skills/demo | 正常返回 `None`，目标目录包含源文件 | 实测读回 SKILL.md 的原内容 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1202-L1209) | `source_dir` 是宿主目录，`target_dir` 是环境可写目录 | 实测接受 /runtime/skills/demo | 正常返回 `None`，目标目录包含源文件 | 实测读回 SKILL.md 的原内容 |

**接续**　换技能目标路径时沿用同一文件作读回检查。 [两个新版本的技能文件读回](../../investigations/05-skills-upload/skills-upload-output.txt) · [问题 05](../../investigations/05-skills-upload/README.md)
