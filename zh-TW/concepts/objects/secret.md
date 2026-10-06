# Secret

Secret 解決了密碼、token、金鑰等敏感資料的設定問題，而不需要把這些敏感資料暴露到映像檔或者 Pod Spec 中。Secret 可以以 Volume 或者環境變數的方式使用。

## Secret 型別

Secret 常見型別如下：

* `Opaque`：用來存放一般鍵值資料。Secret 的 `.data` 欄位以 Base64 編碼，Base64 不是加密；需保護資料時，應設定 etcd 靜態加密並限制 RBAC 存取。
* `kubernetes.io/dockerconfigjson`：存放私有映像檔儲存庫的認證設定。
* `kubernetes.io/service-account-token`：保留給需長期相容憑證的情境；不會在現代 Kubernetes 中自動為每個 ServiceAccount 建立。Pod 通常透過 projected volume 取得短期權杖。

ServiceAccount 為 Pod 提供 API 身分，但不會自行授予 RBAC 權限。無需呼叫 API 的工作負載應設定 `automountServiceAccountToken: false`。

## API 版本對照表

| Kubernetes 版本 | Core API 版本 |
| :--- | :--- |
| v1.5+ | core/v1 |

## Opaque Secret

Opaque 型別的資料是一個 map 型別，要求 value 是 base64 編碼格式：

```bash
$ echo -n "admin" | base64
YWRtaW4=
$ echo -n "1f2d1e2e67df" | base64
MWYyZDFlMmU2N2Rm
```

secrets.yml

```text
apiVersion: v1
kind: Secret
metadata:
  name: mysecret
type: Opaque
data:
  password: MWYyZDFlMmU2N2Rm
  username: YWRtaW4=
```

建立 secret：`kubectl create -f secrets.yml`。

```text
NAME      TYPE     DATA   AGE
mysecret  Opaque   2      <age>
```

Kubernetes v1.24 起不再自動為每個 ServiceAccount 建立長期 token Secret。不要依賴舊版 `default-token-*` 輸出或將該類 token 用於一般工作負載。

如果是從檔案建立 secret，則可以用更簡單的 kubectl 命令，比如建立 tls 的 secret：

```bash
$ kubectl create secret generic helloworld-tls \
  --from-file=key.pem \
  --from-file=cert.pem
```

## Opaque Secret 的使用

建立好 secret 之後，有兩種方式來使用它：

* 以 Volume 方式
* 以環境變數方式

以下範例用 PostgreSQL 展示 Secret Volume。請先依前文建立 `mysecret`；資料只寫入容器的暫存檔案系統，僅適用於教學，正式資料庫應配置持久儲存與備份。
### 將 Secret 掛載到 Volume 中

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: db
  name: db
spec:
  volumes:
  - name: secrets
    secret:
      secretName: mysecret
  containers:
  - image: postgres:18.6-alpine3.24
    name: db
    env:
    - name: POSTGRES_USER
      valueFrom:
        secretKeyRef:
          name: mysecret
          key: username
    - name: POSTGRES_PASSWORD
      valueFrom:
        secretKeyRef:
          name: mysecret
          key: password
    volumeMounts:
    - name: secrets
      mountPath: "/etc/secrets"
      readOnly: true
    ports:
    - name: postgres
      containerPort: 5432
```

檢視 Pod 中對應的資訊：

```bash
# ls /etc/secrets
password  username
# cat  /etc/secrets/username
admin
# cat  /etc/secrets/password
1f2d1e2e67df
```

### 將 Secret 匯出到環境變數中

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wordpress-deployment
spec:
  replicas: 2
  selector:
    matchLabels:
      app: wordpress
  strategy:
    type: RollingUpdate
  template:
    metadata:
      labels:
        app: wordpress
        visualize: "true"
    spec:
      containers:
      - name: wordpress
        image: wordpress:7.1.2
        ports:
        - containerPort: 80
        env:
        - name: WORDPRESS_DB_USER
          valueFrom:
            secretKeyRef:
              name: mysecret
              key: username
        - name: WORDPRESS_DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysecret
              key: password
```

