# Kubernetes 備份與恢復

[Velero](https://velero.io/) 可備份、恢復和遷移 Kubernetes API 物件，並按所選 provider/plugin 及儲存能力保護持久卷資料。它不是 etcd 災備的替代品，也不能保證應用一致性。

> **當前版本（2026-10-05）**：Velero v1.18.4 是本手冊資料截點前最新穩定版：[官方釋出頁](https://github.com/velero-io/velero/releases/tag/v1.18.4)。本次沒有找到覆蓋 Kubernetes v1.37.1 的明確相容宣告；部署前核對 Velero 支援矩陣與所選 object-store、CSI/snapshot 外掛的相容版本。

## 部署前設計

- 為 Velero server、CLI 和每個 provider/plugin 固定受支援版本，並驗證 release checksum/signature。
- 使用受支援的物件儲存後端和最小權限身分。provider 外掛、storage location 引數、snapshot API 與憑證方式各不相同；按[官方安裝文件](https://velero.io/docs/v1.18/)和外掛文件確定命令，不能把舊 Azure recipe 當通用設定。
- 按恢復目標設計 API 物件、PV 資料和 etcd 的獨立備份。資料庫等有狀態應用需要應用一致性鉤子、原生複製或經驗證的 volume snapshot 流程。
- 加密並限制備份庫及憑證的存取，監控備份失效與保留策略，並定期在隔離環境演練恢復。

舊 Azure 範例會建立 Contributor 權限的 service principal、在本地寫入明文憑證，並使用過時的 provider/設定引數；它不是安全的 Velero v1.18 部署指南，**不要照抄或執行**。請從當前 Azure 外掛文件重新設計身分與儲存設定。

## 建立並檢查備份

先根據所選 provider 設定並驗證 BackupStorageLocation 和必要的 VolumeSnapshotLocation，再檢視 CLI 與叢集狀態：

```bash
velero version
velero backup-location get
velero plugin get
```

建立一次性備份，範圍應按恢復需求選擇：

```bash
velero backup create pre-upgrade-2026-10-05 \
  --include-namespaces production
velero backup describe pre-upgrade-2026-10-05 --details
velero backup logs pre-upgrade-2026-10-05
```

備份物件成功只表示所設定的操作完成，不證明應用資料一致或恢復可用。檢查失敗項、快照狀態、物件儲存內容及應用寫入行為。

## 定期備份

```bash
velero schedule create production-daily \
  --schedule="0 7 * * *" \
  --include-namespaces production \
  --ttl 720h
velero schedule get
```

按業務 RPO、保留要求和 storage cost 調整排程與 TTL。僅對必要 namespace 建立備份，避免把臨時憑證或無關測試資源無限期保留。

## 恢復與遷移

在恢復目標叢集先部署相容的 Velero server 與外掛，再核對 BackupStorageLocation 只讀狀態、目標 namespace、StorageClass、CRD 和外部依賴。恢復前確認不會覆蓋新叢集中正在寫入的物件：

```bash
velero backup get
velero backup describe <BACKUP_NAME> --details
velero restore create --from-backup <BACKUP_NAME>
velero restore get
velero restore describe <RESTORE_NAME>
```

遷移場景需確保兩個叢集存取同一受保護備份儲存，並檢查 PV 資料複製/恢復方式。Velero 不會自動遷移外部資料庫、雲負載平衡器、DNS、KMS 或其他叢集外依賴。

## 參考資料

- [Velero v1.18 文件](https://velero.io/docs/v1.18/)
- [Velero v1.18.4 釋出頁](https://github.com/velero-io/velero/releases/tag/v1.18.4)
- [Kubeadm etcd 備份與恢復](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)
