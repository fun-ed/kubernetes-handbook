# 叢集附加元件

Kubernetes 核心發行版不替你自動安裝所有網路、指標、可觀測性和擴縮容元件。每個外掛應按其官方支援矩陣、叢集 minor 版本、容器執行時和網路要求單獨選型；這裡的“最新穩定版”不等於已經認證支援 Kubernetes v1.37。

- [Pod 網路 / CNI](https://kubernetes.io/docs/concepts/cluster-administration/addons/#networking-and-network-policy)：kubeadm 叢集必須安裝 CNI 後節點才會 Ready。當前本手冊範例為 Calico 3.33.0，官方資料明確支援 Kubernetes 1.35–1.37。
- [CoreDNS](kube-dns.md)：kubeadm 預設安裝 CoreDNS。歷史 kube-dns 檔案僅作背景，舊 YAML 不應重新應用。
- [metrics-server](metrics.md)：僅向 Metrics API 提供即時資源用量，非長期指標儲存系統。當前上游 0.9.0 仍註冊 `metrics.k8s.io/v1beta1`。
- [監控](monitor.md)：可評估 Prometheus 社群 `kube-prometheus-stack`，安裝前核對 chart、CRD 和 Kubernetes 支援範圍。
- [Cluster Autoscaler](cluster-autoscaler.md)：版本通常需與 Kubernetes control plane minor 對齊；截至 2026-10-05，上游尚無經核實的 Kubernetes 1.37 匹配發布/相容條目，本手冊不提供 v1.37 安裝命令。
- [Dashboard 狀態](dashboard.md)：Kubernetes Dashboard 已歸檔，不是可部署的當前元件；參見 Headlamp 專案。
- [GPU 工作負載](gpu.md)：NVIDIA GPU Operator 26.7.1 的 26.7 支援矩陣覆蓋 Kubernetes v1.33–v1.37，但仍應核對完整的平台組合。
- [日誌](logging.md)：Kubernetes 不會預設安裝集中式日誌後端或節點日誌代理，需按當前架構選擇並固定日誌元件。
- [Pod 出站 SNAT](ip-masq-agent.md)：masquerade 行為依賴 CNI/雲平台，不要照用舊版 beta 標籤或 `master` manifest。

本頁面過去列出的 Heapster、早期 kube-dns、Kubernetes Dashboard 安裝包及舊 chart 只保留為歷史背景。不要用舊儲存庫、舊映像檔或未固定版本的 `master` YAML 部署新叢集。

## 參考

- [Kubernetes Addons](https://kubernetes.io/docs/concepts/cluster-administration/addons/)
- [元件版本清單](../component-versions.md)
- [版本偏差與升級策略](../upgrade.md)
