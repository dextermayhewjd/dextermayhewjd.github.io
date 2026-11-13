# 安全与隔离：访问权限与执行边界

[资料总入口](../README.md) · [运行环境](../04-runtime-environment/README.md)

理解工作怎样运行，还要知道它能访问什么、消耗什么，以及与其他工作共享什么。资源分组、权限控制与执行隔离分别承担不同职责。

| 边界 | 首先区分什么 | 相关机制入口 |
| --- | --- | --- |
| API 身份与权限 | 谁在发请求，允许操作哪些资源 | ServiceAccount、RBAC |
| 网络访问 | 哪些连接允许发生 | NetworkPolicy；实际执行依赖相应网络能力 |
| 容器权限 | 进程使用什么身份、具有什么系统能力 | securityContext、Pod Security |
| 资源消耗 | 工作请求或最多可使用多少资源 | requests/limits、ResourceQuota；定义见运行环境主题 |
| 运行时隔离 | 容器与宿主机、其他工作共享哪些底层边界 | 容器运行时、RuntimeClass、可提供更强隔离的运行环境 |

## 与沙箱有关的核心区别

Namespace 提供资源命名与管理范围，不能单独代表完整的安全隔离。Pod/Job 描述执行与管理目标，也不自动说明其中代码被什么强度的边界隔离。

普通容器通常共享宿主内核；更强的隔离可能依赖不同的运行环境。RuntimeClass 用于选择运行时配置，实际隔离能力取决于被选中的运行时和部署方式。

首次学习以能说明边界、识别必要配置为目标；需要实现或排查某种隔离机制时，再展开对应细节。

## 官方入口

- [Multi-tenancy](https://kubernetes.io/docs/concepts/security/multi-tenancy/)
- [RuntimeClass](https://kubernetes.io/docs/concepts/containers/runtime-class/)
- [RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
