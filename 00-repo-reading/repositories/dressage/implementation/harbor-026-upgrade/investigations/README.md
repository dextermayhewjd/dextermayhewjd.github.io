# 怎样集中审核 Dressage 的 Harbor 升级

从 PR-001 选一个要裁定的问题，打开对应调查项。读到能回答“这次为什么要改、实际验证到哪里、凭什么能验收”，就可以停。当前 Dressage 基线是 `3e3142f`，唯一升级目标是 Harbor 0.26.0。0.18.0 是原支持版，0.25.0 仅用于差异对照。[本轮审核入口](../prs/001-harbor-026-compatibility/README.md#review-order) · [全部问题索引](../README.md#investigations)

要回答“这个问题发生在哪一次交接”，打开问题页顶部的三版用法表。它给出具体调用、各版输入和下游实际拿到的输出。要回答“已发现的调用是否都审过”，从 usage 的源码位置索引开始。用法稳定时继续复用已有证据，判断改变时在原调查项追加依据。 [逐项用法](../usage/README.md) · [固定源码位置](../usage/source-index.md#locations)

**原版 Dressage 的测试能抓到哪些升级问题？** 默认套件在 0.26 有三个失败，集中在两个问题。真实工厂预检、日志回收和独立 verifier 的启动目录另有修前复现。审查单个问题时，点击其用法表旁的「原套件在本问题测到了哪里」，就能看到原测试的断言、关联的 U 和仍缺的运行证据。[原套件的实际调用次数](original-test-audit.md#observed) · [按调查项反查 U 和测试缺口](original-test-audit.md#issue-map)

本轮四个独立问题及已有判断的变化可在[0.26 二次复查](upgrade-audit-026.md)对照。每项的输入、运行结果和固定源码仍在对应问题目录。

<a id="new-investigation"></a>

## 发现新情况，写回原页还是开一个目录？

先写一句能用运行结果回答的问题，再查[调查索引](../README.md#investigations)。例如“Harbor 工厂传空字典时，Dressage 会不会执行 bwrap 预检？”属于 01 的另一个输入。要验证“非空日志能否回到 Trial 目录”，观察的是另一份输出，归到 02。[01 的三种输入](01-environment-preflight/README.md#runtime-comparison) · [02 的日志实验](02-output-mounts/README.md#evidence)

确有独立问题时，取下一个空闲编号，建立 `investigations/NN-简短主题/README.md`。开头写**调查问题、当前判断、对应 U**。随后写两边的源码原文、实测输入与输出、处理与验收、判断记录。暂缺运行证据时，写清下一次要观察什么。复现脚本和输出与 README 放在一起。

把新页登记到根目录的调查索引，在相关 U 页和调查页互链，再补上原套件对这项行为的覆盖。确认需要改代码时，才在调查页登记候选修改、验收条件和所属 PR。若配置已经可用，记录验证范围即可。[原套件反查表](original-test-audit.md#issue-map) · [05 的实际结论](05-skills-upload/README.md#evidence)

## 打开一项调查后怎样审

一个问题目录随根因和验收条件建立。准备改实现时，在该问题首页放改前上下文、拟改文件、验收条件及提交状态。实际提交后写入 Dressage SHA 和修后证据，关联 PR 可据此反查。先看 [01 的实例](01-environment-preflight/README.md#implementation) 和[从问题到合并的步骤](../tools/upgrade-sop.md)。

| 顺序 | 这一眼要解决什么 | 页上应直接看到什么 |
| --- | --- | --- |
| 1. 看问题和当前判断 | 哪个输入，在什么调用处，可能产生什么差异？ | 一个能用源码或运行结果推翻的判断。若争议来自外部建议，保留有争议的原句和出处。 |
| 2. 对两边的原文 | Dressage 依赖哪一个参数、字段或副作用？Harbor 实际提供什么？ | 各摘出能解释交接的连续原行。上游注释写了动机，就连同注释引用。我们推导出的因果另写在“据此判断”。每段旁边放固定提交和行号。 |
| 3. 看实际观察 | 在这个版本、这个输入下，观察到了哪一步？ | 直接显示决定结论的输出、错误或实际补丁，并链接完整文件。只有源码或测试断言时写明证据类型，再写缺哪条运行记录。 |
| 4. 作出决定并交接 | 现在可以修实现、改夹具、沿用现状，还是先补验证？ | 写下依据、适用范围和一项可观察的通过条件。停下来时留下下一次需要的输入与观察量。 |

代码块保留原始字符和相对缩进，仅移除各行共有的左侧缩进。固定提交与行号供复核原文和上下文。探测脚本、完整输出、使用过的替身及排除项留在问题目录或其引用的那次实验里。[GitHub 固定版本和行号链接](https://docs.github.com/en/repositories/working-with-files/using-files/getting-permanent-links-to-files) · [本次复现命令与环境](../tools/reproduce.md#run-probes)

## 为什么 02 和 03 要分别作决定

| 审核对象 | 已经拿到的原文 | 这条证据允许作出的决定 |
| --- | --- | --- |
| 02 · 后端回收非空日志 | `actual directory equals Trial directory: True`、`Harbor reports the directory mounted: False`、`nonempty directory copy raised shutil.Error` | 实际绑定和挂载查询有分歧，应修后端。修后用同一份非空日志验收。[02 的完整观察](02-output-mounts/README.md#evidence) |
| 03 · verifier 测试夹具 | 补丁把 `mounts=mounts` 换成 `auto_mounts=mounts`，该测试文件输出 `4 passed in 0.12s` | 夹具应与真实调用对齐。这四项通过只回答夹具问题，02 的非空日志仍有自己的验收。[03 的补丁与输出](03-verifier-fixture/README.md#evidence) |

同一次实验也可以回答多个问题。真实 Job 探测的一行 `plan (attempt, task, agent)` 支持核对 Trial 排列，另一行 `registered` 支持核对回调登记。每个调查项引用各自需要的原行，可以共用一个输出文件。要判断 CANCEL 与 END 的实际次序，还得观察运行中的 Trial。[09 · 计划输出](09-trial-plan/README.md#evidence) · [11 · 注册与执行的边界](11-trial-events/README.md#evidence)

<a id="handoff"></a>

## 暂停、改判或完成时怎样留记录

**在当前调查项的“判断记录”追加一条。** 写日期、核对版本、输入或命令、直接观察、据此保留或修正的结论，以及还缺的一项证据。修后复跑另存输出，让修前、修后和被推翻的理由都可以回查。PR 页只登记对交付范围或下一处审核入口有影响的变化。

问题 11 有一条实际改判。旧验收写“同一次尝试只提交一次”。源码中，已标记取消的 attempt 在提交之前 `return None`，随后进入关闭路由的 `finally`。因此正常路径验一次提交，取消路径验零次提交。真实事件目前只取得注册名单，下一份所需记录是同一 attempt 的事件、提交次数和关闭结果。[11 · 原文](11-trial-events/README.md#sources) · [11 · 改判记录](11-trial-events/README.md#history)

接手人只需要 PR 中的入口、这一页的当前判断和最近一条记录。要核对版本、例外分支或重跑时再打开原件。在本目录运行 `python3 ../tools/check_docs.py` 可对照已存的本地摘录，传入两个源码 checkout 还能逐段比对 Git 原文。[校验用法](../tools/reproduce.md#provenance)

2026-11-18 的讨论原句是“我觉得还是需要有原文 但是也需要有具体的连接用于检查的连接”。本轮据此把源码与已有运行输出放回各调查项正文，集中审核入口放在 PR-001。
