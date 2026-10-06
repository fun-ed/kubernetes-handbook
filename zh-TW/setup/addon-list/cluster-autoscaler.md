# Cluster Autoscaler

Cluster Autoscaler 會呼叫雲平台或基礎設施 provider 的 API 擴縮節點組；安裝方案與權限、節點組模板、排程約束和雲平台強相關，不能使用一個通用 manifest 代替 provider 文件。

上游建議 Cluster Autoscaler 與 Kubernetes control plane **minor 版本匹配**。截至 2026-10-05，最新穩定 Cluster Autoscaler release 為 **1.36.1**；上游 compatibility README 表格尚未列出 Kubernetes v1.37，且沒有經核實的 CA v1.37 穩定釋出。因此本手冊不把 CA 1.36.1 映像檔用於 Kubernetes 1.37，也不編造 v1.37 pin。請檢查[上游 releases](https://github.com/kubernetes/autoscaler/releases)、[相容矩陣](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/README.md)以及雲廠商當前支援矩陣；只有確認存在匹配 v1.37 的 release 後才部署。

舊教程中的 CA v1.3 manifest、手動 RBAC 和 HPA sample 不是當前可用設定。生產環境應按所用 provider 的官方安裝說明生成最小權限策略，並先在非生產叢集驗證 scale-up、scale-down、drain 保護和節點組邊界。
