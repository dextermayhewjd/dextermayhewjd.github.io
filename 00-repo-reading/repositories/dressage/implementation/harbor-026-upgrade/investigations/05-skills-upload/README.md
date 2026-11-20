# 05 · 新路径 `/runtime/skills` 需要改 bwrap 目录常量吗？

**当前判断**　保留 Dressage 现有的 skills 上传实现。目标版 0.26.0 已能把文件写入新路径并读回。

**对应的三版用法表**　[U40 upload_dir 把一个目录交给环境](../../usage/环境执行、文件与挂载/U40-upload_dir%20把一个目录交给环境.md#u40) · [原套件在本问题测到了哪里](../original-test-audit.md#i05)

升级后的默认技能目录变成 `/runtime/skills`，要核对没有预建这个目录时第一次上传是否成功。

最初讨论中的 Gemini 建议是“需在 `_STANDARD_ROOTFS_DIRS` 中补齐”两个目录。要核对的是上传时父目录由谁创建。[原建议全文](../../archive/decisions.md#skills-proposal)

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　上传文件时创建目标目录及其父目录。[environment.py 第 449–450 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L449-L450)

```python
target = self._host_path(target_dir, writable=True)
target.mkdir(parents=True, exist_ok=True)
```

**Harbor 0.18.0**　升级前的默认路径。[paths.py 第 41 行](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/trial/paths.py#L41)

```python
default_skills_dir: PurePosixPath = PurePosixPath("/harbor/skills")
```

**Harbor 0.26.0**　当前 Trial 注入 skills 时采用的新默认路径。[paths.py 第 46 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/paths.py#L46)

```python
default_skills_dir: PurePosixPath = PurePosixPath("/runtime/skills")
```

**据此判断**　换成 `/runtime/skills` 会改变上传地址。Dressage 在上传过程中创建父目录，是否还要预建目录可以直接用一个文件验证。

<a id="evidence"></a>

## 证据与验证范围

**已存输出**　上传 `demo/SKILL.md`，再从新目录读回内容。[skills-upload-output.txt 第 1–5 行](skills-upload-output.txt#L1-L5)

```text
Harbor 0.25.0 | skills
uploaded skill read back from /runtime/skills/demo/SKILL.md

Harbor 0.26.0 | skills
uploaded skill read back from /runtime/skills/demo/SKILL.md
```

文件复制与读回已有实测。实际 Agent 用户能否按其权限读取，是另一个观察点。

## 处理与验收

**下一步**　继续使用 Harbor 选定的路径。在 PR 需要承诺完整技能注入时，给真实 Trial 配一份最小技能，从 Agent 的运行用户检查文件可见性。[Trial 技能入口](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/trial/trial.py#L1844)

**通过条件**　后端上传后能读回相同内容。对承诺了 Agent 注入的配置，还要记录 Agent 能读到的路径和内容。

<a id="history"></a>

## 判断记录

- 2026-11-18　在临时 bwrap 根目录调用真实文件上传方法，0.25 和 0.26 均能从指定新路径读回同一份 `SKILL.md`。当前证据覆盖后端传输。

### 复查入口

- 复现与对照　[文件探测](../02-output-mounts/probe.py) · [读回结果](skills-upload-output.txt)
- 完整调用与配置　[environment.py:445](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L445-L457) · [0.18 paths.py:41](https://github.com/harbor-framework/harbor/blob/v0.18.0/src/harbor/models/trial/paths.py#L41) · [0.26 paths.py:46](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/models/trial/paths.py#L46) · [Trial 上传调用](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/trial/trial.py#L1844-L1860)

[PR-001 如何审查此问题](../../prs/001-harbor-026-compatibility/README.md#skills) · [返回问题索引](../../README.md#investigations)
