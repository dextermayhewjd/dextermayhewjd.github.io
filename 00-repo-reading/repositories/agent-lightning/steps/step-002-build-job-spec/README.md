# Step 002 · 进入 build_job_spec：构造 Job 配置

[项目与唯一进度](../../README.md#current-reading) · [前一步](../step-001-watch-job-events/README.md) · [Kubernetes 基础](../../../kubernetes/README.md)

本步从 Step 000 已读的 `_create_job` 返回到它的 manifest 调用，进入 `build_job_spec`。Step 001 的 watch 路径作为整体背景，当前关注创建请求之前的配置构造。

- 已确认入口：`manifest = build_job_spec(rollout, self._config)`。
- 本步问题：任务与模板如何形成 Job 配置，再交回创建函数？
- 当前展开：用户反馈原卡难读，已按“总任务与输入输出 → 连续阶段 → 局部说明”重排，并添加对应目录和层级编号。先看[函数卡 2.1：模板怎样成为 Job 字典](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/build_job_spec.md#template-input)，env、地址与镜像保留在各自所属阶段。
- 源码：Agent Lightning `0029dbb35c467799d35fee81d15d80264b0d1bd3`；在本地 Markdown 中阅读。

## 本步入口

1. [Scope 与调用面包屑](01-scope.md)：整体位置、进入点、局部阅读顺序与返回处。
2. [短期函数索引](02-short-term-memory/overview.md)：已读调用方与本步的 build_job_spec。
3. [累计函数索引](03-long-term-memory/overview.md)：从 Step 001 的 03 + 02 合并继承的八份记录。
4. [形成过程](04-flow.md)：实际选择、解释、反馈与未知。

## 当前边界

用户已将开头理解为检查 Job 模板，并询问两个 env、LLM 地址和镜像的关系。卡片已按这些疑问补充对应语句与作用，尚未把助手解释记为个人已掌握。YAML 解析、标签、运行约束及脚本/挂载仍按后续问题展开。

读完返回 `_create_job`，由 manifest 接住配置，再进入已有的 Job 提交动作。本步尚未部署 Job 或运行容器。

## 下一处候选：启动命令需要的文件从哪里来

Controller 主干的讲解已基本覆盖，当前讨论是否阶段性收束。下一块建议以真实模板的 `/agl/agents/smith_agent.py` 为线索，连接启动命令、ConfigMap 卷和创建 ConfigMap 的脚本；具体依据和仍需补充的运行约束见[本轮覆盖评估](04-flow.md#controller-closeout-and-pod-prerequisites)。这只是候选阅读范围，尚未开始新的步骤。

**后续用户调整方向**：上面的示例部署路线不作为下一主线。下一阶段优先理解 [Trainer、Gateway、Controller 的通用交接](../../references/framework-components.md)，重点看 Agent 模型交互怎样形成训练数据；[用户反馈与新建议](04-flow.md#framework-components-priority)保留于本步过程。

**进一步核对已有基础后**：Slime 已覆盖完成组数触发、保留未完成任务、协议接入和轨迹组装等核心能力。当前建议收束通读；[增量评估](../../references/slime-incremental-reading.md)中的差异仅供具体问题触发时对照，保留原有已读事实与未知，不再默认安排下一章节。
