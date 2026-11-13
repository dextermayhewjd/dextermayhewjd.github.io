# 3.1 调整前：环境供给主线

[返回当前 scope](../../01-scope.md)

2026-11-04 调整前快照，保留当时的图与图下说明。

### 3.1 放回强化学习的环境供给主线

下图是职责与资源交接图，跨控制器的箭头由 Kubernetes 资源变化连接，不表示一串同步函数调用。

```text
RL batch demand
  -> SandboxFleet / LookaheadWarmer
  -> SandboxTemplate + SandboxWarmPool
  -> [Step 000] WarmPool controller
  -> Sandbox CR -> core Sandbox controller -> Pod

rollout -> SandboxClaim -> available Sandbox -> task / tool calls -> result -> release
              |
              +-> claimed Sandbox leaves pool -> WarmPool reconciles again
```

训练侧决定准备哪类环境、备用多少；本步看 Kubernetes 侧怎样落实备用目标。池创建 Sandbox CR，核心 Sandbox controller 再协调 Pod 等子资源，调度和容器运行由 Kubernetes 完成。领取会使环境离开备用池，因此**备用目标 3 个不是全系统最多运行 3 个**。Claim、任务初始化、执行和释放在这里保留位置，后续再沿实际交接阅读。
