# 資源控制

本文的 API 範例面向 Kubernetes v1.37.1。資源請求和限制由工作負載作者設定，排程與執行時的具體結果仍取決於節點容量、執行時和准入策略。

## CPU 和記憶體請求、限制

- `requests` 是排程器放置 Pod 時考慮的資源量；容器在節點上仍可能使用超過 request 的可用資源。
- 在 Linux 節點，`limits.cpu` 由核心透過節流執行；容器的 `limits.memory` 由 cgroup 限制，達到限制後若仍無法滿足後續記憶體配置，核心可能觸發 cgroup OOM kill（不必等到節點整體記憶體不足）。這與 kubelet 因節點層級記憶體壓力而驅逐 Pod 不同；此說明不適用於 Windows。
- 為工作負載設定經過測量的請求和限制，並結合工作負載峰值、節點可用容量及命名空間策略調整，不要僅複製範例數值。

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: research
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:1.30.5
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
```

`nginx:1.30.5` 是本手冊資料截點前查核的 NGINX stable 範例標籤（並非 Kubernetes v1.37 相容性聲明，也不是不可變 digest）；正式環境應使用組織審查過的映像檔，並依供應鏈策略固定 digest。叢集中先建立 `research` namespace，並確認策略允許此範例映像檔。

資源單位、Pod 彙總和額外資源型別（包括 `ephemeral-storage`、HugePages 與 extended resources）詳見 [Kubernetes 資源管理文件](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)。

## ResourceQuota 與 LimitRange

配額是 namespace 級上限，不會自動給 Pod 設定合理的資源值。以下範例限制 CPU、記憶體與 Pod 數量：

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-compute
  namespace: research
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "50"
```

可用 `LimitRange` 為容器指定預設請求/限制或合法範圍；它與 ResourceQuota 的作用不同：

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: container-defaults
  namespace: research
spec:
  limits:
  - type: Container
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    default:
      cpu: "500m"
      memory: "512Mi"
```

先按團隊工作負載定義額度和預設值，避免預設限制意外壓制應用。檢查實際生效設定：

```bash
kubectl describe resourcequota -n research
kubectl describe limitrange -n research
kubectl get pods -n research
```

## 原地調整 Pod 資源

原地 Pod CPU/記憶體資源調整在 Kubernetes v1.35 成為穩定功能。v1.37 可修改執行中 Pod 的容器 `requests` 與 `limits`，不必為了每次變更都重建 Pod；但節點容量不足時調整可能處於 pending/deferred 狀態，記憶體調整也可能依照 `resizePolicy` 重啟容器。QoS 類別不會因調整而改變，仍需遵循原有類別的資源規則。請先閱讀[官方限制與操作說明](https://kubernetes.io/docs/tasks/configure-pod-container/resize-container-resources/)。
原地調整最早在 v1.27 引入，舊章所述的 v1.33 Beta 是歷史狀態；本章按 v1.35 起穩定的 v1.37 行為說明。

下面的獨立 Pod 用於演示 CPU 調整。請求與限制保持相等，便於遵循 Guaranteed QoS 條件：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resize-demo
  namespace: research
spec:
  containers:
  - name: pause
    image: registry.k8s.io/pause:3.10.2
    resizePolicy:
    - resourceName: cpu
      restartPolicy: NotRequired
    - resourceName: memory
      restartPolicy: RestartContainer
    resources:
      requests:
        cpu: "700m"
        memory: "200Mi"
      limits:
        cpu: "700m"
        memory: "200Mi"
```

應用後將 CPU 的 request 和 limit 一起調整；節點必須有足夠容量：

```bash
kubectl apply -f resize-demo.yaml
kubectl patch pod resize-demo -n research --subresource resize --type=strategic \
  -p '{"spec":{"containers":[{"name":"pause","resources":{"requests":{"cpu":"800m"},"limits":{"cpu":"800m"}}}]}}'
kubectl get pod resize-demo -n research -o yaml
```

檢視 Pod conditions 及 `status.containerStatuses[].resources`，確認實際資源已更新。此實驗只演示 Kubernetes API；不要把臨時修改當作工作負載控制器的期望模板變更。若要持續管理資源，應更新 Deployment/StatefulSet 等控制器的模板並用 rollout 釋出。CPU 與記憶體調整的執行時行為和限制以目標叢集文件為準。

## HugePages 與裝置資源

HugePages 必須由 Linux 節點預先設定並報告為可分配容量，不能超額分配；`hugepages-<size>` 的請求和限制需匹配節點提供的頁大小。參見[HugePages 範例](hugepage.md)和[Kubernetes 操作文件](https://kubernetes.io/docs/tasks/manage-hugepages/scheduling-hugepages/)。

Dynamic Resource Allocation (DRA) 自 Kubernetes v1.34 起 GA，核心 feature gate `DynamicResourceAllocation` 自 v1.35 起鎖定啟用。DRA 資源需有相容的裝置驅動和叢集設定；DeviceClass、ResourceClaim 等物件的欄位及可用能力依賴具體驅動，不存在可對所有 GPU/FPGA 驅動通用的假定引數。不要把裝置配額、裝置汙點、自動重新分配或清理策略寫成未經驅動/API schema 驗證的通用 YAML。按[官方 DRA 概念](https://kubernetes.io/docs/concepts/resource-management/dynamic-resource-allocation/)及[設定和分配裝置的步驟](https://kubernetes.io/docs/tasks/configure-pod-container/assign-resources/)操作。官方文件提示當前排程器不支援 DRA 裝置資源的搶佔。

GPU 的 NVIDIA Operator、驅動要求和 Kubernetes 支援範圍見[GPU 章節](gpu.md)；不要把舊的 `resource.k8s.io/v1alpha2` 範例或未經驗證的第三方 ResourceClaim schema 直接應用到叢集。

## VPA 與監控工具

Vertical Pod Autoscaler (VPA) 是獨立安裝的擴充套件控制器，需先安裝與目標 Kubernetes 版本相容的 VPA release 和 CRD。VPA 的 API、更新模式及其與原地 Pod resize 的整合由 VPA 自身版本決定；Kubernetes 原生 resize 穩定，並不代表任意 VPA manifest 都支援 `InPlace`。按[VPA 上游安裝、特性與限制說明](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler)選擇並驗證版本。

`kubectl top` 依賴叢集已安裝並正常工作的 Metrics API provider；它不是歷史命令範例的替代品，也不等同於完整的容量監控。任何額外診斷工具都應核實維護狀態、基準版本、映像檔、權限和對節點的存取範圍後再部署。
