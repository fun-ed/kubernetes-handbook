# kube-controller-manager

`kube-controller-manager` 執行內建控制器，這些控制器會觀察 Kubernetes API 物件，並協調實際狀態逐步符合期望狀態。控制器會管理 Deployment、Job、Node、ServiceAccount 及 PersistentVolume 等資源。控制器實際行為取決於已啟用的控制器、設定及叢集已安裝的資源；不要假設每種 API 資源在所有部署中都有控制器執行。

依據供應商及叢集架構，雲端整合也可能由獨立的 `cloud-controller-manager` 執行，負責管理雲端專屬的 Node、路由或負載平衡器資源。請遵循叢集發行版及雲端服務供應商支援的設定，不要在執行中的叢集自行新增或移除控制器旗標。

## 設定與高可用性

Controller-manager 命令列旗標及設定欄位會隨 Kubernetes 版本變動。對於 kubeadm 管理的控制平面，請檢查該 kubeadm 版本產生的 manifest 及相符參考文件。不要沿用包含已移除旗標（例如 `--enable-dynamic-provisioning` 或 `--feature-gates=AllAlpha=true`）的舊命令。

高可用設定會使用 leader election，讓多個執行個體中只有目前的主節點主動執行控制工作。資源鎖及啟動設定由叢集發行版管理；現代設定使用 Lease 協調。請遵循目標版本的控制平面高可用程序，不要手動修改 leader-election 註解。

## 指標與安全服務

舊版在連接埠 `10252` 透過未驗證 HTTP 存取指標的範例已過時。上游 controller-manager 的安全服務端點使用 HTTPS，並採用驗證及授權；標準安全連接埠為 `10257`，但實際位址、憑證及存取政策取決於部署設定。不要將控制平面端點公開至公用網路，也不要為了抓取指標而停用驗證。請使用叢集文件指定的監控整合方式，並僅授予必要的指標存取權限。

## Node 生命週期

Node 監控間隔、驅逐行為及容忍度預設值由控制平面設定，且可能因版本與叢集拓樸而不同。請勿依賴固定的區域速率或複製控制器旗標；請參閱目前的 [Node 狀態及驅逐文件](https://kubernetes.io/docs/concepts/architecture/nodes/)與目標 v1.37.1 部署的命令列參考。

## 參考文件

- [Kubernetes 控制器](https://kubernetes.io/docs/concepts/architecture/controller/)
- [kube-controller-manager v1.37.1 命令列參考](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-controller-manager/)
- [Cloud Controller Manager](https://kubernetes.io/docs/concepts/architecture/cloud-controller/)
- [高可用叢集](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)

先前的指標輸出、啟動旗標及 Node 驅逐細節已保存在[歷史歸檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/concepts/components/controller-manager-legacy-zh-TW.md)。
