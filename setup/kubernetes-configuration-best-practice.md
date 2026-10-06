# Kubernetes 配置最佳实践

本文针对 Kubernetes v1.37.1 整理资源配置建议。正式部署前，应依目标集群 API 与组件版本核对字段、策略和兼容范围；将清单纳入版本控制，但不得提交凭证或敏感配置。

## 声明式资源

- 使用当前受支持的 API 版本，并依[弃用指南](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)检查已移除 API。API 迁移可能需要调整 selector、字段结构或行为，不能只替换 `apiVersion`。
- 对 Deployment、StatefulSet 等控制器明确指定 selector，并确保它与 Pod template labels 一致。新工作负载优先使用适当的控制器或 Job，不要把单独创建的 Pod 当作具有自我修复能力的部署。
- 以 Service DNS 名称访问服务；只有确有需要时才配置 `hostNetwork` 或 `hostPort`，因为它们会共享节点网络或造成端口冲突。
- 采用最小权限 RBAC。检查 Service、NetworkPolicy 和 Pod selector 是否只匹配预期对象；避免空 selector 或宽泛的集群级授权。
- 对 API 资源清单使用 `kubectl apply --dry-run=server --validate=strict -f <file>` 做目标集群预检。CRD、自定义资源和 admission webhook 需要相应 CRD、controller/webhook 前置条件；dry-run 不能证明业务行为可用。

## 镜像与 Secret

- 固定经过审阅的镜像版本；需要不可变部署时固定 digest。不要在生产工作负载使用 `:latest` 或假设可变 tag 不会移动。
- 使用 Secret 管理敏感数据，并依实际威胁模型限制读取权限、加密静态数据及轮换凭证。不要把 token、私钥或 kubeconfig 写入镜像、源代码或公开日志。

## 资源与安全

- 为工作负载设定经过容量评估的 CPU、memory requests/limits；为可被逐出的应用配置合理的 PodDisruptionBudget，并避免 selector 为空。
- 使用 Pod Security Admission 的 namespace labels 或维护中的策略实现约束 Pod 权限。PodSecurityPolicy 已移除；不要使用 PSP 清单或旧 seccomp 注解。
- NetworkPolicy 是否生效取决于所选 CNI 的实现；部署前确认 provider 支持并验证 ingress/egress 策略。

官方参考：[Configuration Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)、[Workload Resources](https://kubernetes.io/docs/concepts/workloads/controllers/)、[RBAC 最佳实践](https://kubernetes.io/docs/concepts/security/rbac-good-practices/)、[镜像](https://kubernetes.io/docs/concepts/containers/images/)。
