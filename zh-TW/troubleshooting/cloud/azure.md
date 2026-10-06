# Azure／AKS 排錯

本頁以 Kubernetes v1.36／v1.37 為基準，整理可透過 Kubernetes API 與受支援 Azure 工具進行的唯讀初查。AKS 託管控制平面、AKS 節點、使用外部 Azure Cloud Controller Manager 的自管叢集，其元件與可存取日誌各不相同；請勿將一種部署方式的 Pod 名稱、標籤、Cloud Provider 設定或修復步驟套用至另一種環境。

舊版 Azure in-tree cloud provider、ServiceNodeExclusion alpha feature gate、舊式 Service Principal 憑證命令與舊 AKS 隧道／Periscope 操作已移至[歷史封存](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/zh-TW/troubleshooting/cloud/azure.md)。該檔僅供追溯，不是目前的修復流程。

## LoadBalancer Service 一直 Pending 或無法連線

先檢查 Service 的事件、位址、連接埠與流量政策；以下命令只讀取 Kubernetes API：

```bash
NAMESPACE='<namespace>'
SERVICE='<service-name>'
kubectl describe service "$SERVICE" -n "$NAMESPACE"
kubectl get service "$SERVICE" -n "$NAMESPACE" -o yaml
kubectl get endpointslices -n "$NAMESPACE" -l "kubernetes.io/service-name=$SERVICE" -o wide
kubectl get pods -n "$NAMESPACE" -o wide
```

若沒有可用的 EndpointSlice 後端，先檢查 Service selector、Pod readiness 與 targetPort；若有後端但外部仍無法連線，核對 AKS Load Balancer SKU／前端 IP、探測狀態、NSG／路由及所用流量政策，並分別從叢集內與外部用戶端測試。`externalTrafficPolicy: Local` 等設定會影響節點是否有本機就緒端點及探測結果；不要只憑單一 NodePort 測試判定整個 Load Balancer 故障。依 AKS 叢集版本查看 Azure 控制平面事件與診斷資料；託管控制平面日誌不一定能透過 `kubectl logs kube-controller-manager` 存取。

AKS 當前負載平衡器設定與排錯請依 [Azure Kubernetes Service 文件](https://learn.microsoft.com/azure/aks/configure-load-balancer-standard)及[AKS 疑難排解](https://learn.microsoft.com/azure/aks/troubleshooting)核對。不要直接編輯雲端 NSG、路由表或負載平衡器作為排錯捷徑；先確認叢集／Service 設定及組織變更流程。

## Pod 到 Pod、Service 或 Azure 資源的連線異常

```bash
kubectl get nodes -o wide
kubectl -n kube-system get pods -o wide
kubectl get networkpolicies -A
kubectl get services -A
kubectl get endpointslices -A
```

比對故障 Pod 與目的端的 Node、Pod IP、Service 連接埠及相關 NetworkPolicy。AKS 網路模式、CNI、Pod／Service CIDR 和網路外掛版本會改變封包路徑；透過獲准的節點管理通道檢查相應 CNI 日誌與 Azure 網路診斷資料。不要套用舊版 Azure CNI/kubenet 假設、手動新增 Pod CIDR 路由或停用主機防火牆。

## Node 未註冊、NotReady 或雲端初始化未完成

```bash
kubectl get nodes -o wide
kubectl describe node '<node-name>'
kubectl get events -A --sort-by=.metadata.creationTimestamp
```

檢查 Node Conditions、taint 和 Events，並依叢集管理方式查閱 AKS 節點健康／升級狀態；自管叢集則透過核准的節點管理通道檢查 kubelet、CRI runtime 與外部 cloud-controller-manager 的日誌和權限。`node.cloudprovider.kubernetes.io/uninitialized` taint 表示雲端初始化尚未完成，但不代表應手動移除 taint 或任意新增 toleration。託管控制平面不一定公開 CCM Pod；不要使用舊版 selector 尋找假設存在的元件。

## AKS GPU Node 未回報 `nvidia.com/gpu`

```bash
kubectl describe node '<gpu-node>'
kubectl get pods -A -o wide
```

確認 `Capacity`／`Allocatable`、Node Pool VM SKU／OS、GPU 管理模式，以及 AKS 管理的驅動或所選 GPU Operator／Device Plugin 狀態。依 [AKS NVIDIA GPU 指南](https://learn.microsoft.com/azure/aks/use-nvidia-gpu)與本手冊[GPU 工作負載指南](../../setup/addon-list/gpu.md)逐一比對，不要部署舊版裝置外掛清單或只替換映像檔標籤。舊版 `extensions/v1beta1` DaemonSet 範例另存於[歷史封存](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/troubleshooting/cloud/azure-gpu-device-plugin.md)，不可套用。

## 憑證、配額及 Azure 控制平面錯誤

使用 AKS 時，先從 Azure Portal／Azure CLI 的叢集 Activity log、診斷設定與支援工具查看失敗操作、配額及身分識別錯誤。自管 Azure cloud-controller-manager／CSI driver 則檢查該元件使用的受控識別或工作負載身分、最小必要 RBAC、API 錯誤碼及資源提供者配額。不要在命令列、日誌或 YAML 中輸入／輸出 client secret、SAS token 或 bearer token；憑證輪替依 Microsoft 當前身分識別文件及組織密鑰管理程序執行。

## 持久卷問題

先檢查 PVC、PV、StorageClass 與 CSI 元件事件；Azure Disk／Azure Files 的當前故障排查見 [Azure Disk CSI](../pv/azuredisk.md)及 [Azure Files CSI](../pv/azurefile.md)指南。AKS 儲存類型與雲端操作還須核對當前的 [AKS 疑難排解文件](https://learn.microsoft.com/azure/aks/troubleshooting)。

## 參考文件

- [AKS 疑難排解](https://learn.microsoft.com/azure/aks/troubleshooting)
- [AKS Standard Load Balancer](https://learn.microsoft.com/azure/aks/configure-load-balancer-standard)
- [AKS NVIDIA GPU 工作負載](https://learn.microsoft.com/azure/aks/use-nvidia-gpu)
- [Kubernetes Service](https://kubernetes.io/docs/concepts/services-networking/service/)
