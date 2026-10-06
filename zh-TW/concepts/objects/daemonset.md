# DaemonSet

DaemonSet 保證在每個 Node 上都執行一個容器副本，常用來部署一些叢集的日誌、監控或者其他系統管理應用。典型的應用包括：

* 日誌收集，比如 fluentd，logstash 等
* 系統監控，比如 Prometheus Node Exporter，collectd，New Relic agent，Ganglia gmond 等
* 系統程式，比如 kube-proxy、CoreDNS 以及叢集網路或儲存元件

## API 版本

| API version | 狀態 |
| :--- | :--- |
| `apps/v1` | 當前版本 |
| `extensions/v1beta1`、`apps/v1beta1`、`apps/v1beta2` | 歷史 API，已從當前 Kubernetes 版本移除 |

以下清單展示一個最小的 DaemonSet。生產環境的日誌代理通常需要節點級讀取權限和特定日誌路徑，應使用代理維護者針對目標執行時和發行版的安裝說明，不要假設容器日誌位於 Docker 專用目錄：

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

## 滾動更新

v1.6 + 支援 DaemonSet 的滾動更新，可以透過 `.spec.updateStrategy.type` 設定更新策略。目前支援兩種策略

* OnDelete：預設策略，更新模板後，只有手動刪除了舊的 Pod 後才會建立新的 Pod
* RollingUpdate：更新 DaemonSet 模版後，自動刪除舊的 Pod 並建立新的 Pod

在使用 RollingUpdate 策略時，還可以設定

* `.spec.updateStrategy.rollingUpdate.maxUnavailable`, 預設 1
* `spec.minReadySeconds`，預設 0

### 回復

v1.7 + 還支援回復

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

## 指定 Node 節點

DaemonSet 會忽略 Node 的 unschedulable 狀態，有兩種方式來指定 Pod 只執行在指定的 Node 節點上：

* nodeSelector：只排程到匹配指定 label 的 Node 上
* nodeAffinity：功能更豐富的 Node 選擇器，比如支援集合操作
* podAffinity：排程到滿足條件的 Pod 所在的 Node 上

### nodeSelector 範例

首先給 Node 打上標籤

```bash
kubectl label nodes node-01 disktype=ssd
```

然後在 daemonset 中指定 nodeSelector 為 `disktype=ssd`：

```yaml
spec:
  nodeSelector:
    disktype: ssd
```

### nodeAffinity 範例

nodeAffinity 目前支援兩種：requiredDuringSchedulingIgnoredDuringExecution 和 preferredDuringSchedulingIgnoredDuringExecution，分別代表必須滿足條件和優選條件。比如下面的例子代表排程到包含標籤 `kubernetes.io/e2e-az-name` 並且值為 e2e-az1 或 e2e-az2 的 Node 上，並且優選還帶有標籤 `another-node-label-key=another-node-label-value` 的 Node。

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

### podAffinity 範例

podAffinity 基於 Pod 的標籤來選擇 Node，僅排程到滿足條件 Pod 所在的 Node 上，支援 podAffinity 和 podAntiAffinity。這個功能比較繞，以下面的例子為例：

* 如果一個 “Node 所在 Zone 中包含至少一個帶有 `security=S1` 標籤且執行中的 Pod”，那麼可以排程到該 Node
* 不排程到 “包含至少一個帶有 `security=S2` 標籤且執行中 Pod” 的 Node 上

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

## 靜態 Pod

除了 DaemonSet，還可以使用靜態 Pod 來在每臺機器上執行指定的 Pod，這需要 kubelet 在啟動的時候指定 manifest 目錄：

```bash
kubelet --pod-manifest-path=/etc/kubernetes/manifests
```

然後將所需要的 Pod 定義檔案放到指定的 manifest 目錄中。

注意：靜態 Pod 不能透過 API Server 來刪除，但可以透過刪除 manifest 檔案來自動刪除對應的 Pod。
