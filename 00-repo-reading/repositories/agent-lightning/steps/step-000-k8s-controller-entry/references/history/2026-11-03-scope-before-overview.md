> 历史快照：2026-11-03 在用户要求先看完整 Reconciler 骨架前保存。这里的局部起点与待回答问题已被当前 scope 修订，保留用于回查。

# 01 · 从 K8sReconciler.run 建立控制器的整体位置

[试读正文](../../README.md) · [函数索引](../../02-short-term-memory/overview.md) · [过程记录](../../04-flow.md)

## 1. 阅读目标

- 整体目标：承接 Slime 的执行环境接口，理解 Agent 任务在 Kubernetes 中怎样被创建、跟踪与收束。
- 本步问题：`K8sReconciler.run` 从哪里被调用，怎样组织周期检查与 Job 事件观察？先区分控制器运行与单条 rollout 执行。
- 确认依据：用户在首步建议后表示“好的那么我们开始吧”，同时要求先在本地 README 试读。[完整记录](../../04-flow.md#start-confirmation)。
- 短期记忆：`run` 的调用场景、输入、内部组合与返回边界；个人解释按实际回答保存。

## 2. 找到指挥官函数

入口是 [`agentlightning/controller/k8s_reconciler.py:126` 的 `K8sReconciler.run`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L126)。它组织两条持续工作的协程，是当前问题的编排入口。

对象来自 `controller/__main__.py` 的 `_run_controller`：选中 k8s 路径后，用 API Gateway 客户端与控制器配置创建 `K8sReconciler`，然后 `await reconciler.run()`。客户端的完整初始化、信号处理和配置解析只作背景。

## 3. 给出真正干活的核心骨架

本轮采用 k8s 模式的正常路径。下面是源码节选，仅省略日志和取消处理；两个调用原本没有显式参数，因此保留无参形式。

```python
async def run(self) -> None:
    await asyncio.gather(
        self._periodic_reconcile_loop(),  # 周期性对照 rollout 与 Job
        self._watch_jobs_loop(),          # 持续观察 Job 事件
    )
```

| 位置 | 本轮阅读深度 | 读完返回哪里 |
| --- | --- | --- |
| `_run_controller:28、43` | 只补控制器对象、API Gateway 客户端和调用来路 | `K8sReconciler.run:126` |
| `run:133–136` | 看清两个调用的组合与等待；先回答正文观察点 | 按回答选择下面的必要局部 |
| `_periodic_reconcile_loop:147` → `_reconcile_once:161` | 先定位周期调用；需要核对单次检查处理多少任务时，最多下钻至 `_reconcile_once` | 回 `run` 的第一条工作线 |
| `_watch_jobs_loop:292` → `_handle_job_event:311` | 先知道观察和交接职责；具体事件分支暂不展开 | 回 `run` 的第二条工作线 |

**停止位置**：能解释控制器与单条任务的关系，以及两条工作线各看哪一侧。Job YAML、Pod 配置、网络、资源、完整状态机和退出恢复的实现留待后续具体问题。列表中的导航不表示已经读完这些函数，也不预建其函数卡片。

固定源码为 `0029dbb35c467799d35fee81d15d80264b0d1bd3`；本步没有真实运行证据，取消和停止信号也不在本轮正常路径的结论内。
