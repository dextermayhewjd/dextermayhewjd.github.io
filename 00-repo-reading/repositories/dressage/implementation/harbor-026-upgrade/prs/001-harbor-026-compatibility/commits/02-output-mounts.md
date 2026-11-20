# C02 · 让 Harbor 在 Trial 收尾时正确回收 Dressage 沙箱的日志

**本笔决策**　Dressage 按 Harbor 的宿主挂载清单绑定日志目录，让 Harbor 收尾时能正确判断要不要复制日志。

修前 `8827b11` · Harbor 0.26.0 · 已推送 `8023acd`。

**C02 的问题出在 Agent 写完日志之后，Harbor 判断要不要把日志复制回来。**

假设 Agent 在沙箱里写了一行 `hello`。在我们复现问题的那次运行里，Dressage 已经把沙箱日志目录挂到了宿主机的 Trial 目录。“挂载”在这里的意思是，两个路径指向同一份文件。

```text
Agent 在沙箱里写入      /logs/agent/probe.log
                               ↓ 同一份文件
宿主机立刻就能读到      trials/t1/agent/probe.log
```

所以，Harbor 收尾时只需要确认文件已经在那里，就可以结束。实际发生的却是：

1. **Harbor 问 Dressage 的环境对象**：“`/logs/agent` 已经挂到这个 Trial 的日志目录了吗？”
2. **环境对象回答 `False`。** Dressage 建沙箱时采用了这条挂载，但 Harbor 0.26 用来回答这个问题的挂载清单里没有它。
3. **Harbor 据此尝试复制 1 次，复制失败。** 源目录和目标目录实际是同一个目录，`download_dir()` 报了 `shutil.Error`。宿主机读到的仍是原文件。

这次实测中，`probe.log` 仍然可读。第 2 步暴露了矛盾，原因在更早的建沙箱阶段：**Harbor 的自动挂载开关关着，Dressage 却把日志目录自动挂上了。C02 要让 Dressage 遵守这个开关。**

固定开关为关，用户也没有手动指定挂载。只看这一份日志：

| | Agent 写完后，文件在哪里？ | Harbor 收尾时查询到什么？ | 复制一次会怎样？ |
| --- | --- | --- | --- |
| 修前实测 | 已经在宿主 Trial 目录 | `False` | 从该目录复制到自身，失败 |
| 修后实测 | 还在沙箱自己的目录 | `False` | 从沙箱复制到宿主 Trial 目录，成功 |

## ① 上游约定 · Harbor 核对日志实际挂到了哪里

挂到正确位置后，日志收集仍会运行，但可以直接跳过复制。**上游改的是收集流程中“凭什么跳过复制”的判断。** 下面跟同一个默认直挂场景，看两个版本实际走到哪一行。

```python
# Harbor 0.18 · Trial._download_agent_logs()
if self.agent_environment.capabilities.mounted:        # Dressage 支持挂载 → True，进入这里
    await self.agent_environment.prepare_logs_for_host()
    self._are_agent_logs_downloaded = True
    return                                            # 本次直接结束，调用 download_dir 0 次
```

```python
# Harbor 0.26 · Trial._download_role_logs()，仅摘录本例经过的判断和无过滤下载分支
if self.agent_environment.is_path_mounted(source_dir, target_dir):  # 默认关闭时查到 False；修前沙箱却已直挂
    await self.agent_environment.prepare_logs_for_host()
    return                                                         # 查询为 True 才在此结束，本次没走到

await self.agent_environment.download_dir(                         # 本次走到这里，发起 1 次复制
    source_dir=source_dir.as_posix(),                              # 沙箱 /logs/agent，实际已指向下面的目录
    target_dir=target_dir,                                         # 宿主 Trial 的 agent_dir，复制到自身时报错
)
```

0.18 问的是「这个后端支持挂载吗？」。从 0.25 起，Harbor 问的是「沙箱里的这个目录，实际指向本次 Trial 要读取的那个宿主目录吗？」。这一区别在用户把 `/logs/agent` 改绑到另一个目录时很重要。后端依然支持挂载，Trial 却必须复制一次才能拿到日志。

## ② 修前表现 · 同一份日志被复制到自身

固定 Dressage C01 `8827b11`、Harbor 0.26.0 和同一份非空日志，只改变日志在回收前的位置。以下是本轮实际回放结果。

