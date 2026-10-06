# Kubernetes Feature Gates

Feature gate 是逐元件控制 Alpha/Beta 功能的 `名称=true|false` 開關。可用名稱、階段、預設值和生命週期會隨 Kubernetes 版本改變；不要從舊版本設定中複製整串 gate。

當前目標為 Kubernetes v1.37.1。以下只是官方 v1.37 表格中的少量範例，不是推薦的生產開關清單：

| Gate | v1.37 階段與預設值 | 說明 |
| --- | --- | --- |
| `MemoryQoS` | Beta，預設 `true` | v1.37 從 Alpha 轉為 Beta；按 kubelet 文件及工作負載特徵驗證記憶體控制效果。 |
| `HPAScaleToZero` | Beta，預設 `true` | v1.37 從 Alpha 轉為 Beta；需確認 HPA 設定和目標指標源滿足該功能要求。 |
| `KubeletInUserNamespace` | Beta，預設 `true` | v1.37 從 Alpha 轉為 Beta；僅對相應 kubelet/user namespace 部署有效。 |
| `AtomicWriteVolumeUserFields` | Alpha，預設 `false` | v1.37 新增 Alpha gate；僅在理解該功能限制後才評估啟用。 |
| `AllowUnsafeMalformedObjectDeletion` | Beta，預設 `true` | v1.37 從 Alpha 轉為 Beta。名稱包含 unsafe；不要僅為消除物件刪除錯誤而隨意更改此安全相關行為。 |

階段和預設值引用自 [Kubernetes v1.37 Feature Gates 官方表格](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/)。該表格會隨釋出更新。部署時還需檢視實際元件的 feature-gate 支援情況，因為一個 gate 不一定適用於所有元件。

## 設定原則

- 只在功能仍處於 Alpha/Beta 且官方文件要求時設定 gate。GA 功能通常不再需要 gate；已移除 gate 會導致啟動引數無效或被拒絕。
- 在所有相關元件上協調設定，例如 API server 和對應控制器；逐步釋出期間確認元件版本和 gate 組合相容。
- 修改 kubeadm 管理的控制平面時，透過受支援的 kubeadm 設定/升級流程變更，避免直接編輯生成的靜態 Pod manifest 後失去設定一致性。
- 上線前使用與目標 Kubernetes **同 minor 版本**的官方 gate 表格、API 文件和發行說明稽核；不要把本頁範例當作長期相容承諾。

檢視完整的 [Feature Gates](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/) 表格和 [Configure Feature Gates](https://kubernetes.io/docs/tasks/administer-cluster/feature-gates/) 操作指南。