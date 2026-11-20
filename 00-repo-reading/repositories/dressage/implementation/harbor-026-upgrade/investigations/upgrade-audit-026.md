# Dressage 升级 Harbor 0.26.0 的第二轮审核

固定 Dressage `3e3142f`。运行时对照以原支持版 0.18.0 为基线，验收目标为 **0.26.0**。复算 341 个跟踪文件里的既有索引后，继续从两条入口核对行为：CLI 将 Job 交给 Dressage 插件，训练入口由 Dressage 调用 Harbor Job 后消费结果。本轮仍有 61 项用法，新增的四个问题都来自已有交接。默认套件本轮复跑为 0.18 的 66 通过、0.26 的 63 通过和 3 失败，每版另有 8 项端到端用例排除。[固定源码索引](../usage/source-index.md#locations) · [逐项用法](../usage/README.md#routes) · [原套件的断言范围](original-test-audit.md#observed)

**覆盖核对结果**　61/61 个用法有问题页入口，25/25 个问题目录与用法能双向核对。这里的 25 包含版本决策、已复现缺陷、行为变化与待验分支。13 的最终 ID 在受控队列中已经核过，16–17 的 E2B 服务端则需要云端运行。链接覆盖和实际运行覆盖分别查[反查表](original-test-audit.md#issue-map)与[七组剩余运行边界](../usage/README.md#remaining)。

## 同一份输入，哪些结果变了？

| 输入与交接 | 0.18 → 0.26 的观察 | 对升级的判断 |
| --- | --- | --- |
| 用 Dressage 的 bwrap 后端做独立评测 | 旧版把题目 `tests/` 交给后端；0.26 在本地无专用 verifier 定义的场景先交付 `environment/`，再由 Verifier 上传测试。Dressage 仍把启动目录整体复制到 `/tests`。省略空的 `environment/` 会在测试上传前失败，非空目录的环境文件会进入 `/tests`。 | **修生产后端。** 另一个失败在评分后才发生：DAPO 已写出分数 1，默认挂载回收却抛出 `DownloadVerifierDirError`。修挂载和修启动输入各要一条回归断言。[21 启动输入](21-separate-verifier-input/README.md) · [02 评分后的文件回收](02-output-mounts/README.md) |
| 向 Claude Code 注入 Trial 路由 | 随仓 Qwen 配置在 0.26 的命令启动参数中仍选中 Gateway 和本次凭证。显式模型地址或凭证选择器会改变最终选择；某些配置在插件登记前就被 Job 预检拒绝。 | **按配置判定。** 对承诺强制路由的配置，显式限定可接受的连接设置，并验证请求实际到达预期 Trial。这里已测到命令执行边界，尚缺 Gateway 的接收记录。[06 Job 入场](06-agent-credential-preflight/README.md) · [07 路由](07-agent-routing/README.md) |
| 允许重试一次，首轮出现同一异常 | 物理尝试数随异常而变。仅 step 记 `RuntimeError` 为 1 → 2；Agent 非零退出为 2 → 1；API 配额异常为 1 → 2。受控的成功重试里，最终 Trial ID、manifest 和两个 Sample 对得上。 | **决定接受哪个重试策略。** 需要分别断言执行了几次、最后哪次参与训练，以及旧尝试能否排除。Dressage 的整组重试还有独立入口。[22 重试策略](22-retry-policy/README.md) · [13 最终采用](13-final-attempt/README.md) |
| 本地 dataset 目录只取前两题 | 在探测目录中，旧版取文件系统遍历的前两项，0.26 排序后取前两项。同样的配置会选到不同题目。显式指定的 tasks 列表是另一条输入路径。 | **确认实验题集。** 若要复现旧实验，保存具体题目身份并核对展开后的列表。[23 本地题目选择](23-local-dataset-selection/README.md) |
| 用 0.26 的真实数据源读取 0.18 checkpoint | 在固定 Job 名、两题、相同种子的输入上，`load(1)` 报 `source_digest mismatch`，游标没有前移。0.26 写、0.26 读可在两个哈希种子下恢复 cursor=1、sample index=2。 | **发布时明确续训边界。** 若要支持旧 checkpoint，还需在真实题集上验证恢复后的下一组、任务顺序及训练状态。[19 五次恢复](19-checkpoint-digests/README.md#checkpoint-replay) |
| 运行随仓 CLI 的配置渲染，观察宿主进程的副作用 | 0.26 默认会把命令结束事件交到遥测发送边界；设置 `HARBOR_TELEMETRY=0` 时没有这条调用。探测在联网前截住。Job 完成或报错时还有独立的事件入口。 | **确认离线部署的宿主设置。** Sandbox 的网络策略与 Harbor 宿主的遥测开关分别验收。[24 宿主遥测](24-host-telemetry/README.md) |

## 哪些原有判断可以收窄？

- **运行失败的 Trial 也可能有分数。** 同一个单步 Agent 抛出 `RuntimeError`，关闭物理重试后，0.18 跳过 verifier，0.26 继续评测。受控 verifier 在 0.26 返回 0.75，Dressage 保留异常并拒绝生成训练样本。只比评分数值会漏掉训练采纳条件。[12 评分与训练判定](12-reward-validity/README.md) · [真实生命周期的结果](12-reward-validity/lifecycle-rewards.txt)

- **正常、取消和脱敏有了运行证据。** 在受控 Trial 取消路径上，Dressage 未提交轨迹，关闭对应路由一次。0.26 的 END 回调读取已经处理过的 Trial 文件；判断日志内容要注明在哪个事件处读取。外部 bundle 的落点与 Trial 目录是两个观察位置。[11 事件与清理](11-trial-events/README.md) · [08 脱敏](08-trial-output-redaction/README.md)
- **插件能加载与产物能提交要分别验。** 从固定提交构建的 wheel 可由 0.26 按短名 `dressage` 找到正确的类。让插件的 store 在写 manifest 时抛出合成 I/O 错误，两版 Harbor 的 CLI 收尾函数都会记录 warning 并返回。因此验收 CLI rollout 时，需要读取本次 manifest 的 `committed`、最终尝试及其文件。训练分区直接等待插件，走自己的提交和错误处理路径。原有 gated rollout 测试断言 Harbor 的奖励，training 测试断言 manifest 文件存在。升级验收应再核对提交标记和尝试身份。[rollout 原断言](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_gated_e2e.py#L100-L102) · [training 原断言](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_gated_e2e.py#L134-L139) · [wheel 和收尾的实测](04-version-checks/wheel-output.txt) · [CLI 收尾](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/cli/job_plugins.py#L94-L103) · [训练调用](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L759-L766)
- **目前的运行环境足够重放这些路径，正式安装仍须单验。** 目标 wheel 的基础依赖在本机实验环境里缺 `fastmcp` 和 `semver`；基线 Dressage wheel 的 extra 仍锁 0.18。发布时应在干净 Python 3.12 环境安装更新过的 extra 并检查依赖，再从短名运行一题。[04 安装与版本检查](04-version-checks/README.md)

## 覆盖到哪里，哪里还需要运行？

| 审核方向 | 能据此回答什么 | 还缺什么 |
| --- | --- | --- |
| 固定源码的接触面、安装与发现 | 191 个归档位置能反查用法或排除理由，61 项用法都有版本依据。wheel 能按短名发现。 | 自定义类、动态配置与部署镜像的实际依赖需要以要支持的配置运行。扫描按已知接收对象和别名取候选行。[扫描规则](../tools/scan_harbor_surface.py) |
| 配置、顺序、生命周期与副作用 | 受控任务已覆盖地址选择、目录选择、奖励文件、重试、取消、收尾时序和数据源跨进程恢复。 | 完整 CLI 的第一条模型请求、真实任务产物交付、不同执行阶段的网络策略，以及带活动子进程的清理仍需实测。[七组用法的边界](../usage/README.md#remaining) |
| 最终训练与外部服务 | 受控结果链验证一个物理尝试能一路对到训练 Sample。E2B 的模板键随资源规格变化，SDK 替身也已观察到续租与停止后的回收。[三版离线输出](16-e2b-template/e2b-offline-output.txt) | 从 Slime 入口跑完分区、组选择及训练/评测返回值。若发布范围包含随仓 E2B 配方，要补齐 E2B extra，固定远端 `ref: latest` 实际解出的题目版本，再验 lock、启动、回收和长任务续租。[本地 Dockerfile 依赖实验](16-e2b-template/sdk-output.txt) · [随仓数据集引用](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/harbor_job_configs/terminal-bench-2-e2b.yaml#L19-L22) · [PR 验收表](../prs/001-harbor-026-compatibility/README.md#acceptance) · [16 E2B 启动](16-e2b-template/README.md) · [17 E2B 续租](17-e2b-renewal/README.md) |

**下一轮优先跑一个能打通工厂、独立 verifier 和结果交付的本地 Trial。** 先修 01、02、21，同时更新 03 的夹具。让修后的真实 `JobResult` 读回奖励 1，再按 07 核对一次实际请求、按 13 核对最终 manifest。这样能同时验证修复位置和下游结果。[01 工厂预检](01-environment-preflight/README.md) · [03 测试夹具](03-verifier-fixture/README.md) · [PR 执行顺序](../prs/001-harbor-026-compatibility/README.md#test-order)
