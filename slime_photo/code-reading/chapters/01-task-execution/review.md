# 4.1 连续任务回顾

[主线讲解](walkthrough.md) · [唯一阅读路线](../../repo-reading-route.md)

本章已完成静态讲解与来源核对。阅读反馈与运行证据统一见[当前接续](../../repo-reading-route.md#当前接续)，不在本文件重复维护；以下练习尚未执行。

先说明 Pre-4、Launch Agent 与模型请求的真实时间关系，区分组件动作编号和阅读目录的位置。

1. 用一份任务参数从 generate 准备走到最后清理，每进入一个组件都说清输入、职责、输出以及返回位置。
2. 指出 Harness 等待 CLI 时的模型请求循环，区分外层任务与单轮请求。
3. 区分 CLI 退出码、代码 diff、任务 reward、训练 Sample 和 Session 轨迹。
4. 解释 evaluation 返回与训练导出的不同；指出流式/非流式响应和 record_turn 的实际调用顺序。
5. 沿 prepare_workspace 失败走一遍环境退出、ABORTED 返回与 Session 清理，并说明哪些步骤尚未有真实运行证据。

读完后再更新路线中的本章范围与学习状态。后续策略、队列、集群和训练内部实现仍属于后续单元。

## Pre-4 准备检查

- 把 Adapter Service 的 tokenizer、解析配置、Adapter、HTTP 服务和回连地址逐项对上后续消费者。
- 用同一个任务解释 state、md、sid/Session、sb、题目文件怎样形成。
- 指出默认采样和题目正文各保存在哪里，为什么不会直接变成额外的 run 参数。
- 读 run 的参数逐项说明来源，再指出 run 内部还要做哪些配置与启动。

## Harness/Sandbox 的调用书签

- 从 run:97 进入 ensure_agent_user → sb.exec → SDK，说明三元组结果和环境副作用，再回 run:98。
- 说明 Claude write_config 不读取 ctx；模型地址与 sid 在 launch_and_wait 的 env 中使用。
- 区分 exec 三元组、exec_and_wait 二元组、Harness 整数与任务 reward。
- 指出创建/安装已在 Pre-4 完成，以及退出后的 git_diff、kill 尝试和独立评分位置。
