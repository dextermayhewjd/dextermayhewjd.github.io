# md：整理后供各阶段使用的题目信息

[返回参考目录](generate-input-context.md) · [基础样本](base-sample.md) · [题目编号](instance-id.md)

**`md` 是 `swe.get_metadata(base_sample, protocol)` 返回的字典。** 它从基础样本中整理出题目编号、镜像、工作目录和评测资料，供后面的调用使用。

## 大概长什么样

以下是 `scaleswe` 场景的字段示意，值为教学构造；问题描述和评测字段省略，没有运行该任务：

```python
md = {
    "protocol": "scaleswe",
    "instance_id": "issue-123",
    "image": "example-image",
    "workdir": "/workspace/repo",
    # 其他字段省略
}
```

- `instance_id` 保存题目编号；这里的 `issue-123` 是示意值，具体问题内容在 `problem_statement` 中。
- `image` 是用于创建沙箱的镜像标识；`workdir` 是沙箱内的工作目录路径。

## 从哪里来，交给哪里

```python
md = swe.get_metadata(base_sample, protocol)
instance_id = md["instance_id"]
```

- `base_sample` 是原有的 `Sample` 对象；`md` 是按当前约定整理出的题目信息字典。原始信息可以有不同来源，此处先使用整理后的字段。
- 原始题目信息主要从样本的 `metadata` 等属性读取；`protocol` 由调用方指定，再体现在返回字典中。可用 [base_sample 的源码测试示例](base-sample.md#源码中现成的构造示例)对照对象和字典的关系。
- 当前取出 `md["instance_id"]`，供取得执行编号时使用。
- 后续 `md["image"]` 用于创建环境；`prepare_workspace` 接收工作目录和 `md`；`run_evaluation` 继续从 `md` 取得评测所需资料。

> `md` 把后面几个阶段要用的题目信息整理在一起；每个调用从中使用自己需要的内容。

各字段的兼容来源、回退顺序和完整评测资料结构，留到相应问题再展开。

<details>
<summary>源码与原始讨论</summary>

- 固定提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`；以上为静态源码说明。
- [get_metadata 与两种返回结构](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L77-L137)；[generate 中的使用位置](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L185-L219)。
- [原始输入背景问题](../../step-005-agent-preparation/04-flow.md#session-id-reading-boundary)；[本次拆分](../../step-005-agent-preparation/04-flow.md#split-input-references)。整理不表示新增掌握或运行证据。
- [2026-10-22 的首次整体复述](../../step-005-agent-preparation/04-flow.md#sample-definition-and-example)：用户已将 md 与题目字段、get_metadata 及取出 instance_id 联系起来；本轮补充镜像标识、问题编号与原始数据来源的含义，不将其扩大为全部元数据规则已掌握。

</details>
