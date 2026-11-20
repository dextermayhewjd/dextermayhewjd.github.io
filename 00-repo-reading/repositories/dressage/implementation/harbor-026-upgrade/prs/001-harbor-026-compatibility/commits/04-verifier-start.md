# C04 · 评分脚本还在，为什么独立评分沙箱启动失败？

**本笔决策**　Dressage 启动独立评分沙箱时留出空的 `/tests`，由 Harbor 随后把题目的评分文件上传进去。

修前 `600b8cd` · Harbor 0.26.0 · 已推送 `e6c0ce4`。[Dressage 提交](https://github.com/dextermayhewjd/Dressage/commit/e6c0ce4912c3edaa1ead0a353419b399a3a3ca87)

想跟着当时的排查过程走，可以从②的题目开始，沿③读报错变量，回①找路径来源，再用④的两种改法和⑤的文件断言作判断。

## ① 上游约定 · 先启动评分环境，再上传宿主机提供的测试

Harbor 上游 PR #3258 同时改了 `trial.py` 的两处调用，随 0.24.0 发布。这里对照 0.18.0 和本次目标 0.26.0，只看由宿主机提供测试的题目。

**创建独立评分环境时**，`Trial._separate_verifier_env()` 传给环境工厂的实参变了（旧版第 619 行，新版第 1118 行）。

```diff
-            environment_dir=self._verifier_env_build_context(step_cfg),
+            environment_dir=definition.directory,
```

同一道题，旧行传 `task/tests/`，新行传 `task/environment/`。`definition` 是评分环境的配置。

**创建评分器时**，`Trial._run_separate_verifier()` 传入的上传开关也变了（旧版第 580 行，新版第 1080 行）。

```diff
-                    skip_tests_upload=True,
+                    skip_tests_upload=definition.bundled_tests,
```

旧版跳过上传，靠 Dressage 在启动时放好测试。新版在本题得到 `False`，意思是**沙箱启动后由 Harbor 发起上传**。

## ② 修前表现 · 有评分脚本，却在启动时停下

题目问 `2 + 2`。做题沙箱已经交卷，答案是 `4`。现在用**另一个沙箱**评分。题目提供了 `task/tests/test.sh`，省略了可选的 `task/environment/`。预期是脚本运行，Trial 收到 1 分。

固定原 Dressage 基线 `3e3142f` 和上述题目，回放得到两种结果：

```text
Harbor 0.18    启动评分沙箱成功 → 执行 test.sh → Trial 收到 1 分
Harbor 0.26    启动评分沙箱时抛出 NotADirectoryError → Trial 没有收到奖励
```

在升级分支 C03（`600b8cd`）上用 Harbor 0.26 再做一次对照，只改目录是否存在。同样开启自动挂载，留一个空的 `environment/` 时，Harbor 向沙箱的 `/tests` 上传 1 次，Trial 收到 1 分；省略目录时，上传 0 次。

**第一次可以停在这里。** 新版停在评分沙箱的 `start()`，脚本还没上传。追问原因时，从③的 `is_dir()` 接着看。

## ③ 原因定位 · 后端把环境目录当成了测试目录

```python
# DressageEnvironment.start()，C03 第 410–412 行
if self._separate_verifier:
    if not self.environment_dir.is_dir():
        raise NotADirectoryError(self.environment_dir)
```

这道题的脚本一直在 `task/tests/test.sh`。在同一历史基线的回放里，第 411 行用的 `self.environment_dir` 在 0.18 指向 `task/tests/`，在 0.26 指向本题省略的 `task/environment/`。所以同一行检查在旧版通过，在新版抛错。这就把②的启动失败定位到这一行。这个参数的来源见①。

## ④ 修复决策 · 移除启动时的提前复制，保留评分器上传

### 只给复制加一个条件会怎样？

先在 C03 临时副本中试「目录存在才复制」。缺目录的题重新得了 1 分。接着在同一道题的环境目录放入普通文件 `agent-input.txt`，检查沙箱刚启动、Harbor 还没上传测试的那一刻。三份代码使用相同的 Harbor 0.26.0 和输入。

| 只改变 Dressage 的哪一处 | 缺目录的题 | 有普通文件的题：启动时沙箱 `/tests` 里有什么？ | 有普通文件的题：最终奖励 |
| --- | --- | --- | --- |
| 原代码 | 启动中止，无奖励 | `agent-input.txt` | 1 |
| 仅在目录存在时复制 | 启动成功，得 1 分 | `agent-input.txt` | 1 |
| 移除整段提前复制 | 启动成功，得 1 分 | 空目录 | 1 |

只看最终分数，后两种修法都像是正确的。检查启动时的文件清单，才能看出「目录存在才复制」仍然会把环境材料放进评分目录。

### 谁接手上传？为什么可以删掉旧分支？

```python
# Harbor · Trial._separate_verifier_env()，trial.py 第 1135、1145 行
await env.start(force_build=False)  # Dressage 已在 _initialize_rootfs() 中创建空的 /tests/
yield env                           # Trial 接到 target_env，通过 environment=target_env 交给评分器

# Harbor · Verifier.verify()，verifier.py 第 209、220–223 行
if not self._skip_tests_upload:     # 本题进入此分支
    # ...选好题目的测试文件后
    await self.environment.upload_dir(
        source_dir=source_dir,                # 题目筛选出的测试文件，其中有 test.sh
        target_dir=str(env_paths.tests_dir),  # 评分沙箱里的 /tests/
    )
```

Harbor 负责决定上传时机。这里的 `self.environment` 是刚启动的 Dressage 评分环境，其 `upload_dir()` 第 446–458 行负责复制。临时回放中，四组输入都只向 `/tests` 上传 1 次，上传后沙箱里的 `test.sh` 和源文件逐字节一致。

因此候选补丁只删 `DressageEnvironment.start()` 第 410–419 行的提前复制分支。`start()` 继续初始化沙箱，`upload_dir()` 继续搬文件。

```diff
-        if self._separate_verifier:
-            if not self.environment_dir.is_dir():
-                raise NotADirectoryError(self.environment_dir)
-            await asyncio.to_thread(
-                shutil.copytree,
-                self.environment_dir,
-                _rootfs_path(self._rootfs, PurePosixPath("/tests")),
-                dirs_exist_ok=True,
-                symlinks=True,
-            )
         relay_path = self._session_root / "relay.py"
```

<a id="formal-check"></a>

## ⑤ 回归验证 · 同时核对评分沙箱的文件和奖励

**旧测试为什么漏掉了？** 隔离测试自己给 verifier 传了 `task/tests/`，把脚本放在那里，要求刚启动就能看到 `test.sh`。实际的 Harbor 0.26 Trial 传入 `task/environment/`，随后才上传测试。

**刚启动时看隔离。** 两个沙箱的 `/tests` 都应为空。只向评分沙箱上传一个脚本后，隔离测试在评分侧读回原始字节，并再次确认 Agent 侧仍为空。

**评分时看实际收到的文件。** 正式集成测试在宿主机准备 `tests/test.sh` 和 `tests/fixtures/answer.txt`，从 Harbor 的 `Trial._run_separate_verifier()` 进入。运行中的评分脚本把此刻的 `/tests` 复制到评分日志目录的 `received/`，再读取答案并写奖励。测试从这个快照核对全部相对路径与字节。下面节选正式断言。

```python
assert actual_files == {
    "test.sh": (tests_dir / "test.sh").read_bytes(),
    "fixtures/answer.txt": (tests_dir / "fixtures/answer.txt").read_bytes(),
}
assert json.loads(trial.paths.reward_json_path.read_text()) == {"reward": 1}
assert result.rewards == {"reward": 1}
```

**实测这条断言能发现什么？** 修前，含普通文件的题在评分沙箱里多出了 `agent-input.txt`，文件清单比对失败。修后，在一次性沙箱中模拟漏传 `fixtures/answer.txt`，脚本无法产生奖励。另一轮只给上传后的 `test.sh` 追加一行注释，脚本仍能给分，字节比对仍能发现差异。

### 执行真实回归所需的权限与复验结果

**复评 P2 · 已处理。** 复评环境装有 `bwrap`，但三种题目都停在创建 `NETLINK_ROUTE` socket 这一步。仅让 bwrap 在断网沙箱中运行 `/bin/true` 就能复现相同的权限错误，全程无需加载 Harbor。0.26 升级改变了评分文件的交付方式，新增的真实回归同时暴露了测试机器原有的权限限制。

**两种环境各验一次。** 三例共用测试夹具 `bwrap_network_namespace`，每个测试模块执行一次探测。受限环境定向运行得到 **3 项跳过**，原因明确为 `NETLINK_ROUTE: Operation not permitted`；具备权限的环境运行完整 `test_environment.py`，**15 项全过**，包括三次真实评分。另用临时替身模拟挂载失败，pytest 报 setup error。能力探测通过后，文件和奖励断言照常执行。

**同一探测也识别命名空间配额耗尽。** 用临时替身回放 bwrap 0.9.0 对命名空间配额或嵌套深度达到上限的完整诊断，修前三例均报 setup error，修后三例均跳过。单独模拟磁盘空间不足和挂载失败时，两者仍报错。具备权限和可用配额的机器复跑环境测试，15 项全过。[bwrap 创建命名空间时的错误分支](https://github.com/containers/bubblewrap/blob/v0.9.0/bubblewrap.c#L2703-L2715)

**正式工作树的结果。** 以 C03 `600b8cd` 为基线、Harbor 0.26.0 为依赖。先只改测试，四项定向用例 1 过 3 败。应用 C04 并修订隔离断言后，完整的 `test_environment.py` 共 15 项全过。四组 DAPO 评分回放全过，每次启动时 `/tests` 都为空，磁盘和 Trial 收到的奖励均为 1。C04 的未提交差异已单独审查。

全仓套件在收集阶段停下。相同解释器在 C03 和 C04 都有六个模块无法导入。五个缺少 `torch`（`test_engine_rebalancing`、`test_mopd_loss`、`test_mopd_metrics`、`test_proxy` 和 `test_tq_training_hydration`），`test_reward_registry` 无法导入 `get_reward_context`。

在升级笔记根目录，用加载了目标 Dressage、Harbor 0.26.0 且能运行 bwrap 的 Python 复跑：

```bash
python investigations/21-separate-verifier-input/separate_verifier.py --check-compatible
```

正式测试入口是 Dressage 的 `tests/integrations/harbor/test_environment.py::test_trial_uploads_host_tests_to_separate_verifier`。该测试分别用缺目录、空目录和含普通文件的目录运行。C04 应随 0.26 的版本切换一起合入，0.18 仍依赖启动时复制脚本。

## 证据索引

| 核对哪一节 | 打开后看什么 | 证据入口 |
| --- | --- | --- |
| ②④ 的三组对照 | `baseline` 是 C03 原代码，`guard` 只在环境目录存在时复制，`candidate` 移除旧复制。每条记录给出启动时文件清单、向 `/tests` 的上传次数、上传脚本字节是否一致、异常、磁盘和 Trial 奖励。 | [Harbor 0.26.0 十二组实测原始输出](../../../investigations/21-separate-verifier-input/c04-026-comparison.jsonl) |
| ④ · 启动与交接 | Trial 如何等待 `env.start()`、交出 `env`、把 `target_env` 传给评分器并等待 `verify()`。 | [启动与 yield](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L1115-L1145) · [接收环境并创建评分器](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L1053-L1097) · [等待 verify](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L986-L990) |
| ④ · 上传与执行 | 评分器保存环境对象，上传时调用 Dressage 的目录复制实现，随后在该环境里执行评分命令。 | [评分器保存环境](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/verifier/base.py#L33) · [Harbor 发起上传](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/verifier/verifier.py#L205-L223) · [Dressage 实际复制](https://github.com/dextermayhewjd/Dressage/blob/8023acdaaba3fafe58a340a23e02608a6663a72a/dressage/integrations/harbor/environment.py#L446-L458) · [执行评分命令](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/verifier/verifier.py#L245-L272) |
| ① · 原始改动 | 在提交的 `src/harbor/trial/trial.py` diff 中查找 `environment_dir=` 和 `skip_tests_upload=`。 | [Harbor 上游提交 3e30cca0（PR #3258）](https://github.com/harbor-framework/harbor/commit/3e30cca047a4d0dc1fb209bf5a74ff761b794b90) |
| ① · 旧约定 | 0.18 传入测试目录，创建评分器时跳过上传。 | [工厂收到的实参](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L617-L623) · [旧版目录选择](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L656-L664) · [旧版跳过上传](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L571-L581) |
| ① · 新约定 | 0.26 选出环境目录，设置上传开关，并把测试交给后端。 | [目录选择](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/task/verifier_mode.py#L138-L139) · [Trial 交接参数](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L1071-L1127) · [Verifier 上传测试](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/verifier/verifier.py#L209-L226) |
| ②③ · 修前现象 | 四组输入怎样构造、何时记录沙箱内容；三版历史对照使用早于 C02 的基线。 | [修前回放原始输出](../../../investigations/21-separate-verifier-input/separate-verifier-output.txt) · [回放脚本](../../../investigations/21-separate-verifier-input/separate_verifier.py) · [调查 21 的历史对照](../../../investigations/21-separate-verifier-input/README.md#evidence) |
| ③④ · 根因与候选改法 | 根文件系统预建 `/tests`，独立 verifier 随后向其中复制文件。C02 与 C03 的这两处实现相同。 | [Dressage 标准目录](https://github.com/dextermayhewjd/Dressage/blob/8023acdaaba3fafe58a340a23e02608a6663a72a/dressage/integrations/harbor/environment.py#L45-L57) · [Dressage 启动与复制](https://github.com/dextermayhewjd/Dressage/blob/8023acdaaba3fafe58a340a23e02608a6663a72a/dressage/integrations/harbor/environment.py#L393-L419) |
| ⑤ · 测试范围 | C03 调整了挂载夹具；调查 21 记录测试目录的原夹具、复现条件和验收范围。 | [C03 提交卡](03-verifier-fixture.md) · [调查 21](../../../investigations/21-separate-verifier-input/README.md) |
