# S08 现代上下文压缩教学示例

这份单文件程序使用公开 Claude API，解释 token 计数、完整工具轮次、签名摘要、工作资料恢复和失败时保留原历史。它不是 Claude Code 内部源码的复刻。

## 离线运行

Python 3.10 或更新版本即可，不需要 API Key 或第三方包：

```bash
python3 code.py --demo
```

示例在临时目录中建立虚构项目，使用脚本化模型响应展示主流程。离线计数是用于观察状态的估算，不是真实 tokenizer。临时项目在演示结束时清理。

## 真实 API 模式

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade anthropic
export MODEL_ID=claude-sonnet-4-6
python3 code.py --live --root /path/to/project --budget 160000
```

另需通过自己的环境配置设置 `ANTHROPIC_API_KEY`。模型与服务端必须支持 `compact-2026-09-04` 按需压缩 Beta 和 token 计数接口。自定义网关不一定提供这些能力。真实模式会产生 API 请求与费用；仓库验证没有运行此模式。

`--budget` 是应用选择的输入预算，要低于所用模型的真实窗口并留出响应余量，不是程序自动发现的模型容量。终端可输入任务、`/context`、`/compact [focus]` 或 `/quit`。

示例只给模型 `read_file` 和 `compact` 工具；应用保存 `.s08-modern/` 下的消息日志及大输出快照。压缩后重新读取 `CLAUDE.md`、`PLAN.md` 与最近读取的最多五个文件，并尝试刷新 Git 状态。

## 代码中的设计选择

- 模型请求压缩时先回传本轮全部工具结果，下一轮边界才压缩。
- 真实模式使用官方输入 token 计数，不用字符长度判断窗口。
- 返回的 `compaction` 块连同签名原样保留，并置于历史首部。
- 先构造并检查“摘要 + 恢复上下文”，通过后才替换活跃历史。
- 未返回有效摘要或恢复后超预算时不覆盖历史，错误由调用方处理。
- 连续记录原消息；大文件输出限制进入上下文的节选长度并另外保存原文。

选择最近读取文件、恢复文件名及五千 token 文件引用门槛是这份教学程序的应用策略；现代 Claude Code 的完整 Skills、memory、Hooks、后台调度和缓存管理不在这个最小示例中。

## 离线验证

在博客源码仓库根目录执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_s08_modern.py
```

用例检查工具配对、签名原样保留、失败不覆盖、计数输入、资料刷新、大文件引用、完整快照和输出截断状态。测试不会发网络请求，也不能证明服务端可用性或真实模型摘要质量。

依据（2026-10-01）：

- https://platform.claude.com/docs/en/build-with-claude/compaction-on-demand
- https://platform.claude.com/docs/en/build-with-claude/token-counting
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls
- https://code.claude.com/docs/en/context-window
