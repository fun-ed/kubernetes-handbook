# Kubernetes 設定最佳實務

本文針對 Kubernetes v1.37.1 整理資源設定建議。正式部署前，應依目標叢集 API 與元件版本核對欄位、策略及相容範圍；將清單納入版本控制，但不得提交憑證或敏感設定。

## 宣告式資源

- 使用目前受支援的 API 版本，並依[棄用指南](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)檢查已移除的 API。API 遷移可能需要調整 selector、欄位結構或行為，不能只替換 `apiVersion`。
- 對 Deployment、StatefulSet 等控制器明確指定 selector，並確保它與 Pod template labels 一致。新工作負載優先使用適當的控制器或 Job，不要把單獨建立的 Pod 當成具有自我修復能力的部署。
- 以 Service DNS 名稱存取服務；只有確有需要時才設定 `hostNetwork` 或 `hostPort`，因為它們會共用節點網路或造成連接埠衝突。
- 採用最小權限 RBAC。檢查 Service、NetworkPolicy 和 Pod selector 是否只比對預期物件；避免空 selector 或寬泛的叢集層級授權。
- 對 API 資源清單使用 `kubectl apply --dry-run=server --validate=strict -f <file>` 做目標叢集預檢。CRD、自訂資源和 admission webhook 需要相應 CRD、controller/webhook 前置條件；dry-run 不能證明業務行為可用。

## 映像檔與 Secret

- 固定經審閱的映像檔版本；需要不可變部署時固定 digest。不要在正式工作負載使用 `:latest`，也不要假設可變 tag 不會移動。
- 使用 Secret 管理敏感資料，並依實際威脅模型限制讀取權限、加密靜態資料及輪替憑證。不要把 token、私鑰或 kubeconfig 寫入映像檔、原始碼或公開記錄。

## 資源與安全

- 為工作負載設定經容量評估的 CPU、memory requests/limits；為可能遭驅逐的應用設定合理的 PodDisruptionBudget，並避免 selector 為空。
- 使用 Pod Security Admission 的 namespace labels 或維護中的策略實作限制 Pod 權限。PodSecurityPolicy 已移除；不要使用 PSP 清單或舊 seccomp 註解。
- NetworkPolicy 是否生效取決於所選 CNI 的實作；部署前確認 provider 支援並驗證 ingress/egress 策略。

官方參考：[Configuration Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)、[Workload Resources](https://kubernetes.io/docs/concepts/workloads/controllers/)、[RBAC 最佳實務](https://kubernetes.io/docs/concepts/security/rbac-good-practices/)、[映像檔](https://kubernetes.io/docs/concepts/containers/images/)。
