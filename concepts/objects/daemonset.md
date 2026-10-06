# DaemonSet

DaemonSet 保证在每个 Node 上都运行一个容器副本，常用来部署一些集群的日志、监控或者其他系统管理应用。典型的应用包括：

* 日志收集，比如 fluentd，logstash 等
* 系统监控，比如 Prometheus Node Exporter，collectd，New Relic agent，Ganglia gmond 等
* 系统程序，比如 kube-proxy、CoreDNS 以及集群网络或存储组件

## API 版本

| API version | 状态 |
| :--- | :--- |
| `apps/v1` | 当前版本 |
| `extensions/v1beta1`、`apps/v1beta1`、`apps/v1beta2` | 历史 API，已从当前 Kubernetes 版本移除 |

以下清单展示一个最小的 DaemonSet。生产环境的日志代理通常需要节点级读取权限和特定日志路径，应使用代理维护者针对目标运行时和发行版的安装说明，不要假设容器日志位于 Docker 专用目录：

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-agent-example
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: node-agent-example
  template:
    metadata:
      labels:
        app: node-agent-example
    spec:
      containers:
      - name: pause
        image: registry.k8s.io/pause:3.10.2
```

## 滚动更新

v1.6 + 支持 DaemonSet 的滚动更新，可以通过 `.spec.updateStrategy.type` 设置更新策略。目前支持两种策略

* OnDelete：默认策略，更新模板后，只有手动删除了旧的 Pod 后才会创建新的 Pod
* RollingUpdate：更新 DaemonSet 模版后，自动删除旧的 Pod 并创建新的 Pod

在使用 RollingUpdate 策略时，还可以设置

* `.spec.updateStrategy.rollingUpdate.maxUnavailable`, 默认 1
* `spec.minReadySeconds`，默认 0

### 回滚

v1.7 + 还支持回滚

```bash
# 查询历史版本
$ kubectl rollout history daemonset <daemonset-name>

# 查询某个历史版本的详细信息
$ kubectl rollout history daemonset <daemonset-name> --revision=1

# 回滚
$ kubectl rollout undo daemonset <daemonset-name> --to-revision=<revision>
# 查询回滚状态
$ kubectl rollout status ds/<daemonset-name>
```

## 指定 Node 节点

DaemonSet 会忽略 Node 的 unschedulable 状态，有两种方式来指定 Pod 只运行在指定的 Node 节点上：

* nodeSelector：只调度到匹配指定 label 的 Node 上
* nodeAffinity：功能更丰富的 Node 选择器，比如支持集合操作
* podAffinity：调度到满足条件的 Pod 所在的 Node 上

### nodeSelector 示例

首先给 Node 打上标签

```bash
kubectl label nodes node-01 disktype=ssd
```

然后在 daemonset 中指定 nodeSelector 为 `disktype=ssd`：

```yaml
spec:
  nodeSelector:
    disktype: ssd
```

### nodeAffinity 示例

nodeAffinity 目前支持两种：requiredDuringSchedulingIgnoredDuringExecution 和 preferredDuringSchedulingIgnoredDuringExecution，分别代表必须满足条件和优选条件。比如下面的例子代表调度到包含标签 `kubernetes.io/e2e-az-name` 并且值为 e2e-az1 或 e2e-az2 的 Node 上，并且优选还带有标签 `another-node-label-key=another-node-label-value` 的 Node。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: with-node-affinity
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: kubernetes.io/e2e-az-name
            operator: In
            values:
            - e2e-az1
            - e2e-az2
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 1
        preference:
          matchExpressions:
          - key: another-node-label-key
            operator: In
            values:
            - another-node-label-value
  containers:
  - name: with-node-affinity
    image: registry.k8s.io/pause:3.10.2
```

### podAffinity 示例

podAffinity 基于 Pod 的标签来选择 Node，仅调度到满足条件 Pod 所在的 Node 上，支持 podAffinity 和 podAntiAffinity。这个功能比较绕，以下面的例子为例：

* 如果一个 “Node 所在 Zone 中包含至少一个带有 `security=S1` 标签且运行中的 Pod”，那么可以调度到该 Node
* 不调度到 “包含至少一个带有 `security=S2` 标签且运行中 Pod” 的 Node 上

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: with-pod-affinity
spec:
  affinity:
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: security
            operator: In
            values:
            - S1
        topologyKey: topology.kubernetes.io/zone
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: security
              operator: In
              values:
              - S2
          topologyKey: kubernetes.io/hostname
  containers:
  - name: with-pod-affinity
    image: registry.k8s.io/pause:3.10.2
```

## 静态 Pod

除了 DaemonSet，还可以使用静态 Pod 来在每台机器上运行指定的 Pod，这需要 kubelet 在启动的时候指定 manifest 目录：

```bash
kubelet --pod-manifest-path=/etc/kubernetes/manifests
```

然后将所需要的 Pod 定义文件放到指定的 manifest 目录中。

注意：静态 Pod 不能通过 API Server 来删除，但可以通过删除 manifest 文件来自动删除对应的 Pod。

