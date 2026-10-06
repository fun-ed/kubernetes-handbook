# PV 排錯

本章介紹持久化儲存異常（PV、PVC、StorageClass等）的排錯方法。

一般來說，無論 PV 處於什麼異常狀態，都可以執行 `kubectl describe pv/pvc <pod-name>` 命令來檢視當前 PV 的事件。這些事件通常都會有助於排查 PV 或 PVC 發生的問題。

```bash
kubectl get pv
kubectl get pvc
kubectl get sc

kubectl describe pv <pv-name>
kubectl describe pvc <pvc-name>
kubectl describe sc <storage-class-name>
```

## 儲存資源洩漏問題（v1.33+）

從 Kubernetes v1.33 開始，系統提供了防止 PersistentVolume 資源洩漏的保護機制。以下是相關的排錯方法：

### 檢查 PV Finalizer

如果 PV 刪除時卡在 Terminating 狀態，檢查是否存在防洩漏 finalizer：

```bash
kubectl get pv <pv-name> -o yaml | grep finalizers -A 5
```

正常的 CSI 動態 PV 應該包含：
```yaml
finalizers:
- kubernetes.io/pv-protection
- external-provisioner.volume.kubernetes.io/finalizer
```

### 驗證 CSI External-Provisioner 版本

確保 CSI external-provisioner 版本為 v5.0.1 或更高：

```bash
kubectl get pods -n kube-system | grep provisioner
kubectl describe pod <csi-provisioner-pod> -n kube-system | grep Image
```

### 排查儲存後端連線問題

如果 PV 刪除掛起，可能是儲存後端無法存取：

```bash
# 检查 CSI 驱动程序日志
kubectl logs <csi-provisioner-pod> -n kube-system

# 检查存储后端状态
kubectl get volumeattachments
kubectl describe volumeattachment <attachment-name>
```

### 強制清理洩漏的 PV

**注意：僅在確認儲存後端資源已手動清理時使用**

```bash
# 移除防泄漏 finalizer
kubectl patch pv <pv-name> -p '{"metadata":{"finalizers":null}}'

# 或者编辑 PV 移除特定 finalizer
kubectl edit pv <pv-name>
```

### 監控儲存資源使用

定期檢查是否存在孤立的儲存資源：

```bash
# 列出所有 PV 及其状态
kubectl get pv -o wide

# 检查未绑定的 PV
kubectl get pv | grep Available

# 查看存储类配置
kubectl get storageclass -o yaml
```
