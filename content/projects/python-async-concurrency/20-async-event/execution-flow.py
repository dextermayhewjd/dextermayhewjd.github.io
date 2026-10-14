# T = 本次执行顺序；L = example.py 的真实行号。
# 每行只记录一份任务的执行；空白列的等待持续到该任务的 RESUME。
# FLAG 是同一个 release 对象里的标志，不是 fetch 的返回值。
# +------+-------------------------------+----------------------------+-------+
# | STEP | MAIN                          | FETCH                      | FLAG  |
# +------+-------------------------------+----------------------------+-------+
# | T01  | L5-14 create Event and Task   |                            | False |
# | T02  | L15 WAIT: next turn           |                            | False |
# | T03  |                               | L9-10 WAIT: set at T04     | False |
# | T04  | L16-18 RESUME; set; after set |                            | True  |
# | T05  | L19 WAIT: FETCH END           |                            | True  |
# | T06  |                               | L10-12 RESUME; return; END | True  |
# | T07  | L19 RESUME; print received    |                            | True  |
# +------+-------------------------------+----------------------------+-------+
# T02: MAIN 在 L15 让出本轮执行，FETCH 才开始运行。
# T03: FETCH 在 L10 等 release.set()，没有执行 L11、L12。
# T04: MAIN 在 L17 设置标志；FETCH 可以恢复，但 MAIN 继续执行 L18。
# T05: MAIN 在 L19 等 FETCH 结束；这次等待的是 task，不是 Event。
# T06: FETCH 到这里才从 L10 恢复，wait() 返回 True，L12 返回样本组列表。
# T07: MAIN 的 await task 得到样本组列表，随后 print。
