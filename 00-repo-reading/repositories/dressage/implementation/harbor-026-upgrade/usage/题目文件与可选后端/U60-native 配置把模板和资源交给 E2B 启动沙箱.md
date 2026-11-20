# U60 · native 配置把模板和资源交给 E2B 启动沙箱

<a id="u60"></a>

[题目文件与可选后端目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[terminal-bench-2-e2b.yaml 11](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/harbor_job_configs/terminal-bench-2-e2b.yaml#L11)

```yaml
type: e2b
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor e2b.py 1488–1497](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/e2b.py#L1488-L1497) | 在要创建远端沙箱时记下模板、资源配置和超时，使用运行此次任务的 E2B 账号时再核对。 |
| ② 结果　[Harbor e2b.py 1535–1551](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/e2b.py#L1535-L1551) | 对照返回句柄与沙箱 ID，再向同一 ID 执行一条已知输出的命令。目录中的 YAML 解析只覆盖配置。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/e2b.py#L106-L109) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/e2b.py#L227-L230) | Harbor Job YAML 选 `type: e2b`，Dressage profile 选 `mode: native`。模板由 Harbor 后端生成或查找 | 配置可解析，E2B 服务是否接受模板待验 | 以环境名与环境哈希生成模板名，创建远端沙箱 | 构造器的模板引用有本地实测，云端接收及命令执行待验 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/e2b.py#L108-L111) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/environments/e2b.py#L228-L233) | Harbor Job YAML 选 `type: e2b`，Dressage profile 选 `mode: native`。模板由 Harbor 后端生成或查找 | 配置可解析，E2B 服务是否接受模板待验 | 以环境名与环境哈希生成模板名，创建远端沙箱 | 构造器的模板引用有本地实测，云端接收及命令执行待验 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/e2b.py#L528-L546) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/e2b.py#L901-L907) | Harbor Job YAML 选 `type: e2b`，Dressage profile 选 `mode: native`。模板由 Harbor 后端生成或查找 | 配置可解析，E2B 服务是否接受模板待验 | 模板键包括资源配置和 recipe `r5`，创建远端沙箱 | 构造器的模板引用有本地实测，云端接收及命令执行待验 |

**离线实测补充。** 本机能导入 SDK；若使用 Dockerfile 路径，读取 WORKDIR 会因缺少 `dockerfile-parse` 失败。还未到达模板构建或云端创建。[实测记录](../../investigations/16-e2b-template/sdk-output.txt)

同一镜像固定 1024 MB，CPU 从 1 改为 2，0.18、0.25 均产生同一模板引用。0.26 分别产生 `c1-m1024-r5`、`c2-m1024-r5`。另显式指定预建模板时，SDK 替身接到相同的模板名。[三版输出](../../investigations/16-e2b-template/e2b-offline-output.txt)

**接续**　用目标账户和具体模板启动一个远端环境，保存模板标识及首次 exec 的结果。 [rollout-native-remote.yaml 5](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dressage_profiles/rollout-native-remote.yaml#L5) · [两份 YAML 和三版字段](../../investigations/18-example-configs/job-config-output.txt) · [问题 16](../../investigations/16-e2b-template/README.md) · [问题 18](../../investigations/18-example-configs/README.md)
