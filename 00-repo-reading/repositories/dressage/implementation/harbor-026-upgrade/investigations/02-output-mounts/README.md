# 02 · 为什么 Harbor 回收日志时会把目录复制回它自己？

**当前判断**　修 Dressage 的 bwrap 日志挂载映射。Harbor 0.25 和 0.26 都已复现非空目录复制失败。独立 verifier 会因此在奖励文件写出后抛错，Trial 得不到评分结果。

**对应的三版用法表**　[U42 download_dir 回收环境里的非空日志目录](../../usage/环境执行、文件与挂载/U42-download_dir%20回收环境里的非空日志目录.md#u42) · [U44 Trial 回收前查询挂载是否与宿主目录对应](../../usage/环境执行、文件与挂载/U44-Trial%20回收前查询挂载是否与宿主目录对应.md#u44) · [U58 verifier 读取评分结果](../../usage/题目文件与可选后端/U58-Harbor%20Verifier%20读取运行产生的%20reward.json.md#u58) · [原套件在本问题测到了哪里](../original-test-audit.md#i02)

Trial 收尾时，已经直接写入宿主机的日志应留在原处，位于另一目录的日志才需要复制。

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　`bwrap` 的实际绑定取自 `_mounts`。[environment.py 第 537–539 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L537-L539)

```python
def _build_harbor_mounts(self) -> dict[PurePosixPath, tuple[Path, bool]]:
    mounts: dict[PurePosixPath, tuple[Path, bool]] = {}
    for mount in self._mounts:
```

**Harbor 0.26.0**　挂载查询使用的 `_host_mounts` 受 `auto_mounting` 控制。[base.py 第 338–340 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L338-L340)

```python
self._host_mounts = (
    self._mounts if self.auto_mounting else list(user_mounts.values())
)
```

**Harbor 0.26.0**　日志回收根据挂载查询决定是否直接返回。[trial.py 第 823–825 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L823-L825)

```python
if self.agent_environment.is_path_mounted(source_dir, target_dir):
    await self.agent_environment.prepare_logs_for_host()
    return
```

**据此判断**　自动绑定的日志目录已指向 Trial 的宿主目录。默认设置下 Harbor 查询不到这条绑定，于是再次下载。Dressage 解析出的复制源与目标是同一目录。

<a id="evidence"></a>

## 证据与验证范围

**已存输出**　在 `/logs/agent` 写一个非空文件，按 Trial 的判断调用真实 `download_dir`。[log-recovery-output.txt 第 7–11 行](log-recovery-output.txt#L7-L11)

```text
Harbor 0.26.0 | logs
actual directory equals Trial directory: True
Harbor reports the directory mounted: False
Trial branch: download_dir
nonempty directory copy raised shutil.Error
```


**原来的调用方实际看到了什么？** 同一配置由 `Trial.create` 通过 import path 构造真实 Dressage 后端，每版都向映射到宿主的 `/logs/agent` 写入一个非空文件，再调用 Harbor 原方法 `Trial._download_agent_logs()`。两处计数都调用原实现。 [复现脚本](trial_log_recovery.py) · [三版原始输出](trial-log-recovery.txt)

| 在这次回收中观察什么 | 0.18.0 | 0.25.0 | 0.26.0 |
| --- | --- | --- | --- |
| 准备宿主日志 / 下载目录的调用次数 | 1 / 0 | 0 / 1 | 0 / 1 |
| 方法返回值 / 已下载标记 | `None` / `True` | `None` / `True` | `None` / `True` |
| 宿主原文件 / Trial 错误日志 | 字节相同，无复制错误 | 字节相同，记录 `shutil.Error` | 字节相同，记录 `shutil.Error` |

文件在调用前已通过绑定存在于宿主。新版尝试把目录复制到自身，Trial 捕获异常，仍将回收标为完成。这次使用临时目录，替代了后端可执行文件的位置查询，实际执行了建环境和日志回收。完整 Job、Agent 执行和 verifier 另行验收。 [0.18 回收分支](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L458-L465) · [0.26 捕获异常](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L823-L843) · [0.26 标记回收完成](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L798-L814)

<a id="mount-matrix"></a>

### 只换一个挂载位置，Trial 能收到同一份日志吗？

两次都从 `Trial._download_agent_logs()` 进入，写入同一份 `probe.log`。第二次用 Trial 配置把 `/logs/agent` 显式绑定到另一个宿主目录。回收前确认 Trial 自己的 `agent_dir/probe.log` 尚未出现，再读回收后的文件并逐字节比较。[回放代码](trial_log_recovery.py) · [六次实测的退出码、复制次数和文件结果](trial-log-mount-matrix.txt)

| 文件在回收前放在哪里 | 验收要看到什么 | 0.18.0 | 0.25.0 | 0.26.0 |
| --- | --- | --- | --- | --- |
| 已经在 Trial 的日志目录 | 下载 0 次，原文件可读，无复制错误 | 通过 | 下载 1 次，记录复制到自身的错误 | 同 0.25 |
| 显式绑定在另一个宿主目录 | 下载 1 次，Trial 新收到字节相同的文件，无复制错误 | 下载 0 次，标记已下载，Trial 目录缺文件 | 通过 | 通过 |

六次调用都返回 `None`，已下载标记也都为 `True`。0.18 按后端整体的 `capabilities.mounted` 跳过下载，因此显式覆盖时漏收文件。目标版按实际的源目录和 Trial 目标目录判断，已经能正确处理这个覆盖场景。修 0.26 的默认直挂映射时，应让这两个输入各自满足表中的验收。[0.18 跳过下载的位置](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L458-L465) · [0.26 的路径判断](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L816-L838)

<a id="verifier-reward"></a>

### 奖励已经写出，Trial 能否取得评分结果？

使用 Dressage 生成的单题 DAPO，在临时目录放入一条正确的合成 Agent 结果，直接运行真实 `Trial._run_separate_verifier()`。独立 bwrap 执行生成的 `test.sh`，三版的宿主 verifier 目录里都写出了 `{"reward": 1}`。0.18 默认返回同一奖励。0.25、0.26 默认配置都继续尝试把非空的 `/logs/verifier` 复制到它自身，Harbor 将底层 `shutil.Error` 转为 `DownloadVerifierDirError`，调用方收不到 `VerifierResult`。[完整回放代码](../21-separate-verifier-input/separate_verifier.py) · [三版默认和自动挂载的输出](../21-separate-verifier-input/separate-verifier-output.txt) · [0.26 的下载、异常传播和奖励读取顺序](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/verifier/verifier.py#L274-L310)

保持题目和答案不变，只在 0.25、0.26 的环境 kwargs 设 `auto_mounting=True`，两版都跳过目录下载并返回 reward 1。修后用默认配置运行 `python separate_verifier.py --case default-mounts --check-compatible`，要求磁盘奖励和 Trial 返回值都等于 1。这个对照验证挂载对评分交付的影响，预检和 Agent 模型调用在本次入口之前。[独立 verifier 的输入目录另见问题 21](../21-separate-verifier-input/README.md)

## 处理与验收

**下一步**　在 Dressage 构造 bwrap 挂载的位置，使 Harbor 查询到的宿主目录与实际绑定一致。具体采用自动挂载还是对齐映射，先用回归用例约束显式覆盖和只读行为。

用 `python trial_log_recovery.py --check-compatible` 验证直挂场景。它要求原文件字节一致、回收完成、没有目录复制及相应错误。相同输入在当前 Dressage 基线上，0.18.0 退出 0，0.25.0 与 0.26.0 均因再次复制退出 1。修复后可原样重跑。 [三版退出码](trial-log-recovery.txt#L16-L18)

**通过条件**　从真实 Trial 回收入口分别测试两种目录。直挂的非空目录跳过复制，文件仍可读。换成另一宿主目录后，目标应收到文件。独立 verifier 还须实际返回磁盘上已有的奖励。artifacts 和显式挂载按各自路径核对，夹具测试单独验收。[现有挂载用例](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L115) · [问题 03 的夹具](../03-verifier-fixture/README.md)

<a id="history"></a>

## 判断记录

- 2026-11-11　在 0.25 的静态对照中发现 `_mounts` 与 `_host_mounts` 分工改变。
- 2026-11-18　临时对齐 verifier 夹具后，四项环境测试通过。随后以非空日志单独调用真实 `download_dir`，在 0.26 复现目录复制错误，确认需要修改生产后端。
- 2026-11-18　用相同 Dressage 基线和临时日志复核 0.25、0.26。两版都观测到同一宿主目录、挂载查询为 False、非空复制抛出 `shutil.Error`。二进制定位在探测中替代，文件映射与复制使用真实方法。
- 2026-11-18　从原 Trial 入口分别跑默认直挂和显式改绑，三个版本共六次。另一个目录的日志在目标版能正确交付，旧版在相同输入下漏收。将两项断言归到本问题，修复时可同时验证修正项和已有行为。[两种输入的对照](#mount-matrix)
- 2026-11-19　在 C01 `435e9f2` 和 Harbor 0.26.0 上复跑 `trial_log_recovery.py --check-compatible`，默认直挂下载 1 次、出现复制错误、退出 1；加 `--separate-source` 后下载 1 次、文件如期交付、退出 0。在导出的源码副本上将 `_host_mounts` 对齐到 bwrap 采用的 `_mounts` 后，分别下载 0 和 1 次，两次读回的字节都一致，无复制错误，退出 0。正式工作树仍是 C01，本轮回放只执行了 Agent 日志回收。[C02 提交卡与待验条件](../../prs/001-harbor-026-compatibility/commits/02-output-mounts.md)

<a id="switch-review"></a>

### 提交前 review · 显式关闭自动挂载时，候选代码会生成什么命令？

用 Harbor 0.26.0 分别从 C01 和加入一行候选改法的临时副本构造真实 `DressageEnvironment`。固定 `auto_mounts=[/logs/agent]`，另在用户 `mounts` 中显式传入只读 `/logs/verifier`。比较 `env.is_path_mounted("/logs/agent", paths.agent_dir)` 与 `env._bwrap_command("true", cwd="/app")` 的参数。观察终点为命令生成。

| 实现与开关 | 查询 agent 日志已挂载 | 命令含 agent 的自动 `--bind` | 命令含 verifier 的显式 `--ro-bind` |
| --- | --- | --- | --- |
| C01，关闭 | False | 是 | 是 |
| 一行候选，关闭 | True | 是 | 是 |
| C01 与一行候选，分别开启 | True | 是 | 是 |

这行候选能让查询和现有命令一致。要对齐 Harbor 内置本地后端的开关约定，关闭时还要从 bwrap 命令中省略自动绑定，显式只读绑定则应保留。这是方案 review 要求修改的具体原因。真实沙箱内的只读 I/O 仍须在正式实现上验证。[Harbor 的开关及实际挂载断言](https://github.com/harbor-framework/harbor/blob/4b59c5c46239e92f6c9fde772bdc1a70bdaead02/tests/unit/environments/test_auto_mounting.py#L59-L75)

### 复查入口

- 复现与对照　[0.25 挂载规则](https://github.com/harbor-framework/harbor/blob/v0.25.0/src/harbor/environments/base.py#L267-L275) · [探测脚本](probe.py) · [非空目录输出](log-recovery-output.txt) · [运行准备](../../tools/reproduce.md#setup)
- 完整调用与配置　[environment.py:537](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L537-L565) · [environment.py:467](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L467-L479) · [base.py:313](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/base.py#L313-L340) · [is_path_mounted](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/base.py#L895-L918) · [trial.py:815](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/trial/trial.py#L815-L872)

<a id="oracle-log-start"></a>

### C04 后的完整 Oracle Trial · 第一次写日志时，目录已经在吗？

2026-11-19，固定 Dressage `e6c0ce4`、Harbor 0.26.0、Linux bwrap 和同一道单步题。两次均从 `Trial.run()` 运行 Oracle，使用共享评分环境和 `public` 网络模式。解法写入 `/app/answer.txt` 并输出 `solved`，评分脚本读取答案后写出奖励。只改变 `auto_mounting`。

| 配置 | `start()` 返回时，沙箱内的 `/logs/{agent,verifier,artifacts}` | 第一次写 `oracle.txt` | Trial 结果 |
| --- | --- | --- | --- |
| 省略开关，使用 0.26 默认值 | 三个子目录均缺失 | shell 重定向到 `/logs/agent/oracle.txt` 报 `No such file or directory` | 无奖励，`DownloadVerifierDirError` |
| `auto_mounting=True` | 三个子目录均存在 | 宿主 Trial 目录收到 `agent/oracle.txt` | `{"reward": 1}` |

下一笔先补默认配置的完整 Trial 回归，检查收回的 `oracle.txt` 含 `solved` 且返回奖励为 1。既有 C02 测试用 `upload_file()` 写入样本日志，这个辅助操作顺带创建父目录，因而覆盖的是回收阶段。回到 `DressageEnvironment.start()` 时，分别核对沙箱内创建目录和绑定宿主目录的条件。[启动时创建目录](https://github.com/dextermayhewjd/Dressage/blob/e6c0ce4912c3edaa1ead0a353419b399a3a3ca87/dressage/integrations/harbor/environment.py#L393-L405)

这次升级按日志写入位置确定 C05 的范围。

- 默认配置由 C05a 准备沙箱目录。[C05a · 沙箱自有的日志目录](../../prs/001-harbor-026-compatibility/commits/05-log-directories/05a-sandbox-log-directories.md)
- 手动挂载空 `/logs` 的普通日志用例保留为已知回归。[C05b · 暂停决定与同题对照](../../prs/001-harbor-026-compatibility/commits/05-log-directories/05b-mounted-output-directories.md#mount-path-fix)

[C02 · 已有日志的交付](../../prs/001-harbor-026-compatibility/README.md#mounts) · [返回问题索引](../../README.md#investigations)
