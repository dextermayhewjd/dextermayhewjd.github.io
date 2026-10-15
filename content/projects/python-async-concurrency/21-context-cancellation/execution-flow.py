# L = example.py 行号；从上往下读，每行只在一列执行。
# MAIN 与 WORK 是两个 Task；resource 是 WORK 内的 boot_agent_sandbox。
# WAIT = 等待；RESUME = 恢复；YIELD = 交出资源；END = 任务结束。
# +------+-------------------------------+-----------------------------------+-----------------------------+
# | STEP | MAIN (exercise)               | WORK (work / resource)            | OUTPUT                      |
# +------+-------------------------------+-----------------------------------+-----------------------------+
# | T01  | L29 create; L30 WAIT(entered) |                                   |                             |
# | T02  |                               | work L23 ENTER -> T03             |                             |
# | T03  |                               | resource L7 print; L8 WAIT(loop)  | boot demo-image case-cancel |
# | T04  |                               | resource L8 RESUME; L9-10 prepare |                             |
# | T05  |                               | resource L11 YIELD -> T06         |                             |
# | T06  |                               | work L23-25 use; set entered      | inside True                 |
# | T07  |                               | work L26 WAIT(sleep)              |                             |
# | T08  | L30 RESUME; L31 cancel        |                                   |                             |
# | T09  | L32-33 WAIT(task)             |                                   |                             |
# | T10  |                               | work L26 CancelledError           |                             |
# | T11  |                               | work L23 EXIT -> T12              |                             |
# | T12  |                               | resource L11 error; L13 print     | closing case-cancel         |
# | T13  |                               | resource L14 WAIT(loop)           |                             |
# | T14  |                               | resource L14 RESUME; L15-16 close | closed case-cancel          |
# | T15  |                               | work L23 cancelled; END           |                             |
# | T16  | L33 raises; L34-35 except     |                                   | cancelled after cleanup     |
# +------+-------------------------------+-----------------------------------+-----------------------------+
# T01: MAIN 在 L30 等进入通知；T06 发通知，MAIN 到 T08 才恢复。
# T06-T07: set 只发通知；WORK 继续到 L26 等待，随后才轮到 MAIN。
# T08-T10: 本次先请求取消，MAIN 在 L33 让出执行，WORK 随后处理取消。
# T12: L11 收到同一个 CancelledError，进入 finally；T13 等关闭。
# T09-T16: MAIN 一直等 WORK；资源关闭、WORK 结束后，才确认取消。
