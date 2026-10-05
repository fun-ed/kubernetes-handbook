# Secret

Secret 解决了密码、token、密钥等敏感数据的配置问题，而不需要把这些敏感数据暴露到镜像或者 Pod Spec 中。Secret 可以以 Volume 或者环境变量的方式使用。

## Secret 类型

Secret 有三种类型：

* Opaque：base64 编码格式的 Secret，用来存储密码、密钥等；但数据也通过 base64 --decode 解码得到原始数据，所有加密性很弱。
* `kubernetes.io/dockerconfigjson`：用来存储私有 docker registry 的认证信息。
* `kubernetes.io/service-account-token`： 用于被 serviceaccount 引用。serviceaccout 创建时 Kubernetes 会默认创建对应的 secret。Pod 如果使用了 serviceaccount，对应的 secret 会自动挂载到 Pod 的 `/run/secrets/kubernetes.io/serviceaccount` 目录中。

备注：serviceaccount 用来使得 Pod 能够访问 Kubernetes API

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

```bash
# kubectl get secret
NAME                  TYPE                                  DATA      AGE
default-token-cty7p   kubernetes.io/service-account-token   3         45d
mysecret              Opaque                                2         7s
```

注意：其中 default-token-cty7p 为创建集群时默认创建的 secret，被 serviceacount/default 引用。

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

### 将 Secret 挂载到 Volume 中

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
  containers:
  - image: gcr.io/my_project_id/pg:v1
    name: db
    volumeMounts:
    - name: secrets
      mountPath: "/etc/secrets"
      readOnly: true
    ports:
    - name: cp
      containerPort: 5432
      hostPort: 5432
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
        image: wordpress:6
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

 **注意** ：

1、`kubernetes.io/dockerconfigjson` 和 `kubernetes.io/service-account-token` 类型的 secret 也同样可以被挂载成文件 \(目录\)。 如果使用 `kubernetes.io/dockerconfigjson` 类型的 secret 会在目录下创建一个. dockercfg 文件

```bash
root@db:/etc/secrets# ls -al
total 4
drwxrwxrwt  3 root root  100 Aug  5 16:06 .
drwxr-xr-x 42 root root 4096 Aug  5 16:06 ..
drwxr-xr-x  2 root root   60 Aug  5 16:06 ..8988_06_08_00_06_52.433429084
lrwxrwxrwx  1 root root   31 Aug  5 16:06 ..data -> ..8988_06_08_00_06_52.433429084
lrwxrwxrwx  1 root root   17 Aug  5 16:06 .dockercfg -> ..data/.dockercfg
```

如果使用 `kubernetes.io/service-account-token` 类型的 secret 则会创建 ca.crt，namespace，token 三个文件

```bash
root@db:/etc/secrets# ls
ca.crt    namespace  token
```

2、secrets 使用时被挂载到一个临时目录，Pod 被删除后 secrets 挂载时生成的文件也会被删除。

```bash
root@db:/etc/secrets# df
Filesystem     1K-blocks    Used Available Use% Mounted on
none           123723748 4983104 112432804   5% /
tmpfs            1957660       0   1957660   0% /dev
tmpfs            1957660       0   1957660   0% /sys/fs/cgroup
/dev/vda1       51474044 2444568  46408092   6% /etc/hosts
tmpfs            1957660      12   1957648   1% /etc/secrets
/dev/vdb       123723748 4983104 112432804   5% /etc/hostname
shm                65536       0     65536   0% /dev/shm
```

但如果在 Pod 运行的时候，在 Pod 部署的节点上还是可以看到：

```bash
# 查看 Pod 中容器 Secret 的相关信息，其中 4392b02d-79f9-11e7-a70a-525400bc11f0 为 Pod 的 UUID
"Mounts": [
  {
    "Source": "/var/lib/kubelet/pods/4392b02d-79f9-11e7-a70a-525400bc11f0/volumes/kubernetes.io~secret/secrets",
    "Destination": "/etc/secrets",
    "Mode": "ro",
    "RW": false,
    "Propagation": "rprivate"
  }
]
#在 Pod 部署的节点查看
root@VM-0-178-ubuntu:/var/lib/kubelet/pods/4392b02d-79f9-11e7-a70a-525400bc11f0/volumes/kubernetes.io~secret/secrets# ls -al
total 4
drwxrwxrwt 3 root root  140 Aug  6 00:15 .
drwxr-xr-x 3 root root 4096 Aug  6 00:15 ..
drwxr-xr-x 2 root root  100 Aug  6 00:15 ..8988_06_08_00_15_14.253276142
lrwxrwxrwx 1 root root   31 Aug  6 00:15 ..data -> ..8988_06_08_00_15_14.253276142
lrwxrwxrwx 1 root root   13 Aug  6 00:15 ca.crt -> ..data/ca.crt
lrwxrwxrwx 1 root root   16 Aug  6 00:15 namespace -> ..data/namespace
lrwxrwxrwx 1 root root   12 Aug  6 00:15 token -> ..data/token
```

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

> **安全更新（Kubernetes v1.33）**
>
> 1. **Service Account Token Integration for Kubelet Credential Providers**（Alpha）：推荐使用 Pod 的服务账户令牌动态获取镜像拉取凭证，避免长期密钥的安全风险。详见[安全章节](../../practice/security.md#镜像拉取认证安全v133-新特性)。
>
> 2. **Ensure Secret Pulled Images**（Alpha）：通过 `KubeletEnsureSecretPulledImages` 特性门控，确保只有具备适当凭证的 Pod 才能访问私有镜像，即使镜像已存在于节点上。详见[安全章节](../../practice/security.md#镜像拉取安全v133-新特性)。

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

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: foo
spec:
  containers:
    - name: foo
      image: janedoe/awesomeapp:v1
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

```yaml
apiVersion: v1
kind: Secret
metadata:
  ...
data:
  ...
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
