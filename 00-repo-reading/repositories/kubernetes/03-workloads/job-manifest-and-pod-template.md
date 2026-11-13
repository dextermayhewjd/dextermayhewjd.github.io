# Job 清单与 Pod 模板

[工作负载入口](README.md) · [Pod 与 Job](pods-and-jobs.md) · [镜像、命令与环境变量](../04-runtime-environment/container-image-and-env.md)

Job 清单描述整个 Job；其中的 `spec.template` 是 Kubernetes 的 **Pod 模板**，描述 Job 要创建怎样的 Pod。

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: demo-job              # Job 的名称
spec:
  template:                  # Job 内部的 Pod 模板
    spec:
      restartPolicy: Never   # Pod 配置
      containers:
        - name: worker
          image: busybox:1.36 # 这个容器使用的镜像
          command: ["sh", "-c", "echo $MESSAGE"]
          env:
            - name: MESSAGE  # 这个容器的环境变量
              value: hello
```

这是用于阅读字段位置的示例，没有实际部署。`containers` 是列表，环境变量写在各个容器条目中。

另外，项目可能用外部**文本模板**生成整份 Job 清单，例如先替换 `{{ job_name }}` 这样的占位符，再发送给 API Server。这个生成过程与 Kubernetes 的 `spec.template` 不是同一层：前者生成清单文本，后者是生成后的 Job 对象中的 Pod 模板字段。Kubernetes 本身不负责解释这些文本占位符。

## 官方来源

- [Job 的 Pod Template](https://kubernetes.io/docs/concepts/workloads/controllers/job/#pod-template)
- [为容器定义环境变量](https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/)
