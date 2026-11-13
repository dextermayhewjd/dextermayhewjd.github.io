# 控制器与协调循环：持续推进期望状态

[架构入口](README.md) · [一次 Job 的整体流程](../00-overview/job-lifecycle.md)

**控制器持续观察资源，判断当前情况与资源要求之间的差距，并采取或请求相应动作。** 这个过程称为协调，通常会被资源事件或再次检查触发。

```text
observe resources -> compare with desired state -> act -> observe again
```

## 用 Job 理解协调

对于一个要求成功完成工作的 Job，控制器会观察它及关联 Pod。根据 Job 的配置与当前结果，控制器可能创建所需的 Pod，或更新 Job 的完成、失败情况。

Job 控制器通过 Kubernetes API 管理对象；节点上的 kubelet 和运行时承担具体执行。控制器的“采取动作”不等于自己直接运行容器。

## 协调不是复制字段

`spec` 与 `status` 的字段并不需要同形。例如 Job 的期望完成数量与已经成功的 Pod 数量表达相关但不同的信息。控制器依据这种资源的规则判断是否达成目标。

同一个资源可能被重复观察。理解协调函数时，优先看：

- 读取哪些对象和状态。
- 用什么标识把对象对应起来。
- 在哪种差异下创建、更新或删除资源。
- 动作后由谁观察结果、怎样继续收敛。

具体控制器的重试、限速、冲突处理和幂等细节，围绕实际问题逐项展开。

## 一次协调返回，不等于环境已就绪

1. 控制器可以提交缺少的 Pod 对象，然后结束本次调用。
2. Scheduler、kubelet 和运行时继续推进调度与容器启动。
3. 新的资源状态可触发下一次协调，控制器据此更新观察状态。

“本次操作没有返回错误”和“工作已经就绪”是不同结论。记录未就绪或失败原因也是协调的一部分，不要求所有资源先成功才更新状态。

协调器通常不是等待整个任务执行结束的函数。具体通过事件、定时检查或重排再次运行，要回到各控制器的实现；本页不规定一种统一客户端框架。

## 官方来源

- [Controllers](https://kubernetes.io/docs/concepts/architecture/controller/)
- [Objects In Kubernetes](https://kubernetes.io/docs/concepts/overview/working-with-objects/)
