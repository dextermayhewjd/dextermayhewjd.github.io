# Pod 地址与 Service：访问入口与实际连接

[运行环境](README.md) · [标签与选择器](../02-resource-model/labels-and-selectors.md)

**Pod 地址描述具体运行实例，Service 为一组后端提供服务发现和访问抽象。** 创建访问入口对象与实际发起连接，是不同的动作。

## 1. 对象之间怎样关联

1. Pod 的状态可以报告它的 IP 地址；替换 Pod 后地址可能改变。
2. 带 selector 的 Service 通过标签选择后端 Pod，并声明服务端口与目标端口等信息。
3. Kubernetes 的相关组件根据这些对象维护后端信息和访问路径；应用按服务名称或适用地址发起请求。

普通 ClusterIP Service 通常有集群虚拟 IP。Headless Service 不分配这种虚拟 IP，可以通过 DNS 直接发现后端地址；不要把所有 Service 都理解为同一种转发方式。

## 2. 协调 Service 做什么

控制器可以根据需求创建 Service，或修正 selector、端口等配置。归属检查用于防止误操作其他工作的资源。

这些对象操作不等于主动尝试连接应用。即使 Service 已存在，后端 Pod 就绪、进程监听、网络权限与实际路径等仍会影响访问结果。

## 3. 与 Ready 的关系

Pod Ready、Service 对象存在、一次连接成功、业务任务完成是不同事实。上层控制器怎样综合这些事实，要看它自己的状态定义，不能从一个字段推断全部成立。

## 来源

- [Service](https://kubernetes.io/docs/concepts/services-networking/service/)
- [DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
- [阅读来源记录](../references/learning-sources.md)
