# kubeadm

`kubeadm` 是建置符合 Kubernetes 最佳實踐的叢集的工具，負責引導控制平面、設定基礎元件，並生成 Node 加入叢集所需的憑證與命令。具體安裝步驟和約束取決於作業系統、CRI 執行時與網路外掛；Kubernetes v1.37.1 叢集請使用對應版本的 [kubeadm 安裝與管理指南](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/)。

## 元件與叢集初始化

`kubeadm` 叢集需要相容的 CRI 執行時、kubelet、kubeadm、控制平面元件以及一個能執行 NetworkPolicy 的 CNI 網路外掛。kubeadm 會檢查環境並部署控制平面靜態 Pod；叢集 DNS 通常由 CoreDNS 提供。CNI 具體設定由網路外掛負責。

不要套用本頁舊版的 Docker Engine/Frakti、手寫 CNI bridge 設定、未固定的 Flannel/Weave 清單、Calico v3.1 安裝 URL 或 `--kubernetes-version stable` 範例。網路外掛選擇和 Pod CIDR 必須與發行版及叢集網路規劃相符。

## Node 加入

叢集初始化成功後，kubeadm 會輸出加入命令。只在目標 Node 上使用該叢集當前生成的命令，並按官方指南保護臨時 bootstrap token 與發現憑證；不要從 kubeadm token 列表中篩選後複用長期憑證。

## 重置與移除

`kubeadm reset` 會更改本機叢集狀態，並不保證清理 CNI、使用者資料、持久卷、雲資源或其他叢集外資源。執行前應確認目標節點、備份需求及發行版清理流程；不要把它當作通用的叢集解除安裝命令。

* [kubeadm 安裝叢集](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)
* [kubeadm 參考文件](https://kubernetes.io/docs/reference/setup-tools/kubeadm/)
* [kubeadm 官方原始碼](https://github.com/kubernetes/kubernetes/tree/v1.37.1/cmd/kubeadm)
