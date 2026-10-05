# ServiceAccount

ServiceAccount 为 Pod 中的进程提供 Kubernetes API 身份；它不授予权限，授权由 RBAC 等授权机制决定。ServiceAccount 是 namespace-scoped 资源，每个 Namespace 通常都会有一个 `default` ServiceAccount。

Pod 未指定 `serviceAccountName` 时，ServiceAccount admission 会将其设为该 Namespace 的 `default` ServiceAccount。除非 Pod 或 ServiceAccount 禁用了自动挂载，Pod 通常会通过 projected volume 获得短期 API 凭证。不要依赖创建 ServiceAccount 时自动生成长期 `kubernetes.io/service-account-token` Secret 的旧行为；Kubernetes v1.24 起默认不再自动生成此类 Secret。

若工作负载不需要访问 Kubernetes API，可通过 `automountServiceAccountToken: false` 禁用令牌自动挂载。不要将令牌写入清单、日志或源代码；需要外部客户端凭证时，优先使用短期 TokenRequest 工作流，并妥善保护凭证。

## ServiceAccount 与 RBAC

下面的示例创建一个只能在 `default` Namespace 中读取 Pod 的 ServiceAccount。实际应用应仅授予工作负载必需的权限：

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: pod-reader
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: default
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pod-reader
  namespace: default
subjects:
- kind: ServiceAccount
  name: pod-reader
  namespace: default
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: pod-reader
```

在 Pod 模板中通过 `spec.serviceAccountName` 指定身份；验证授权时使用 `kubectl auth can-i`，不要通过解码或打印 Bearer Token 来排错。

```yaml
spec:
  serviceAccountName: pod-reader
```

## 镜像拉取凭证

私有镜像仓库凭证通过 Kubernetes Secret 的 `imagePullSecrets` 配置。ServiceAccount 可以附加 `imagePullSecrets`，由使用该 ServiceAccount 的 Pod 继承；不要把镜像凭证配置成 API 访问令牌。

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: image-puller
  namespace: default
imagePullSecrets:
- name: registry-credentials
```

详情请参阅 [ServiceAccount 文档](https://kubernetes.io/docs/concepts/security/service-accounts/)和 [RBAC 文档](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)。