| 回收前，`probe.log` 在哪里？ | Trial 应当做什么？ | 修前实际发生了什么？ |
| --- | --- | --- |
| **已经在 Trial 的 `agent_dir/`**。现有 Dressage 在默认配置下建立了这条绑定。 | 跳过下载，原文件可读。 | 尝试复制 1 次，因源和目标是同一目录而失败，记录 `shutil.Error`。原文件仍在。 |
| **在另一个宿主目录 `external-agent-logs/`**。用户显式改绑，Trial 目录起初没有该文件。 | 下载 1 次，让 Trial 收到原字节。 | 下载 1 次，文件如期出现，字节一致。这个分支已经正确。 |

两次调用都返回 `None`，都把日志标为已下载。第一行的复制异常被 Harbor 记入 Trial 日志。从返回值或“已下载”标志看，两次没有差别。

## ③ 原因定位 · 实际绑定和路径查询用了两份清单

```python
# DressageEnvironment._build_harbor_mounts
for mount in self._mounts:                   # Includes automatic and explicit mounts.
    ...

# Harbor 0.26 BaseEnvironment.__init__
self._host_mounts = (
    self._mounts if self.auto_mounting else list(user_mounts.values())
)
```

`auto_mounting` 默认是 `False`。此时 Harbor 只在 `_host_mounts` 中登记用户显式声明的绑定，`is_path_mounted()` 也查这张表。Dressage 却从包含自动绑定的 `_mounts` 构造 bwrap 命令。于是对同一个 `/logs/agent`，**沙箱已经直挂到 Trial 目录，Harbor 查询却得到 `False`**。多余的下载发生在下一步，分歧在建环境时就产生了。

## ④ 修复决策 · bwrap 遵守自动开关和用户显式挂载

本地工作树只改了 `_build_harbor_mounts()` 选择挂载项的一行。识别独立 verifier 的 `_is_separate_verifier_session()` 继续读取完整的 `self._mounts`。

```diff
-        for mount in self._mounts:
+        for mount in self._host_mounts:
```

这样，开启自动挂载时可以直接把日志写进 Trial 目录。关闭时，自动绑定应从 bwrap 命令中消失，用户显式配置的绑定仍应保留，包括只读属性。

**为什么不直接写 `self._host_mounts = self._mounts`？** 这行改法在临时副本上让前述两例分别下载 0 次和 1 次，看似修好了。但显式关闭自动挂载后，bwrap 仍然生成自动 `--bind`。它改正了 Harbor 对现状的报告，同时保留了违背开关的行为。

## ⑤ 回归验证 · 查下载次数，再比对收回的日志字节

### 5.1 原测试直接调用环境，漏了 Trial 决定是否下载的分支

原有的 `test_paths_mounts_and_arbitrary_artifacts_remain_safe` 测路径越界、只读限制和文件上传。其中一次真实调用是 `await environment.upload_file(source, "/var/results/artifact.txt")`。直接传输可以成功，即使 Harbor 在收尾时选错了下载分支。这条安全测试应保留。

### 5.2 新增集成测试怎样抓住这次故障？

本地的 `tests/integrations/harbor/test_environment.py::test_trial_recovers_agent_logs` 参数化了三种配置。每次都写同样的非空 `probe.log`，从真实的 `Trial._download_agent_logs()` 进入。`download_dir` 在计数时仍执行原方法。

| 配置 | 回收前 Trial 目录已有文件？ | 应下载几次？ | 这一例能发现什么？ |
| --- | --- | --- | --- |
| 开启自动挂载，使用 Trial 默认日志目录 | 有 | 0 | 已经直挂却又复制到自身。 |
| 关闭自动挂载，显式把日志改绑到另一宿主目录 | 无 | 1 | 用户改绑被忽略，或跳过下载使 Trial 漏了日志。 |
| 关闭自动挂载，没有显式绑定日志目录 | 无 | 1 | 关闭开关后 bwrap 仍把日志直写到宿主。 |

下面按验收表简写共同断言。

```python
assert target_file.exists() == expected_before
await trial._download_agent_logs()
assert download.await_count == expected_downloads
assert target_file.read_bytes() == sample
assert "Failed to download logs" not in trial.paths.log_path.read_text()
```

