# 21 · 独立 verifier 启动时，Harbor 传入的是哪个目录？

**当前判断**　需要修 Dressage 的 bwrap 启动逻辑。对于从宿主上传测试的独立 verifier，Harbor 0.25 和 0.26 把 Agent 的环境定义目录传给后端，再由 Verifier 上传题目的测试。当前后端却要求这个目录存在，并把其中的普通文件复制进 `/tests`。省略空 `environment/` 的题目在测试上传前报 `NotADirectoryError`。

**对应的三版用法表**　[U31 Trial 构造环境](../../usage/环境构造与生命周期/U31-DressageEnvironment.__init__%20接收%20Trial%20的环境参数.md#u31) · [U37 启动 bwrap](../../usage/环境构造与生命周期/U37-Environment.start%20把本次%20bwrap%20会话准备为可用.md#u37) · [原套件覆盖](../original-test-audit.md#i21)

<a id="sources"></a>

## 两边的源码原文

**Harbor 0.18.0** 从任务的测试目录或步骤测试目录创建独立 verifier，随后跳过上传测试。Dressage 原来可以直接用收到的目录准备 `/tests`。[旧版目录选择](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L656-L664) · [旧版跳过上传](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L571-L581)

**Harbor 0.26.0** 在测试目录没有专用镜像、Dockerfile 或 Compose 定义时，解析结果中的目录是 `paths.environment_dir`，紧随的 `False` 是 `bundled_tests`。[verifier_mode.py 第 138–139 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/task/verifier_mode.py#L138-L139)

```python
paths.environment_dir,
False,
```

Trial 将这个目录交给后端，并用 `bundled_tests` 设置 Verifier 的 `skip_tests_upload`。在本例中，Verifier 会在启动后选择实际的 `tests/` 并上传到 `/tests`。0.25 已采用同样的目录选择。[0.26 环境构造](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L1115-L1127) · [0.26 Verifier 参数](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L1071-L1081) · [测试上传](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/verifier/verifier.py#L209-L226) · [0.25 的解析结果](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/task/verifier_mode.py#L121-L133)

**Dressage 3e3142f** 在独立 verifier 的 `start` 中仍要求这个目录存在。[environment.py 第 409–411 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L409-L411)

```python
if self._separate_verifier:
    if not self.environment_dir.is_dir():
        raise NotADirectoryError(self.environment_dir)
```

目录存在时，后端将其内容递归复制到 rootfs 的 `/tests`。文件随后仍会留在该目录，除非真正的测试上传恰好覆盖同名文件。[Dressage 的复制目标](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L412-L418) · [上传目录使用合并复制](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L445-L457)

<a id="evidence"></a>

## 证据与验证范围

三版都由 Dressage 生成一题 DAPO，将合成的正确答案作为待交付的 Agent 日志，再调用真实 `Trial._run_separate_verifier()`。bwrap、制品上传、生成的 `tests/test.sh` 与 `verify.py`、Harbor Verifier、后端清理均实际执行。在后端原 `start` 返回时记录 `/tests` 的文件列表。这次未运行模型、Gateway 或整个 Job。[运行脚本](separate_verifier.py) · [逐版本输出和兼容断言退出码](separate-verifier-output.txt)

| 题目输入 | 0.18.0 | 0.25.0、0.26.0 |
| --- | --- | --- |
| DAPO 生成的空 `environment/` | 启动时 `/tests` 已有三份测试文件，返回 reward 1 | 启动时 `/tests` 为空，随后 Harbor 上传测试。启用自动挂载时返回 reward 1 |
| 移除该空目录，保留完整 `tests/` | 同样返回 reward 1 | Trial 成功创建，独立 verifier 启动时报 `NotADirectoryError`，未生成奖励 |
| 在 `environment/` 增加 `agent-input.txt` | 启动时只有三份测试文件，返回 reward 1 | 启动时 `/tests` 出现 `agent-input.txt`，本题随后仍返回 reward 1 |

后两组和空目录对照组在 0.25、0.26 均设 `auto_mounting=True`，使 verifier 的日志交付能成功，单独观察输入。旧版沿用本来的直挂。原样 DAPO 总会创建空 `environment/`，在目标版默认挂载下，它实际触发的是奖励文件写出后的回收错误。[生成器创建目录](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/dataset_tools/dapo/prepare_dataset.py#L335-L347) · [问题 02 的评分结果](../02-output-mounts/README.md#verifier-reward)

## 处理与验收

在本次只交付 0.26 的后端中，由 Harbor 的 Verifier 上传宿主测试。bwrap 已限制镜像、Dockerfile 和 Compose 定义，独立 verifier 的普通启动可以直接准备空的 `/tests`。原套件手工把 `task/tests` 作为 `environment_dir`，调整其独立 verifier 夹具时也应对齐新版的输入与上传顺序。[现有定义检查](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/environment.py#L355-L362) · [原测试构造位置](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L44-L48) · [问题 03 的挂载夹具](../03-verifier-fixture/README.md)

分别运行 `python separate_verifier.py --case missing-envdir --check-compatible` 和 `python separate_verifier.py --case nonempty-envdir --check-compatible`。修复后应都取回 reward 1，且后一项的 `tests_at_start` 不含 Agent 环境材料。去掉 `--case` 会一并验收问题 02 的默认挂载。运行需要 Linux 和可正常建立断网命名空间的 bwrap，后端构造还会定位 python3、claude 与 curl。[回放脚本](separate_verifier.py) · [三版运行结果](separate-verifier-output.txt)

<a id="history"></a>

## 判断记录

- 2026-11-18　三版各执行四组输入。0.18 的兼容断言退出 0。0.25 和 0.26 在默认挂载、缺目录、非空目录三组均退出兼容要求，原因分列于问题 02 和本页。
- 2026-11-19　C04 已在 Dressage 升级分支本地提交为 `e6c0ce4`。提交前使用 Harbor 0.26.0 复跑环境测试文件，15 项通过。[修复与回归记录](../../prs/001-harbor-026-compatibility/commits/04-verifier-start.md#formal-check)

[PR-001 的 C04 · 独立 verifier 启动](../../prs/001-harbor-026-compatibility/README.md#verifier-start) · [返回问题索引](../../README.md#investigations)
