# C07c · Codex 活动 profile 会选择哪个 provider？

**来源与状态**　C07 评审意见 ②。Harbor 0.26.0，客户端选择顺序按 Codex 0.118.0 源码核对。定向修复已在工作树验证，尚未提交。

## ① 上游约定 · Harbor 配置顶层 provider，Codex 读取活动 profile

Harbor 将 Gateway 地址写给顶层选中的原生 provider；找不到对应的原生条目时，它会配置内置 OpenAI provider。Codex 读取最终 TOML 时，当前活动 profile 的 `model_provider` 优先于顶层值。

## ② 修前表现 · 顶层选了 openai，活动 profile 却选了 alternate

配置里有 `profile = "prod"`，并在 `profiles.prod.model_provider` 写了 `alternate`。修前，插件通过校验并尝试申请 Gateway；Harbor 准备上传的 TOML 中仍保留活动 profile 的选择。该配置可以让客户端选择另一个 provider，实际模型请求去向未做 CLI 端到端实测。

## ③ 原因定位 · 原来的断言停在顶层连接，没有问哪个 profile 生效

`Codex._build_effective_config()` 给顶层 provider 配置 Gateway，也保留用户的 profiles。若只看 `model_connection` 或顶层地址，便会遗漏 Codex 对活动 profile 的最后一次选择。未启用的 profile 不参与这次选择。

## ④ 修复决策 · 只比较活动 profile 与 Harbor 配置 Gateway 的 provider

活动 profile 省略 provider，或显式选中同一个 provider，可以继续启动。它选择另一个 provider，就在分配 Gateway 前拒绝整 Job。未启用的 provider 和普通推理选项保留。文件输入复用 C07b 的 Job 私有副本机制，保存经校验的 TOML。

## ⑤ 回归验证 · 从待上传 TOML 找到生效的 provider 和密钥来源

内联配置和本地 TOML 各跑 5 种组合。两种冲突方向均验证第一个合法 Trial 也未分配凭证；三个正常组合覆盖继承顶层、显式选择相同的 OpenAI provider 和相同的自定义 provider。成功用例核对最终 TOML 中选中的地址与 Harbor 为该 provider 提供的 Trial 凭证，并确认未启用的 profile 保留。文件用例同时覆盖校验后源文件发生变化。

测试入口是 Dressage 的 `tests/integrations/harbor/test_execution.py::test_codex_active_profile_uses_gateway_provider`。TOML 和凭证变量经过实测，客户端的选择顺序来自源码。[Harbor 合成最终 TOML](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/agents/installed/codex.py#L1987-L2011) · [Codex 选择活动 provider](https://github.com/openai/codex/blob/rust-v0.118.0/codex-rs/core/src/config/mod.rs#L2113-L2125) · [返回 C07 总览](README.md)
