# 元件按需安裝順序

本手冊介紹多個可選元件，不代表應將它們全部安裝到同一個叢集。先確認要解決的問題、目標 Kubernetes 版本、發行版，以及現有的網路、儲存與身分驗證方案。只安裝這次需要的元件，並固定至已檢視的版本；各元件章節中的版本與相容性限制優先於通用順序。

## 先檢查，再安裝

1. 確認 Kubernetes 與發行版版本、節點作業系統與核心版本、可用的 CPU／記憶體／磁碟、網路範圍，以及現有 CNI、DNS、CSI、Ingress 或 Gateway 實作。
2. 確認元件官方 Kubernetes 支援聲明、前置條件、資料持久性，以及升級／復原方式。若沒有正式相容矩陣，不要宣稱已支援目標版本。
3. 規劃 Namespace、ServiceAccount、RBAC、Secret、網路策略、資源請求與配額。使用獨立身分執行控制器，不要預設授予 `cluster-admin`。
4. 先準備必要的底層服務，再安裝控制器。先確認 API 與 CRD 已就緒，最後才建立自訂資源與工作負載。
5. 每次只加入一項變更，在隔離環境驗證健康狀態、網路路徑、儲存行為與復原流程，再決定是否推廣。

先確認主網路與 Pod 連線能力，再準備必要的 DNS 與儲存服務。之後安裝控制器及其 CRD 與平台 API，最後才部署應用程式工作負載。叢集發行版已提供的服務不要重複安裝或替換。

## 本手冊主題的安裝順序

以下是相依順序，不是要在同一個叢集中安裝所有項目的清單。詳細安裝命令、版本限制與故障排除，請以連結章節及對應版本的官方文件為準。

### 網路基礎

- [Cilium](../extension/network/cilium.md) 作為主 CNI 時，先確認叢集尚未執行不相容的主 CNI，並依所選版本的官方安裝文件設定。現有 Cilium v1.20.2 相容矩陣未列出 Kubernetes v1.37，不要宣稱已支援。若要使用 [Cilium BGP 與 IPv6](../extension/network/cilium-bgp-ipv6.md)，先驗證 Pod／節點的 IPv6 路由、位址配置與對端路由政策，再啟用 BGP 對外發布。控制平面可連線不代表路由已安全收斂；不要發布未經審核的前綴。
- [nftables kube-proxy 模式](../network/nftables.md)是 kube-proxy 的一種選擇，不是 Kubernetes v1.37 的預設模式。確認 Linux 核心至少為 5.13，並核對發行版與 CNI 的相容要求後再切換。若 Cilium 以 eBPF 取代 kube-proxy，不要同時依本手冊安裝 nftables kube-proxy 路徑；只能依所選 Cilium 版本的 Proxy 模式文件設定。

### 儲存與虛擬化

- [Longhorn](../extension/volume/longhorn.md) v1.13.0 需要節點磁碟、網路與 CSI。先檢查磁碟分割區、容量、節點標籤、StorageClass、複本政策、備份目標與復原演練，再安裝控制器並建立磁碟區。本書隔離實驗使用 Longhorn V1，並在 StorageClass 明確設定 `dataEngine: "v1"`。Longhorn V1 與 V2 資料引擎的核心和硬體前置條件不同，不能只切換 StorageClass 參數就改用 V2；請依該章和對應版本文件分別確認條件。
- [KubeVirt](../apps/kubevirt.md) 先檢查節點是否提供所需的 KVM 硬體虛擬化、虛擬機磁碟所需的持久化儲存與網路。接著安裝 Operator，等待相關 CRD 顯示 `Established=True`，建立 `KubeVirt` 自訂資源並等待狀態成為 `Available=True`，再建立 VirtualMachine。先準備 PVC 與可開機的虛擬機磁碟，並在隔離的測試 Namespace 驗證映像檔、網路與啟動權限。

### 工作流程與平台控制器

