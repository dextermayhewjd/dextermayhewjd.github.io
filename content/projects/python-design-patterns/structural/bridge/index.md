---
title: "桥接 · Bridge"
description: "让两个变化维度可以独立组合。"
weight: 20
hideMeta: true
ShowToc: true
pythonVersion: "3.12"
---

[总览](../../) / [结构型](../)

## 1. 要解决什么问题

**使用心智模型：把“画什么形状”和“采用什么绘制方式”分开；形状持有一个渲染器，两边可以独立扩展，再按共同接口组合。**

**组合的前提：**每个接入的 renderer 都必须提供兼容的 `draw_primitive(name: str) -> str`，并能处理上层传来的形状名称。方法名、参数、返回值和行为含义都要符合共同约定。

当一个类在多个正交维度上扩展时（例如形状 Shape 和颜色 Color，或者控制端 Remote 与设备 Device），传统继承会导致类数量呈笛卡尔积爆炸式增长（如 RedCircle, BlueCircle, RedSquare 等）。

## 2. 在 Python 中怎样表达

Shape[R] 保存满足 RenderBackend 协议的渲染器，Circle 重写 draw。形状与 VectorRenderer、RasterRenderer 两个渲染实现通过组合连接，R 描述渲染器类型。

**运行前先观察：**Circle 的渲染器换成 RasterRenderer 后，draw 把绘制动作交给谁？

## 3. Python 3.12 完整示例

复制下面代码保存为 `.py` 文件，使用 Python 3.12 运行。示例只使用标准库。

采用本地项目的 Python 3.12 原例，仅补充中文注释。[下载完整示例](example.py)。

```python
"""
Bridge - Python 3.12+ Example: PEP 695 Generic Bridge & @override
"""
from dataclasses import dataclass
from typing import Protocol, override


class RenderBackend(Protocol):
    def draw_primitive(self, name: str) -> str: ...


class VectorRenderer:
    def draw_primitive(self, name: str) -> str:
        return f"Vector drawing of {name}"


class RasterRenderer:
    def draw_primitive(self, name: str) -> str:
        return f"Raster pixels for {name}"


@dataclass
class Shape[R: RenderBackend]:
    renderer: R

    def draw(self) -> str:
        return self.renderer.draw_primitive("generic_shape")


class Circle[R: RenderBackend](Shape[R]):
    @override
    def draw(self) -> str:
        # 圆形将绘制操作交给当前绑定的渲染器。
        return self.renderer.draw_primitive("circle")


if __name__ == "__main__":
    c = Circle(VectorRenderer())
    print(c.draw())
```

运行输出：

```text
Vector drawing of circle
```

### 3.1 Bridge 把哪两件事分开？ {#bridge-mental-model}

先看本例中的两个职责：

| 形状这一边 | 渲染器这一边 |
| --- | --- |
| `Circle` 决定要画 `"circle"` | `VectorRenderer` 按矢量方式处理绘制请求 |
| 将请求交给自己保存的 `renderer` | `RasterRenderer` 按像素方式处理同一个请求 |

形状和绘制方式是两个可以分别变化的选择。Bridge 将它们拆开，用对象组合连接起来。

#### 共同接口是组合的前提 {#bridge-interface-contract}

**每个接入的 renderer 都必须提供上层需要的 `draw_primitive` 方法。** 本例通过 RenderBackend 约定：

- 接收一个 `str` 类型的形状名称，例如 `"circle"`。
- 按这个形状名称处理绘制请求。
- 返回 `str` 类型的结果，供形状的 `draw()` 返回给调用方。

因此，仅有同名方法还不够，参数、返回值和实际行为也要匹配。新增形状时，仍需确认目标渲染器能够处理它；不能把“两个方向独立扩展”理解为任意对象都能直接组合。

#### 同一个 Circle，可以搭配不同渲染器

下面复用主例的类定义，分别创建两种组合：

```python
vector_circle = Circle(VectorRenderer())  # Circle 保存一个矢量渲染器。
raster_circle = Circle(RasterRenderer())  # 同一个形状类，也能保存像素渲染器。

print(vector_circle.draw())
print(raster_circle.draw())
```

输出：

```text
Vector drawing of circle
Raster pixels for circle
```

这里没有创建 `VectorCircle` 和 `RasterCircle` 两个形状类。Circle 只提供一次形状逻辑，具体绘制方式交给不同对象处理。

真正连接两边的是 Circle.draw 中这一句：

```python
return self.renderer.draw_primitive("circle")  # 将“画圆”的请求委托给当前渲染器。
```

主例用字符串模拟绘制结果，并没有实际生成图像。

#### 为什么要这样拆？

假设以后增加方形，或者增加一种 SVG 绘制方式：

| 新需求 | 扩展哪一边 | 可以复用什么 |
| --- | --- | --- |
| 新增方形 | 写新的形状类，提出 `"square"` 请求 | 已有渲染器，不必再写两套方形类 |
| 新增 SVG 绘制方式 | 写实现 `draw_primitive` 的新渲染器 | 已有 Circle，形状逻辑不用重复 |

表中是后续扩展示意，主例没有实现 Square 或 SVGRenderer。是否值得拆开，取决于实际是否存在这两个需要独立扩展的方向；仅仅把一个对象放进另一个对象，并不足以说明用了 Bridge。

### 3.2 按需回查代码关系

<details id="bridge-composition">
<summary>A · Circle(VectorRenderer()) 把对象放在哪里？</summary>

`Shape` 用 `@dataclass` 声明了 `renderer` 字段，生成的构造方法会接收并保存它；Circle 继承了这一构造方式。

