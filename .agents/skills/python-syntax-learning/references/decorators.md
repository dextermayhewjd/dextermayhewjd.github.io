# 装饰器的最小边界

如果读者尚不知道函数可以赋值和传递，第一单元先建立这个关系：

```python
def greet():
    print("called")
    return "hi"

saved = greet
print("assigned")
print(saved())
```

输出：

```text
assigned
called
hi
```

1. `greet` 指向函数对象；`greet()` 是调用它。
2. `saved = greet` 让另一个名字指向同一对象，不会调用函数。
3. `saved()` 通过这个名字调用函数，得到返回值。

后续再建立“函数接收函数并返回函数”，最后说明 `@decorate` 与函数名重新绑定的关系。返回新 wrapper 是常见用法，不是装饰器必须满足的唯一形式。需要闭包保存原函数时再解释闭包；不要在未说明作用的情况下同时塞入 `*args`、`**kwargs`、`functools.wraps` 和参数化装饰器。

若用户明确要求本轮看懂 `@` 的最小实例，应在本轮补足必要前置关系并提供实例，而不是只给一个未来课程计划。已有基础、当前目标和用户指定范围始终决定拆分粒度。
