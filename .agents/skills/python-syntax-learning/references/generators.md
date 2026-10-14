# 生成器的最小边界

可以用一个 `yield` 和一次 `next()` 观察创建与推进，避免同时引入循环消费、发送数据及异步迭代。

```python
def numbers():
    print("entered")
    yield 10

g = numbers()
print("created")
value = next(g)
print(value)
```

输出：

```text
created
entered
10
```

1. 含 `yield` 的普通 `def` 定义产生生成器函数；不要把 `yield` 称为“返回后结束函数”。
2. 调用创建生成器对象，函数体此时未开始。
3. 第一次 `next(g)` 推进函数体，到 `yield` 产出值并暂停。

这个例子只取一个值。再次推进、正常耗尽、`StopIteration`、`for` 消费可在读者理解第一次推进后展开。读者若已经掌握迭代协议，就从缺失的部分开始，不重教完整入门链。
