---
title: "21.3 · @ 装饰器：把函数交给另一个函数处理"
description: "第 21 单元拆分学习的第 3 步：@ 装饰器：把函数交给另一个函数处理。"
weight: 213
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** 前面的[函数调用例子](../01-async-def/#coroutine-definition)已经用过“函数名加括号”和向参数传值。本节继续用这两个基础，先把“函数本身”与“调用函数”分清。
>
> **本课新增的问题：** 能否把一个函数本身作为参数，交给另一个函数处理，再把处理后的入口交给调用方？

## 1. 函数名与调用：怎样把函数交给别人？

后面要让标准库处理我们写的资源管理函数，因此先理解“把函数交给别人”这个动作。本节使用普通函数就能观察，不需要用到 `yield`；它与 21.2 分别准备一块基础，之后在 21.4 汇合。

先认清两个写法：`greet` 指向函数本身，`greet()` 才是执行函数体。我们可以把函数赋给别的名字，也可以把它作为参数交给另一个函数。

## 2. @decorate：先观察装饰时和调用时的输出

[下载 example.py](example.py)，运行 `python3 example.py`。

<div class="async-coordination-code">

```python
def decorate(func):
    print("decorator received function")
    return func


@decorate
def greet():
    print("greet called")


def main():
    saved = greet
    print("function saved")
    saved()


if __name__ == "__main__":
    main()
```

</div>

实际输出：

```text
decorator received function
function saved
greet called
```

## 3. @decorate：把三个动作分开读

先按实际输出的顺序读：**装饰函数 → 保存函数 → 调用函数。**

<span id="32-decoratefunc接收函数返回一个可调用入口"></span>
<span id="33-decorate定义之后把函数交给-decorate"></span>

### 3.1 @decorate：在定义处先处理函数

定义 `greet` 时，把刚创建的函数对象交给 `decorate`。`decorate` 的参数 `func` 接收这个对象，先打印 `decorator received function`，再把同一个函数返回，名称 `greet` 随后绑定到这个返回值。

这一步调用了 `decorate`，但没有调用 `greet` 的函数体，所以尚未打印 `greet called`。

这段写法：

```python
@decorate
def greet():
    print("greet called")
```

等价于下面的定义与重新绑定。它是语法对照，不需要在主例子后再运行一遍：

```python
def greet():
    print("greet called")

greet = decorate(greet)
```

本例返回的仍是原函数；装饰器也可以返回新的入口，具体行为取决于它的实现。

<span id="31-saved--greet保存函数并没有执行它"></span>

### 3.2 saved = greet：进入 main，再保存函数

装饰完成后，脚本才运行到末尾的 `main()`。`main` 中的 `saved = greet` 让另一个名字指向同一函数，然后打印 `function saved`。赋值没有调用函数，因此仍未打印 `greet called`。

### 3.3 saved()：最后执行函数体

执行到 `saved()` 时，才调用它所指向的函数，进入 `greet` 的函数体，打印 `greet called`。这对应输出的第三行。

因此，传递或保存函数本身，与调用它，是不同的动作；`@decorate` 中确实发生了调用，但被调用的是 `decorate`。

## 4. @：本节只带走两件事

1. 函数名可以作为值赋给别的名字，也可以作为参数传递；写括号才表示调用。
2. `@decorate` 把定义好的函数交给 decorate，再用返回值重新绑定函数名。装饰时与调用时是两个阶段。

自查：本例打印 `decorator received function` 时，是否已经打印过 `greet called`？

<details><summary>查看解释</summary>

没有。装饰器接收了函数对象，并未调用它；主例子后来执行 saved()，才运行 greet 的函数体。

</details>

下一节使用标准库提供的装饰器，把已经认识的准备、yield 和关闭连接到 async with。

---

[上一节：21.2 · yield：交出一个值，并暂停在原处](../21-yield-pause/) · [下一节：21.4 · asynccontextmanager：把准备和关闭接到 async with](../21-async-contextmanager/) · [返回学习路线](../learning-route/)
