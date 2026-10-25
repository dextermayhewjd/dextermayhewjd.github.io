# ClaudeCodeHarness.install_cli

完整安装记录见 [common.py::install_npm_cli](../common.py/install_npm_cli.md)。本文件保留 Claude Code 的参数适配与委托入口。

- 源码定位：[slime/agent/harness/claude_code.py:36–42](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/claude_code.py#L36-L42)，由助手核对。
- 首次接触：Step 5，先在启动沙箱的骨架中定位，2026-10-22 接续展开。
- 最近认识更新：2026-10-22，用户明确指出这里主要传入参数，具体安装实现应读 common；此前关于本机材料与远端环境的表述继续保留在原始讨论中。

**2026-10-24 当前版本接续**：当前方法在 [claude_code.py:38–55](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L38-L55)，由 `boot_agent_sandbox:135` 把已就绪的 `cand` 交进来，成功后回到 `143` 的 `sb = cand`。本步采用 Sunabako、Claude Code 且未设置 `SLIME_AGENT_CC_NATIVE_TARBALL` 的场景，继续走下面的 npm 委托；这条委托语句与旧版 AST 相同。

设置 native 包时，当前方法先走上传原生包、解包和检查的另一分支，正常返回后不会执行 npm 安装。本轮只定位该分支，内部实现留待需要时阅读。下面保留 `2f231865` 的入口说明与原始行号；版本核对不改变个人认识日期。

`ClaudeCodeHarness` 实现 `BaseHarness.install_cli` 接口。本方法读取 Node 和 Claude Code 包的路径，指定 Claude 检查命令，再 `await install_npm_cli(...)`。公共函数负责实际安装的编排；这是一处显式委托调用。

当前路径由 `SWE_AGENT="claude_code"` 选中此 Harness。`boot_agent_sandbox:111` 把已经进入的 `cand` 传为 `sb`；安装完成后返回 `None`，再回到父函数的 `sb = cand`。参数来源、场景输入输出与安装阶段统一见上面的主记录。

来源与历史：

- 固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`：Harness 选择见 `generate.py:45–52`，调用与返回位置见 `109–115`；配置与本方法见 `claude_code.py:19–20、36–42`；基类接口见 `harness/common.py:63–66`。
- [Step 5 · 首次进入 CLI 安装](../../../../../../04-flow.md#install-cli-entry)保留最初原话与交接说明；[上传与远端安装](../../../../../../04-flow.md#upload-and-remote-install)保留后续复述和疑问；[本次主次调整](../../../../../../04-flow.md#common-install-primary-record)记录改为引用入口的依据。
- 尚未展开的等待、重试与包版本问题保存在主记录的“尚不清楚”中。本轮仅静态核对，没有读取真实配置、上传文件或运行安装。
