# 叢集部署

## 自建叢集

需要自行管理 Linux control plane 和 worker 節點時，使用本儲存庫針對 Kubernetes v1.37.1 編寫的 [kubeadm 部署指南](kubeadm.md)。先核對[元件版本清單](../component-versions.md)、[版本偏差策略](../upgrade.md)和目標網路外掛官方相容矩陣。

kubeadm 用於建立最小可用叢集，不是基礎設施自動化平台。正式環境還需規劃控制平面的高可用端點、憑證備份、etcd 備份與還原、網路和防火牆、儲存、存取控制、監控、升級及災難復原。

本儲存庫也提供 [k0s](k0s.md)和 [RKE2](rke2.md)指南及固定版本的設定範例。它們是整合 Kubernetes、執行環境與附加元件的發行版。發行版本、內含的 Kubernetes 版本與預設元件組合須分別核對，不能只因發行版更新就認為已支援本書的 v1.37 基線。詳細版本與來源請參閱[現行元件與範例版本核對](../component-current-status.md)。

如使用其他叢集自動化工具，請核對其當前文件、目標 Kubernetes minor 的支援宣告及升級路徑。本目錄不再保留舊版叢集建立教程。歷史 Azure、Windows、LinuxKit、kOps、Kubespray 和其他部署流程見[歸檔索引](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/index.md)；歸檔步驟不適用於 Kubernetes v1.36/v1.37。

## 託管叢集

對於 GKE、EKS、AKS 等託管產品，使用對應雲廠商官方文件、支援的 Kubernetes 版本列表、升級說明和其受支援的網路/儲存外掛。不要執行歷史 kube-up、acs-engine 或本儲存庫舊指令碼來建立雲資源。

## Kubernetes 官方文件

- [kubeadm 安裝](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)
- [kubeadm 建立叢集](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)
- [生產環境部署工具](https://kubernetes.io/docs/setup/production-environment/tools/)
- [叢集高可用](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)
