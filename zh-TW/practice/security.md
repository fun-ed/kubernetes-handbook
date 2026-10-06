# Kubernetes 工作負載安全

Kubernetes 安全需同時考量驗證、授權、准入、工作負載隔離、網路、節點與供應鏈。以下是適用於 Kubernetes v1.37 的通用起點，並非對特定發行版、CNI、執行階段或正式環境的認證。部署前請以目標平台的安全基線及 [Kubernetes v1.37 安全文檔](https://kubernetes.io/docs/concepts/security/)為準。

## 命名空間 Pod 安全標準

Pod Security Admission 可依命名空間標籤實施 Pod Security Standards。先以 `warn` 和 `audit` 評估現有工作負載，再決定是否啟用 `enforce`；此策略不會自動修改 Pod。以下範例固定使用 v1.37 策略版本：

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

符合 `restricted` 標準的 Pod 範例：

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

實際應用通常需要明確指定非 root UID/GID、可寫入目錄及資源限制，並驗證映像檔入口程式與磁碟區權限。完整限制請參閱 [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/) 與 [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)。

## 身分、權限與 Secret

- 為每個工作負載建立專用 ServiceAccount，只授予完成任務所需的 RBAC 權限；不需要 Kubernetes API 的 Pod 設定 `automountServiceAccountToken: false`。
- 使用短期、可輪替的 ServiceAccount 憑證，避免手動建立長期 token Secret。限制 Secret 讀取權限，並依平台要求設定靜態加密。
- 人類使用者透過受支援的外部身分提供者或用戶端憑證進行驗證；Kubernetes 不提供通用的 User 物件資料庫。
- 限制對 `pods/exec`、`pods/attach`、`nodes/proxy` 等敏感子資源的存取，並審查准入控制與稽核策略。

參考：[ServiceAccount](https://kubernetes.io/docs/concepts/security/service-accounts/)、[RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) 與 [Secret 加密](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)。

## 容器與節點隔離

使用 `securityContext` 設定非 root、唯讀根檔案系統、禁止權限提升、移除 capabilities 與 seccomp。AppArmor、SELinux、User Namespaces、sysctl 和補充群組策略的可用性，也取決於 Linux 核心、CRI 執行階段、節點設定、磁碟區與發行版；請逐項核對 v1.37 官方文件和平台支援範圍，不要只因清單中有該欄位就推斷節點支援。

- [Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [User Namespaces](https://kubernetes.io/docs/concepts/workloads/pods/user-namespaces/)
- [Seccomp](https://kubernetes.io/docs/tutorials/security/seccomp/)
- [AppArmor](https://kubernetes.io/docs/tutorials/security/apparmor/)
- [Sysctl](https://kubernetes.io/docs/tasks/administer-cluster/sysctl-cluster/)

NetworkPolicy 只有在所用網路實作支援並執行時才會生效；請為 ingress 與 egress 建立最小允許規則，並在目標 CNI 上驗證 DNS、健康檢查和應用程式流量。

## 安全基線與持續維護

映像檔應固定可信版本或 digest，掃描相依項目與映像檔，並保護建置、簽章和發布憑證。依目標發行版及 CIS Kubernetes Benchmark 版本選擇檢查工具；執行前應審查工具版本、節點存取權限、主機掛載及資源清單。檢查結果是風險線索，不等同於安全認證。持續追蹤 Kubernetes 與元件安全公告，並依受支援的升級路徑及時安裝修補程式。

本頁舊版 PSP、Alpha annotation、過時 feature-gate、長期憑證及未固定版本的 kube-bench 安裝範例已移至[歷史封存](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/zh-TW/practice/security.md)。請勿執行封存中的命令或清單。
