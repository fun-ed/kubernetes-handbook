# Secret

Secret 解决了密码、token、密钥等敏感数据的配置问题，而不需要把这些敏感数据暴露到镜像或者 Pod Spec 中。Secret 可以以 Volume 或者环境变量的方式使用。

## Secret 类型

Secret 常見型別如下：

* `Opaque`：用來存放一般鍵值資料。Secret 的 `.data` 欄位以 Base64 編碼，Base64 不是加密；需保護資料時，應設定 etcd 靜態加密並限制 RBAC 存取。
* `kubernetes.io/dockerconfigjson`：存放私有映像檔儲存庫的認證設定。
* `kubernetes.io/service-account-token`：保留給需長期相容憑證的情境；不會在現代 Kubernetes 中自動為每個 ServiceAccount 建立。Pod 通常透過 projected volume 取得短期令牌。

ServiceAccount 為 Pod 提供 API 身分，但不會自行授予 RBAC 權限。無需呼叫 API 的工作負載應設定 `automountServiceAccountToken: false`。

## API 版本对照表

| Kubernetes 版本 | Core API 版本 |
| :--- | :--- |
| v1.5+ | core/v1 |

## Opaque Secret

Opaque 类型的数据是一个 map 类型，要求 value 是 base64 编码格式：

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

创建 secret：`kubectl create -f secrets.yml`。

```text
NAME      TYPE     DATA   AGE
mysecret  Opaque   2      <age>
```

Kubernetes v1.24 起不再自動為每個 ServiceAccount 建立長期 token Secret。不要依賴舊版 `default-token-*` 輸出或將該類 token 用於一般工作負載。

如果是从文件创建 secret，则可以用更简单的 kubectl 命令，比如创建 tls 的 secret：

```bash
$ kubectl create secret generic helloworld-tls \
  --from-file=key.pem \
  --from-file=cert.pem
```

## Opaque Secret 的使用

创建好 secret 之后，有两种方式来使用它：

* 以 Volume 方式
* 以环境变量方式

以下範例用 PostgreSQL 展示 Secret Volume。請先依前文建立 `mysecret`；資料只寫入容器的暫存檔案系統，僅適用於教學，正式資料庫應配置持久儲存與備份。
### 将 Secret 挂载到 Volume 中

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

查看 Pod 中对应的信息：

```bash
# ls /etc/secrets
password  username
# cat  /etc/secrets/username
admin
# cat  /etc/secrets/password
1f2d1e2e67df
```

### 将 Secret 导出到环境变量中

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

### 将 Secret 挂载指定的 key

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

创建 Pod 成功后，可以在对应的目录看到：

```bash
# kubectl exec db ls /etc/secrets/tst
psd
usr
```

服務帳戶短期權杖通常由 projected volume 提供，kubelet 會在有效期限內更新令牌。不要自行掛載長期 `kubernetes.io/service-account-token` Secret，也不要到節點檔案系統讀取容器憑證。令牌 Secret 的歷史輸出和舊 kubelet 路徑已移至[歷史歸檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/concepts/serviceaccount-token-legacy.md)。

## kubernetes.io/dockerconfigjson

`kubernetes.io/dockerconfigjson` 类型的 Secret 用 `.dockerconfigjson` 键保存 registry 认证配置。下例中的 `registry.example.invalid` 是保留的无效域名，`demo-user`、`REPLACE_ME` 和 `demo@example.com` 都是虚构值，不能用于真实拉取。不要把真实凭证写入仓库，或放在命令行参数和 shell 历史中；生产凭证应从 Secret Manager 或受控本地配置注入。腾讯云 TCR 的技术主机示例为 `ccr.ccs.tencentyun.com`，实际 endpoint 请使用腾讯云当前文档或控制台给出的值。

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

创建命令会生成 `kubernetes.io/dockerconfigjson` 类型的 Secret，其中 `.dockerconfigjson` 是合法 Docker 配置的 Base64 编码。下面是省略动态 metadata 后的示例；该值解码为 JSON，且只包含上面的虚构占位数据。

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

通过 Base64 解码可以查看 JSON 结构：

```bash
kubectl get secret myregistrykey --namespace=default -o jsonpath='{.data.\.dockerconfigjson}' | base64 --decode
```

```json
{"auths":{"registry.example.invalid":{"username":"demo-user","password":"REPLACE_ME","email":"demo@example.com","auth":"ZGVtby11c2VyOlJFUExBQ0VfTUU="}}}
```

如果已通过受控方式生成 `dockerconfig.json`，也可以直接从文件创建 Secret：

```bash
kubectl create secret generic myregistrykey \
  --namespace=default \
  --type=kubernetes.io/dockerconfigjson \
  --from-file=.dockerconfigjson=./dockerconfig.json
```

在创建 Pod 的时候，通过 `imagePullSecrets` 来引用刚创建的 `myregistrykey`:
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

`kubernetes.io/service-account-token` 是兼容用途的长期 token Secret，不会在现代集群中为每个 ServiceAccount 自动创建。Pod 通常使用自动投射的短期 token；不要手工创建长期 token Secret 来配置工作负载。

```bash
kubectl create deployment nginx --image=nginx:1.30.5
kubectl exec deployment/nginx -- ls /var/run/secrets/kubernetes.io/serviceaccount
```

## 存储加密

Secret 默认以 Base64 编码传输和序列化；Base64 不是加密。若需保护 etcd 中的 Secret，应按当前 [Encryption at Rest 文档](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)配置 API Server 加密提供程序，并安全管理、轮换和备份密钥。

API Server 当前使用 `--encryption-provider-config` 指定加密配置文件。旧版 `EncryptionConfig` YAML、示例密钥和 `kubectl get secrets -o json | kubectl update -f -` 批量改写命令已过时且不安全，本页不提供可直接应用的密钥配置。加密策略变更是数据迁移操作，执行前须遵循目标版本文档并验证备份与恢复流程；不得将密钥写入仓库或日志。
## 不可变 Secret

> 不可变 Secret 在 v1.21.0 进入稳定版本。

对于大量使用 Secret 的 集群而言（如有数万个各不相同的 Secret 给 Pod 挂载），禁止更改 Secret 的数据有很多好处：

* 保护应用，使之免受意外更新所带来的负面影响。
* 通过大幅降低对 kube-apiserver 的压力提升集群性能，这是因为 Kubernetes 会关闭不可变 Secret 的监视操作。

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

## Secret 与 ConfigMap 对比

相同点：

* key/value 的形式
* 属于某个特定的 namespace
* 可以导出到环境变量
* 可以通过目录 / 文件形式挂载 \(支持挂载所有 key 和部分 key\)

不同点：

* Secret 可以被 ServerAccount 关联 \(使用\)
* Secret 可以存储 register 的鉴权信息，用在 ImagePullSecret 参数中，用于拉取私有仓库的镜像
* Secret 的 `data` 字段使用 Base64 编码，不代表加密；是否进行静态加密取决于 API Server 的加密配置。
* Secret volume 由 kubelet 投射到 Pod；避免通过日志、镜像或命令输出暴露内容。

## 参考文档

* [Secret](https://kubernetes.io/docs/concepts/configuration/secret/)
* [Specifying ImagePullSecrets on a Pod](https://kubernetes.io/docs/concepts/configuration/secret/)
