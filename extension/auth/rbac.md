# RBAC 授权

Kubernetes 的基于角色的访问控制（Role-Based Access Control，RBAC）通过角色定义权限，再用绑定将权限授予用户、组或服务账号。权限按规则累加，RBAC 不提供拒绝规则。应只授予主体完成工作所需的权限。

## 前言

RBAC API 使用 `rbac.authorization.k8s.io/v1`。历史上，该 API 在 Kubernetes 1.6 进入 beta，并在 1.8 成为稳定版。配置 API Server 时，将 RBAC 加入授权器链；可以使用 `--authorization-mode=...,RBAC`，也可以使用 `--authorization-config` 配置文件。详见[官方 RBAC 文档](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)。

## RBAC 与 ABAC

鉴权决定用户是否可以使用 Kubernetes API 执行某项操作。授权适用于 kubectl 等客户端，也适用于集群内通过 Kubernetes API 操作集群的应用。

RBAC 策略由 Kubernetes API 对象管理，适合通过 Role、ClusterRole 及其绑定授予权限。下文的 ABAC 迁移示例仅记录旧集群行为，不是当前配置指南，切勿照搬。

对于新部署和权限管理，应使用 RBAC 并按最小权限原则配置。有关授权机制的当前说明，请参阅 [Kubernetes 授权文档](https://kubernetes.io/docs/reference/access-authn-authz/authorization/)。

## 基础概念

需要理解 RBAC 一些基础的概念和思路，RBAC 是让用户能够访问 [Kubernetes API 资源](https://kubernetes.io/docs/reference/) 的授权方式。

![RBAC &#x67B6;&#x6784;&#x56FE; 1](../../.gitbook/assets/rbac1%20%281%29.png)

在 RBAC 中定义了两个对象，用于描述在用户和资源之间的连接权限。

### Role 与 ClusterRole

Role（角色）是一系列权限的集合，例如一个角色可以包含读取 Pod 的权限和列出 Pod 的权限。Role 只能用来给某个特定 namespace 中的资源作鉴权，对多 namespace 和集群级的资源或者是非资源类的 API（如 `/healthz`）使用 ClusterRole。

```yaml
# Role 示例
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  namespace: default
  name: pod-reader
rules:
- apiGroups: [""] #"" indicates the core API group
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
```

```yaml
# ClusterRole 示例
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  # "namespace" omitted since ClusterRoles are not namespaced
  name: secret-reader
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "watch", "list"]
```

### RoleBinding 和 ClusterRoleBinding

RoleBinding 把角色（Role 或 ClusterRole）的权限映射到用户或者用户组，从而让这些用户继承角色在 namespace 中的权限。ClusterRoleBinding 让用户继承 ClusterRole 在整个集群中的权限。

ServiceAccount 的用户名格式为 `system:serviceaccount:<namespace>:<name>`。某个命名空间内所有 ServiceAccount 都属于 `system:serviceaccounts:<namespace>` 组；所有命名空间的 ServiceAccount 都属于 `system:serviceaccounts` 组。

```yaml
# RoleBinding 示例（引用 Role）
# This role binding allows "jane" to read pods in the "default" namespace.
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: read-pods
  namespace: default
subjects:
- kind: User
  name: jane
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

![RBAC &#x67B6;&#x6784;&#x56FE; 2](../../.gitbook/assets/rbac2.png)

```yaml
# RoleBinding 示例（引用 ClusterRole）
# This role binding allows "dave" to read secrets in the "development" namespace.
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: read-secrets
  namespace: development # This only grants permissions within the "development" namespace.
subjects:
- kind: User
  name: dave
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: secret-reader
  apiGroup: rbac.authorization.k8s.io
```

### ClusterRole 聚合

从 v1.9 开始，在 ClusterRole 中可以通过 `aggregationRule` 来与其他 ClusterRole 聚合使用（该特性在 v1.11 GA）。

比如

```yaml
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: monitoring
aggregationRule:
  clusterRoleSelectors:
  - matchLabels:
      rbac.example.com/aggregate-to-monitoring: "true"
rules: [] # Rules are automatically filled in by the controller manager.
---
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: monitoring-endpoints
  labels:
    rbac.example.com/aggregate-to-monitoring: "true"
# These rules will be added to the "monitoring" role.
rules:
- apiGroups: [""]
  resources: ["services", "endpoints", "pods"]
  verbs: ["get", "list", "watch"]
```

### 默认 ClusterRole

API Server 会创建一组默认 ClusterRole 和 ClusterRoleBinding。名称以 `system:` 开头的角色由集群控制平面管理，不应随意修改。角色的具体清单随 Kubernetes 版本变化，参见[默认角色和绑定](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#default-roles-and-role-bindings)。

## ABAC 迁移示例（不安全的历史说明）

以下内容只用于说明旧 ABAC 集群与 RBAC 集群的权限差异，不是迁移操作步骤。ABAC 规则可能授予宽泛权限；在多个授权器组成的链中，任一授权器允许请求时，请求就会获准，RBAC 不会收窄 ABAC 已允许的权限。新配置应使用 RBAC 并授予应用所需的最小权限。

下面的命令是旧版示例，**不安全且已过时，请勿执行**。它使用 `nginx:latest` 和 `curl -k`（跳过 TLS 证书校验），也假设 Pod 能读取长期有效的 ServiceAccount Token。现代集群通常为 Pod 投射可轮换的短期令牌，应用仍须获得相应授权。

```bash
# HISTORICAL AND UNSAFE. Do not run this example.
$ kubectl run nginx --image=nginx:latest
$ kubectl exec -it $(kubectl get pods -o jsonpath='{.items[0].metadata.name}') bash
$ apt-get update && apt-get install -y curl
$ curl -ik \
  -H "Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
  https://kubernetes/api/v1/namespaces/default/pods
```

## 宽泛的 cluster-admin 绑定（不安全的历史示例）

将 `cluster-admin` 授予 `system:serviceaccounts` 会让所有命名空间中的所有 ServiceAccount 都获得集群管理员权限。**这会造成严重的安全风险，以下命令仅作历史记录，切勿在集群中执行。**

```bash
# HISTORICAL AND UNSAFE. Do not run this example.
kubectl create clusterrolebinding permissive-binding \
  --clusterrole=cluster-admin \
  --user=admin \
  --user=kubelet \
  --group=system:serviceaccounts
```

## 推荐配置

* 针对命名空间内的资源，使用 Role 和 RoleBinding。
* 针对集群级资源，或需要跨所有命名空间授权时，使用 ClusterRole 和 ClusterRoleBinding。
* 针对多个指定命名空间中的资源，可以使用 ClusterRole 和各命名空间中的 RoleBinding。

## 开源工具

* [liggitt/audit2rbac](https://github.com/liggitt/audit2rbac)
* [reactiveops/rbac-manager](https://github.com/reactiveops/rbac-manager)
* [jtblin/kube2iam](https://github.com/jtblin/kube2iam)

## 参考文档

* [认证](https://kubernetes.io/docs/reference/access-authn-authz/authentication/)
* [授权](https://kubernetes.io/docs/reference/access-authn-authz/authorization/)
* [RBAC 授权](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
* [RBAC 最佳实践](https://kubernetes.io/docs/concepts/security/rbac-good-practices/)
* [ServiceAccount](https://kubernetes.io/docs/concepts/security/service-accounts/)
