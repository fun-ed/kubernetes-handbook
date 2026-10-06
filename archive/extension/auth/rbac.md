# RBAC 不安全历史示例（封存）

> 以下为历史权限示例，包含可能将 cluster-admin 授予所有 ServiceAccount 的命令；不得在集群执行。

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
