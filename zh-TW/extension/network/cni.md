# CNI 與本機網路實驗

CNI（Container Network Interface）定義容器執行環境呼叫網路外掛的介面與設定格式；它本身不是完整的 Kubernetes Pod 網路實作。Kubernetes v1.37.1 源碼固定 CNI plugins v1.9.1 為依賴版本，但這不代表 Kubernetes 會自動安裝網路，也不代表每個 CNI provider 都已獲 v1.37 認證。叢集必須依發行版和所選 provider 的版本化文件設定單一主 CNI、IPAM、CIDR、路由與網路策略。

舊版本機實驗包含 CNI 0.3.x 範例、namespace/bridge 操作及主機網路變更命令，已移至[封存原始實驗](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/zh-TW/extension/network/cni.md)；不要將其套用到目前叢集。

參考：[Kubernetes 網路模型](https://kubernetes.io/docs/concepts/services-networking/)、[CNI plugins v1.9.1 release](https://github.com/containernetworking/plugins/releases/tag/v1.9.1)、[目前 CNI 版本與限制](README.md)。
