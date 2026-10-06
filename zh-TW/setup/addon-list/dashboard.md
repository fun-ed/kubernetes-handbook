# Kubernetes Dashboard 狀態

**Kubernetes Dashboard 上游專案已於 2026-01-21 歸檔**，儲存庫位於 `kubernetes-retired` 組織下，不再是應安裝到新 Kubernetes v1.37 叢集的維護中元件。參見[歸檔儲存庫](https://github.com/kubernetes-retired/dashboard)。本頁不提供舊版本 manifest、靜態 ServiceAccount token 或 Helm 安裝命令。

如果需要 Web UI，可評估仍維護的 [Headlamp](https://headlamp.dev/) 專案，並按它的當前安裝指南、版本相容資料和組織的認證/授權要求部署。存取叢集管理 UI 應透過正式身分認證並遵守最小權限；不要使用歷史教程中長期有效的管理員 bearer token，也不要向公網暴露未受保護的 Dashboard。

> **歷史說明：** 本儲存庫舊頁面所記錄的 Dashboard v2.0.0-beta8 是多年以前的預覽版說明。它僅解釋舊叢集管理介面的歷史，不適用於 Kubernetes v1.37.1。