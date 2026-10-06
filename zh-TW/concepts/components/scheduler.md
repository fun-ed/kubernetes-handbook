# kube-scheduler

kube-scheduler 負責分配排程 Pod 到叢集內的節點上，它監聽 kube-apiserver，查詢還未分配 Node 的 Pod，然後根據排程策略為這些 Pod 分配節點（更新 Pod 的 `NodeName` 欄位）。

排程器需要充分考慮諸多的因素：

* 公平排程
* 資源高效利用
* QoS
* affinity 和 anti-affinity
* 資料本地化（data locality）
* 內部負載干擾（inter-workload interference）
* deadlines

## 指定 Node 節點排程

有三種方式指定 Pod 只執行在指定的 Node 節點上

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

## Taints 和 tolerations

Taints 和 tolerations 用於保證 Pod 不被排程到不合適的 Node 上，其中 Taint 應用於 Node 上，而 toleration 則應用於 Pod 上。

目前支援的 taint 型別

* NoSchedule：新的 Pod 不排程到該 Node 上，不影響正在執行的 Pod
* PreferNoSchedule：soft 版的 NoSchedule，儘量不排程到該 Node 上
* NoExecute：新的 Pod 不排程到該 Node 上，並且刪除（evict）已在執行的 Pod。Pod 可以增加一個時間（tolerationSeconds），

然而，當 Pod 的 Tolerations 匹配 Node 的所有 Taints 的時候可以排程到該 Node 上；當 Pod 是已經執行的時候，也不會被刪除（evicted）。另外對於 NoExecute，如果 Pod 增加了一個 tolerationSeconds，則會在該時間之後才刪除 Pod。

比如，假設 node1 上應用以下幾個 taint

```bash
kubectl taint nodes node1 key1=value1:NoSchedule
kubectl taint nodes node1 key1=value1:NoExecute
kubectl taint nodes node1 key2=value2:NoSchedule
```

下面的這個 Pod 由於沒有 tolerate`key2=value2:NoSchedule` 無法排程到 node1 上

```yaml
tolerations:
- key: "key1"
  operator: "Equal"
  value: "value1"
  effect: "NoSchedule"
- key: "key1"
  operator: "Equal"
  value: "value1"
  effect: "NoExecute"
```

而正在執行且帶有 tolerationSeconds 的 Pod 則會在 600s 之後刪除

```yaml
tolerations:
- key: "key1"
  operator: "Equal"
  value: "value1"
  effect: "NoSchedule"
- key: "key1"
  operator: "Equal"
  value: "value1"
  effect: "NoExecute"
  tolerationSeconds: 600
- key: "key2"
  operator: "Equal"
  value: "value2"
  effect: "NoSchedule"
```

DaemonSet 管理的 Pod 會獲得對 `node.kubernetes.io/unreachable` 和 `node.kubernetes.io/not-ready` 的容忍，以便節點狀態短暫異常時不被立即驅逐。

## 優先順序排程

Pod 優先順序自 Kubernetes v1.14 起為 Stable。v1.37 使用 `scheduling.k8s.io/v1` 的 PriorityClass，不需要開啟 `PodPriority` feature gate 或舊版 `runtime-config`。舊版啟用方法僅適用於已停止支援的 v1.8-v1.10。

在指定 Pod 的優先順序之前需要先定義一個 PriorityClass（非 namespace 資源），如

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000
globalDefault: false
description: "This priority class should be used for XYZ service pods only."
```

其中

* `value` 為 32 位整數的優先順序，該值越大，優先順序越高
* `globalDefault` 用於未設定 PriorityClassName 的 Pod，整個叢集中應該只有一個 PriorityClass 將其設定為 true

然後，在 PodSpec 中透過 PriorityClassName 設定 Pod 的優先順序：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    env: test
spec:
  containers:
  - name: nginx
    image: nginx:1.30.5
    imagePullPolicy: IfNotPresent
  priorityClassName: high-priority
```

## 多排程器

如果預設的排程器不滿足要求，還可以部署自定義的排程器。並且，在整個叢集中還可以同時執行多個排程器例項，透過 `podSpec.schedulerName` 來選擇使用哪一個排程器（預設使用內建的排程器）。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  # 选择使用自定义调度器 my-scheduler
  schedulerName: my-scheduler
  containers:
  - name: nginx
    image: nginx:1.30.5
