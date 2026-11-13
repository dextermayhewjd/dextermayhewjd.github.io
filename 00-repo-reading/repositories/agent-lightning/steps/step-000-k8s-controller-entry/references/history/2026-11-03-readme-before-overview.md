> 链接维护说明：用户已撤回尚未接触就提前创建的函数卡；本文指向这些卡片的旧链接现改为固定版本源码。历史叙述保留。

> 历史快照：2026-11-03 在用户要求先看完整 Reconciler 骨架前保存。这里的局部起点与待回答问题已被当前 scope 修订，保留用于回查。

# Step 000 · Kubernetes 控制器怎样开始工作

[项目与当前进度](../../../../README.md#current-reading) · [范围与源码导航](../../01-scope.md) · [函数记录](../../02-short-term-memory/overview.md) · [讨论过程](../../04-flow.md)

> 先在本地 README 中试读和修改。这里是本步正文，暂不建立 Hugo 网页。

## 1. 我们现在站在哪里

前面从 Slime 的五个沙箱接口出发，提出了“如何使用执行环境”和“如何在集群里管理任务”的区别，[原话与澄清](../../../../README.md#sandbox-and-k8s)继续保留。

现在站在 Agent Lightning 的 **Controller 启动点**：API Gateway 保存 rollout 任务及状态，Kubernetes 保存实际的 Job。先找出把两边连接起来的控制器入口。

本步从 `K8sReconciler.run()` 进入，先看它怎样组织工作；训练器怎样生成任务、Job 模板怎样写，暂时只保留位置。

## 2. 这个控制器对象从哪里来

`agentlightning/controller/__main__.py` 的 `_run_controller` 选中 `runner_type="k8s"` 后，创建控制器并调用它：

```python
# 教学裁剪：只保留 k8s 路径，省略配置实参、导入与信号处理。
async with AgentLightningAsyncClient(...) as api:
    reconciler = K8sReconciler(api=api, config=config)
    await reconciler.run()
```

这里先认识两个输入：`api` 是访问 **Agent Lightning API Gateway** 的客户端；`config` 是控制器配置。这里的 `api` 不是 Kubernetes 客户端，后者在控制器需要访问集群时另行取得。

## 3. 先只看 run 的核心

下面是正常路径的源码节选，省略日志和取消处理，保留真实调用与等待关系：

```python
async def run(self) -> None:
    await asyncio.gather(
        self._periodic_reconcile_loop(),
        self._watch_jobs_loop(),
    )
```

先把两个被调用者当作有明确职责的黑箱：

| 调用 | 本轮先知道的职责 |
| --- | --- |
| `_periodic_reconcile_loop()` | 周期性对照 rollout 与 Job 的状态，并处理需要协调的任务 |
| `_watch_jobs_loop()` | 持续观察 Job 事件，将相关完成或失败状态交给处理函数 |

本轮先观察 `run` 的参数、这两个调用怎样组合，以及调用方在哪里等待；不要急着展开所有状态分支。

<a id="first-observation"></a>

## 4. 第一个观察点

**假设 Gateway 里已有 10 条待执行的 rollout。看上面的启动方式和 `run` 的参数，这条启动路径需要为每条任务再调用一次 `run()`，还是一次调用就会开始持续管理这些任务？你的判断依据是什么？**

先说当前判断。接着按回答回看周期循环中的实际代码，核对控制器与单条任务的关系；目前未记录用户对此问题的回答。

需要回查时看 [K8sReconciler.run 函数卡](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L126)。`run()` 内部职责和当前函数的返回边界保存在卡片，后续实际问答保存在 [04-flow](../../04-flow.md#first-observation)。

<details>
<summary>本步来源与记录边界</summary>

- 固定源码：`0029dbb35c467799d35fee81d15d80264b0d1bd3`，2026-11-03 静态核对。
- 调用方：[`_run_controller` 的对象创建](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/__main__.py#L28)与 [等待 run](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/__main__.py#L43)。
- 本步入口：[`K8sReconciler.run`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L126)。
- 这是本项目的第一步，`03` 暂无前序继承；Slime 的已有记录作为带来源的外部参考，不改写成 Agent Lightning 的函数记忆。
- 未运行 Controller、Kubernetes Job 或模型训练；没有将材料准备视为用户已经理解。

</details>
