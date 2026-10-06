# 叢集高可用

本頁概述 Kubernetes 控制平面高可用性（HA）的目前設計要點，目標為 Kubernetes v1.37.1。部署應採用 kubeadm v1.37 文件或發行版維護的流程；本頁不是完整安裝手冊，也不構成正式環境認證。

## 控制平面拓樸

kubeadm HA 支援 stacked-etcd（每個控制平面節點執行 etcd 成員）與 external-etcd 兩種拓樸。兩者都需要規劃穩定且具備備援的 API server endpoint（通常由負載平衡器提供）、控制平面節點故障領域、API server 健康檢查、憑證生命週期與復原方案。外部負載平衡器、DNS、網路連線及防火牆是平台前置條件，應由相應團隊獨立設定與驗證。

選擇拓樸時，應依故障領域、維運能力、節點數量、資源預算與 etcd 延遲評估。多個 API server 不會自動提供高可用入口；用戶端、負載平衡器與控制平面節點都必須能在故障時切換。請勿將控制平面服務位址、憑證或測試 IP 當成通用設定。

## etcd 與備份

- kubeadm v1.37.1 的 etcd 預設映像檔為 **3.7.0**；這是 Kubernetes 固定值，不是上游最新版本或第三方相容性聲明。
- stacked-etcd 將 etcd 成員與控制平面節點置於相同故障領域；external-etcd 將資料層與控制平面分離，但會增加獨立節點、網路與憑證管理需求。
- 維持奇數個 etcd 成員，並為選舉和多數派 quorum 保留足夠資源與低延遲網路。失去多數派時，無法只靠增加 API server 恢復 etcd 寫入能力。
- 採用受支援的快照與復原流程，保護快照、加密傳輸，並定期在隔離環境演練復原。備份成功不代表資料一致性或復原能力已獲驗證。

復原與升級須遵循 etcd 及叢集發行版指定的版本順序；不可只替換映像檔、複製舊憑證指令碼或跨版本重用舊設定。

## kubeadm 部署前檢查

1. 選擇並測試可靠的 `controlPlaneEndpoint`，確認所有控制平面與工作節點都可連線。
2. 依 [Kubernetes v1.37 kubeadm HA 指南](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)準備節點、CRI v1 執行階段、cgroup driver、網路與負載平衡器。
3. 使用與 kubeadm v1.37 相符的 `kubeadm.k8s.io/v1beta4` 設定格式；逐項驗證憑證散布、SAN、RBAC、API server 健康檢查及控制平面 join 順序。共享憑證金鑰應透過安全管道傳遞並設定有效期限。
4. 部署後檢查 etcd 成員健康、API endpoint 故障切換、控制平面元件狀態、DNS、CNI、持續性儲存與告警；在維護時段演練節點替換及 etcd 復原。

詳細流程與拓樸清單請參閱 [kubeadm 高可用叢集](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)、[etcd 叢集操作指南](https://etcd.io/docs/v3.7/op-guide/)及本手冊[元件版本矩陣](../setup/component-versions.md)。

本頁舊版的 cfssl R1.2 下載、手動 etcd 3.1 Pod/systemd 設定、舊 kubeadm `MasterConfiguration` 與 `kubeadm alpha phase` 操作已移至[歷史封存](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/zh-TW/practice/ha.md)。請勿執行封存中的指令碼或清單。