```

排程器的範例參見 [這裡](../../extension/scheduler.md)。

## 排程器擴充套件

Scheduling Framework 可透過外掛擴充套件排程過程。自定義外掛需要由對應的排程器二進位或定製建置提供，不能僅將外掛名稱寫入叢集預設 kube-scheduler 的設定就啟用。設定檔案 API 使用 `kubescheduler.config.k8s.io/v1`；欄位和外掛階段請按目標 Kubernetes 版本的[排程器設定文件](https://kubernetes.io/docs/reference/scheduling/config/)核對。

### 儲存容量評分（v1.37 Beta）

`StorageCapacityScoring` 在 v1.33 為 Alpha，並於 v1.37 升為預設啟用的 Beta。該特性擴充套件 VolumeBinding 外掛，根據可用儲存容量參與節點評分；無需手工設定 `--feature-gates=StorageCapacityScoring=true`。

這一能力用於適用的動態卷供應場景，仍依賴 CSI driver 提供準確的儲存容量資訊與叢集的 StorageClass/排程設定。使用 `WaitForFirstConsumer` 等延遲綁定設定前，請確認儲存驅動支援並遵循其文件。自定義 kube-scheduler 設定請使用 `kubescheduler.config.k8s.io/v1` 並參考上游設定 API。

### Dynamic Resource Allocation（DRA）排程

Kubernetes v1.37 的 DRA 核心能力已在 v1.34 達到 GA；`DynamicResourceAllocation` feature gate 自 v1.35 起鎖定為啟用狀態。v1.37 無需手動設定 `--feature-gates=DynamicResourceAllocation=true`，也不能將其關閉。DRA 驅動和各獨立 DRA 特性仍有各自的版本與 feature gate 狀態，使用前核對對應驅動和目標版本文件。

`DynamicResources` 是 kube-scheduler 的 DRA 外掛。需要自定義外掛引數時，應按實際版本的 `DynamicResourcesArgs` schema 設定：支援 `filterTimeout`（由 `DRASchedulerFilterTimeout` 控制）和 `bindingTimeout`（需要 `DRADeviceBindingConditions` 與 `DRAResourceClaimDeviceStatus`）。`scoringStrategy` 不是該 args 的欄位，不能放進 scheduler 設定。請查閱 [v1.37 kube-scheduler 設定 API](https://github.com/kubernetes/kubernetes/blob/v1.37.1/staging/src/k8s.io/kube-scheduler/config/v1/types_pluginargs.go)；不要複製本頁此前的虛構策略設定。

Pod 可透過 `resourceClaims[].resourceClaimName` 引用預先存在、由相容 DRA 驅動管理的 ResourceClaim，並在容器 `resources.claims` 中引用其 claim 名稱。以下為 `spec` 片段，不是可獨立應用的 Pod：先按所選驅動文件建立並授權 ResourceClaim，再補齊實際容器映像檔和其他 Pod 欄位。

```yaml
spec:
  containers:
  - name: workload
    resources:
      claims:
      - name: gpu
  resourceClaims:
  - name: gpu
    resourceClaimName: precreated-gpu-claim
```

### 排程策略

> 注意，排程策略只在 1.23 之前的版本中支援。從 1.23 開始，使用者需要切換到上述排程外掛的方式。

kube-scheduler 還支援使用 `--policy-config-file` 指定一個排程策略檔案來自定義排程策略，比如

```javascript
{
"kind" : "Policy",
"apiVersion" : "v1",
"predicates" : [
    {"name" : "PodFitsHostPorts"},
    {"name" : "PodFitsResources"},
    {"name" : "NoDiskConflict"},
    {"name" : "MatchNodeSelector"},
    {"name" : "HostName"}
    ],
"priorities" : [
    {"name" : "LeastRequestedPriority", "weight" : 1},
    {"name" : "BalancedResourceAllocation", "weight" : 1},
    {"name" : "ServiceSpreadingPriority", "weight" : 1},
    {"name" : "EqualPriority", "weight" : 1}
    ],
"extenders":[
    {
        "urlPrefix": "http://127.0.0.1:12346/scheduler",
        "apiVersion": "v1beta1",
        "filterVerb": "filter",
        "prioritizeVerb": "prioritize",
        "weight": 5,
        "enableHttps": false,
        "nodeCacheCapable": false
    }
    ]
}
```

## 其他影響排程的因素

* 如果 Node Condition 處於 MemoryPressure，則所有 BestEffort 的新 Pod（未指定 resources limits 和 requests）不會排程到該 Node 上
* 如果 Node Condition 處於 DiskPressure，則所有新 Pod 都不會排程到該 Node 上
* 為了保證 Critical Pods 的正常執行，當它們處於異常狀態時會自動重新排程。Critical Pods 是指
  * annotation 包括 `scheduler.alpha.kubernetes.io/critical-pod=''`
  * tolerations 包括 `[{"key":"CriticalAddonsOnly", "operator":"Exists"}]`
  * priorityClass 為 `system-cluster-critical` 或者 `system-node-critical`

## 啟動 kube-scheduler 範例

```bash
kube-scheduler --address=127.0.0.1 --leader-elect=true --kubeconfig=/etc/kubernetes/scheduler.conf
```

## kube-scheduler 工作原理

kube-scheduler 排程原理：

```text
For given pod:

    +---------------------------------------------+
    |               Schedulable nodes:            |
    |                                             |
    | +--------+    +--------+      +--------+    |
    | | node 1 |    | node 2 |      | node 3 |    |
    | +--------+    +--------+      +--------+    |
    |                                             |
    +-------------------+-------------------------+
                        |
                        |
                        v
    +-------------------+-------------------------+

    Pred. filters: node 3 doesn't have enough resource

    +-------------------+-------------------------+
                        |
                        |
                        v
    +-------------------+-------------------------+
    |             remaining nodes:                |
    |   +--------+                 +--------+     |
    |   | node 1 |                 | node 2 |     |
    |   +--------+                 +--------+     |
    |                                             |
    +-------------------+-------------------------+
                        |
                        |
                        v
    +-------------------+-------------------------+

    Priority function:    node 1: p=2
                          node 2: p=5

    +-------------------+-------------------------+
                        |
                        |
                        v
            select max{node priority} = node 2
