# Kubernetes 使用者与工作负载身份

Kubernetes API 透过认证机制识别用户与工作负载，再由授权与准入机制决定请求可执行的操作。Kubernetes 本身不维护一般使用者的 User 对象或密码数据库；人类使用者通常由外部身份提供者认证，工作负载则使用 ServiceAccount。请依 Kubernetes v1.37 官方[认证](https://kubernetes.io/docs/reference/access-authn-authz/authentication/)与[授权](https://kubernetes.io/docs/reference/access-authn-authz/authorization/)文档配置集群。

## 人类使用者

为人类用户优先配置平台支持的 OIDC 或其他外部认证整合，并透过 RBAC 绑定群组到最小权限的 Role/ClusterRole。客户端凭据应由身份提供者或受控的证书流程签发；避免共享管理员 kubeconfig、把私钥放进仓库，或使用 `--insecure-skip-tls-verify`。

若采用客户端证书，证书中的 subject 通常映射为用户名（Common Name）及群组（Organization）。Kubernetes CSR API 不会自动替任意 CSR 签名：管理员必须确认受信任的 signer、请求用途与授权流程。使用 `certificates.k8s.io/v1` 时应提供 `signerName`、`usages` 和 Base64 编码的 PEM CSR，并仅由获授权的审批者批准。细节见 [Certificate Signing Requests](https://kubernetes.io/docs/reference/access-authn-authz/certificate-signing-requests/)；不要照用本页历史归档中的 `v1beta1` CSR、宽泛权限或跳过 TLS 验证的 kubeconfig。

## 工作负载 ServiceAccount

每个工作负载应使用专用 ServiceAccount 与最小 RBAC。无需访问 API 的 Pod 可关闭 token 自动挂载；需要 API 的程序使用 Kubernetes 投射的短期凭据。管理员可按需签发短期 token：

```bash
kubectl create token app-reader --namespace app
```

输出属于敏感凭据，不要写入 shell 历史、日志或版本控制。`kubectl create token` 请求服务器签发具有限期的 token；不要依赖自动生成的永久 token Secret。参考 [ServiceAccount](https://kubernetes.io/docs/concepts/security/service-accounts/) 与 [RBAC 最佳实践](https://kubernetes.io/docs/concepts/security/rbac-good-practices/)。

工作负载 RBAC 应限定 namespace、资源与动词；只有确有跨 namespace 或集群范围需求时才使用 ClusterRole。定期检查 RoleBinding、ClusterRoleBinding 与 ServiceAccount 的实际权限。

## 授权检查

在确认 `kubectl` 指向预期集群后，可使用 `kubectl auth can-i` 检查当前身份权限；命令会查询 API Server：

```bash
kubectl auth can-i get pods --namespace app
kubectl auth can-i create deployments --namespace app
```

将旧版 CSR 与 ServiceAccount 操作示例保留在[历史归档](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/practice/user-management.md)，仅供迁移参考；它们不属于 v1.37 的部署步骤。
