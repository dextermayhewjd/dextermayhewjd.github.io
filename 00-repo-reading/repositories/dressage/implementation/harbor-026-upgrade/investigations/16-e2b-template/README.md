# 16 · native E2B 路径能否用目标版本的 SDK 和模板启动任务？

**当前判断**　保留两份示例 Job 的 E2B 配置。模板构建和真实云端启动仍待验证。

**对应的三版用法表**　[U60 native 配置把模板和资源交给 E2B 启动沙箱](../../usage/题目文件与可选后端/U60-native%20配置把模板和资源交给%20E2B%20启动沙箱.md#u60) · [原套件在本问题测到了哪里](../original-test-audit.md#i16)

能从 YAML 解析出 `e2b`，只回答了选中了哪个后端。实际能否领取或构建该任务的模板，要到 E2B 启动时观察。

<a id="sources"></a>

## 两边的源码原文

**Dressage 3e3142f**　Terminal-Bench 示例选择 E2B 并要求删除环境。[terminal-bench-2-e2b.yaml 第 10–12 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/harbor_job_configs/terminal-bench-2-e2b.yaml#L10-L12)

```yaml
environment:
  type: e2b
  delete: true
```

**Harbor 0.26.0**　0.26 的 E2B extra 指定 SDK 下限。[pyproject.toml 第 73 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/pyproject.toml#L73)

```toml
e2b = ["e2b>=2.52.0", "dockerfile-parse>=2.0.1"]
```

**Harbor 0.26.0**　Harbor 的原注释解释了模板为何要区分 CPU 和内存。[e2b.py 第 558–561 行](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/e2b.py#L558-L561)

```python
E2B fixes CPU and memory at template build time, so two trials that share a
Dockerfile but request different resources need different builds. Harbor's
environment hash does not include resources; the tag does.
"""
```

**据此判断**　配置能选出 E2B，真实启动还依赖 SDK、任务镜像和指定资源对应的模板。0.26 的后端会把资源变体和 recipe 版本写进模板 tag。

<a id="evidence"></a>

## 证据与验证范围

**已存配置输出**　解析两份 0.26 Job，倒数第二列给出选中的环境类型。[job-config-output.txt 第 9–11 行](../18-example-configs/job-config-output.txt#L9-L11)

```text
Harbor 0.26.0 | n_samples=2 seed=7 shuffle=False
tau3-bench-e2b | sierra-research/tau3-bench | Qwen/Qwen3.5-4B | e2b | 9780cd6492be13
terminal-bench-2-e2b | terminal-bench/terminal-bench-2 | Qwen/Qwen3.5-4B | e2b | eaa28aafd82982
```

两份配置都选择 e2b。本机的目标版 overlay 能导入 E2B SDK 2.64.0；进一步用一个本地 Dockerfile 读取 WORKDIR，调用在导入 `dockerfile_parse` 时失败。该额外依赖也出现在 0.18 的 Harbor E2B extra 中。选择 E2B 时需安装目标版的完整 extra；实际模板标识、云端创建及清理仍待取得。[离线探测](sdk_probe.py) · [实际输出](sdk-output.txt) · [0.26 E2B 使用这个读取函数的位置](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/e2b.py#L872-L879) · [0.18 已有的额外依赖](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/pyproject.toml#L62)

**只改变 CPU 数时，后端选择的本地模板引用是否变化？** 对同一个 `docker_image`、1024 MB 内存分别要求 1、2 CPU，从三版真实 `EnvironmentFactory.create_environment_from_config` 构造 E2B 后端。0.18 和 0.25 的两次引用相同，均为 `demo__e6f60e442f62`。0.26 生成相同的模板名，两个 tag 分别为 `c1-m1024-r5` 和 `c2-m1024-r5`。此处比较构造时的本地引用；远端 build ID 由服务端决定。[三版输入与断言](e2b_offline.py) · [三版实测输出](e2b-offline-output.txt) · [0.26 模板名与 tag 的赋值](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/e2b.py#L895-L906)

另给 0.26 指定预建模板 `fixture-template`，正常调用 `start(False)`，SDK 替身收到的 `create(template=...)` 与指定值一致。这条路径直接使用预建模板的资源配置，独立于上面由后端生成资源 tag 的比较。[传入 SDK 的值](e2b-offline-output.txt#L6) · [预建模板的分支](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/environments/e2b.py#L1512-L1540)

## 处理与验收

<a id="cloud-review"></a>

**这次升级要观察到哪一层？** Dressage 随仓的 Terminal-Bench 2 用 E2B。训练分区在 bwrap 模式覆盖环境类，native 模式沿用 Job 选定的后端。本地 bwrap 的预检、挂载和独立 verifier 输入分别在对应问题验收。E2B 保留单独的云端验收入口。 [随仓使用场景](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/docs/harbor.md#L7-L11) · [训练分区的环境选择](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L556-L578)

确认 E2B rollout 时，可以沿现有 `terminal-bench-e2b` 用例跑一题。它把题数、尝试数和并发都降到 1，结束时检查 `JobResult` 中有有限数值的 reward，0 分也能满足这一断言。另看该 Trial 的请求有没有到达预期 Gateway，并按同一 sandbox ID 核实云端清理。远端训练另有检查 manifest 的用例。需要承诺长任务时，再进入问题 17 观察一次真实续租。 [单题配置](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_gated_e2e.py#L28-L41) · [rollout 及奖励断言](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_gated_e2e.py#L63-L102) · [远端训练用例](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_gated_e2e.py#L117-L139) · [长任务续租](../17-e2b-renewal/README.md)

**下一步**　在具备 E2B 账户和可达测试 Gateway 的环境中，按目标版 E2B extra 安装。选一份随仓 Job 启动一题，记录实际模板、沙箱启动和返回结果。[已有云端测试入口](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_gated_e2e.py#L93)

**通过条件**　目标版能选择或构建与资源相符的模板，任务能执行、访问测试 Gateway 并交回结果。在取得这一记录前，PR 上登记已验证的配置解析、模板引用和 SDK 替身调用。

<a id="history"></a>

## 判断记录

- 2026-11-18　已核对两个发布版的 E2B 依赖和 0.26 的模板生成逻辑。此前举出的 CPU 和内存只是一个资源配置实例。云端构建、启动均待执行。

### 复查入口

- 复现与对照　[0.25 依赖](https://github.com/harbor-framework/harbor/blob/v0.25.0/pyproject.toml#L68) · [配置输出](../18-example-configs/job-config-output.txt) · [默认测试范围](../00-version-target/pytest-replay.txt)
- 完整调用与配置　[Terminal-Bench Job](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/harbor_job_configs/terminal-bench-2-e2b.yaml) · [τ³-bench Job](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/harbor_job_configs/tau3-bench-e2b.yaml) · [docs/harbor.md:104](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/docs/harbor.md#L104) · [pyproject.toml:73](https://github.com/harbor-framework/harbor/blob/v0.26.0/pyproject.toml#L73) · [e2b.py:528](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/e2b.py#L528-L568) · [e2b.py:1365](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/environments/e2b.py#L1365)

[PR-001 如何审查此问题](../../prs/001-harbor-026-compatibility/README.md#e2b) · [返回问题索引](../../README.md#investigations)
