# PodPreset（历史 API）

PodPreset 曾是用于向匹配标签的 Pod 注入环境变量、卷等配置的 Alpha API。该 API 与 admission controller 已在较早的 Kubernetes 版本中移除；`settings.k8s.io/v1alpha1`、相关 feature gate 和旧版示例在 v1.37 不可用。不要尝试开启历史 `--runtime-config` 或 `PodPreset` 准入插件。

当前可按需求在 Deployment、StatefulSet 等 Pod 模板中显式配置 `env`、`envFrom`、`volumes` 和 `volumeMounts`；可复用的非敏感配置存放在 ConfigMap，敏感值存放在 Secret。需要动态变更 Pod 时，应评估与目标版本兼容、受维护且有清晰安全边界的 admission webhook。

请参阅 [ConfigMap 文档](https://kubernetes.io/docs/concepts/configuration/configmap/)、[Secret 文档](https://kubernetes.io/docs/concepts/configuration/secret/)以及 [Admission Webhook 文档](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/)。
