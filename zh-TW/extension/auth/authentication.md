# 認證

Kubernetes API 的認證（authentication）將請求對映為使用者、UID、組及附加屬性，之後由授權器判斷是否允許操作。Kubernetes 不提供普通使用者物件；使用者目錄和身分生命週期由外部系統管理。API 請求應使用 TLS，並設定明確的認證方式；不要依賴未加密 HTTP 或匿名存取。

## 常用認證方式

* **X.509 客戶端證書**：kube-apiserver 透過 `--client-ca-file` 信任客戶端證書；subject 的 CN 對映使用者名稱、O 對映組。證書私鑰只能由可信身分管理系統控制，不能把叢集 CA 私鑰發給使用者。
* **ServiceAccount Token**：工作負載身分使用短期、自動輪換的 TokenRequest/projected token。不要把長期 token 寫入映像檔或自行建立長期 Secret token。ServiceAccount 名稱格式為 `system:serviceaccount:<namespace>:<name>`；其組包括 `system:serviceaccounts` 和 `system:serviceaccounts:<namespace>`。
* **Bootstrap Token**：只用於叢集引導。自託管 API server 使用 `--enable-bootstrap-token-auth`；controller-manager 需要 `tokencleaner`。kubeadm 會管理相應叢集引導流程。不要將 bootstrap token 當作長期使用者憑證。
* **OIDC / JWT、Webhook TokenReview、Authenticating Proxy**：根據叢集發行版和身分提供商文件設定；驗證 issuer、audience、TLS CA 和可信代理請求頭來源。
* **靜態 Token 檔案**：API server 仍支援該機制，但憑證輪換和撤銷困難，不適合常規生產身分管理。

Kubernetes v1.37.1 不支援舊文件中的 `--basic-auth-file` 靜態密碼認證或舊 Keystone 實驗性認證 flags。不要部署這些舊設定。完整認證方式、結構化認證設定與匿名存取限制請參考 [Authenticating](https://kubernetes.io/docs/reference/access-authn-authz/authentication/)。

## TokenReview Webhook

Kubernetes v1.37.1 的 `kube-apiserver` 預設以 `authentication.k8s.io/v1beta1` 作為 TokenReview webhook 的 wire version。這個版本選擇的是 webhook 請求/響應協議，與 API server 對外提供的 REST API 版本不同。只實現 v1 的 webhook 必須設定 `--authentication-token-webhook-version=v1`；無論選擇哪個版本，響應的 API version 和 kind 都必須與請求完全一致。參見 v1.37.1 原始碼中的[預設值](https://github.com/kubernetes/kubernetes/blob/v1.37.1/pkg/kubeapiserver/options/authentication.go#L237-L242)和[flag 定義](https://github.com/kubernetes/kubernetes/blob/v1.37.1/pkg/kubeapiserver/options/authentication.go#L480-L481)。

Webhook 收到的請求範例：

```json
{
  "apiVersion": "authentication.k8s.io/v1beta1",
  "kind": "TokenReview",
  "spec": {
    "token": "BEARER_TOKEN"
  }
}
```

認證成功時的響應範例：

```json
{
  "apiVersion": "authentication.k8s.io/v1beta1",
  "kind": "TokenReview",
  "status": {
    "authenticated": true,
    "user": {
      "username": "jane@example.com",
      "uid": "user-123",
      "groups": ["developers"]
    }
  }
}
```

Webhook 應驗證呼叫身分、妥善保護 TLS 憑證，並只在驗證憑證成功後填充 `status.user`。參考 [Webhook Token Authentication](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#webhook-token-authentication)。

## kubectl exec credential plugin

`exec` credential plugin 是客戶端側擴充套件。新 kubeconfig 優先使用 `client.authentication.k8s.io/v1`；v1 設定要求明確設定 `interactiveMode`。v1beta1 仍可用於相容場景；不要使用已移除的 `v1alpha1` ExecCredential API。

```yaml
users:
  - name: example-user
    user:
      exec:
        apiVersion: client.authentication.k8s.io/v1
        command: example-credential-plugin
        interactiveMode: IfAvailable
```

Exec plugin 以本地程序執行，應只使用受信任、可審計的二進位檔案。認證 token / client certificate 等憑證應由外掛透過 stdout 返回正確版本的 `ExecCredential`，不要把金鑰寫進 kubeconfig 或日誌。參見 [Client-go credential plugins](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#client-go-credential-plugins)。

## 映像檔拉取憑證外掛

Kubelet credential provider exec 外掛用於按需獲取映像檔登錄站憑證，與使用者存取 kube-apiserver 的 exec credential plugin 不同。該能力自 Kubernetes v1.26 穩定；使用 Pod ServiceAccount Token 為映像檔拉取提供身分是 v1.34 起預設開啟的 Beta 功能，設定名為 `KubeletServiceAccountTokenForCredentialProviders`。請依據 kubelet 版本和外掛實現設定 `CredentialProviderConfig`，不要使用本文舊的 feature gate 名稱或不完整 `tokenAttributes` 設定。參考 [Configure a kubelet image credential provider](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-credential-provider/)。

## 更多資料

* [Authentication reference](https://kubernetes.io/docs/reference/access-authn-authz/authentication/)
* [ServiceAccount credentials](https://kubernetes.io/docs/concepts/security/service-accounts/#authenticating-credentials)
* [Managing certificates](https://kubernetes.io/docs/tasks/administer-cluster/certificates/)
