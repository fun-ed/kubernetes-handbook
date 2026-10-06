# 大規模 Kubernetes 叢集

Kubernetes 官方大規模叢集指南指出，v1.37 的設計目標包括不超過 5,000 個節點、每個節點不超過 110 個 Pod、全叢集不超過 150,000 個 Pod 與 300,000 個容器。這些是官方規模邊界，並非對任意雲端平台、CNI、工作負載或擴充元件組合的效能保證。請參閱[官方大規模叢集指南](https://kubernetes.io/docs/setup/best-practices/cluster-large/)並針對目標環境進行容量測試。

## 規劃與擴充

- 先定義工作負載與故障領域，量測 API Server 請求負載、etcd 延遲/磁碟、節點資源、Pod 密度、DNS、網路、儲存及日誌/監控負載。擴充前設定批次和速率限制，避免雲端供應商配額、執行個體建立限速或控制平面瞬間負載成為瓶頸。
- 控制平面需跨故障區域提供備援 API endpoint；官方指南建議每個故障區域至少有一個控制平面執行個體。先垂直擴充控制平面，再依觀察到的瓶頸決定是否橫向增加執行個體。負載平衡器、健康檢查、跨區流量成本與故障切換須依平台個別驗證。
- 持續監控並調整擴充元件資源：每節點執行的 DaemonSet、單一副本或分區級服務、可水平擴充的控制器有不同容量模型。可使用 VPA recommender 等工具輔助估算請求與限制，但應審查建議並逐步發布。
- 為 CoreDNS、metrics-server 等叢集關鍵擴充元件評估合適的 PriorityClass；優先權不會創造節點容量，仍須預留資源並測試搶占影響。

## etcd 與事件負載

大規模叢集可評估將 Event 物件寫入專用 etcd 執行個體，以隔離事件負載。這需要額外 etcd 節點與 API Server 設定，並非通用預設最佳化；請先量測事件速率、儲存及 API Server 負載，再依官方 etcd 操作指南設計備份、監控、TLS 與復原流程。kubeadm v1.37.1 的預設 etcd 3.7.0 僅是 kubeadm 固定值，不等同於大規模叢集設計或 etcd 上游最新版本。

## 容量驗證

在隔離且接近正式環境拓樸的環境中逐步增加節點與負載，記錄 Kubernetes/runtime/CNI 版本、節點規格、外掛、請求速率、資源使用量、錯誤率及復原行為。驗證雲端配額、API Server 與 etcd 延遲、控制平面故障切換、DNS、網路和儲存；單次基準測試結果不構成容量承諾。效能參數應依 v1.37 官方指南、發行版說明與實際量測調整，請勿複製舊版固定 kube-apiserver/kubelet 參數或 Docker 專用設定。

本章早期資料包含 etcd 3.2/3.1、Docker 專用參數、已移除的擴充元件路徑、過期效能數據與未經驗證的通用 API Server 參數，已移至[歷史封存](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/zh-TW/practice/big-cluster.md)。請勿將封存中的命令、資源片段或數值作為目前的容量設定。
