# Resource Quota

資源配額（Resource Quotas）是用來限制使用者資源用量的一種機制。

它的工作原理為

* ResourceQuota 作用於 Namespace；同一 Namespace 可以有多個配額物件，所有適用配額都會共同限制資源使用
* 當配額限制 `requests.*` 或 `limits.*` 時，Pod 必須提供相應資源值；可使用 [LimitRange](https://kubernetes.io/docs/concepts/policy/limit-range/) 注入預設值
* 配額用盡後，建立或更新請求可能會被拒絕；檢視 ResourceQuota 的 `status.used` 與事件進行排查

## 啟用與使用資源配額

ResourceQuota 透過 API Server 的准入控制實施。標準 Kubernetes 叢集通常啟用 ResourceQuota 准入外掛；託管發行版可能提供自己的設定方式。確認叢集設定後，在目標 Namespace 中建立 `ResourceQuota` 物件。

## 資源配額的型別

* 計算資源，包括 cpu 和 memory
  * cpu, limits.cpu, requests.cpu
  * memory, limits.memory, requests.memory
* 儲存資源，包括儲存資源的總量以及指定 storage class 的總量
  * requests.storage：儲存資源總量，如 500Gi
  * persistentvolumeclaims：pvc 的個數
  * `<storage-class-name>.storageclass.storage.k8s.io/requests.storage` 和 `<storage-class-name>.storageclass.storage.k8s.io/persistentvolumeclaims`：按 StorageClass 限制 PVC 儲存量及數量
  * `requests.ephemeral-storage` 和 `limits.ephemeral-storage`：臨時儲存配額
* 物件數，即可建立的物件的個數
  * pods, replicationcontrollers, configmaps, secrets
  * resourcequotas, persistentvolumeclaims
  * services, services.loadbalancers, services.nodeports

計算資源範例

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-resources
spec:
  hard:
    pods: "4"
    requests.cpu: "1"
    requests.memory: 1Gi
    limits.cpu: "2"
    limits.memory: 2Gi
```

物件個數範例

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: object-counts
spec:
  hard:
    configmaps: "10"
    persistentvolumeclaims: "4"
    replicationcontrollers: "20"
    secrets: "10"
    services: "10"
    services.loadbalancers: "2"
```

## LimitRange

預設情況下，Kubernetes 中所有容器都沒有任何 CPU 和記憶體限制。LimitRange 用來給 Namespace 增加一個資源限制，包括最小、最大和預設資源。比如

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: mylimits
spec:
  limits:
  - max:
      cpu: "2"
      memory: 1Gi
    min:
      cpu: 200m
      memory: 6Mi
    type: Pod
  - default:
      cpu: 300m
      memory: 200Mi
    defaultRequest:
      cpu: 200m
      memory: 100Mi
    max:
      cpu: "2"
      memory: 1Gi
    min:
      cpu: 100m
      memory: 3Mi
    type: Container
```

將 LimitRange 應用於已存在的 Namespace 後，可檢視配額預設值與限制：

```bash
kubectl apply -f limitrange.yaml -n <namespace>
kubectl describe limits mylimits -n <namespace>
```

## 配額範圍

每個配額在建立時可以指定一系列的範圍

| 範圍 | 說明 |
| :--- | :--- |
| Terminating | podSpec.ActiveDeadlineSeconds&gt;=0 的 Pod |
| NotTerminating | podSpec.activeDeadlineSeconds=nil 的 Pod |
| BestEffort | 所有容器的 requests 和 limits 都沒有設定的 Pod（Best-Effort） |
| NotBestEffort | 與 BestEffort 相反 |

## 原地 Pod 資源調整與配額

原地 Pod 資源調整在 Kubernetes v1.33 達到 Beta、v1.35 達到 GA。資源配額仍應使用受支援的標準資源項（如 `requests.cpu`、`limits.memory`）管理；不要新增 `count/pods.resize`、`count/pods.resize-enabled` 或 `count/pods.resize-active` 等未定義配額鍵來控制同時進行的 resize。

調整是否成功還取決於 Pod 的 resize policy、節點與容器執行時能力及當前配額。請使用受支援的 Pod resize API，並結合 Pod 狀態、事件和 ResourceQuota 的實際用量排錯；VPA 或其他自動化控制器的行為需另行驗證。