显式改绑那一例，在回收**前**另验 `assert (external_logs / "probe.log").read_bytes() == sample`。这样即使最终文件到了 Trial 目录，也能辨别 Dressage 是否真的使用了用户指定的来源。另查关闭开关时生成的 bwrap 命令，自动日志 `--bind` 应消失，显式只读 `--ro-bind` 应保留。

### 5.3 当前证据与下次升级的通过条件

**已实测。** 在当前 C01 `8827b11` 上，从升级笔记根目录运行下面两条命令。默认配置仍然复制到自身，显式改绑能正确交付，与初版 C01 `435e9f2` 的记录一致。

```bash
python investigations/02-output-mounts/trial_log_recovery.py --check-compatible                    # exit 1
python investigations/02-output-mounts/trial_log_recovery.py --check-compatible --separate-source  # exit 0
```

旧回放假定默认直挂，保留作修前证据。在同一个 Harbor 0.26.0 环境中，对基线加入新的三个用例，得到 2 过 1 败，只有关闭自动挂载时文件过早出现在宿主目录。再应用第 ④ 节的一行改动，三例全过。修后复跑用 `pytest tests/integrations/harbor/test_environment.py -k trial_recovers_agent_logs`。

**下游实测。** 在真实 bwrap 中，默认配置的独立 verifier 写出 `{"reward": 1}`，Trial 返回同一奖励。沙箱写出的 `/logs/artifacts/check.txt` 经 Trial 收集后字节一致。另一次显式只读挂载验证中，文件可读、写入失败，自动 agent 日志绑定未出现在 bwrap 命令中。

**环境测试文件仍有两项旧失败。** C01 基线为 7 过 2 败，C02 工作树为 10 过 2 败。同一对 verifier 测试均在夹具构造阶段报 `separate verifier does not have Harbor's verifier mount shape`。C03 接续这项夹具适配。

**个人仓库提交**　`8023acd fix(harbor): honor automatic mount settings in bwrap`。提交前在 Harbor 0.26.0 上复跑三种日志回归，全部通过。Verifier 夹具调整归 C03，完整 CLI Trial 和训练入口由 PR-001 验收。[英文提交说明与 diff](https://github.com/dextermayhewjd/Dressage/commit/8023acdaaba3fafe58a340a23e02608a6663a72a)

## 证据索引

| 核对哪一节 | 打开后看什么 | 证据入口 |
| --- | --- | --- |
| ① 上游约定 | 对照旧版判断后端能力、新版查询两个路径，以及改动来源。 | [Harbor 0.18 回收判断](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L458-L465) · [Harbor 0.26 回收与错误处理](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L798-L843) · [上游改动](https://github.com/harbor-framework/harbor/commit/4b59c5c46239e92f6c9fde772bdc1a70bdaead02) |
| ② 修前现象 | 看同一份日志的下载次数、目标字节和复制错误。 | [三版原始回放输出](../../../investigations/02-output-mounts/trial-log-mount-matrix.txt) |
| ③ 根因 | 对照 bwrap 的绑定来源、Harbor 的宿主挂载清单和路径查询。 | [Dressage 构造挂载](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L537-L550) · [Harbor 选出宿主挂载](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L313-L340) · [Harbor 查询两个路径](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L895-L915) |
| ④ 候选修法 | 查临时赋值的结果，以及关闭开关时实际生成的 bwrap 参数。 | [调查 02 · 临时实验](../../../investigations/02-output-mounts/README.md#history) · [调查 02 · 开关对照](../../../investigations/02-output-mounts/README.md#switch-review) · [Harbor 对自动挂载的测试](https://github.com/harbor-framework/harbor/blob/4b59c5c46239e92f6c9fde772bdc1a70bdaead02/tests/unit/environments/test_auto_mounting.py#L59-L74) |
| ⑤ 测试与复跑 | 定位旧测试、日志回放的真实入口及可执行命令。 | [Dressage 原有路径测试](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L115-L155) · [修前回放脚本](../../../investigations/02-output-mounts/trial_log_recovery.py) · [复跑手册 · U42、U44](../../../tools/reproduce.md#run-probes) |
| ⑤ 下游验收 | 查磁盘评分与 Trial 返回结果的对照，以及整份 PR 的验收边界。 | [调查 02 · verifier 奖励](../../../investigations/02-output-mounts/README.md#verifier-reward) · [PR-001 的合入条件](../README.md#acceptance) |
