# 环境构造与生命周期 · U31–U38

这些调用由 Harbor 发起，接收方是 Dressage 的 bwrap 后端。`start()` 和 `stop()` 的交付是环境的状态变化。 [全部用法](../README.md)

| 编号 | 交接 |
| --- | --- |
| [U31](U31-DressageEnvironment.__init__%20接收%20Trial%20的环境参数.md#u31) | DressageEnvironment.__init__ 接收 Trial 的环境参数 |
| [U32](U32-Environment.type%20返回后端标识.md#u32) | Environment.type 返回后端标识 |
| [U33](U33-Environment.capabilities%20给%20Harbor%20报告能力.md#u33) | Environment.capabilities 给 Harbor 报告能力 |
| [U34](U34-EnvironmentFactory%20调用%20DressageEnvironment.preflight.md#u34) | EnvironmentFactory 调用 DressageEnvironment.preflight |
| [U35](U35-BaseEnvironment%20构造时反向调用%20_validate_definition.md#u35) | BaseEnvironment 构造时反向调用 _validate_definition |
| [U36](U36-validate_network_policy_support%20接收%20Harbor%20的阶段网络策略.md#u36) | validate_network_policy_support 接收 Harbor 的阶段网络策略 |
| [U37](U37-Environment.start%20把本次%20bwrap%20会话准备为可用.md#u37) | Environment.start 把本次 bwrap 会话准备为可用 |
| [U38](U38-Environment.stop%20结束本次会话并释放资源.md#u38) | Environment.stop 结束本次会话并释放资源 |
