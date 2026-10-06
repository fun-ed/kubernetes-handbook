# Kubernetes 工作负载安全

Kubernetes 安全需要同时考虑身份验证、授权、准入、工作负载隔离、网络、节点与供应链。以下是适用于 Kubernetes v1.37 的通用起点，不是对特定发行版、CNI、运行时或生产环境的认证。部署前请以目标平台的安全基线及 [Kubernetes v1.37 安全文档](https://kubernetes.io/docs/concepts/security/)为准。

## 命名空间 Pod 安全标准

Pod Security Admission 可依命名空间标签实施 Pod Security Standards。先用 `warn` 与 `audit` 评估现有工作负载，再决定是否启用 `enforce`；策略不会自动修改 Pod。下例固定使用 v1.37 策略版本：

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: restricted-workloads
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: v1.37
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: v1.37
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: v1.37
```

符合 `restricted` 标准的 Pod 示例：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: restricted-example
  namespace: restricted-workloads
spec:
  securityContext:
    runAsNonRoot: true
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: app
      image: registry.k8s.io/pause:3.10.2
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: ["ALL"]
```

实际应用通常需要显式指定非 root UID/GID、可写目录及资源限制，并验证镜像入口程序与卷权限。完整限制见 [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/) 与 [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)。

## 身份、权限与 Secret

- 为每个工作负载创建专用 ServiceAccount，只授予完成任务所需的 RBAC 权限；不需要 Kubernetes API 的 Pod 设置 `automountServiceAccountToken: false`。
- 使用短期、可轮换的 ServiceAccount 凭据，避免手动创建长期 token Secret。限制 Secret 的读取权限，并按平台要求配置静态加密。
- 对人类用户使用受支持的外部身份提供者或客户端证书认证；Kubernetes 不提供通用的 User 对象数据库。
- 限制对 `pods/exec`、`pods/attach`、`nodes/proxy` 等敏感子资源的访问，并审查准入控制与审计策略。

参考：[ServiceAccount](https://kubernetes.io/docs/concepts/security/service-accounts/)、[RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) 与 [Secret 加密](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)。

## 容器与节点隔离

使用 `securityContext` 配置非 root、只读根文件系统、禁止提权、capability drop 与 seccomp。AppArmor、SELinux、User Namespaces、sysctl 和补充组策略的可用性还取决于 Linux 内核、CRI runtime、节点配置、卷与发行版；逐项核对 v1.37 官方文档和平台支持，不要仅凭清单字段存在就推断节点支持。

- [Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [User Namespaces](https://kubernetes.io/docs/concepts/workloads/pods/user-namespaces/)
- [Seccomp](https://kubernetes.io/docs/tutorials/security/seccomp/)
- [AppArmor](https://kubernetes.io/docs/tutorials/security/apparmor/)
- [Sysctl](https://kubernetes.io/docs/tasks/administer-cluster/sysctl-cluster/)

NetworkPolicy 只有在所用网络实现支持并执行时才会产生隔离效果；为 ingress 与 egress 建立最小允许规则，并在目标 CNI 上验证 DNS、健康检查和应用流量。

## 安全基线与持续维护

为镜像固定可信版本或 digest，扫描依赖与镜像，并保护构建、签名和发布凭据。按目标发行版及 CIS Kubernetes Benchmark 版本选择检查工具；审查其版本、节点访问权限、主机挂载及清单后再运行。检查结果是风险线索，不等同于安全认证。持续跟踪 Kubernetes 与组件安全公告，并按受支持的升级路径及时安装修复。

本页旧版 PSP、Alpha annotation、过时 feature-gate、长期凭据及未固定 kube-bench 安装示例已移入[历史归档](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/practice/security.md)。不要执行归档中的命令或清单。