### 將 Secret 掛載指定的 key

```text
apiVersion: v1
kind: Pod
metadata:
  labels:
    name: db
  name: db
spec:
  volumes:
  - name: secrets
    secret:
      secretName: mysecret
      items:
      - key: password
        mode: 511
        path: tst/psd
      - key: username
        mode: 511
        path: tst/usr
  containers:
  - image: nginx:1.30.5
    name: db
    volumeMounts:
    - name: secrets
      mountPath: "/etc/secrets"
      readOnly: true
    ports:
    - name: cp
      containerPort: 80
      hostPort: 5432
```

建立 Pod 成功後，可以在對應的目錄看到：

```bash
# kubectl exec db ls /etc/secrets/tst
psd
usr
```

服務帳戶短期權杖通常由 projected volume 提供，kubelet 會在有效期限內更新權杖。不要自行掛載長期 `kubernetes.io/service-account-token` Secret，也不要到節點檔案系統讀取容器憑證。令牌 Secret 的歷史輸出和舊 kubelet 路徑已移至[歷史歸檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/concepts/serviceaccount-token-legacy.md)。

## kubernetes.io/dockerconfigjson

`kubernetes.io/dockerconfigjson` 型別的 Secret 用 `.dockerconfigjson` 鍵儲存 registry 認證設定。下例中的 `registry.example.invalid` 是保留的無效域名，`demo-user`、`REPLACE_ME` 和 `demo@example.com` 都是虛構值，不能用於真實拉取。不要把真實憑證寫入儲存庫，或放在命令列引數和 shell 歷史中；生產憑證應從 Secret Manager 或受控本地設定注入。騰訊雲 TCR 的技術主機範例為 `ccr.ccs.tencentyun.com`，實際 endpoint 請使用騰訊雲當前文件或控制檯給出的值。

```bash
kubectl create secret docker-registry myregistrykey \
  --namespace=default \
  --docker-server=registry.example.invalid \
  --docker-username=demo-user \
  --docker-password=REPLACE_ME \
  --docker-email=demo@example.com
secret/myregistrykey created
```

