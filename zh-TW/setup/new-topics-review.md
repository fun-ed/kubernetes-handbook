# 新主題整合檢閱記錄

**Kubernetes 基準：** v1.37.1。**來源截點：** 2026-10-05。本記錄涵蓋七組新增章節及安裝順序指南。它補充先前的現行內容檢閱，不取代或改寫該記錄。

## 範圍與來源證據

| 主題 | 版本證據與相容性限制 |
| --- | --- |
| Argo CD | v3.5.3 於 2026-09-14 發布。該版本固定的測試表列出 Kubernetes 1.33 至 1.36，未列 1.37。[發行版](https://github.com/argoproj/argo-cd/releases/tag/v3.5.3) · [測試版本](https://github.com/argoproj/argo-cd/blob/v3.5.3/docs/operator-manual/tested-kubernetes-versions.md) |
| Argo Workflows | v4.1.4 於 2026-09-18 發布。未找到肯定的官方 Kubernetes v1.37 矩陣。版本化 RBAC 指南記載，workflow executor 需要對 `workflowtaskresults` 規則授予 `create` 與 `patch`。[發行版](https://github.com/argoproj/argo-workflows/releases/tag/v4.1.4) · [RBAC](https://github.com/argoproj/argo-workflows/blob/v4.1.4/docs/workflow-rbac.md) |
| KubeVirt | v1.9.0 是截點時查到的最高穩定版，於 2026-07-30 發布。排除預發布版 v1.10.0-alpha.0；已檢視的官方資料未宣稱支援 Kubernetes v1.37。[發行版](https://github.com/kubevirt/kubevirt/releases/tag/v1.9.0) |
| Kubeflow | Community Distribution 26.03.1 於 2026-06-15 發布。它包含各自獨立版本化的專案，例如 Pipelines 2.16.1、Trainer 2.2.0、Istio 1.30.1、cert-manager 1.20.2、Dex 2.45.1 與 Notebooks v1.11.0。發行說明提及 Kubernetes 1.36 CI，但未說明支援 v1.37。本記錄未將採 CalVer 的發行版冒充為單一 SemVer 元件加入自動發布追蹤清單。[發行版](https://github.com/kubeflow/community-distribution/releases/tag/26.03.1) |
| Longhorn | v1.13.0 與 chart 1.13.0 於 2026-09-29 發布。發行說明列出 Kubernetes v1.34 為最低版本；這不是對整體 v1.37.1 平台組合的認證。[發行版](https://github.com/longhorn/longhorn/releases/tag/v1.13.0) · [chart](https://github.com/longhorn/longhorn/blob/v1.13.0/chart/Chart.yaml) |
| Cilium BGP 與 IPv6 | 指南使用既有的 Cilium v1.20.2 基準。其版本化 Kubernetes 矩陣列出 1.33 至 1.36，未列 v1.37。本主題章節沿用既有版本基準，不將 BGP 專題當成新版本稽核。[矩陣](https://docs.cilium.io/en/v1.20/operations/support/) · [BGP v2 設定](https://docs.cilium.io/en/v1.20/network/bgp-control-plane/bgp-control-plane-configuration/) |
| nftables | 指南記錄 Kubernetes v1.37 kube-proxy 行為：nftables 模式已 GA，但不是預設模式；Linux 核心最低版本為 5.13。[Kubernetes 文件](https://kubernetes.io/docs/reference/networking/virtual-ips/#nftables-proxy-mode) |
| Istio Ambient | 指南使用既有的 Istio 1.31.1 基準。官方支援表的範圍到 Kubernetes 1.36 為止，因此本記錄不宣稱相容 v1.37。[Istio 1.31 ambient 安裝](https://istio.io/v1.31/docs/ambient/install/) · [支援表](https://istio.io/latest/docs/releases/supported-releases/) |

## 整合與驗證狀態

七組新增章節為 `apps/devops/argo-cd.md`、`apps/kubevirt.md`、`apps/kubeflow.md`、`extension/volume/longhorn.md`、`extension/network/cilium-bgp-ipv6.md`、`network/nftables.md` 與 `apps/istio/ambient.md`，各有 `zh-TW/` 對應版本。`apps/devops/argo.md` 現在明確標示 Argo Workflows。`setup/component-installation-order.md` 及繁體中文版本說明按需安裝的相依順序、工具安裝與資料安全界線。
兩份目錄都已連結新章節，相關本機索引也提供入口。繁體中文涵蓋清單記錄實際存在的 Markdown 成對檔案。元件追蹤清單新增 Argo Workflows、Longhorn 與 KubeVirt；沒有肯定 v1.37 支援證據時，支援狀態保持未確認。Kubeflow 以多專案 CalVer 發行版記錄，不視為單一 SemVer 追蹤項目。Cilium 與 Istio 的既有版本基準未升級。

先前的 178 組檔案檢閱仍是歷史快照。未改寫其來源雜湊與結論，也未把這些新章節或 Cilium、kube-proxy 的少量交叉連結修改追溯納入。先前檢閱未涵蓋這些新頁面。

主整合者记录的驗證命令、結果、來源指紋與未涵蓋範圍，請見[驗證報告](new-topics-review.json)。本主題內容負責人未執行安裝器或叢集命令。
