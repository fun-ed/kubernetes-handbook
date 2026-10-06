# PV 排錯

先確認 PVC 所在 Namespace、Pod、PV 與 StorageClass，再從 Events 和 CSI 資源狀態定位問題。舊版指南中檢查特定 external-provisioner 映像檔版本及移除 PV finalizer 的指令已移至[歷史封存](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/zh-TW/troubleshooting/pv/README.md)；不要將強制移除 finalizer 當作一般清理步驟。

```bash
NAMESPACE='<namespace>'
PVC='<pvc-name>'
kubectl get pvc "$PVC" -n "$NAMESPACE" -o wide
kubectl describe pvc "$PVC" -n "$NAMESPACE"
kubectl get pv -o wide
kubectl get storageclass
kubectl get csidrivers
kubectl get events -n "$NAMESPACE" --sort-by=.metadata.creationTimestamp
```

若 PVC 未綁定，依 Events 檢查 StorageClass、CSI provisioner、容量、拓撲、配額與後端權限。若卷掛載或解除掛載失敗，檢查相關 Pod／Node Events、PV、`VolumeAttachment`、`CSINode` 及驅動日誌：

```bash
kubectl describe pv '<pv-name>'
kubectl get volumeattachments
kubectl get csinodes
kubectl -n kube-system get pods -o wide
```

CSI controller/node Pod 名稱、容器和 Namespace 由驅動及叢集發行版決定；先找出實際物件，再讀取對應日誌。PV 停留在 `Terminating` 時，檢查被引用的 PVC/Pod、reclaim policy、驅動健康狀態及 finalizer 對應的清理責任者。CSI deletion finalizer 可用來等待外部後端清理；不要手動清除 finalizer、刪除 `VolumeAttachment`，或在未核實資料保留政策時刪除雲端卷。若後端無法使用，遵循驅動／雲服務商的復原流程，並保留事件、物件 YAML 和日誌供支援人員診斷。

Azure 專項流程見 [Azure Disk CSI](azuredisk.md) 與 [Azure Files CSI](azurefile.md)。Kubernetes CSI Volume 概念見[官方文件](https://kubernetes.io/docs/concepts/storage/volumes/#csi)；最終處置應遵循所用驅動與發行版的受支援流程。
