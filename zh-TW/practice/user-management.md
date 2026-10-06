# Kubernetes 使用者與工作負載身分

Kubernetes API 透過驗證機制識別使用者與工作負載，再由授權與准入機制決定請求可執行的操作。Kubernetes 本身不維護一般使用者的 User 物件或密碼資料庫；人類使用者通常由外部身分提供者驗證，工作負載則使用 ServiceAccount。請依 Kubernetes v1.37 官方[驗證](https://kubernetes.io/docs/reference/access-authn-authz/authentication/)與[授權](https://kubernetes.io/docs/reference/access-authn-authz/authorization/)文件設定叢集。

## 人類使用者

人類使用者優先設定平台支援的 OIDC 或其他外部驗證整合，再透過 RBAC 將群組綁定至最小權限的 Role/ClusterRole。用戶端憑證應由身分提供者或受控的憑證流程簽發；避免共用管理員 kubeconfig、將私密金鑰放進儲存庫，或使用 `--insecure-skip-tls-verify`。

若採用用戶端憑證，憑證中的 subject 通常會對應至使用者名稱（Common Name）及群組（Organization）。Kubernetes CSR API 不會自動替任意 CSR 簽署：管理員必須確認受信任的 signer、請求用途與授權流程。使用 `certificates.k8s.io/v1` 時應提供 `signerName`、`usages` 和 Base64 編碼的 PEM CSR，且只能由獲授權的核准者核准。細節請參閱 [Certificate Signing Requests](https://kubernetes.io/docs/reference/access-authn-authz/certificate-signing-requests/)；請勿照用本頁歷史封存中的 `v1beta1` CSR、寬泛權限或略過 TLS 驗證的 kubeconfig。

## 工作負載 ServiceAccount

每個工作負載應使用專用 ServiceAccount 與最小 RBAC。無須存取 API 的 Pod 可關閉 token 自動掛載；需要 API 的程式使用 Kubernetes 投射的短期憑證。管理員可依需求簽發短期 token：

```bash
kubectl create token app-reader --namespace app
```

輸出屬於敏感憑證，請勿寫入 shell 歷史、日誌或版本控制。`kubectl create token` 會要求伺服器簽發具有有效期限的 token；請勿依賴自動產生的永久 token Secret。參考 [ServiceAccount](https://kubernetes.io/docs/concepts/security/service-accounts/) 與 [RBAC 最佳實務](https://kubernetes.io/docs/concepts/security/rbac-good-practices/)。

工作負載 RBAC 應限制命名空間、資源與動詞；只有確有跨命名空間或叢集範圍需求時才使用 ClusterRole。定期檢查 RoleBinding、ClusterRoleBinding 與 ServiceAccount 的實際權限。

## 授權檢查

確認 `kubectl` 指向預期叢集後，可使用 `kubectl auth can-i` 檢查目前身分的權限；命令會查詢 API Server：

```bash
kubectl auth can-i get pods --namespace app
kubectl auth can-i create deployments --namespace app
```

舊版 CSR 與 ServiceAccount 操作範例保留於[歷史封存](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/zh-TW/practice/user-management.md)，僅供遷移參考，並非 v1.37 部署步驟。
