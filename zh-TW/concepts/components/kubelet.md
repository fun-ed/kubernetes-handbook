# kubelet

kubelet 執行在每個工作節點上，負責管理排程到該節點的 Pod，並向 API Server 報告節點和 Pod 狀態。其 HTTPS API 預設監聽 TCP 10250。請限制存取範圍，只允許控制平面和獲准的運維人員存取。

## 節點管理

節點管理主要是節點自注冊和節點狀態更新：

* Kubelet 可以透過設定啟動引數 --register-node 來確定是否向 API Server 註冊自己；
* 如果 Kubelet 沒有選擇自注冊模式，則需要使用者自己設定 Node 資源資訊，同時需要告知 Kubelet 叢集上的 API Server 的位置；
* Kubelet 在啟動時透過 API Server 註冊節點資訊，並定時向 API Server 傳送節點新訊息，API Server 在接收到新訊息後，將資訊寫入 etcd

## Pod 管理

### 獲取 Pod 清單

kubelet 從 API Server 接收排程到本節點的 Pod，並負責讓 Pod 達到期望狀態。它不直接監視 etcd。靜態 Pod 可由 kubelet 設定中的 `staticPodPath` 指定本地清單目錄；靜態 Pod 的狀態會透過對應的 Mirror Pod 報告給 API Server。

建立 Pod 時，kubelet 透過 CRI 請求容器執行時建立 Pod sandbox 和容器。執行時使用的 sandbox 映像檔由叢集設定決定。Pod 網路由節點上的 CNI 實現設定，卷由相應的卷外掛（包括 CSI 驅動）處理。kubelet 再把執行狀態報告給 API Server。

### Static Pod

所有以非 API Server 方式建立的 Pod 都叫 Static Pod。Kubelet 將 Static Pod 的狀態彙報給 API Server，API Server 為該 Static Pod 建立一個 Mirror Pod 和其相匹配。Mirror Pod 的狀態將真實反映 Static Pod 的狀態。當 Static Pod 被刪除時，與之相對應的 Mirror Pod 也會被刪除。

## 容器健康檢查

Pod 支援三類探針，用於檢查容器和應用的狀態：

* `startupProbe` 判斷應用是否完成啟動。設定後，在啟動探針成功之前，kubelet 不會執行 liveness 和 readiness 探針。
* `livenessProbe` 檢查容器是否仍能正常工作。連續失敗會導致 kubelet 按 Pod 重啟策略重啟容器。
* `readinessProbe` 檢查應用是否準備好接收流量。探針失敗時，EndpointSlice 控制器會更新該 Pod 對應端點的就緒狀態。

探針支援 exec、TCP socket 和 HTTP 檢查。探針定義位於 Pod 中相應容器的設定下。

## 節點和容器度量

cAdvisor 整合在 kubelet 中，不再單獨監聽舊版 4194 連接埠。授權後，可透過 kubelet HTTPS API（預設 10250）或 API Server 節點代理讀取 `/metrics`、`/metrics/cadvisor` 和 `/stats/summary`。

```bash
kubectl get --raw "/api/v1/nodes/<node-name>/proxy/stats/summary"
```

Kubernetes v1.37 的 kubelet 不再在 `/stats/summary` 中返回 `userDefinedMetrics`，也不再匯出 cAdvisor 應用自定義度量。容器度量的具體欄位和可用系列以當前 kubelet 文件及發行說明為準。
## Memory Manager 的歷史說明

以下內容記錄 Kubernetes v1.21 時期的 Alpha 功能狀態，不代表 v1.37 的功能門控狀態。當前設定請查閱 [KubeletConfiguration API](https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/)。

## Kubelet Eviction（驅逐）

Kubelet 會監控資源的使用情況，並使用驅逐機制防止計算和儲存資源耗盡。在驅逐時，Kubelet 將 Pod 的所有容器停止，並將 PodPhase 設定為 Failed。

Kubelet 定期（`housekeeping-interval`）檢查系統的資源是否達到了預先設定的驅逐閾值，包括

