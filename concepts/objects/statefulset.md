# StatefulSet

StatefulSet 是为了解决有状态服务的问题（对应 Deployments 和 ReplicaSets 是为无状态服务而设计），其应用场景包括

* 稳定的持久化存储，即 Pod 重新调度后还是能访问到相同的持久化数据，基于 PVC 来实现
* 稳定的网络标志，即 Pod 重新调度后其 PodName 和 HostName 不变，基于 Headless Service（即没有 Cluster IP 的 Service）来实现
* 有序部署，有序扩展，即 Pod 是有顺序的，在部署或者扩展的时候要依据定义的顺序依次依序进行（即从 0 到 N-1，在下一个 Pod 运行之前所有之前的 Pod 必须都是 Running 和 Ready 状态），基于 init containers 来实现
* 有序收缩，有序删除（即从 N-1 到 0）

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
kubectl run dns-test --image=busybox:1.36 --restart=Never --rm -it -- \
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

v1.7 + 支持 StatefulSet 的自动更新，通过 `spec.updateStrategy` 设置更新策略。目前支持两种策略

* OnDelete：当 `.spec.template` 更新时，并不立即删除旧的 Pod，而是等待用户手动删除这些旧 Pod 后自动创建新 Pod。这是默认的更新策略，兼容 v1.6 版本的行为
* RollingUpdate：当 `.spec.template` 更新时，自动删除旧的 Pod 并创建新 Pod 替换。在更新时，这些 Pod 是按逆序的方式进行，依次删除、创建并等待 Pod 变成 Ready 状态才进行下一个 Pod 的更新。

### Partitions

RollingUpdate 还支持 Partitions，通过 `.spec.updateStrategy.rollingUpdate.partition` 来设置。当 partition 设置后，只有序号大于或等于 partition 的 Pod 会在 `.spec.template` 更新的时候滚动更新，而其余的 Pod 则保持不变（即便是删除后也是用以前的版本重新创建）。

```bash
# 设置 partition 为 3
$ kubectl patch statefulset web -p '{"spec":{"updateStrategy":{"type":"RollingUpdate","rollingUpdate":{"partition":3}}}}'
statefulset "web" patched

# 更新 StatefulSet
$ kubectl patch statefulset web --type='json' -p='[{"op":"replace","path":"/spec/template/spec/containers/0/image","value":"gcr.io/google_containers/nginx-slim:0.7"}]'
statefulset "web" patched

# 验证更新
$ kubectl delete po web-2
pod "web-2" deleted
$ kubectl get po -lapp=nginx -w
NAME      READY     STATUS              RESTARTS   AGE
web-0     1/1       Running             0          4m
web-1     1/1       Running             0          4m
web-2     0/1       ContainerCreating   0          11s
web-2     1/1       Running             0          18s
```

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

1. 推荐在 Kubernetes v1.9 或以后的版本中使用
2. 所有 Pod 的 Volume 必须使用 PersistentVolume 或者是管理员事先创建好
3. 为了保证数据安全，删除 StatefulSet 时不会删除 Volume
4. StatefulSet 需要一个 Headless Service 来定义 DNS domain，需要在 StatefulSet 之前创建好

