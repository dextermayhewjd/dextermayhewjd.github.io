# C05 · Oracle 的第一份日志写在哪里？

同一道 Oracle 题，Agent 在沙箱里写 `/logs/agent/oracle.txt`，Harbor 在 Trial 收尾时收回这份日志。C05 追的是这个文件从第一次写入到最终交付的过程。

<a id="shared-analysis"></a>

## 共同分析 · Harbor 要什么，修前发生了什么？

### ① 上游约定 · 环境就绪时，Agent 能写第一份日志

共同要求是 **`DressageEnvironment.start()` 返回时，Agent 能在沙箱的 `/logs/agent/` 写入文件**。这道题跑通后，Harbor 应取回含 `solved` 的日志，并从 verifier 取得奖励 1。Harbor 0.26 用 `auto_mounts` 声明要准备的输出目录，用 `auto_mounting` 决定是否自动绑定到宿主机。[Harbor 0.26 对两个参数的说明](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L241-L246)

<a id="mount-choice"></a>

0.18 的常规路径由 Harbor 传入日志子目录绑定，Dressage 按清单执行。0.26 默认关闭自动挂载，此时只绑定用户显式写在 `mounts` 里的宿主路径。[Harbor 0.26 选择宿主挂载的代码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L329-L340)

| 用户怎么运行 bwrap Job | 第一轮升级如何交付日志 |
| --- | --- |
| 希望延续原版日志直挂流程 | 在 Harbor Job 的 `environment.kwargs` 中设置 `auto_mounting: true`。日志直写 Trial 目录。[C02](../02-output-mounts.md) |
| 关闭自动挂载，日志写在沙箱自己的目录 | Dressage 准备沙箱输出目录，Harbor 在 Trial 收尾时取回日志。[C05a](05a-sandbox-log-directories.md) |
| 关闭自动挂载，手动把自己的空目录挂到 `/logs` | 记录为相对 0.18 的已知回归。这道 Oracle 题预建宿主 `agent/` 和 `verifier/` 后，普通日志可交付，奖励为 1。[C05b 同题对照](../../../../investigations/02-output-mounts/c05-mount-experiments.md#c05b-empty-mount) |

### ② 修前表现 · 两种配置下，Oracle 都写不出第一行

用修前提交 `e6c0ce4`（C04）跑同一道题。第一组用默认配置，第二组手动挂一个全新的空宿主目录，让实验能看出 `agent/` 是否由 Dressage 创建。两组都没能交付日志和奖励。C02 的测试先用 `upload_file()` 放入一份日志，它顺手建好了父目录。完整 Trial 让 Oracle 自己写第一行，才观察到缺少 `agent/`。[默认配置的修前现场](../../../../investigations/02-output-mounts/README.md#oracle-log-start) · [手动父挂载的版本对照](../../../../investigations/02-output-mounts/c05-mount-experiments.md#mounted-parent-trial) · [U37 的原观察点](../../../../usage/环境构造与生命周期/U37-Environment.start%20把本次%20bwrap%20会话准备为可用.md#u37)

## 升级范围 · 谁准备日志目录？

### ③ 原因定位 · 挂上宿主目录以后，Agent 看到哪一个 `/logs`？

C02 让 Dressage 只绑定 Harbor 选出的宿主挂载，启动代码也用这份清单建目录。无手动挂载时，清单为空。手动挂整个 `/logs` 时，清单只含父目录。[C02 改了哪份清单](../02-output-mounts.md)

**为什么不能两次都只在沙箱原来的文件树里建 `agent/`？** 在第一种配置里，这么建，Agent 马上就能看到。在第二种配置里，挂载生效后，Agent 打开 `/logs` 看到的是 `host-logs/` 的内容。哪怕原来的文件树里已经有 `agent/`，空的 `host-logs/` 也会把它遮住。[绑定挂载如何遮住原目录内容](https://docs.docker.com/engine/storage/bind-mounts/#bind-mounting-over-existing-data)

<a id="sandbox-log-dirs"></a>

### ④ 修复决策 · C05a 纳入升级，C05b 暂停

C05a 在 Dressage 管理的沙箱文件树里创建目录。手动宿主挂载的内容由用户布置，目录为空只能说明此刻没有条目，目录归属和初始化权限还需要明确约定。第一轮保留 C05a 的提交 `8f51d19`，C05b 待上游确认支持范围。[C05a 实现](05a-sandbox-log-directories.md) · [C05b 暂停决定](05b-mounted-output-directories.md#read-only-parent)

<a id="combined-verification"></a>

### ⑤ 回归验证 · 在 Trial 目录读日志并核对奖励

C05a 的默认 Oracle Trial 收回含 `solved` 的 `agent/oracle.txt`，得到奖励 1。手动空挂载另留一条普通日志用例，记录原版、C05a 基线和历史候选的实际交付。[C05a 验证记录](05a-sandbox-log-directories.md#first-commit-review) · [C05b 普通日志对照](05b-mounted-output-directories.md#delivery-acceptance)

[返回 PR-001 的提交顺序](../../README.md#review-order)
