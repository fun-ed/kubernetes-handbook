# Kubernetes 升級與版本偏差

本頁以 Kubernetes v1.37.1（截至 2026-10-05）為當前手冊版本。具體升級前，逐項檢查官方[版本偏差策略](https://kubernetes.io/releases/version-skew-policy/)、[kubeadm 升級指南](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/)和所用發行版或雲廠商的支援政策。

## v1.37 叢集的元件版本約束

版本偏差按 **minor** 版本計算，不等於“任意較新/較舊版本都相容”。同一元件也應儘量保持相同 patch 版本。

- **kube-apiserver：** 高可用叢集中各 API server 最多相差一個 minor 版本，例如升級期間可暫時同時執行 v1.36 和 v1.37。
- **kubelet：** 不得比任何 API server 新；單一 v1.37 API server 時，最多可舊三個 minor（v1.34–v1.37）。如果 API server 混跑 v1.36/v1.37，kubelet 不得高於較舊的 v1.36 API server。
- **kube-proxy：** 不得比任何 API server 新，最多可比 API server 舊三個 minor；它與所在節點 kubelet 也最多相差三個 minor。高可用滾動升級時同時滿足兩項限制。
- **kube-controller-manager、kube-scheduler、cloud-controller-manager：** 不得比它們通訊的 API server 新，最多舊一個 minor。API server 混跑時不得高於其中最舊的 API server。
- **kubectl：** 通常允許比 API server 舊或新一個 minor；高可用 API server 混跑期間需遵守官方策略對混合版本的額外限制。

具體矩陣和邊界條件以[官方版本偏差策略](https://kubernetes.io/releases/version-skew-policy/)為準。kubeadm 有額外的工具版本規則，也必須遵守。

## 升級順序

Kubernetes 不支援跳過 minor 版本升級。逐 minor 完成升級，例如 v1.35 → v1.36 → v1.37；在每一跳中先把 control plane 升到目標 minor，再逐節點升級 kubelet。單控制平面叢集也不得跳級。

使用 kubeadm 的叢集按官方流程升級：

1. 閱讀目標版本的發行說明和 API 棄用指南；確認 admission webhook、CRD、operator 和應用可以處理新資源版本及欄位。
2. 把 kubeadm 的套件儲存庫切換到目標 minor 專屬的 `pkgs.k8s.io` 儲存庫，並按 kubeadm 升級文件操作。v1.37 套件儲存庫不是跨 minor 的滾動通道。
3. 高可用叢集按 kubeadm 官方流程逐臺升級 control-plane 節點。kubeadm 會在各節點一併升級該節點的 kube-apiserver、controller-manager 和 scheduler，並透過本地 API endpoint 操作；不需要等所有 API server 升完後再把這些靜態 Pod 作為獨立階段升級。外部部署的 cloud-controller-manager 及負載平衡/API endpoint 切換須按其獨立部署和雲廠商流程處理；涉及目標版本的遷移應等所有 API server 都已升級到目標版本後進行。
4. 每個節點升級 kubelet 前先 drain；按官方節點升級流程執行。不要把舊文件中的 kubelet 原地跨 minor 升級命令照搬到新版本。
5. 按各外掛上游說明單獨檢查並升級 CNI、CSI、CoreDNS 外部定製項和自定義擴充套件。kubeadm 不會替所有外掛自動升級。
6. 檢查節點、系統 Pod、API discovery、控制器與應用，再解除維護。

升級 etcd、發行版核心、containerd 或雲 provider 時，還需各自使用對應專案的相容與備份恢復流程。對 etcd 等持久化資料先驗證可恢復備份，不要把叢集升級當作可逆操作。

## Kubernetes v1.37 的注意事項

- kubeadm v1.37.1 預設使用 etcd 3.7.0、CoreDNS 1.14.6 和 pause 3.10.2。這些是 kubeadm 預設值；不要僅因外部專案有更新版本就直接替換映像檔。
- kubelet 的 `KubeletCgroupDriverFromCRI` 在執行時支援 `RuntimeConfig` 時可自動讀取 cgroup driver；v1.37 對舊 runtime 的相容回復仍存在，移除已延後至 v1.38。新部署應優先讓 containerd/CRI-O 與 kubelet 使用 `systemd`，不要依賴舊式回復行為。
- kube-proxy 的 IPVS 模式已棄用；nftables 模式已 GA，但 v1.37 並非預設模式。切換代理模式須單獨評估核心、規則管理及回復策略。
- `metrics.k8s.io/v1` 的 API 穩定狀態不表示所有 metrics API 後端都已實現該版本。使用 metrics-server 時先檢查其相容矩陣和 APIService discovery；例如 v0.9.0 上游 manifest 註冊 `metrics.k8s.io/v1beta1`。

## API 與 feature gate 檢查

- 對每個升級源版本，按官方[棄用指南](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)檢查被移除的 API。API 遷移可能需要調整 schema、selector、欄位型別或 webhook，而不只是替換 API 字串。
- 按叢集實際版本和元件檢視 [Feature Gates](feature-gates.md) 及[官方表格](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/)。不要繼續設定已經 GA 或已移除的 gate；Alpha/Beta gate 的啟用範圍、預設值可能每個 minor 改變。
- 查閱 [Kubernetes v1.37.1 發行說明](https://raw.githubusercontent.com/kubernetes/kubernetes/v1.37.1/CHANGELOG/CHANGELOG-1.37.md)及[遷移說明](kubernetes-v1.37.md)，逐項檢查應用和外掛行為變化。

## 參考

- [Kubernetes version and version-skew support policy](https://kubernetes.io/releases/version-skew-policy/)
- [升級 Kubernetes 叢集（kubeadm）](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/)
- [安裝 kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)
- [API deprecation guide](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)
- [Feature Gates](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/)