# 历史判断入口

每次核查的证据与修正已归入对应问题的 README。当前入口见[问题索引](../README.md#investigations)。

<a id="fixture-check"></a>

## 第一轮 bwrap 测试

[两项 verifier 测试为何失败](../investigations/03-verifier-fixture/README.md) · [另一项安装版本断言为何失败](../investigations/04-version-checks/README.md) · [非空日志回收如何改变后续修复范围](../investigations/02-output-mounts/README.md)

下面保留第一次对照后的判断。当时调整夹具后四项环境测试通过，后续单独对非空日志复现的复制错误记录在问题 02。

完整的生产导入、两种启动入口、回调、配置和文件协议见 [Dressage 使用 Harbor 的接入点清单](integration-inventory.md)。

2026-11-18 按用户指定的 `/home/hongshi/projects/Dressage` 提交 `3e3142f` 导出临时副本。在 Python 3.12 的同一依赖环境分别使用已安装的 Harbor 0.18.0 和本地发布标签构建的 0.26.0 wheel，运行整个 `tests/integrations/harbor` 目录。原始测试结果为 0.18 **66 passed**，0.26 **63 passed、3 failed**。两次均有 **8 deselected**，即项目默认排除的 `harbor_e2e`。

- 0.26 一项失败来自明确断言已安装 `harbor==0.18.0`。另两项在构造独立 verifier 时均报 `separate verifier does not have Harbor's verifier mount shape`。旧夹具传 `mounts`，0.26 的真实 Trial 将日志挂载传给 `auto_mounts`。仅在临时夹具中改为后者，重新运行 `test_environment.py` 得到 **4 passed**，含真实 bwrap 文件读写。生产代码未修改。[夹具](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_environment.py#L60) · [Harbor 0.26 verifier 调用](https://github.com/harbor-framework/harbor/blob/v0.26.0/src/harbor/trial/trial.py#L1115-L1127)
- 计划排列测试使用手工 Job，插件测试由测试代码调用 hook，部分数据源测试替换 JobConfig 和任务 resolver。通过说明 Dressage 能处理给定输入，真实 Harbor 发出事件的顺序及最终 RL 数据的交接仍需独立验收。[计划测试](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_contracts.py#L108) · [插件测试](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_execution.py#L64) · [数据源夹具](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_data_path.py#L323)
- 下一份升级 PR 应按承诺的范围验收。先对齐版本约束和夹具，把真实 `Job.create → on_job_start` 放入回归测试，再观察新版真实 Trial 的正常、取消路径。若承诺 RL 训练接入，检查由真实 Trial 交回的结果可转成对应 Sample，并核对重试时最终 attempt 的选择。本轮未运行付费或训练端到端用例。[端到端测试](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_gated_e2e.py#L93)

<a id="gemini-review"></a>

## 从原七项核查定位独立问题

| 原核查项 | 对应问题目录 |
| --- | --- |
| 1 · 环境契约 | [01 工厂预检的签名](../investigations/01-environment-preflight/README.md) · [02 非空日志目录被复制回自身](../investigations/02-output-mounts/README.md) · [03 独立 verifier 的测试夹具](../investigations/03-verifier-fixture/README.md) · [05 技能目录上传](../investigations/05-skills-upload/README.md) |
| 2 · Job 创建前的鉴权 | [06 Job 创建时的凭证检查](../investigations/06-agent-credential-preflight/README.md) |
| 3 · Agent 模型路由与输出脱敏 | [07 实际请求到达的 Gateway](../investigations/07-agent-routing/README.md) · [08 Trial 目录脱敏与 bundle 位置](../investigations/08-trial-output-redaction/README.md) |
| 4 · JobPlan 与 JobLock | [09 Trial 排列与原模板配对](../investigations/09-trial-plan/README.md) · [10 临时 Job 生成 lock](../investigations/10-job-lock/README.md) |
| 5 · 结果与失败处理 | [11 CANCEL 与 END 事件时序](../investigations/11-trial-events/README.md) · [12 评测有效分数与训练采纳](../investigations/12-reward-validity/README.md) · [13 重试后最终进入训练的尝试](../investigations/13-final-attempt/README.md) |
| 6 · 网络与 E2B | [14 bwrap 的阶段网络策略](../investigations/14-phase-network-policy/README.md) · [15 Agent 的 Web 工具开关](../investigations/15-web-tools/README.md) · [16 E2B 模板启动](../investigations/16-e2b-template/README.md) · [17 E2B 长任务续租](../investigations/17-e2b-renewal/README.md) |
| 7 · 配置与 checkpoint | [04 安装依赖与版本检查](../investigations/04-version-checks/README.md) · [18 随仓 Job YAML 的含义](../investigations/18-example-configs/README.md) · [19 旧数据源 checkpoint 的识别](../investigations/19-checkpoint-digests/README.md) |

工作树归属、Dressage 基线与目标版本的选择见[00 版本选择](../investigations/00-version-target/README.md)。

<a id="skills-proposal"></a>

### 问题 05 最初要核查的原句

用户提供的 Gemini 分析在“默认 Skills 目录”一项写道（合并原消息中的折行）：

> Harbor 0.25 / 0.26 默认将注入的 skills 挂载/上传到 /runtime/skills，需在 _STANDARD_ROOTFS_DIRS 中补齐 PurePosixPath("/runtime") 和 PurePosixPath("/runtime/skills")（同时保留 /harbor/skills 兼容旧 task）。

这句话是调查的起点。是否需要改目录常量，可以用一次没有预建父目录的上传及读回来裁定。[05 的源码和判断](../investigations/05-skills-upload/README.md#sources) · [05 的实验输出](../investigations/05-skills-upload/README.md#evidence)
