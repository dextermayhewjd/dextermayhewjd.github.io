# 1.3 · 框架入口怎样交接输入和结果

本文保留助手此前的解释与源码核对，供按需查阅；它不是学习者已经表达的认知，不随个人记忆自动继承。


[本步入口](../README.md) · [完整记忆](initial-map-assistant.md)

这是起点的源码定位说明。完整带读尚未开展，本页保留已核对的调用和未知边界，供下一步接续。

## 先定位启动时的交接

以下摘自固定提交的 `train.py::main()` 第 110–113 行，省略外层日志、清理和异常处理：

```python
startup = create_rollout_manager(args, restore_plan=restore_plan)
train(
    startup.args, startup.placements, startup.manager, startup.num_rollout_per_epoch, startup.restore_plan
)
```

`startup` 的这些属性由调用方交给 [train](source-notes/train.py/train.md)。本步先核对参数确实这样传递；各属性的完整类型、资源结构和工厂创建过程后续再读。[main 的独立记录](source-notes/train.py/main.md)保存这一层的职责。

| 调用交接 | 输入或取得的数据 | 结果被谁使用 |
| --- | --- | --- |
| main → create_rollout_manager | `args`、`restore_plan` | main 取得 `startup`，读取其属性 |
| main → train | `startup.args`、`placements`、`manager`、`num_rollout_per_epoch`、`restore_plan` | train 使用这组配置与组件组织工作；正常结束后返回 main |

## 再定位一轮数据的交接

以下分别摘自 `train.py` 第 51、67、90 行，中间省略条件分支、checkpoint 和资源操作。`async_train` 这一行展示不使用 critic 的分支；三行不表示源码中紧挨执行。

```python
rollout_data_ref = ray.get(rollout_manager.generate.remote(rollout_id))
```

```python
ray.get(actor_model.async_train(rollout_id, rollout_data_ref))
```

```python
actor_model.update_weights()
```

| 调用交接 | 当前能够确认的输入输出 | 留待展开 |
| --- | --- | --- |
| train → RolloutManager.generate | 传入 `rollout_id`；调用方通过 `ray.get` 取得远端方法的返回结果 | 生成批次的完整数据格式与不同传输方式 |
| train → actor_model.async_train | 交出同一轮编号和 `rollout_data_ref`，等待训练调用 | 训练组件内部如何消费数据 |
| train → actor_model.update_weights | 调用权重更新方法 | 参数传输和模型服务内部机制 |

[RolloutManager.generate 的记录](source-notes/slime/ray/rollout.py/RolloutManager.generate.md)只解释当前入口怎样把内部结果交回。这里不能仅凭变量名断定 `rollout_data_ref` 就是样本列表，也不能把一次远端调用和一份任务等同。

## 这一步保存的理解与下一问

已有基本关系是：启动代码把准备结果交给循环；循环请求一轮生成数据，再把结果交给训练侧，随后进行权重更新。具体任务执行是其中一层，完整实现将按问题逐步展开。

这是助手基于源码整理的解释，用户理解未确认，也没有实际运行证据。下一步沿 `main()` 阅读时，在复制后的记忆中补充实际看清的输入和生命周期，不预先把所有服务、恢复和数据分支展开。
