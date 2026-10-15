# L = example.py 行号；从上往下读，每行只在一列执行。
# CALLER 与 RESOURCE 属于同一个 Task。
# WAIT(loop) = 等下一轮调度；YIELD(sb) = 交出资源。
# +------+------------------------------+------------------------------------+----------------------------+
# | STEP | CALLER (exercise)            | RESOURCE (boot_agent_sandbox)      | OUTPUT                     |
# +------+------------------------------+------------------------------------+----------------------------+
# | T01  | L20-21 ENTER -> T02          |                                    |                            |
# | T02  |                              | L7 print; L8 WAIT(loop)            | boot demo-image case-error |
# | T03  |                              | L8 RESUME; L9-10 prepare           |                            |
# | T04  |                              | L11 YIELD(sb) -> T05               |                            |
# | T05  | L21 as sandbox; L22 print    |                                    | inside True                |
# | T06  | L23 raise; L21 EXIT -> T07   |                                    |                            |
# | T07  |                              | L11 ValueError; L13 print          | closing case-error         |
# | T08  |                              | L14 WAIT(loop)                     |                            |
# | T09  |                              | L14 RESUME; L15-16 close           | closed case-error          |
# | T10  | L24 except; L25 print        |                                    | error work failed          |
# | T11  | L26 print                    |                                    | outside False              |
# +------+------------------------------+------------------------------------+----------------------------+
# T04-T07: 生成器停在 L11；使用区报错后，ValueError 被送回这里。
# T08: 清理停在 L14 等待；调用方还不能进入 L24 的 except。
# T09-T10: 先关闭资源，再让外层 except 处理原来的 ValueError。
