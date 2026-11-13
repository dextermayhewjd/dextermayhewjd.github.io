# 容器配置：镜像、启动命令与环境变量

[运行环境入口](README.md) · [Job 与 Pod 模板](../03-workloads/job-manifest-and-pod-template.md)

同一个容器条目可以同时指定以下内容：

```yaml
containers:
  - name: worker
    image: busybox:1.36                  # 选用镜像
    imagePullPolicy: IfNotPresent        # 节点缺少该镜像时拉取
    command: ["sh", "-c", "echo $MESSAGE"] # 启动时执行什么
    env:
      - name: MESSAGE                   # 给容器进程的配置
        value: hello
```

这是 Pod 配置片段，没有实际执行。

- **image** 引用容器镜像，提供运行所需的文件系统、程序和依赖；构建镜像与在工作负载中引用镜像是两个动作。
- **command/args** 用来配置启动命令及参数，相关文件也可能由 Volume 挂载提供。
- **env** 属于这个容器，不是整个 Pod 自动共享的一张变量表。配置中的环境变量可以覆盖镜像预设的同名变量，但这不会重建镜像。

在 Job 清单中，这些字段位于 `spec.template.spec.containers[]`。环境变量中的 URL 由应用程序解释；Kubernetes 不会根据变量名自动知道它是不是数据库、模型服务或代理地址。

默认 Pod 网络中，容器内的 `localhost` 指向该 Pod 的网络环境，不能直接理解成运行控制器的机器。服务地址需要从实际调用它的进程所在位置可达。

## 官方来源

- [Images](https://kubernetes.io/docs/concepts/containers/images/)
- [为容器定义环境变量](https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/)
- [Pod 中的资源共享与通信](https://kubernetes.io/docs/concepts/workloads/pods/)
