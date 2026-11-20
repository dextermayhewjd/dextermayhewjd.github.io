# C05a · 在沙箱自有的 `/logs` 下创建 `agent/`

[C05 · 日志挂载方式](README.md)　**C05a（沙箱自有目录）** · [C05b（手动空挂载，已暂停）](05b-mounted-output-directories.md)

**本笔决策**　默认配置下，Dressage 在沙箱自己的文件树里建好输出目录，让 Oracle 能写第一份日志。

修前 `e6c0ce4` · Harbor 0.26.0 · 已本地提交 `8f51d19`。

## ① 上游约定 · 关闭自动挂载时，沙箱仍要提供输出目录

Harbor 0.26 的接口说明给出了分工。**`auto_mounts`** 告诉后端本次 Trial 需要哪些输出目录。**`auto_mounting`** 决定其中的自动挂载是否绑定到宿主机。

## ② 修前表现 · 默认 Trial 打不开第一份日志

这次关闭自动挂载，也没有显式挂载。Oracle 本来会写出答案 `4`，并把运行输出 `solved` 留在沙箱的 `/logs/agent/oracle.txt`。实际 shell 打开这个日志文件就失败了，解法还没开始执行。

| Dressage 启动沙箱时要决定什么？ | Harbor 的预期 | 修前实测 |
| --- | --- | --- |
| 沙箱里要创建这个目录吗？ | **要。** Agent 马上要往里面写文件。 | **缺失。** 只建了父目录 `/logs`。 |
| 要直接绑定到宿主 Trial 目录吗？ | **不用。** 日志写在沙箱里，收尾时再下载。 | **未绑定。** 符合开关设置。 |

## ③ 原因定位 · 建目录的循环取了空的宿主挂载清单

```python
# DressageEnvironment.start()，第 404–405 行
for target in self._harbor_mounts:  # 本次要绑定到宿主机的目标，此例为空
    _rootfs_path(self._rootfs, target).mkdir(parents=True, exist_ok=True)
```

**第 1 行选的是表格第二行的清单，第 2 行做的却是表格第一行的事。** C02 在 `_build_harbor_mounts()` 里把 `self._mounts` 换成了 `self._host_mounts`。关闭自动挂载且没有显式绑定时，得出的 `self._harbor_mounts` 为空。上面是 C04 的代码，循环走零次，沙箱里的 `/logs/agent` 就漏建了。Oracle 第一次写日志时报 `No such file or directory`。收尾时看到的 `DownloadVerifierDirError` 是后续错误。

## ④ 修复决策 · 在沙箱文件树中准备没有宿主挂载的输出目录

**第一笔的实际代码。** 没有宿主挂载覆盖目标时，`start()` 直接在沙箱文件树里建好目录。下面是此次新增循环，省略了源码中的英文注释。

```python
for value in self._mount_targets(writable_only=True):
    target = _environment_path(value)
    if not _is_within(target, _LOGS):
        raise ValueError("Dressage bwrap only accepts Harbor /logs mounts")
    if not any(_is_within(target, mount) for mount in self._harbor_mounts):
        _rootfs_path(self._rootfs, target).mkdir(parents=True, exist_ok=True)
```

默认 Trial 的 `/logs/agent` 就在这里建好，Oracle 随后能打开 `oracle.txt` 写日志。该回归在 C04 副本中因缺少 `oracle.txt` 失败，在升级工作树中通过，并验证了日志包含 `solved`、奖励为 1。

## ⑤ 回归验证 · 从 Oracle 第一次写日志验到 Trial 收到奖励

| 观察的是哪一刻？ | 谁准备第一份日志？ | 这条测试能回答什么？ |
| --- | --- | --- |
| C02 · 日志已经写好 | 测试调用 `env.upload_file()` 上传 `probe.log`，它会顺手创建父目录。 | 三种挂载配置下，Harbor 下载几次、收回的字节对不对？ |
| C05 · Agent 第一次写日志 | 测试只准备题目。默认挂载配置下，`Trial.run()` 让 Oracle 自己写 `oracle.txt`。 | 宿主收到的日志里有 `solved` 吗？Verifier 检查答案后，Trial 收到 1 分了吗？ |

<a id="first-commit-review"></a>

**第一笔的提交依据。** 两次验证均使用默认挂载配置。

- **评审者反馈。** 评审机无法运行隔离网络用例，改用公共网络后实测收回 `agent/oracle.txt`，Verifier 返回 `{"reward": 1}`。
- **提交前复跑。** 保留题目的 `no-network` 配置，原有 15 项环境测试和新 Oracle 回归共 16 项通过。新回归同时检查日志中有 `solved` 和奖励为 1。
- **Dressage 提交。** `8f51d19` · `fix(harbor): create sandbox-owned output directories before agent execution`。在本地 `compat/harbor-0.26` 分支运行 `git show 8f51d19` 可查看完整 diff。

## 证据索引

- **定位错误。** [Dressage 创建目录的循环](https://github.com/dextermayhewjd/Dressage/blob/e6c0ce4912c3edaa1ead0a353419b399a3a3ca87/dressage/integrations/harbor/environment.py#L393-L405) · [Oracle 指定日志文件](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/agents/oracle.py#L110-L116)
- **核对上游约定。** [两个参数的原文](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/base.py#L241-L246) · [Trial 提供的输出目录](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/trial/trial.py#L2089-L2122) · [Mosaic 后端按可写目标建目录](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/mosaic.py#L496)
- **复查测试。** [C02 旧测试写入日志的位置](https://github.com/dextermayhewjd/Dressage/blob/e6c0ce4912c3edaa1ead0a353419b399a3a3ca87/tests/integrations/harbor/test_environment.py#L216-L229) · [C02 的评审记录](../../../../investigations/02-output-mounts/README.md#switch-review) · [完整 Trial 的两组实测](../../../../investigations/02-output-mounts/README.md#oracle-log-start) · [固定三个目录的实验补丁](../../../../investigations/02-output-mounts/c05-sandbox-log-directories.patch)

<a id="mounted-parent-trial"></a>
<a id="mounted-parent-result"></a>
<a id="mounted-parent-review"></a>
<a id="mount-layout-review"></a>

用户手动挂载空的 `/logs` 时，按相对 0.18 的已知回归记录。[C05b 暂停决定](05b-mounted-output-directories.md) · [修前与候选对照](../../../../investigations/02-output-mounts/c05-mount-experiments.md#c05b-empty-mount)

[回到父卡⑤，对照两种配置的结果](README.md#combined-verification)
