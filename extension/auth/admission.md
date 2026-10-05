# 准入控制

准入控制（admission）在请求完成认证（authentication）和授权（authorization）之后、对象写入存储之前，对创建、更新、删除及部分连接操作进行验证或修改。`get`、`list`、`watch` 读请求不会经过 admission。

Kubernetes v1.37.1 内置 admission controller 的默认启用清单以官方参考为准；不要沿用旧版 `--admission-control` 配置或照搬一个固定插件列表。自托管 kube-apiserver 使用 `--enable-admission-plugins` / `--disable-admission-plugins`（部分发行版通过自己的配置管理），变更控制平面配置前先确认发行版文档。

## Pod 安全：使用 Pod Security Admission

PodSecurityPolicy（PSP）已在 Kubernetes v1.25 移除。Pod Security Admission（PSA）自 v1.25 起稳定，并作为内置 admission controller 默认启用；按需要给 namespace 设置 Pod Security Standards 标签，例如先开启 `warn` / `audit` 检查，再评估是否启用 `enforce`：

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: team-a
  labels:
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: v1.37
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: v1.37
```

确认工作负载满足策略后，再将 `pod-security.kubernetes.io/enforce: restricted` 和对应版本标签加入 namespace。不要把旧 PSP 清单或 PSP admission 配置用于 v1.37。参考 [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) 与 [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)。

## ValidatingAdmissionPolicy

对可用 CEL 表达的校验策略，优先评估内置 `ValidatingAdmissionPolicy` / `ValidatingAdmissionPolicyBinding`，减少外部 webhook 依赖。复杂校验或对象变更仍可使用 webhook；查看 [ValidatingAdmissionPolicy](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/) 的 API 版本、binding 和 failure 配置。

## Admission webhook

Webhook 配置使用 `admissionregistration.k8s.io/v1` 中的 `ValidatingWebhookConfiguration` 或 `MutatingWebhookConfiguration`，Webhook server 收发 `admission.k8s.io/v1` `AdmissionReview`。不要使用已经移除的 `v1alpha1` Initializer / GenericAdmissionWebhook API；API object kind 也不是 `ValidatingAdmissionWebhook`。

下面是 validating webhook 的最小示例。将 `BASE64_ENCODED_CA_BUNDLE` 替换为签发 webhook HTTPS 服务证书的 CA PEM 内容的 base64 编码，并确保证书 SAN 包含 `example-service.example-namespace.svc`。

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: pod-policy.example.com
webhooks:
  - name: pod-policy.example.com
    admissionReviewVersions: ["v1"]
    sideEffects: None
    failurePolicy: Fail
    matchPolicy: Equivalent
    timeoutSeconds: 5
    clientConfig:
      service:
        namespace: example-namespace
        name: example-service
        path: /validate
        port: 443
      caBundle: BASE64_ENCODED_CA_BUNDLE
    rules:
      - apiGroups: [""]
        apiVersions: ["v1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["pods"]
        scope: Namespaced
```

生产 webhook 会成为控制面的关键依赖。示例设置 `failurePolicy: Fail`，如果 API server 无法连接 webhook 或调用超时，匹配的 Pod CREATE/UPDATE 请求会被拒绝。使用策略前，应先确认 webhook 服务、DNS、TLS 证书和回调端点可用。只有在安全检查允许跳过时才使用 `Ignore`；避免规则覆盖 webhook 自身启动所需的资源，以免 fail-closed 阻断恢复所需的 Pod。参考 [Dynamic Admission Control](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/) 和 [内置 admission controllers](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)。

## 历史配置

旧版 PSP、Initializers、`ExternalAdmissionHookConfiguration`、`admissionregistration.k8s.io/v1alpha1`、`--admission-control` 以及 `PersistentVolumeLabel` 等配置示例不适用于 Kubernetes v1.37.1；不要部署这些片段。旧插件名称和默认值以对应 Kubernetes 旧版本文档为准。
