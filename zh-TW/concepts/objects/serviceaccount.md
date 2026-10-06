# ServiceAccount

ServiceAccount 為 Pod 中的程序提供 Kubernetes API 身分；它不授予權限，授權由 RBAC 等授權機制決定。ServiceAccount 是 namespace-scoped 資源，每個 Namespace 通常都會有一個 `default` ServiceAccount。

Pod 未指定 `serviceAccountName` 時，ServiceAccount admission 會將其設為該 Namespace 的 `default` ServiceAccount。除非 Pod 或 ServiceAccount 禁用了自動掛載，Pod 通常會透過 projected volume 獲得短期 API 憑證。不要依賴建立 ServiceAccount 時自動生成長期 `kubernetes.io/service-account-token` Secret 的舊行為；Kubernetes v1.24 起預設不再自動生成此類 Secret。

若工作負載不需要存取 Kubernetes API，可透過 `automountServiceAccountToken: false` 禁用權杖自動掛載。不要將權杖寫入清單、日誌或原始碼；需要外部客戶端憑證時，優先使用短期 TokenRequest 工作流，並妥善保護憑證。

## ServiceAccount 與 RBAC

下面的範例建立一個只能在 `default` Namespace 中讀取 Pod 的 ServiceAccount。實際應用應僅授予工作負載必需的權限：

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

在 Pod 模板中透過 `spec.serviceAccountName` 指定身分；驗證授權時使用 `kubectl auth can-i`，不要透過解碼或列印 Bearer Token 來排錯。

```yaml
spec:
  serviceAccountName: pod-reader
```

## 映像檔拉取憑證

私有映像檔登錄站憑證透過 Kubernetes Secret 的 `imagePullSecrets` 設定。ServiceAccount 可以附加 `imagePullSecrets`，由使用該 ServiceAccount 的 Pod 繼承；不要把映像檔憑證設定成 API 存取權杖。

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: image-puller
  namespace: default
imagePullSecrets:
- name: registry-credentials
```

詳情請參閱 [ServiceAccount 文件](https://kubernetes.io/docs/concepts/security/service-accounts/)和 [RBAC 文件](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)。
