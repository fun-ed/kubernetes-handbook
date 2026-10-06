# Azure Files CSI 排錯

Kubernetes v1.36／v1.37 的 Azure Files 應透過 Azure Files CSI driver 使用；舊版 `kubernetes.io/azure-file` in-tree StorageClass、過時的 RBAC 範例與固定權限／Windows 錯誤記錄已移至[歷史封存](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/zh-TW/troubleshooting/pv/azurefile.md)，不可作為目前設定或修復步驟。

AKS 管理的驅動和自管 CSI 安裝方式不同。先依 [AKS Azure Files CSI 文件](https://learn.microsoft.com/azure/aks/create-volume-azure-files)確認驅動、StorageClass、SMB/NFS 協定、帳戶網路和驗證方式；掛載選項與身分驗證應符合所用協定和驅動版本，不要將舊版 `0777` 或明文儲存帳戶金鑰範例複製到新叢集。

## PVC 無法綁定或檔案共享配置失敗

```bash
NAMESPACE='<namespace>'
PVC='<pvc-name>'
kubectl get pvc "$PVC" -n "$NAMESPACE" -o wide
kubectl describe pvc "$PVC" -n "$NAMESPACE"
kubectl get storageclass
kubectl get csidrivers
kubectl get events -n "$NAMESPACE" --sort-by=.metadata.creationTimestamp
```

檢查 StorageClass 的 CSI provisioner 與參數、帳戶／共享配額、訂閱區域、網路防火牆與驅動身分權限。不要因錯誤訊息泛稱找不到儲存帳戶，就為所有 ServiceAccount 授予建立 Secret 的權限。

## Pod 掛載失敗或掛載後無法讀寫

```bash
kubectl describe pod '<pod-name>' -n "$NAMESPACE"
kubectl describe pvc "$PVC" -n "$NAMESPACE"
kubectl get pv
kubectl get volumeattachment
kubectl get csinodes
kubectl -n kube-system get pods -o wide
```

依 Pod/PVC Events、PV、VolumeAttachment 與目標 Node CSI Pod 日誌區分驗證失敗、SMB/NFS 網路連線、DNS、協定／掛載選項或 POSIX 權限問題。若需查看 CSI 日誌，先依發行版找出實際 Azure Files CSI controller/node Pod 及容器名稱；AKS 託管元件名稱或日誌存取方式可能不同。確認 Node 到儲存端點的 DNS、連接埠、防火牆／私有端點路由與目前使用的驗證方式。不要在日誌、命令列歷史或清單中暴露儲存帳戶金鑰、SAS token 或其他憑證。

SMB 掛載的 Unix 擁有者、模式與 `fsGroup` 行為取決於協定、CSI 驅動參數與儲存服務設定；不要只為避開 `Operation not permitted` 就以 root 執行容器、遞迴 `chown` 大型共享目錄，或放寬至 `0777`。先確認共享是否支援應用程式要求的語意，再依目前驅動文件選擇安全設定。

## 刪除 PVC 或共享失敗

先確認 Pod 已停止使用 PVC，並依 PV reclaim policy、備份和保留規定評估資料影響。若共享仍被掛載或 CSI 回報刪除錯誤，收集 PVC/PV、Pod、VolumeAttachment、CSI 日誌及 Azure 錯誤碼，依叢集發行版和驅動版本流程處理。不要強制移除 finalizer 或直接刪除雲端共享來繞過 CSI 狀態管理。

## 參考文件

- [AKS Azure Files CSI 驅動與動態配置](https://learn.microsoft.com/azure/aks/create-volume-azure-files)
- [AKS 儲存疑難排解](https://learn.microsoft.com/azure/aks/troubleshooting)
- [Kubernetes CSI Volume](https://kubernetes.io/docs/concepts/storage/volumes/#csi)
- [Kubernetes VolumeAttachment API](https://kubernetes.io/docs/reference/kubernetes-api/config-and-storage-resources/volume-attachment-v1/)
