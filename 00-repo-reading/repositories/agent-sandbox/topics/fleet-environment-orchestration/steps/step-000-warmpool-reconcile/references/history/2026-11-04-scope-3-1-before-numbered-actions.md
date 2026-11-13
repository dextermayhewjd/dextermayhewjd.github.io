# 3.1 编号拆分前的图下说明

[返回当前 scope](../../01-scope.md)

2026-11-04 调整前快照，保留当时的图及段落式说明。

### 3.1 放回强化学习的环境供给主线

下图是职责与资源交接示意，`# Step 000` 标出本步位置。这里跟随从预热池领取环境的路径；跨控制器的箭头由 Kubernetes 资源变化连接，不表示一串同步函数调用，也不是可执行代码。

```python
RL batch demand
  -> SandboxFleet / LookaheadWarmer
  -> SandboxTemplate + SandboxWarmPool
  -> WarmPool controller  # Step 000: current focus
  -> Sandbox CR -> core Sandbox controller -> Pod

rollout -> SandboxClaim -> available Sandbox -> task / tool calls -> result -> release
              |
              +-> claimed Sandbox leaves pool -> WarmPool reconciles again
```

**整条主线是：训练提出环境需求 → 提前备好环境 → rollout 领取并使用 → 取回结果并释放。** 领取造成的备用缺口，再由预热池按目标补充。

图的**上半段负责准备环境**。训练侧确定需要哪类环境、备用多少，`SandboxFleet / LookaheadWarmer` 将这些需求落实为模板与预热池配置：`SandboxTemplate` 描述环境，`SandboxWarmPool` 记录备用目标。WarmPool controller 据此创建 Sandbox CR，再由核心 Sandbox controller 协调 Pod，交给 Kubernetes 调度和运行。

图的**下半段使用上半段准备的环境**。rollout 通过 `SandboxClaim` 领取 Sandbox，完成题目初始化与工具交互，取回所需结果后释放。**环境被领取后就离开备用池，补充备用可以与这条 rollout 的执行并行进行。** 所以备用目标 3 个只约束池内备用数量，已领取、正在执行的环境另计；图中的回路从领取处接回补池。

**Step 000 聚焦上半段的 WarmPool controller：接收已有的模板和备用目标，协调池内 Sandbox 的数量。** 本步围绕“目标 3 个、当前 1 个”看清怎样统计、补充并记录观察结果。创建 Sandbox CR 之后的 Pod 管理，以及下半段的领取、使用和释放，保留为后续交接位置。
