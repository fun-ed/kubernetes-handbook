> HISTORICAL: This chapter includes removed kube-controller-manager flags, an obsolete unauthenticated metrics endpoint, and version-specific controller and eviction details. Do not use its command as a current v1.37 configuration. Preserved from `concepts/components/controller-manager.md`.

# kube-controller-manager

Controller Manager 由 kube-controller-manager 和 cloud-controller-manager 組成，是 Kubernetes 的大腦，它透過 apiserver 監控整個叢集的狀態，並確保叢集處於預期的工作狀態。

![](https://github.com/fun-ed/kubernetes-handbook/blob/main/.gitbook/assets/post-ccm-arch%20%284%29.png)

kube-controller-manager 由一系列的控制器組成

* Replication Controller
* Node Controller
* CronJob Controller
* Daemon Controller
* Deployment Controller
* Endpoint Controller
* Garbage Collector
* Namespace Controller
* Job Controller
* Pod AutoScaler
* RelicaSet
* Service Controller
* ServiceAccount Controller
* StatefulSet Controller
* Volume Controller
* Resource quota Controller

cloud-controller-manager 在 Kubernetes 啟用 Cloud Provider 的時候才需要，用來配合雲服務提供商的控制，也包括一系列的控制器，如

* Node Controller
* Route Controller
* Service Controller

從 v1.6 開始，cloud provider 已經歷多次重大重構，以便在不修改 Kubernetes 核心程式碼的同時建置自訂雲端服務供應商支援。請參閱[這裡](https://github.com/fun-ed/kubernetes-handbook/blob/main/extension/cloud-provider.md)查看如何為雲端服務供應商建置新的 Cloud Provider。

## Metrics

Controller manager metrics 提供了控制器內部邏輯的效能度量，如 Go 語言執行時度量、etcd 請求延時、雲服務商 API 請求延時、雲端儲存請求延時等。Controller manager metrics 預設監聽在 `kube-controller-manager` 的 10252 連接埠，提供 Prometheus 格式的效能度量資料，可以透過 `http://localhost:10252/metrics` 來存取。

```text
$ curl http://localhost:10252/metrics
...
# HELP etcd_request_cache_add_latencies_summary Latency in microseconds of adding an object to etcd cache
# TYPE etcd_request_cache_add_latencies_summary summary
etcd_request_cache_add_latencies_summary{quantile="0.5"} NaN
etcd_request_cache_add_latencies_summary{quantile="0.9"} NaN
etcd_request_cache_add_latencies_summary{quantile="0.99"} NaN
etcd_request_cache_add_latencies_summary_sum 0
etcd_request_cache_add_latencies_summary_count 0
# HELP etcd_request_cache_get_latencies_summary Latency in microseconds of getting an object from etcd cache
# TYPE etcd_request_cache_get_latencies_summary summary
etcd_request_cache_get_latencies_summary{quantile="0.5"} NaN
etcd_request_cache_get_latencies_summary{quantile="0.9"} NaN
etcd_request_cache_get_latencies_summary{quantile="0.99"} NaN
etcd_request_cache_get_latencies_summary_sum 0
etcd_request_cache_get_latencies_summary_count 0
...
```

## kube-controller-manager 啟動範例

```bash
kube-controller-manager \
  --enable-dynamic-provisioning=true \
  --feature-gates=AllAlpha=true \
  --horizontal-pod-autoscaler-sync-period=10s \
  --horizontal-pod-autoscaler-use-rest-clients=true \
  --node-monitor-grace-period=10s \
  --address=127.0.0.1 \
  --leader-elect=true \
  --kubeconfig=/etc/kubernetes/controller-manager.conf \
  --cluster-signing-key-file=/etc/kubernetes/pki/ca.key \
  --use-service-account-credentials=true \
  --controllers=*,bootstrapsigner,tokencleaner \
  --root-ca-file=/etc/kubernetes/pki/ca.crt \
  --service-account-private-key-file=/etc/kubernetes/pki/sa.key \
  --cluster-signing-cert-file=/etc/kubernetes/pki/ca.crt \
  --allocate-node-cidrs=true \
  --cluster-cidr=10.244.0.0/16 \
  --node-cidr-mask-size=24
```

## 控制器

### kube-controller-manager

kube-controller-manager 由一系列的控制器組成，這些控制器可以劃分為三組

1. 必須啟動的控制器
   * EndpointController（已棄用，Kubernetes 1.33+，但仍需要維持相容性）
   * ReplicationController
   * PodGCController
   * ResourceQuotaController
   * NamespaceController
   * ServiceAccountController
   * GarbageCollectorController
   * DaemonSetController
   * JobController
   * DeploymentController
   * ReplicaSetController
   * HPAController
   * DisruptionController
   * StatefulSetController
   * CronJobController
   * CSRSigningController
   * CSRApprovingController
   * TTLController
2. 預設啟動的可選控制器，可透過選項設定是否開啟
   * TokenController
   * NodeController
   * ServiceController
   * RouteController
   * PVBinderController
   * AttachDetachController
3. 預設禁止的可選控制器，可透過選項設定是否開啟
   * BootstrapSignerController
   * TokenCleanerController

### cloud-controller-manager

cloud-controller-manager 在 Kubernetes 啟用 Cloud Provider 的時候才需要，用來配合雲服務提供商的控制，也包括一系列的控制器

* CloudNodeController
* RouteController
* ServiceController

### cloud-controller-manager 啟動時序協調

cloud-controller-manager 在叢集啟動過程中需要特別注意啟動時序問題。由於 kubelet 啟動時會給 Node 新增 `node.cloudprovider.kubernetes.io/uninitialized=NoSchedule` taint，而 cloud-controller-manager 負責移除該 taint，這可能導致啟動時序衝突。

#### 關鍵啟動引數設定

* `--leader-elect=true`: 啟用多例項選主，確保高可用
* `--node-status-update-frequency`: 與 kubelet 協調節點狀態更新頻率
* `--node-monitor-period`: 監控節點狀態的檢查週期
* `--use-service-account-credentials=true`: 使用單獨的服務賬號憑證

#### 部署最佳實踐

1. **排程策略**: 使用 nodeSelector 將 cloud-controller-manager 排程到控制平面節點
2. **容忍度設定**: 設定適當的 tolerations 以處理節點 taint
3. **高可用性**: 使用 Deployment 或 DaemonSet 而非靜態 Pod
4. **網路模式**: 在某些環境下使用 `hostNetwork: true` 避免網路依賴

## 高可用

在啟動時設定 `--leader-elect=true` 後，controller manager 會使用多節點選主的方式選擇主節點。只有主節點才會呼叫 `StartControllers()` 啟動所有控制器，而其他從節點則僅執行選主演算法。

多節點選主的實現方法見 [leaderelection.go](https://github.com/kubernetes/client-go/blob/master/tools/leaderelection/leaderelection.go)。它實現了多種資源鎖（Endpoint、ConfigMap 或 Lease，kube-controller-manager 和 cloud-controller-manager 傳統上使用 Endpoint 鎖，但 Endpoint API 已棄用，新版本推薦使用 Lease 鎖），透過更新資源的 Annotation（`control-plane.alpha.kubernetes.io/leader`），來確定主從關係。

## 高效能

從 Kubernetes 1.7 開始，所有需要監控資源變化情況的呼叫均推薦使用 [Informer](https://github.com/kubernetes/client-go/blob/master/tools/cache/shared_informer.go)。Informer 提供了基於事件通知的只讀快取機制，可以註冊資源變化的回撥函式，並可以極大減少 API 的呼叫。

Informer 的使用方法可以參考 [這裡](https://github.com/fun-ed/kubernetes-handbook/tree/main/examples/client/informer)。

## Node 驅逐

預設情況下，Kubelet 每隔 10s (--node-status-update-frequency=10s) 更新 Node 的狀態，而 kube-controller-manager 每隔 5s 檢查一次 Node 的狀態 (--node-monitor-period=5s)。kube-controller-manager 會在 Node 未更新狀態超過 40s 時 (--node-monitor-grace-period=40s)，將其標記為 NotReady (Node `Ready` Condition: `True` on healthy, `False` on unhealthy and not accepting pods, `Unknown` on no heartbeat)。當 Node 超過 5m 未更新狀態，則 kube-controller-manager 會驅逐該 Node 上的所有 Pod。

Kubernetes 會自動給 Pod 新增針對 `node.kubernetes.io/not-ready` 和 `node.kubernetes.io/unreachable` 的容忍度，且設定 `tolerationSeconds=300`。你可以透過 tolerations 設定 Pod 的容忍度，來覆蓋預設的設定：

```yaml
tolerations:
- key: "node.kubernetes.io/unreachable"
  operator: "Exists"
  effect: "NoExecute"
  tolerationSeconds: 10
- key: "node.kubernetes.io/not-ready"
  operator: "Exists"
  effect: "NoExecute"
  tolerationSeconds: 10
```

Node 控制器在節點異常後，會按照預設的速率（`--node-eviction-rate=0.1`，即每10秒一個節點的速率）進行 Node 的驅逐。Node 控制器按照 Zone 將節點劃分為不同的組，再跟進 Zone 的狀態進行速率調整：

* Normal：所有節點都 Ready，預設速率驅逐。
* PartialDisruption：即超過33% 的節點 NotReady 的狀態。當異常節點比例大於 `--unhealthy-zone-threshold=0.55` 時開始減慢速率：
  * 小叢集（即節點數量小於 `--large-cluster-size-threshold=50`）：停止驅逐
  * 大叢集，減慢速率為 `--secondary-node-eviction-rate=0.01`
* FullDisruption：所有節點都 NotReady，返回使用預設速率驅逐。但當所有 Zone 都處在 FullDisruption 時，停止驅逐。
