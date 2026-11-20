# C05b · 手动挂载空 `/logs` 的已知回归（暂停）

<a id="mount-path-fix"></a>

[C05 父卡](README.md) · [C05a 沙箱自有目录](05a-sandbox-log-directories.md) · [回到原版的一次 Trial](../../../../README.md#original-integration)

**C05b 已复现，修复暂缓。** 在空宿主目录里补建子目录，确实能让同一道 Oracle 题重新交付日志和评分。但“目录现在是空的”无法证明它由本次 Trial 独占，也无法判断用户是否希望 Dressage 改动它。PR-001 草稿保留 C02 的日志直挂和 C05a 的沙箱日志，并向上游披露手动空挂载的已知回归。[第一轮的三种运行方式](README.md#mount-choice)

## ① 上游约定 · Agent 在哪里写，Harbor 从哪里收？

Oracle 在沙箱写 `/logs/agent/oracle.txt`。这次显式绑定的是父目录 `/logs`，所以在运行中，宿主上的同一份文件是 `host-logs/agent/oracle.txt`。Trial 收尾时把 Agent 日志交到自己的 `agent/`，把常规发布产物交到 `artifacts/logs/artifacts/`。[Harbor 的挂载开关](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/base.py#L241-L246) · [Agent 日志回收](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L798-L838)

## ② 修前表现 · 空目录挡住了 Oracle 的第一行日志

在 C05a 基线 `8f51d19`，把空宿主目录挂到 `/logs`，Oracle 打不开 `/logs/agent/oracle.txt`，收尾报 `DownloadVerifierDirError`。若用户事先建好 `agent/` 和 `verifier/`，这道题能交付普通日志并得 1 分。[修前与候选对照](../../../../investigations/02-output-mounts/c05-mount-experiments.md#c05b-empty-mount)

## ③ 原因定位 · 沙箱原来的目录被空宿主目录遮住

```python
# C05a 的 start()。本例 target 为 /logs/agent，mount 为 /logs。
if not any(_is_within(target, mount) for mount in self._harbor_mounts):
    _rootfs_path(self._rootfs, target).mkdir(parents=True, exist_ok=True)
```

条件为假，Dressage 跳过建目录。此时 Agent 打开 `/logs` 看到的是空的 `host-logs/`，第一行日志需要的父目录就缺在这里。[停在第一次写入前的实测](../../../../investigations/02-output-mounts/c05-mount-experiments.md#first-write-probe)

<a id="read-only-parent"></a>

## ④ 修复决策 · 宿主目录的初始化由谁授权？

| 怎么走到这一步 | 哪个观察改变了决定 |
|---|---|
| 用同一道题回查原版 | 0.18 会在手动父挂载上再挂日志子目录。0.26 默认只留下手动父挂载。原本能收到的两份日志和奖励都消失了，因此值得尝试修复。[版本对照](../../../../investigations/02-output-mounts/c05-mount-experiments.md#original-integration-parity) |
| 先试通用挂载检查 | 空挂载跑通了，但另一组原本能原样交付日志的配置被拒绝启动，还有一组原本应报缺失的只读输入被意外创建。继续扩大启动检查会改变已有用户配置的行为。[同题控制组](../../../../investigations/02-output-mounts/c05-mount-experiments.md#c05b-plain-comparison) |
| 再试只初始化全新空目录 | 窄版恢复了普通日志和评分。评审仍指出，用户指定的空源可能就是 Trial 的回收目录，通过另一个宿主挂载路径访问时，两者名字不同。此时补建 `agent/` 就会改写回收区。目录初始化中途失败还可能留下半成品，重试时又被当作用户预建的目录。[窄版候选](../../../../investigations/02-output-mounts/c05b-empty-log-mount.patch) |

**停止的理由。** C05a 在 Dressage 创建的沙箱文件树里建目录，归属明确。C05b 要在用户指定的宿主目录里写入并处理失败后的清理。启动代码能观察到目录为空，却缺少区分“交给后端初始化的工作目录”和“碰巧为空的用户或 Trial 目录”的约定。两版候选已归档，普通日志的复现继续保留。[工作树与归档记录](../../README.md#current-status)

**请维护者决定**　显式绑定一个空宿主目录到 `/logs`，是否应当授权 bwrap 后端初始化其中的输出子目录？若这属于正式用法，就约定可修改哪些目录、失败后谁负责清理，再单独提修复。如果它是升级的合入条件，就把 C05b 列为阻塞项。

<a id="delivery-acceptance"></a>

## ⑤ 回归证据 · 普通日志和评分

同一道单步题在 Trial 目录核对 `agent/oracle.txt` 的 `b"solved\n"`、`agent/run/probe.log` 的 `b"fresh probe\n"`，以及 verifier 奖励。0.18 原版和 0.26 空目录候选都交付了两份日志并得 1 分，C05a 基线缺两份日志和奖励。复现用例保存在调查目录。[Oracle 用例](../../../../investigations/02-output-mounts/c05b_log_delivery.py) · [版本与预建目录对照](../../../../investigations/02-output-mounts/c05-mount-experiments.md#c05b-empty-mount)

### 可直接用于上游 PR 的说明

> **Known bwrap regression with a manually mounted, empty `/logs`.** The same Oracle trial delivered both expected log files and a reward of 1 on Harbor 0.18. On 0.26, with automatic mounting disabled, the empty host directory hides the sandbox log directories. The trial then fails to deliver either log or a reward. Precreating `agent/` and `verifier/` in the host directory restored both logs and the reward for this task. Jobs that want logs written directly to the Trial directories can enable `environment.kwargs.auto_mounting`.
>
> We tested a fix that initializes an empty host directory during startup. It restored this trial, but the mount source can also refer to a Trial collection directory under another path. We propose deferring host-directory initialization until its ownership and cleanup rules are explicit. Should initializing a caller-supplied empty `/logs` be a requirement for merging the 0.26 upgrade?