```

kube-scheduler 排程分為兩個階段，predicate 和 priority

* predicate：過濾不符合條件的節點
* priority：優先順序排序，選擇優先順序最高的節點

predicates 策略

* PodFitsPorts：同 PodFitsHostPorts
* PodFitsHostPorts：檢查是否有 Host Ports 衝突
* PodFitsResources：檢查 Node 的資源是否充足，包括允許的 Pod 數量、CPU、記憶體、GPU 個數以及其他的 OpaqueIntResources
* HostName：檢查 `pod.Spec.NodeName` 是否與候選節點一致
* MatchNodeSelector：檢查候選節點的 `pod.Spec.NodeSelector` 是否匹配
* NoVolumeZoneConflict：檢查 volume zone 是否衝突
* MaxEBSVolumeCount：檢查 AWS EBS Volume 數量是否過多（預設不超過 39）
* MaxGCEPDVolumeCount：檢查 GCE PD Volume 數量是否過多（預設不超過 16）
* MaxAzureDiskVolumeCount：檢查 Azure Disk Volume 數量是否過多（預設不超過 16）
* MatchInterPodAffinity：檢查是否匹配 Pod 的親和性要求
* NoDiskConflict：檢查是否存在 Volume 衝突，僅限於 GCE PD、AWS EBS、Ceph RBD 以及 ISCSI
* GeneralPredicates：分為 noncriticalPredicates 和 EssentialPredicates。noncriticalPredicates 中包含 PodFitsResources，EssentialPredicates 中包含 PodFitsHost，PodFitsHostPorts 和 PodSelectorMatches。
* PodToleratesNodeTaints：檢查 Pod 是否容忍 Node Taints
* CheckNodeMemoryPressure：檢查 Pod 是否可以排程到 MemoryPressure 的節點上
* CheckNodeDiskPressure：檢查 Pod 是否可以排程到 DiskPressure 的節點上
* NoVolumeNodeConflict：檢查節點是否滿足 Pod 所引用的 Volume 的條件

priorities 策略

* SelectorSpreadPriority：優先減少節點上屬於同一個 Service 或 Replication Controller 的 Pod 數量
* InterPodAffinityPriority：優先將 Pod 排程到相同的拓撲上（如同一個節點、Rack、Zone 等）
* LeastRequestedPriority：優先排程到請求資源少的節點上
* BalancedResourceAllocation：優先平衡各節點的資源使用
* NodePreferAvoidPodsPriority：alpha.kubernetes.io/preferAvoidPods 欄位判斷, 權重為 10000，避免其他優先順序策略的影響
* NodeAffinityPriority：優先排程到匹配 NodeAffinity 的節點上
* TaintTolerationPriority：優先排程到匹配 TaintToleration 的節點上
* ServiceSpreadingPriority：儘量將同一個 service 的 Pod 分佈到不同節點上，已經被 SelectorSpreadPriority 替代 \[預設未使用\]
* EqualPriority：將所有節點的優先順序設定為 1\[預設未使用\]
* ImageLocalityPriority：儘量將使用大映像檔的容器排程到已經下拉了該映像檔的節點上 \[預設未使用\]
* MostRequestedPriority：儘量排程到已經使用過的 Node 上，特別適用於 cluster-autoscaler\[預設未使用\]

> **程式碼入口路徑**
>
> 在release-1.9及之前的程式碼入口在plugin/cmd/kube-scheduler，從release-1.10起，kube-scheduler的核心程式碼遷移到pkg/scheduler目錄下面，入口也遷移到cmd/kube-scheduler

## 參考文件

* [Pod Priority and Preemption](https://kubernetes.io/docs/concepts/configuration/pod-priority-preemption/)
* [Configure Multiple Schedulers](https://kubernetes.io/docs/tasks/administer-cluster/configure-multiple-schedulers/)
* [Taints and Tolerations](https://kubernetes.io/docs/concepts/configuration/taint-and-toleration/)
* [Advanced Scheduling in Kubernetes](https://kubernetes.io/blog/2017/03/advanced-scheduling-in-kubernetes/)
