# 准入控制

准入控制（admission）在請求完成認證（authentication）和授權（authorization）之後、物件寫入儲存之前，對建立、更新、刪除及部分連線操作進行驗證或修改。`get`、`list`、`watch` 讀請求不會經過 admission。

Kubernetes v1.37.1 內建 admission controller 的預設啟用清單以官方參考為準；不要沿用舊版 `--admission-control` 設定或照搬一個固定外掛列表。自託管 kube-apiserver 使用 `--enable-admission-plugins` / `--disable-admission-plugins`（部分發行版透過自己的設定管理），變更控制平面設定前先確認發行版文件。

## Pod 安全：使用 Pod Security Admission

PodSecurityPolicy（PSP）已在 Kubernetes v1.25 移除。Pod Security Admission（PSA）自 v1.25 起穩定，並作為內建 admission controller 預設啟用；按需要給 namespace 設定 Pod Security Standards 標籤，例如先開啟 `warn` / `audit` 檢查，再評估是否啟用 `enforce`：

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

確認工作負載滿足策略後，再將 `pod-security.kubernetes.io/enforce: restricted` 和對應版本標籤加入 namespace。不要把舊 PSP 清單或 PSP admission 設定用於 v1.37。參考 [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) 與 [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)。

## ValidatingAdmissionPolicy

對可用 CEL 表達的驗證策略，優先評估內建 `ValidatingAdmissionPolicy` / `ValidatingAdmissionPolicyBinding`，減少外部 webhook 依賴。複雜驗證或物件變更仍可使用 webhook；檢視 [ValidatingAdmissionPolicy](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/) 的 API 版本、binding 和 failure 設定。

## Admission webhook

Webhook 設定使用 `admissionregistration.k8s.io/v1` 中的 `ValidatingWebhookConfiguration` 或 `MutatingWebhookConfiguration`，Webhook server 收發 `admission.k8s.io/v1` `AdmissionReview`。不要使用已經移除的 `v1alpha1` Initializer / GenericAdmissionWebhook API；API object kind 也不是 `ValidatingAdmissionWebhook`。

下面是 validating webhook 的最小範例。將 `BASE64_ENCODED_CA_BUNDLE` 替換為簽發 webhook HTTPS 服務證書的 CA PEM 內容的 base64 編碼，並確保證書 SAN 包含 `example-service.example-namespace.svc`。

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

生產 webhook 會成為控制面的關鍵依賴。範例設定 `failurePolicy: Fail`，如果 API server 無法連線 webhook 或呼叫超時，匹配的 Pod CREATE/UPDATE 請求會被拒絕。使用策略前，應先確認 webhook 服務、DNS、TLS 證書和回撥端點可用。只有在安全檢查允許跳過時才使用 `Ignore`；避免規則覆蓋 webhook 自身啟動所需的資源，以免 fail-closed 阻斷恢復所需的 Pod。參考 [Dynamic Admission Control](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/) 和 [內建 admission controllers](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)。

## 歷史設定

舊版 PSP、Initializers、`ExternalAdmissionHookConfiguration`、`admissionregistration.k8s.io/v1alpha1`、`--admission-control` 以及 `PersistentVolumeLabel` 等設定範例不適用於 Kubernetes v1.37.1；不要部署這些片段。舊外掛名稱和預設值以對應 Kubernetes 舊版本文件為準。
