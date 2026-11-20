# U15 · Job._task_configs 提供已经解析的任务对象

<a id="u15"></a>

[Job 与 Agent 路由目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[compat.py 97](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L97)

```python
return tuple(job._task_configs)
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage compat.py 92–97](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L92-L97) | 查看 `job._task_configs` 的类型、顺序以及第一个 task 对象。 |
| ② 结果　[Dressage compat.py 129–130](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L129-L130) · [Dressage compat.py 158–161](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L158-L161) | 看 `build_trial_plan` 为同一个位置取出的 task，比较单次进程内的对象身份。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L97) | 已经创建的 Job，私有成员应为 list | 本地单题与两题输入实测接受 | 取成 tuple，保留每个原任务对象引用，供 `is` 校验 | 八个 Trial 的对象配对已测 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L110) | 已经创建的 Job，私有成员应为 list | 本地单题与两题输入实测接受 | 取成 tuple，保留每个原任务对象引用，供 `is` 校验 | 八个 Trial 的对象配对已测 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L110) | 已经创建的 Job，私有成员应为 list | 本地单题与两题输入实测接受 | 取成 tuple，保留每个原任务对象引用，供 `is` 校验 | 八个 Trial 的对象配对已测 |

**接续**　升级到另一个标签时核对这个成员是否仍保存原对象。 [compat.py 93-97](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L93-L97) · [三版真实 Job、计划和钩子登记](../../investigations/09-trial-plan/trial-plan-output.txt) · [Job 探测的断言与替身](../../investigations/09-trial-plan/probe.py) · [问题 09](../../investigations/09-trial-plan/README.md)
