# Manage Sandbox 候选稿：源码与材料校验

源码仓库：`/home/fredkeira/projects/slime`；固定提交：`22a89f96835969a47055a659c588f46151f8b07a`。

正文、图和教学示例对应当前本地快照。官方更新单独记录在 `upstream-check.json`，没有更新源码仓库。

本次为静态源码核对：摘录逐段取自本地文件，并与固定 Git blob 核对；未运行 E2B SDK、远端命令、CLI 或模型。示例 JSON 的 SDK 响应是构造值，不是实际执行记录。

## C01

**核对事实：** 从已有环境的 run 用户准备调用进入，正常返回后继续创建 HarnessContext。

- 公共调用骨架：[slime/agent/harness/common.py:81](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L81-L104)

**核对方式与结果：** 静态检查调用和实现；定位范围及摘录见 `source-groups.json`。文件与固定提交内容一致。

## C02

**核对事实：** Sandbox 是 Protocol；E2BSandbox 保存 SDK 句柄和环境标识，实际后端无需继承协议类。

- 公共能力约定：[slime/agent/sandbox.py:23](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L23-L59)
- 包装对象与字段：[slime/agent/sandbox.py:160](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L160-L189)
- 句柄与环境标识赋值：[slime/agent/sandbox.py:294](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L294-L300)

**核对方式与结果：** 静态检查调用和实现；定位范围及摘录见 `source-groups.json`。文件与固定提交内容一致。

## C03

**核对事实：** 用户准备生成 root 命令；调用没有保存三元组，成功返回 None，留下环境副作用。

- 调用处：[slime/agent/harness/common.py:97](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L97-L97)
- 完整用户准备函数：[slime/agent/sandbox.py:390](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L390-L399)
- exec 参数默认值：[slime/agent/sandbox.py:309](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L309-L319)

**核对方式与结果：** 静态检查调用和实现；定位范围及摘录见 `source-groups.json`。文件与固定提交内容一致。

## C04

**核对事实：** exec 经重试包装调用 SDK commands.run；env 改名 envs，成功结果归一化为三元组。示例响应为构造值。

- 发送与正常返回：[slime/agent/sandbox.py:320](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L320-L334)
- SDK 句柄来源：[slime/agent/sandbox.py:298](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L298-L300)

**核对方式与结果：** 静态检查调用和实现；定位范围及摘录见 `source-groups.json`。文件与固定提交内容一致。

## C05

**核对事实：** check 仅控制 CommandExitException 的表达；重放另由瞬时异常识别和 idempotent 提示控制，默认6次总尝试。

- 命令异常：[slime/agent/sandbox.py:335](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L335-L340)
- 默认重试次数：[slime/agent/sandbox.py:168](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L168-L172)
- 瞬时异常识别：[slime/agent/sandbox.py:211](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L211-L235)
- 重试与退避：[slime/agent/sandbox.py:237](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L237-L279)
- 本例重复Git追加：[slime/agent/sandbox.py:394](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L394-L396)

**核对方式与结果：** 静态检查调用和实现；定位范围及摘录见 `source-groups.json`。文件与固定提交内容一致。

## C06

**核对事实：** ensure_agent_user 未保存 exec 结果，返回 None；run 继续建立上下文并在同一环境写配置。

- 用户准备完整函数：[slime/agent/sandbox.py:390](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L390-L399)
- 返回后继续：[slime/agent/harness/common.py:97](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L97-L104)
- 后续配置仍使用 sb：[slime/agent/harness/claude_code.py:44](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/claude_code.py#L44-L55)

**核对方式与结果：** 静态检查调用和实现；定位范围及摘录见 `source-groups.json`。文件与固定提交内容一致。

## C07

**核对事实：** 准备题目通过 write_file；写入支持文本/字节/宿主Path，重试重新打开流；read_file 普通异常最终返回空字符串。

- 题目写入调用：[examples/coding_agent_rl/swe.py:177](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/swe.py#L177-L198)
- 写入实现：[slime/agent/sandbox.py:342](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L342-L378)
- 读取实现：[slime/agent/sandbox.py:380](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L380-L387)

**核对方式与结果：** 静态检查调用和实现；定位范围及摘录见 `source-groups.json`。文件与固定提交内容一致。

## C08

**核对事实：** 构造对象仅保存配置；进入时创建SDK环境，外层安装后yield；finally执行退出，kill普通失败只记warning。

- 构造配置：[slime/agent/sandbox.py:174](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L174-L189)
- 创建与回收：[slime/agent/sandbox.py:281](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L281-L307)
- 外层上下文与安装：[examples/coding_agent_rl/generate.py:95](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L95-L134)
- 使用和结果收集：[examples/coding_agent_rl/generate.py:200](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L200-L219)

**核对方式与结果：** 静态检查调用和实现；定位范围及摘录见 `source-groups.json`。文件与固定提交内容一致。

## C09

**核对事实：** run_agent 使用环境接口并委派 exec_and_wait；两者返回合同不同，等待预算耗尽本身不杀进程。

- run_agent 调用与整数返回：[slime/agent/harness/common.py:107](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L107-L122)
- 长命令入口和返回：[slime/agent/sandbox.py:82](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L82-L145)
- 预算状态：[slime/agent/sandbox.py:62](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L62-L79)
- 退出环境前收集结果：[examples/coding_agent_rl/generate.py:203](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L203-L219)

**核对方式与结果：** 静态检查调用和实现；定位范围及摘录见 `source-groups.json`。文件与固定提交内容一致。
