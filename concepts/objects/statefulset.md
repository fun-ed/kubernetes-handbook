# StatefulSet

StatefulSet 用於管理需要穩定識別資訊或持久儲存的 Pod。它支援下列行為：

* Pod 重新建立後保留序號與穩定網路識別；需搭配 Headless Service。
* `volumeClaimTemplates` 為每個 Pod 建立 PVC，實際持久性取決於 StorageClass、PV 和儲存系統。
* 預設以序號順序建立及縮減 Pod，預設更新策略依序替換 Pod。這些順序由 StatefulSet controller 管理，不是由 init container 實作。`podManagementPolicy: Parallel` 可變更建立及刪除的管理方式。

从上面的应用场景可以发现，StatefulSet 由以下几个部分组成：

* 用于定义网络标志（DNS domain）的 Headless Service
* 用于创建 PersistentVolumes 的 volumeClaimTemplates
* 定义具体应用的 StatefulSet

StatefulSet 中每个 Pod 的 DNS 格式为 `statefulSetName-{0..N-1}.serviceName.namespace.svc.cluster.local`，其中

* `serviceName` 为 Headless Service 的名字
* `0..N-1` 为 Pod 所在的序号，从 0 开始到 N-1
* `statefulSetName` 为 StatefulSet 的名字
* `namespace` 为服务所在的 namespace，Headless Service 和 StatefulSet 必须在相同的 namespace
* `.cluster.local` 为 Cluster Domain

## API 版本

| API version | 状态 |
| :--- | :--- |
| `apps/v1` | 当前版本 |
| `extensions/v1beta1`、`apps/v1beta1`、`apps/v1beta2` | 历史 API，已从当前 Kubernetes 版本移除 |

## 简单示例

示例中的 PVC 依赖集群配置的默认 StorageClass；若没有默认类，请在模板中指定可用的 `storageClassName`，或预先提供匹配的 PV。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  ports:
  - port: 80
    name: web
  clusterIP: None
  selector:
    app: nginx
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: "nginx"
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.30.5
        ports:
        - containerPort: 80
          name: web
        volumeMounts:
        - name: www
          mountPath: /usr/share/nginx/html
  volumeClaimTemplates:
  - metadata:
      name: www
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
```

```bash
kubectl apply -f web.yaml
kubectl get service nginx
kubectl get statefulset web
kubectl get pvc
kubectl get pods -l app=nginx
```

用一次性 BusyBox Pod 查询 StatefulSet Pod 的 DNS 名称：

```bash
kubectl run dns-test --image=busybox:1.37.0 --restart=Never --rm -it -- \
  nslookup web-0.nginx
```

```bash
# 扩容
kubectl scale statefulset web --replicas=5

# 缩容
kubectl scale statefulset web --replicas=3

# 更新镜像
kubectl set image statefulset/web nginx=nginx:1.30.5

# 删除 StatefulSet 和 Headless Service
kubectl delete statefulset web
kubectl delete service nginx

# StatefulSet 删除后 PVC 默认保留；仅在确认数据不再需要时删除
kubectl delete pvc www-web-0 www-web-1
```

## 更新 StatefulSet

StatefulSet 支援 `RollingUpdate` 與 `OnDelete` 更新策略。`RollingUpdate` 會依序更新 Pod；預設按序號由大到小執行，並等待 Pod Ready 後才繼續。`OnDelete` 只更新 StatefulSet 範本，不會自動刪除現有 Pod，必須由操作者逐個刪除以觸發替換。

更新容器映像檔或其他 Pod 範本欄位時，請修改 `web.yaml` 中的 `.spec.template`，再套用及監看：

```bash
kubectl apply -f web.yaml
kubectl rollout status statefulset/web
kubectl get pods -l app=nginx --watch
```

`RollingUpdate` 支援 partition。設為 `2` 時，只有序號大於或等於 2 的 Pod 會更新；較低序號的 Pod 保留舊範本。請在分批發布前確認儲存資料與應用程式版本相容：

```bash
kubectl patch statefulset web --type=merge \
  -p '{"spec":{"updateStrategy":{"type":"RollingUpdate","rollingUpdate":{"partition":2}}}}'
kubectl rollout status statefulset/web
```

解除分批更新前，應確認較高序號的 Pod 已達到所需狀態，再將 partition 設為 0 或移除該欄位。

## Pod 管理策略

v1.7 + 可以通过 `.spec.podManagementPolicy` 设置 Pod 管理策略，支持两种方式

* OrderedReady：默认的策略，按照 Pod 的次序依次创建每个 Pod 并等待 Ready 之后才创建后面的 Pod
* Parallel：并行创建或删除 Pod（不等待前面的 Pod Ready 就开始创建所有的 Pod）

### Parallel 示例

```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  ports:
  - port: 80
    name: web
  clusterIP: None
  selector:
    app: nginx
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: nginx
  podManagementPolicy: Parallel
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.30.5
        ports:
        - containerPort: 80
          name: web
```

可以看到，所有 Pod 是并行创建的

```bash
$ kubectl create -f webp.yaml
service "nginx" created
statefulset "web" created

$ kubectl get po -lapp=nginx -w
NAME      READY     STATUS              RESTARTS  AGE
web-0     0/1       Pending             0         0s
web-0     0/1       Pending             0         0s
web-1     0/1       Pending             0         0s
web-1     0/1       Pending             0         0s
web-0     0/1       ContainerCreating   0         0s
web-1     0/1       ContainerCreating   0         0s
web-0     1/1       Running             0         10s
web-1     1/1       Running             0         10s
```

## ZooKeeper 示例

本页旧版 ZooKeeper 清单使用已移除的 StatefulSet、PodDisruptionBudget API 和 alpha 注解，并依赖年代久远的示例镜像，因此不应在当前集群中应用。请使用维护中的 ZooKeeper 镜像或 Operator，并参阅 Kubernetes [Stateful application 示例](https://kubernetes.io/docs/tutorials/stateful-application/zookeeper/)及所选发行版文档。

## StatefulSet 注意事项

1. 若需在 Pod 重建後保留資料，請使用 `volumeClaimTemplates` 或明確設定的 PersistentVolumeClaim；StatefulSet 不會替所有容器自動提供持久儲存。
2. 預設的 OrderedReady 管理策略會依序建立及刪除 Pod；`Parallel` 策略則不保證此順序。請依工作負載特性選擇策略。
3. 刪除 StatefulSet 不會自動刪除其 PVC。PV 是否保留資料，還取決於儲存後端及 PV reclaim policy；刪除前應確認保留與備份方式。
4. StatefulSet 的 `serviceName` 指定管理 Pod 網路身分的 Service，通常會使用 headless Service。若需要穩定的 Pod DNS，請建立對應 Service 並確認叢集 DNS 設定。

