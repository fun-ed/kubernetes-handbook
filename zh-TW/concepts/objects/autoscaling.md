# Autoscaling

Horizontal Pod Autoscaler（HPA）根據 CPU、記憶體或已註冊的自訂指標調整 Deployment 等可擴縮資源的副本數。

* HPA 控制器定期讀取指標，並按比例計算所需副本數。
* Resource 指標由 Metrics API 提供；Pod、Object 和 External 自訂指標需要相應的指標配接器。
* 使用 HPA 前，需要部署與叢集版本相容的 metrics-server。Kubernetes v1.37 的 `metrics.k8s.io/v1` API 已達穩定版，但 API 後端實際提供的版本取決於所用實作。本書基準 Metrics Server v0.9.0 僅註冊並提供 `metrics.k8s.io/v1beta1`，Kubernetes v1.37.1 的 HPA 資源指標用戶端也使用 v1beta1；`kubectl top` 可先查詢 v1，再回退至 v1beta1。請以叢集 API discovery 為準，不要假設後端提供 v1。[Metrics Server v0.9.0 相容矩陣](https://github.com/kubernetes-sigs/metrics-server/blob/v0.9.0/README.md#compatibility-matrix) · [Kubernetes v1.37.1 HPA client](https://github.com/kubernetes/kubernetes/blob/v1.37.1/pkg/controller/podautoscaler/metrics/client.go)

Node 自動擴充套件請參考 [Cluster Autoscaler](../../setup/addon-list/cluster-autoscaler.md)。

## API 版本

| API version | 狀態 |
| :--- | :--- |
| `autoscaling/v2` | 目前版本，支援 Resource、Pods、Object 和 External metrics |
| `autoscaling/v1` | 仍可用於 CPU 利用率等基本設定，功能有限 |
| `autoscaling/v2beta1`、`autoscaling/v2beta2` | 已移除；分別自 v1.25、v1.26 起不再提供 |
## 範例

```bash
# 建立 Deployment 並設定 CPU request
kubectl create deployment php-apache --image=registry.k8s.io/hpa-example
kubectl set resources deployment/php-apache --requests=cpu=200m
kubectl expose deployment php-apache --port=80

# 建立 HPA
kubectl autoscale deployment php-apache --cpu-percent=50 --min=1 --max=10
kubectl get hpa

# 啟動持續請求負載；觀察 HPA 副本數變化
kubectl run load-generator --image=busybox:1.37.0 --restart=Never -- \
  sh -c 'while true; do wget -q -O- http://php-apache.default.svc.cluster.local >/dev/null; done'
kubectl get hpa --watch

# 停止負載
kubectl delete pod load-generator
```

使用自訂指標時，叢集需要註冊並執行相容的 Custom Metrics 或 External Metrics API adapter。Adapter、指標後端和 HPA 使用的指標名稱與單位必須一致。有關 API 聚合與指標配接器，請參考 Kubernetes [metrics 文件](https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/)及 adapter 專案的版本說明。

以下範例使用 autoscaling/v2，目標 Deployment 需要存在，且各指標 API 必須已由叢集提供：

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: php-apache
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: php-apache
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
  - type: Pods
    pods:
      metric:
        name: packets-per-second
      target:
        type: AverageValue
        averageValue: 1k
  - type: Object
    object:
      describedObject:
        apiVersion: networking.k8s.io/v1
        kind: Ingress
        name: main-route
      metric:
        name: requests-per-second
      target:
        type: Value
        value: 10k
```

## 可設定容忍度（Kubernetes v1.37 GA）

HPA 可在 `autoscaling/v2` 的 `behavior.scaleUp.tolerance` 和 `behavior.scaleDown.tolerance` 分別設定擴容與縮容容忍度。此功能在 Kubernetes v1.37 已達到 GA，不需要啟用 feature gate。

### 功能概述

預設情況下，HPA 使用 10% 的容忍度。明確設定時，值為 0 到 1 之間的小數，例如 0.05 表示 5%：

### 設定範例

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: configurable-tolerance-example
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 2
  maxReplicas: 20
  behavior:
    scaleDown:
      tolerance: 0.05  # 5% 容忍度用於縮容
    scaleUp:
      tolerance: 0     # 0% 容忍度用於擴容（更敏感）
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 容忍度使用場景

1. **高敏感度擴容**：設定較低的擴容容忍度，快速回應負載增加
   ```yaml
   behavior:
     scaleUp:
       tolerance: 0.02  # 2% 容忍度，快速擴容
   ```

2. **保守縮容**：設定較高的縮容容忍度，避免頻繁縮容
   ```yaml
   behavior:
     scaleDown:
       tolerance: 0.15  # 15% 容忍度，穩定縮容
   ```

3. **不同工作負載的自訂策略**：以下是兩種互相獨立的 `spec.behavior` 片段，請依工作負載擇一設定；不要將兩個片段合併為同一個 `behavior` mapping。

   批次工作負載：積極擴容、保守縮容。
   ```yaml
   behavior:
     scaleUp:
       tolerance: 0
     scaleDown:
       tolerance: 0.2
   ```

   Web 服務：平衡策略。
   ```yaml
   behavior:
     scaleUp:
       tolerance: 0.05
     scaleDown:
       tolerance: 0.1
   ```

- 可設定容忍度在 v1.37 為 GA；常見取值需根據工作負載穩定性和回應速度評估。
- 容忍度較低會使 HPA 對指標變化更敏感；透過監控驗證實際擴縮容行為。

## 檢視 HPA 狀態

使用 `kubectl get hpa` 或 `kubectl describe hpa <name>` 檢視目前指標、期望副本數、狀態條件和事件。HPA 的詳細狀態欄位見 [HorizontalPodAutoscaler API](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/horizontal-pod-autoscaler-v2/)。

## Vertical Pod Autoscaler（VPA）

VPA 是獨立於 Kubernetes 核心儲存庫的專案，需要安裝其 CRD 和控制器；API 欄位、更新模式與原地調整的相容性取決於所安裝的 VPA 版本。請以 [VPA 上游文件](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler)和對應版本說明為準，不要直接套用舊版 VPA YAML。

Kubernetes 的原地 Pod 資源調整屬於核心功能，但它本身不會安裝或設定 VPA。HPA 與 VPA 同時控制相同資源時可能互相影響；組合使用前應明確由哪個控制器負責各項資源，並在目標叢集上驗證行為。
## HPA 最佳實踐

* 為容器設定 CPU requests；基於 CPU 利用率的 HPA 需要 requests 才能計算利用率。
* 選擇能代表工作負載的指標，並驗證 metrics API 與後端的可用性。
* 使用 `kubectl top node` 和 `kubectl top pod` 檢查資源指標；這些指令需要正常運作的 metrics-server。
* v1.37 的可設定容忍度已為 GA，可按負載特性設定並監控擴縮容結果。
* 避免讓 HPA 與 VPA 同時調整同一資源，除非已針對使用場景驗證控制策略。

## 參考文件

* [Ensure High Availability and Uptime With Kubernetes Horizontal Pod Autoscaler and Prometheus](https://www.weave.works/blog/kubernetes-horizontal-pod-autoscaler-and-prometheus)
