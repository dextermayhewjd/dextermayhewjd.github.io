# 23 · 同一个本地 dataset 限取两题时，升级后还会抽到原来的题吗？

**当前判断**　当 Job 用 `datasets[].path` 指向本地目录时，0.18 按文件系统枚举顺序收集题目，0.25 和 0.26 先按路径排序。Harbor 随后应用 `n_tasks`。因此同一个目录、同一个数量可以生成不同的训练题目。随仓两份 E2B YAML 使用远程包名，这条本地排序规则不适用于它们。

**对应的三版用法表**　[U11 展开任务来源](../../usage/Job%20与%20Agent%20路由/U11-Job._resolve_task_configs%20展开任务来源.md#u11) · [原套件覆盖](../original-test-audit.md#i23)

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　注册表按解析出的任务顺序创建条目，关闭 shuffle 时按 `sample_offset` 读取。[任务注册顺序](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L680-L689) · [按游标生成样本](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L471-L475)

**Harbor 0.18.0**　按操作系统返回的顺序枚举子目录。[本地数据集展开](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/job/config.py#L171)

```python
for path in self.path.iterdir()
```

**Harbor 0.26.0**　先按路径排序，再过滤有效的题目目录。[本地数据集展开](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/job/config.py#L184)

```python
for path in sorted(self.path.iterdir())
```

随后两版都截取过滤后序列的前 `n_tasks` 项。0.25 已采用与目标版相同的目录排序。[0.18 截取题目](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/job/config.py#L148-L151) · [0.25 目录顺序](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/job/config.py#L178-L184) · [0.26 截取题目](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/job/config.py#L155-L158)

<a id="evidence"></a>

## 证据与验证范围

三个独立进程读取同一个含九道有效题目的目录。每个进程创建真实的 `HarborDataSource`，固定 `rollout_seed=7`、关闭 shuffle，然后通过 `get_samples → resolve_spec` 读回题目目录名。在安装新版本的进程中，仅将 Dressage 的版本门禁设为正在验证的发行版。未启动环境或模型服务。[探测脚本](local_dataset_probe.py) · [三版完整输出](local-selection-output.txt)

| 输入 | 0.18.0 | 0.25.0 / 0.26.0 |
| --- | --- | --- |
| 九题全部进入 | 九题，第一组是 `zeta` | 同九题，第一组是 `alpha` |
| `n_tasks=2` | `zeta, lambda` | `alpha, beta` |

这里的旧版结果取决于文件系统。若某个目录本来的枚举顺序就与排序一致，在那里观察到的两份题单也可能相同。显式 `tasks` 列表按声明顺序展开，远程包的数据集按独立的元数据路径展开。[0.26 显式题单](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job_plan.py#L126-L137) · [0.26 远程包数据集](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/job/config.py#L268-L293)

## 处理与验收

需要将升级后的训练或评测与旧实验逐题对照时，用旧实验记录的实际路径作为显式题单，核对每组的任务身份和顺序。新实验可直接采用 0.26 的排序。若原实验只保留了目录和数量，旧文件系统的枚举顺序无法从这两个值单独恢复。

复现时，先从本目录运行 `python local_dataset_probe.py prepare <新目录>`。再分别在安装目标 Harbor 的 Python 3.12 环境中把 Dressage `3e3142f` 加入模块路径，执行 `python local_dataset_probe.py observe <同一目录>`。输出会同时记录该文件系统的枚举顺序和发出的样本。[探测脚本](local_dataset_probe.py)

[返回问题索引](../../README.md#investigations)