- [Argo Workflows](../apps/devops/argo.md) 與 [Argo CD](../apps/devops/argo-cd.md) 是不同產品，應分別決定是否需要。為 Workflow 設定專用 ServiceAccount，以及完成任務所需的最小 Role／RoleBinding。Workflow executor 的文件化規則至少需要對 `argoproj.io` API group 中的 `workflowtaskresults` 資源授予 `create`、`patch` 權限；再依實際工作流程增加權限，不要沿用預設的高權限身分。Argo CD v3.5.3 的測試表列出 Kubernetes 1.33 至 1.36，未列 v1.37。先決定可信任的 Git 來源、儲存庫憑證與同步權限，再設定 Argo CD 的目標 Namespace 與資源範圍。
- [Kubeflow](../apps/kubeflow.md) 是由多個各自獨立版本化的專案組成的發行版。安裝前先核對所選發行版的元件、資源需求、使用者身分與隔離方式，以及該發行版附帶的 Istio sidecar 相依性。26.03.1 發行說明提到 Kubernetes 1.36 CI，但未聲明支援 v1.37。Kubeflow 使用的 sidecar 版本不等同於可獨立升級的 Ambient 安裝；不可將 [Istio Ambient](../apps/istio/ambient.md) 視為可直接替代的方案。依所選發行版文件驗證使用者身分驗證、流量政策、Notebook／訓練工作負載及資源配額；不要將範例 overlay 當成無條件支援的安裝指令。
- [Istio Ambient](../apps/istio/ambient.md) 先依版本化文件安裝所需的 Gateway API CRD、Istio base、`istiod`、CNI 整合與 `ztunnel`。只有需要 L7 處理時才部署使用 `istio-waypoint` GatewayClass 的 Gateway，並為 Namespace 設定 `istio.io/use-waypoint` 標籤。Istio 1.31.1 官方支援表未列 Kubernetes v1.37。Waypoint 會改變請求身分判定；依所選資料平面設定相應的 L4 或 waypoint L7 AuthorizationPolicy，不要混用兩種模式的主體規則。不要同時使用 sidecar 注入和 Ambient 標籤接入同一工作負載。

## 本機文件工具也按需安裝

- 只建置本書時，只需儲存庫 `.nvmrc` 指定的 Node.js 24.21.0、npm 11.19.0 與鎖定相依套件。依[網站建置指南](site-build.md)使用 `mise install node@24.21.0`，再執行 `mise exec node@24.21.0 -- npm ci`。閱讀章節不需要 Kubernetes 叢集或容器執行環境。
- 只有執行對應的內嵌檢查時才需要 uv；`check-current-content.py` 另要求 `PATH` 中有 Go 1.26.0 或更新版本。詳情見[清單驗證指南](verification.md)。只編輯文件時不必預先安裝這些工具。
- `kubectl`、Helm、CNI／CSI 專用 CLI 與叢集管理工具，只在實際操作目標環境時安裝。先確認工具版本、目標 kubeconfig 與權限；不要把本機開發相依套件當成叢集元件。

## 未使用元件與磁碟空間

先盤點再決定。可使用唯讀命令查看可用磁碟、容器引擎空間、建置快取與本機叢集清單：

```sh
df -h "$HOME"
docker system df -v
docker buildx du
kind get clusters
du -sh "${HOME}/Library/Caches" "${HOME}/.cache" 2>/dev/null
```

這些命令只用來查看，不會判定資料是否可刪除。區分可重建的建置快取、可重新下載的映像檔，以及可能含有唯一資料的容器磁碟區、PVC、PV、資料庫與叢集狀態。不要停止執行中的服務或容器，也不要移除目前使用中的磁碟區、語言執行階段、mise 工具鏈、環境或相依套件。

清理前，由有權限的人確認每個物件的負責人、用途、復原來源與備份。先為設定檔製作附時間戳記的副本；為磁碟區建立 tar 備份；為 Kubernetes 狀態匯出 YAML；為資料庫製作資料庫層級備份，並確認可以復原。只允許人工選擇明確可重建的快取，再依該工具文件單獨清理。不要執行 Docker system／volume prune，不要把 `helm uninstall` 或刪除 PVC／PV／Namespace 當作通用清理步驟。本書維護者不會代替操作者執行清理；本書沒有刪除資料或釋出磁碟空間。