```python
renderer = VectorRenderer()
circle = Circle(renderer)
print(circle.renderer is renderer)  # True：形状持有的正是传入的对象。
```

Circle 继承的是 Shape，它没有继承 VectorRenderer。形状与渲染器之间是持有和委托关系。

</details>

<details id="bridge-types">
<summary>B · R 和 RenderBackend 是桥接本身吗？</summary>

`RenderBackend` 描述渲染器应有的 `draw_primitive` 接口。`R: RenderBackend` 约束渲染器的类型，`renderer: R` 记录形状保存的对象类型。

这些类型声明有助于检查接口。实际运行时的连接仍是 `self.renderer.draw_primitive(...)`；类型参数本身不负责绘制，也不创建渲染器。

Protocol 和类型注解不会自动给对象添加缺少的方法。是否符合约定需要由实现者保证，并由类型检查与实际运行验证。

</details>

### 3.3 与 Adapter 分开记

- **Adapter：**已有两边接口不兼容，用转换层让它们能配合。
- **Bridge：**把两个可独立变化的职责拆开，用组合让它们配合。

**本例一句话：Circle 负责画什么，renderer 负责怎样处理绘制，两边通过持有对象和方法调用连接。**

## 4. 使用边界

两个维度确实需要独立扩展时才值得拆开；只有一种稳定实现时，不必预先建立两套结构。

## 5. 按需对照

<details id="original-python-example">
<summary>历史原例：Python 3.10 写法</summary>

仅用于对照此前的实现，不是本页主例。业务场景可能与上面的 Python 3.12 主例不同。

```python
"""
Bridge - Python 3.10+ Example: Protocol Device & Dataclass Controllers
"""
from dataclasses import dataclass
from typing import Protocol


class Device(Protocol):
    def turn_on(self) -> str: ...
    def turn_off(self) -> str: ...
    def set_channel(self, channel: int) -> str: ...


class SmartTV:
    def turn_on(self) -> str:
        return "SmartTV display waking up"

    def turn_off(self) -> str:
        return "SmartTV entering standby"

    def set_channel(self, channel: int) -> str:
        return f"SmartTV streaming channel {channel}"


class Radio:
    def turn_on(self) -> str:
        return "Radio power amp engaged"

    def turn_off(self) -> str:
        return "Radio powered down"

    def set_channel(self, channel: int) -> str:
        return f"Radio tuned to FM {channel}MHz"


@dataclass
class BasicRemote:
    device: Device

    def power(self) -> str:
        return self.device.turn_on()


@dataclass
class VoiceRemote(BasicRemote):
    def voice_command(self, cmd: str) -> str:
        match cmd:
            case "on":
                return self.device.turn_on()
            case "off":
                return self.device.turn_off()
            case _:
                return f"Voice unrecognized: {cmd}"


if __name__ == "__main__":
    tv = SmartTV()
    remote = VoiceRemote(tv)
    print(remote.power())
    print(remote.voice_command("off"))
```

</details>

<details>
<summary>传统面向对象写法</summary>

观察职责如何通过类、接口和对象之间的调用分开。这份示例与上面的 Python 主例子可能使用不同业务场景。

```python
"""
Bridge - Conceptual Example (Classic GoF)
"""
from abc import ABC, abstractmethod


class Implementation(ABC):
    @abstractmethod
    def operation_implementation(self) -> str:
        pass


class ConcreteImplementationA(Implementation):
    def operation_implementation(self) -> str:
        return "ConcreteImplementationA on platform A."


class ConcreteImplementationB(Implementation):
    def operation_implementation(self) -> str:
        return "ConcreteImplementationB on platform B."


class Abstraction:
    def __init__(self, implementation: Implementation) -> None:
        self.implementation = implementation

    def operation(self) -> str:
        return f"Abstraction: Base operation with:\n{self.implementation.operation_implementation()}"


class ExtendedAbstraction(Abstraction):
    def operation(self) -> str:
        return f"ExtendedAbstraction: Extended operation with:\n{self.implementation.operation_implementation()}"


def client_code(abstraction: Abstraction) -> str:
    return abstraction.operation()


if __name__ == "__main__":
    impl_a = ConcreteImplementationA()
    abs_1 = Abstraction(impl_a)
    print(client_code(abs_1))

    impl_b = ConcreteImplementationB()
    abs_2 = ExtendedAbstraction(impl_b)
    print(client_code(abs_2))
```

</details>

<details>
<summary>适用情况、收益与代价</summary>

### 适用情况

- 如果你想要拆分或重组一个具有多重维度的庞杂类时
- 如果你希望在几个独立维度上扩展一个类时
- 需要在运行时切换不同实现时

### 收益

- 可以创建与平台无关的类和程序
- 客户端代码仅与高层抽象进行交互，不触及平台细节
- 开闭原则：可以独立新增抽象和实现
- 单一职责原则：抽象专注高层逻辑，实现专注底层细节

### 代价

- 对高内聚的类使用该模式可能会使代码变得更加复杂

</details>

<details>
<summary>来源与版本</summary>

代码与基础说明来自 [back_to_design_pattern / bridge](https://github.com/dextermayhewjd/back_to_design_pattern/blob/42e623b8f6d94ec44884f45131e7f15570009577/src/design_patterns/catalog/structural/bridge.py)，快照 `42e623b8f6d9`。

主例取自该模块的 PYTHON312_CODE，类、方法、签名及程序结构与原例一致，仅增加中文注释；本站另提供分块讲解、运行输出和适用边界。

原项目按 MIT 许可提供，见[许可全文](../../license.txt)。

</details>
