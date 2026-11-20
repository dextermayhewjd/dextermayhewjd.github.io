# 08 · Trial 目录脱敏时，Dressage 的 bundle 应该放在哪里？

**当前判断**　0.26 在 END 发出前已清理受测 Trial 文本，回调再写入的测试标记也在退出时被清理。Dressage 位于目录外的 bundle 可按最终物理 ID 从磁盘读回。

**对应的三版用法表**　[U29 TrialHookEvent 的物理 ID、结果对象与输出目录](../../usage/Trial%20事件与目录/U29-TrialHookEvent%20的物理%20ID、结果对象与输出目录.md#u29) · [U30 END 前后的 Trial 目录及外部 bundle 路径](../../usage/Trial%20事件与目录/U30-END%20前后的%20Trial%20目录及外部%20bundle%20路径.md#u30) · [原套件在本问题测到了哪里](../original-test-audit.md#i08)

Trial 收尾要清理输出中的敏感值，Dressage 还要在 END 回调提交并能再次读取这次尝试的结果。

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　磁盘提交在写 bundle 前检查目标位于 Trial 目录外。[artifacts.py 第 480–484 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L480-L484)

```python
if self.mode in {"disk", "both"}:
    output_path = self.bundle_path(bundle)
    _ensure_outside_trial_dir(output_path, trial_dir)
    try:
        await asyncio.to_thread(self._write_model_atomic, output_path, bundle)
```

**Harbor 0.26.0**　Harbor 的原注释解释了 `END` 回调之前为什么先脱敏。[trial.py 第 673–676 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L673-L676)

```python
self.paths.result_path.write_text(self.result.model_dump_json(indent=4))
# END hooks may upload trial files, so scrub them before hooks run.
self._scrub_jobs_dir()
await self._emit(TrialEvent.END)
```

**据此判断**　Harbor 可以在 `END` 回调开始前改写 Trial 文件。Dressage 的路径约束把持久化 bundle 放在该目录之外。还有一次退出时的扫描，需核对最终保留的两类文件。

<a id="evidence"></a>

## 证据与验证范围

**已有测试断言 · Dressage 3e3142f**　用 store 读回 bundle 的 schema 和路由字段。[test_data_path.py 第 84–86 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_data_path.py#L84-L86)

```python
payload = json.loads(store.bundle_path(first).read_text())
assert payload["schema_version"] == "dressage.harbor.trajectory/v2"
assert payload["routing_guarantee"] == "configure_only"
```

同一正常 Job 在三版各写了两份普通 UTF-8 文件。第一份在 Trial 准备阶段写入合成标记，第二份在 END 回调新建。END 读取第一份时，0.18 和 0.25 仍能看到标记，0.26 已清理。Job 返回后，第二份标记只在 0.18 仍可见。三版从 Trial 目录外的真实 Store 读回所选 bundle，UUID 与最终结果一致。标记来自夹具的 Agent env，未观察任意第三方文件、公开配置或 bundle 自身敏感字段的清理效果。[0.18](../22-retry-policy/job-trial-output.txt#L2) · [0.25](../22-retry-policy/job-trial-output.txt#L10) · [0.26](../22-retry-policy/job-trial-output.txt#L18) · [探测范围](../22-retry-policy/probe.py)

## 处理与验收

**下一步**　另验 Store 目标位于 Trial 目录内时的拒绝结果，并按 Dressage 的公开配置字段单独核对脱敏。

**通过条件**　Harbor 声明处理的文件中的测试值已脱敏，外部 bundle 仍可读取、公开配置满足 Dressage 的脱敏约定。Trial 内部的 bundle 路径被拒绝。

<a id="history"></a>

## 判断记录

- 2026-11-18　源码核对确认两端各自的路径检查。全目录、任意第三方日志的脱敏效果尚无实测证据。

### 复查入口

- 复现与对照　[现有提交测试](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_data_path.py#L65)
- 完整调用与配置　[artifacts.py:482](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L482) · [artifacts.py:1133](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1133) · [Trial.run 收尾](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/trial/trial.py#L629-L637) · [END 前清理](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/trial/trial.py#L667-L676) · [_scrub_jobs_dir](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/trial/trial.py#L1247-L1332)

[PR-001 如何审查此问题](../../prs/001-harbor-026-compatibility/README.md#runtime) · [返回问题索引](../../README.md#investigations)
