# U35 · BaseEnvironment 构造时反向调用 _validate_definition

<a id="u35"></a>

[环境构造与生命周期目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[environment.py 355–357](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L355-L357)

```python
def _validate_definition(self) -> None:
    if self.task_env_config.os != TaskOS.LINUX:
        raise ValueError("Dressage bwrap supports Linux tasks only")
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor base.py 396](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L396) | 在基类构造回调 `self._validate_definition()` 时看题目 OS、镜像字段、工作目录和目录里的文件。 |
| ② 结果　[Dressage environment.py 355–371](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L355-L371) | 观察返回到构造方，或记录具体拒绝条件。用同一合法题与同一带镜像定义的题分别对照。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L720-L727) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L215) | 基类以 `self._validate_definition()` 调用，使用已绑定的任务 OS、镜像、环境目录和 workdir | 源码可接收 | 合法定义返回 `None` 继续构造。bwrap 对不支持的 OS、docker_image、Dockerfile 或 workdir 报错 | 正常题目的构造有间接运行证据。拒绝输入待逐例实测 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L936-L943) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/base.py#L331) | 基类以 `self._validate_definition()` 调用，使用已绑定的任务 OS、镜像、环境目录和 workdir | 源码可接收 | 合法定义返回 `None` 继续构造。bwrap 对不支持的 OS、docker_image、Dockerfile 或 workdir 报错 | 正常题目的构造有间接运行证据。拒绝输入待逐例实测 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L1001-L1008) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L396) | 基类以 `self._validate_definition()` 调用，使用已绑定的任务 OS、镜像、环境目录和 workdir | 源码可接收 | 合法定义返回 `None` 继续构造。bwrap 对不支持的 OS、docker_image、Dockerfile 或 workdir 报错 | 正常题目的构造有间接运行证据。拒绝输入待逐例实测 |

**接续**　加入新任务环境类型时对照合法题目和明确不支持的题目。 [environment.py 355-371](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L355-L371) · [基线套件的通过、失败和排除项](../../investigations/00-version-target/pytest-replay.txt) · [两个新版本的技能文件读回](../../investigations/05-skills-upload/skills-upload-output.txt) · [问题 01](../../investigations/01-environment-preflight/README.md) · [问题 03](../../investigations/03-verifier-fixture/README.md)
