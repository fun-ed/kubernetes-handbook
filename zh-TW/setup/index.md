# 搭建 Kubernetes 叢集

本手冊的部署基線為 **Kubernetes v1.37.1**，版本資料截至 2026-10-05。版本快照記錄 v1.37.1 於 2026-09-15 發布；升級與正式環境變更前，請重新核對 [Kubernetes 發布週期](https://kubernetes.io/releases/)與發行說明，並閱讀[現行元件與範例版本核對](component-current-status.md)中的最新查核結果。

- **新建叢集：** [使用 kubeadm 部署 v1.37.1](cluster/kubeadm.md)
- **從舊版本遷移：** [Kubernetes v1.37 遷移說明](kubernetes-v1.37.md)
- **相容版本與上游來源：** [元件版本清單](component-versions.md)
- **現行版本與範例核對：** [元件與 sample YAML 版本核對](component-current-status.md)
- **發行版部署：** [k0s](cluster/k0s.md)與 [RKE2](cluster/rke2.md)。使用發行版自身的 Kubernetes 與相依元件組合，不直接套用 kubeadm 的元件版本。
- **版本偏差與升級順序：** [升級和版本偏差](upgrade.md)
- **功能門控：** [Feature Gates](feature-gates.md)

## Kubernetes v1.37.1 的 kubeadm 預設依賴

下列映像檔版本來自 Kubernetes v1.37.1 的 kubeadm 預設值，並非這些專案在截稿日的最新發布。升級或替換它們需先檢查上游相容性，不能把“最新版本”直接替換進現有叢集。

| 元件 | kubeadm v1.37.1 預設版本 | 說明 |
| --- | --- | --- |
| etcd | 3.7.0 | kubeadm 使用的預設 etcd 映像檔 |
| CoreDNS | 1.14.6 | kubeadm 使用的預設 DNS 映像檔 |
| pause | 3.10.2 | Pod sandbox 映像檔；containerd/CRI-O 設定需匹配 |

[Kubernetes v1.37.1 kubeadm 映像檔預設值](https://raw.githubusercontent.com/kubernetes/kubernetes/v1.37.1/cmd/kubeadm/app/constants/constants.go)；最新穩定元件與單獨維護的版本相容證據見[元件版本清單](component-versions.md)。

## 元件邊界

- Kubernetes 的 Debian/RPM 套件使用 `pkgs.k8s.io` 的 **v1.37 專屬**套件儲存庫；不要再使用已凍結的 `apt.kubernetes.io` 或 `yum.kubernetes.io`。
- Kubernetes 需要實作 CRI v1 的容器執行環境。版本快照記錄 containerd 2.4.1；在 systemd/cgroup v2 主機上使用 systemd cgroup driver。Docker Engine 不能直接作為 CRI runtime；若有遷移需求，先閱讀官方 [Dockershim 遷移指南](https://kubernetes.io/docs/tasks/administer-cluster/migrating-from-dockershim/)。
- kubeadm 不會替你安裝 Pod 網路。CNI provider 必須單獨選型並安裝；例如 Calico 3.33.0 的上游相容資料明確列出 Kubernetes 1.35–1.37。Pod CIDR 必須與所選 provider 設定一致，且不能與節點網路重疊。
- CNI 外掛、`crictl`、監控元件、Helm chart 和雲端供應商的自動擴縮器有各自的發布週期，不能把 Kubernetes 原始碼中的相依版本誤當成整套叢集的自動安裝版本。
- 即使 Kubernetes 將 `metrics.k8s.io/v1` 標為 GA，聚合 API 仍須由實際後端提供相應版本。上游 metrics-server 0.9.0 manifest 註冊的是 `metrics.k8s.io/v1beta1`，應以所部署後端的 discovery 結果為準。

## 舊教程歸檔

針對舊 Kubernetes 版本、已移除 API 或已退役元件的安裝教程與清單已移出當前導航。歸檔目錄保留原始內容，僅供歷史參考；其中的命令和資源不能用於 Kubernetes v1.36/v1.37 部署。

檢視[歸檔索引](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/index.md)。當前自建叢集入口是 [kubeadm v1.37.1 指南](cluster/kubeadm.md)；雲託管 Kubernetes 請使用雲廠商針對目標版本的官方文件。