| Eviction Signal | Condition | Description |
| :--- | :--- | :--- |
| `memory.available` | MemoryPressure | `memory.available` := `node.status.capacity[memory]` - `node.stats.memory.workingSet` （計算方法參考[這裡](https://kubernetes.io/docs/tasks/administer-cluster/memory-available.sh)） |
| `nodefs.available` | DiskPressure | `nodefs.available` := `node.stats.fs.available`（Kubelet Volume以及日誌等） |
| `nodefs.inodesFree` | DiskPressure | `nodefs.inodesFree` := `node.stats.fs.inodesFree` |
| `imagefs.available` | DiskPressure | `imagefs.available` := `node.stats.runtime.imagefs.available`（映像檔以及容器可寫層等） |
| `imagefs.inodesFree` | DiskPressure | `imagefs.inodesFree` := `node.stats.runtime.imagefs.inodesFree` |

這些驅逐閾值可以使用百分比，也可以使用絕對值，如

```bash
--eviction-hard=memory.available<500Mi,nodefs.available<1Gi,imagefs.available<100Gi
--eviction-minimum-reclaim="memory.available=0Mi,nodefs.available=500Mi,imagefs.available=2Gi"`
--system-reserved=memory=1.5Gi
```

這些驅逐訊號可以分為軟碟機逐和硬驅逐

* 軟碟機逐（Soft Eviction）：配合驅逐寬限期（eviction-soft-grace-period和eviction-max-pod-grace-period）一起使用。系統資源達到軟碟機逐閾值並在超過寬限期之後才會執行驅逐動作。
* 硬驅逐（Hard Eviction ）：系統資源達到硬驅逐閾值時立即執行驅逐動作。

驅逐動作包括回收節點資源和驅逐使用者 Pod 兩種：

* 回收節點資源
  * 設定了 imagefs 閾值時
    * 達到 nodefs 閾值：刪除已停止的 Pod
    * 達到 imagefs 閾值：刪除未使用的映像檔
  * 未設定 imagefs 閾值時
    * 達到 nodefs閾值時，按照刪除已停止的 Pod 和刪除未使用映像檔的順序清理資源
* 驅逐使用者 Pod
  * 驅逐順序為：BestEffort、Burstable、Guaranteed
  * 設定了 imagefs 閾值時
    * 達到 nodefs 閾值，基於 nodefs 用量驅逐（local volume + logs）
    * 達到 imagefs 閾值，基於 imagefs 用量驅逐（容器可寫層）
  * 未設定 imagefs 閾值時
    * 達到 nodefs閾值時，按照總磁碟使用驅逐（local volume + logs + 容器可寫層）

## 容器垃圾回收引數（歷史說明）

本節早期的引數對照表描述舊版本的垃圾回收計劃，不是當前設定建議。kubelet 在較新版本中移除了部分容器統計和垃圾回收選項。請根據目標版本的 kubelet 命令列參考和 KubeletConfiguration API 檢查引數，不要從此處複製舊 flag。
## 容器執行時

kubelet 透過 CRI v1 與容器執行時互動，並呼叫 RuntimeService 和 ImageService 管理 Pod sandbox、容器和映像檔。常見實現包括 containerd 和 CRI-O；其他執行時也必須提供相容的 CRI。

Kubernetes v1.24 移除了內建 dockershim。Docker Engine 不能直接作為 kubelet 的 CRI 執行時；需要繼續使用 Docker Engine 的叢集必須自行部署並維護外部配接器，例如 cri-dockerd。容器映像檔由 CRI 執行時管理，不能假定節點上的 Docker CLI 與 kubelet 使用同一套映像檔儲存。

Pod sandbox 映像檔（常稱 pause 映像檔）由執行時設定管理。請使用叢集發行版為目標 Kubernetes 版本提供的設定，避免單獨覆蓋該映像檔。
## Kubelet 設定

kubelet 的生產設定應使用 `KubeletConfiguration` 和叢集發行版規定的設定管理方式。較早章節中的 `--network-plugin`、`--cni-bin-dir`、`--cluster-dns` 和 `--cadvisor-port` 命令列引數不是 Kubernetes v1.37 的通用設定範例。欄位和移除的引數請查閱 [KubeletConfiguration](https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/) 與 [kubelet 命令列參考](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/)。

## kubelet 工作原理

如下 kubelet 內部元件結構圖所示，Kubelet 由許多內部元件構成

Kubelet 當前以 CRI 管理容器執行時，以 CNI 設定 Pod 網路，並由節點上的卷外掛處理儲存。舊版架構圖中的 dockershim、rkt、HTTP manifest server 和獨立 cAdvisor 連接埠不代表 v1.37 的節點元件。

![](../../.gitbook/assets/kubelet%20%283%29.png)

### Pod 啟動流程

![Pod Start](../../.gitbook/assets/pod-start%20%281%29.png)

### 透過 API Server 查詢節點彙總指標

舊版文件曾展示透過 kubelet 的匿名只讀 10255 連接埠存取彙總指標。該連接埠不應啟用或開放。透過 API Server 節點代理查詢時，請使用經授權的 kubeconfig：

```bash
kubectl get --raw "/api/v1/nodes/<node-name>/proxy/stats/summary"
```

## Kubelet API

kubelet HTTPS API 預設監聽 TCP 10250，存取需要透過 kubelet 的認證和授權設定。API Server 也可以根據 RBAC 權限代理到該節點。常見的度量路徑包括 `/metrics`、`/metrics/cadvisor`、`/metrics/resource`、`/metrics/probes` 和 `/stats/summary`。不要啟用或暴露舊版只讀連接埠 10255，也不要將 kubelet API 暴露給不受信任的網路。
