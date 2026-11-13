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
