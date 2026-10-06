# Azure Disk CSI 排錯

Kubernetes v1.36／v1.37 的 Azure Disk 應透過 Azure Disk CSI driver 使用；舊版 `kubernetes.io/azure-disk` in-tree StorageClass、aks-engine 固定值、AzureRM 命令和舊核心事件案例已移至[歷史封存](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/zh-TW/troubleshooting/pv/azuredisk.md)，不可作為目前設定或復原指令。

AKS 管理的驅動和自管 CSI 安裝方式不同。先依叢集發行版和 [AKS Azure Disk CSI 文件](https://learn.microsoft.com/azure/aks/create-volume-azure-disk)確認驅動狀態、StorageClass 和支援的磁碟功能；不要將另一版本 StorageClass 的參數直接套用至目前叢集。

## PVC 無法綁定或動態配置失敗

```bash
NAMESPACE='<namespace>'
PVC='<pvc-name>'
kubectl get pvc "$PVC" -n "$NAMESPACE" -o wide
kubectl describe pvc "$PVC" -n "$NAMESPACE"
kubectl get storageclass
kubectl get csidrivers
kubectl get events -n "$NAMESPACE" --sort-by=.metadata.creationTimestamp
```

依 Events 檢查 StorageClass 的 CSI provisioner、參數、區域／可用區、請求容量、存取模式、訂閱配額及驅動身分權限。先確認 PVC 與 Pod 位於預期命名空間，並依供應商文件核實目前 AKS 叢集支援的磁碟類型和拓撲限制。

## Pod 掛載失敗或多次重試

```bash
kubectl describe pod '<pod-name>' -n "$NAMESPACE"
kubectl describe pvc "$PVC" -n "$NAMESPACE"
kubectl get pv
kubectl get volumeattachment
kubectl get csinodes
kubectl -n kube-system get pods -o wide
```

查看 Pod／PVC Events、PV `nodeAffinity`、`VolumeAttachment` 狀態及目標 Node 的 CSI Node Pod 狀態。若需日誌，先依發行版找出 Azure Disk CSI controller 與 node Pod，再讀取具體容器日誌；AKS 管理的附加元件名稱和日誌存取方式可能不同。核對磁碟目前附加節點、拓撲、節點可附加磁碟上限、磁碟狀態與 Azure API 錯誤；不要因一次 `FailedMount` 就重新啟動 VM、手動卸載磁碟、刪除 `VolumeAttachment` 或直接修改雲端資源。

## PVC／PV 刪除或 Azure 磁碟仍處於附加狀態

刪除宣告前，確認沒有 Pod 使用該 PVC，並依 PV 的 reclaim policy 與組織備份／保留流程確認資料處置。若 CSI 仍回報掛載或分離中，收集 PVC/PV、Pod、VolumeAttachment、CSI 日誌與 Azure 錯誤碼，交由平台管理者按相應 AKS／驅動版本流程處理。不要強制刪除 finalizer、PV 或磁碟資源；此操作可能造成資料遺失或孤兒磁碟。

## 參考文件

- [AKS Azure Disk CSI 驅動與動態配置](https://learn.microsoft.com/azure/aks/create-volume-azure-disk)
- [Kubernetes CSI Volume](https://kubernetes.io/docs/concepts/storage/volumes/#csi)
- [CSI VolumeAttachment API](https://kubernetes.io/docs/reference/kubernetes-api/config-and-storage-resources/volume-attachment-v1/)