> **Kubernetes v1.37**
>
> * `KubeletServiceAccountTokenForCredentialProviders` 自 v1.34 起為預設啟用的 Beta 功能。它允許已設定的 kubelet credential provider 取得 Pod 綁定的 ServiceAccount 權杖；仍需安裝並設定支援此功能的外掛。[官方說明](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-credential-provider/#service-account-token-for-image-pulls)。
> * `KubeletEnsureSecretPulledImages` 自 v1.35 起為預設啟用的 Beta 功能。節點會驗證私有映像檔拉取憑證；實際行為取決於 kubelet 設定及憑證。[映像檔文件](https://kubernetes.io/docs/concepts/containers/images/)。

建立命令會生成 `kubernetes.io/dockerconfigjson` 型別的 Secret，其中 `.dockerconfigjson` 是合法 Docker 設定的 Base64 編碼。下面是省略動態 metadata 後的範例；該值解碼為 JSON，且只包含上面的虛構佔位資料。

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: myregistrykey
  namespace: default
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: eyJhdXRocyI6eyJyZWdpc3RyeS5leGFtcGxlLmludmFsaWQiOnsidXNlcm5hbWUiOiJkZW1vLXVzZXIiLCJwYXNzd29yZCI6IlJFUExBQ0VfTUUiLCJlbWFpbCI6ImRlbW9AZXhhbXBsZS5jb20iLCJhdXRoIjoiWkdWdGJ5MTFjMlZ5T2xKRlVFeEJRMFZmVFVVPSJ9fX0=
```

透過 Base64 解碼可以檢視 JSON 結構：

```bash
kubectl get secret myregistrykey --namespace=default -o jsonpath='{.data.\.dockerconfigjson}' | base64 --decode
```

```json
{"auths":{"registry.example.invalid":{"username":"demo-user","password":"REPLACE_ME","email":"demo@example.com","auth":"ZGVtby11c2VyOlJFUExBQ0VfTUU="}}}
```

如果已透過受控方式生成 `dockerconfig.json`，也可以直接從檔案建立 Secret：

```bash
kubectl create secret generic myregistrykey \
  --namespace=default \
  --type=kubernetes.io/dockerconfigjson \
  --from-file=.dockerconfigjson=./dockerconfig.json
```

在建立 Pod 的時候，透過 `imagePullSecrets` 來引用剛建立的 `myregistrykey`:
`registry.example.invalid/project/awesomeapp:replace-me` 是無法拉取的佔位映像檔；請換成已推送至前述私有儲存庫的實際映像檔標籤。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: foo
spec:
  containers:
    - name: foo
      image: registry.example.invalid/project/awesomeapp:replace-me
  imagePullSecrets:
    - name: myregistrykey
```

### kubernetes.io/service-account-token

`kubernetes.io/service-account-token` 是相容用途的長期 token Secret，不會在現代叢集中為每個 ServiceAccount 自動建立。Pod 通常使用自動投射的短期 token；不要手工建立長期 token Secret 來設定工作負載。

```bash
kubectl create deployment nginx --image=nginx:1.30.5
kubectl exec deployment/nginx -- ls /var/run/secrets/kubernetes.io/serviceaccount
```

## 儲存加密

Secret 預設以 Base64 編碼傳輸和序列化；Base64 不是加密。若需保護 etcd 中的 Secret，應按當前 [Encryption at Rest 文件](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)設定 API Server 加密提供程式，並安全管理、輪換和備份金鑰。

API Server 當前使用 `--encryption-provider-config` 指定加密設定檔案。舊版 `EncryptionConfig` YAML、範例金鑰和 `kubectl get secrets -o json | kubectl update -f -` 批次改寫命令已過時且不安全，本頁不提供可直接應用的金鑰設定。加密策略變更是資料遷移操作，執行前須遵循目標版本文件並驗證備份與恢復流程；不得將金鑰寫入儲存庫或日誌。
## 不可變 Secret

> 不可變 Secret 在 v1.21.0 進入穩定版本。

對於大量使用 Secret 的叢集而言（例如有數萬個不同的 Secret 掛載到 Pod），禁止變更 Secret 資料有不少好處：

* 保護應用，使之免受意外更新所帶來的負面影響。
* 透過大幅降低對 kube-apiserver 的壓力提升叢集效能，這是因為 Kubernetes 會關閉不可變 Secret 的監視操作。

此範例的 `data` 值只是字串 `example` 的 Base64 編碼，不是密碼或加密。請勿將真實憑證寫入文件或版控儲存庫。

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret-v1
type: Opaque
data:
  username: ZXhhbXBsZQ==
immutable: true
```

## Secret 與 ConfigMap 對比

相同點：

* key/value 的形式
* 屬於某個特定的 namespace
* 可以匯出到環境變數
* 可以透過目錄 / 檔案形式掛載 \(支援掛載所有 key 和部分 key\)

不同點：

* Secret 可以被 ServerAccount 關聯 \(使用\)
* Secret 可以儲存 register 的鑑權資訊，用在 ImagePullSecret 引數中，用於拉取私有儲存庫的映像檔
* Secret 的 `data` 欄位使用 Base64 編碼，不代表加密；是否進行靜態加密取決於 API Server 的加密設定。
* Secret volume 由 kubelet 投射到 Pod；避免透過日誌、映像檔或命令輸出暴露內容。

## 參考文件

* [Secret](https://kubernetes.io/docs/concepts/configuration/secret/)
* [Specifying ImagePullSecrets on a Pod](https://kubernetes.io/docs/concepts/configuration/secret/)
