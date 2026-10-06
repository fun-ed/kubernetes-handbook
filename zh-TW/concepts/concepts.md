# Kubernetes 概念

Kubernetes 透過宣告式 API 管理叢集資源。使用者提交期望狀態，控制器持續觀察 API 物件並採取操作，使觀察到的狀態逐步符合期望；這是協調迴路，不保證立即完成，也不代表每項操作都能安全重複。

本章只概述 Kubernetes v1.37 的核心概念。舊版 API、已移除元件及過時的架構敘述已移至[歷史歸檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/concepts/design-principles-legacy-zh-TW.md)。

## API 物件與控制器

Kubernetes API 是叢集狀態與操作的主要介面。許多 API 物件包含描述期望狀態的 `spec`，並可能包含控制器回報觀察狀態的 `status`；物件通常以 `apiVersion`、`kind`、`metadata` 等欄位識別。API 資源的可用版本與欄位依叢集版本及已安裝擴充而異，應查閱目標叢集的 API 文件或 discovery，而非假設所有功能都對應一種內建物件。

控制器讀取 API 狀態並執行協調。控制迴路可能因 API Server、節點、網路或外部相依故障而延遲；應以狀態與事件確認結果，不要把提交成功視為工作已完成。`kubectl` 支援命令式操作，也支援以檔案描述期望狀態的宣告式工作流程。

## Pod 與工作負載

Pod 是 Kubernetes 排程及執行容器的最小單位。同一 Pod 的容器共享網路命名空間，並可透過明確宣告的 `volumes` 共享檔案；它們不會自動共享彼此的根檔案系統。容器間的程序可透過 Pod 網路位址與本機通訊機制互動。

常見工作負載資源包括：

- `Deployment` 管理無狀態工作負載，並協調 ReplicaSet 與 Pod 更新。
- `StatefulSet` 管理具穩定識別與儲存需求的 Pod；其序號及建立、刪除順序取決於 Pod 管理策略。
- `DaemonSet` 在符合條件的節點上維持 Pod。
- `Job` 與 `CronJob` 管理一次性及排程批次工作。

選擇控制器時，應根據應用程式的識別、更新、儲存及完成條件，而非把所有 Pod 都視為可任意替換。

## 網路與服務探索

Pod IP 可能隨 Pod 重建而改變。`Service` 提供穩定的虛擬 IP 或 DNS 名稱，並以 `EndpointSlice` 表示後端端點；叢集網路實作會提供連通性及服務流量轉送。`kube-proxy` 是常見但非唯一的服務代理實作；有些網路外掛提供替代資料平面。

`ClusterIP`、`NodePort`、`LoadBalancer` 與 headless Service 的用途不同。跨叢集或外部流量的路由還需要相應的基礎設施或控制器。若要管理 HTTP、gRPC 等應用層路由，可評估 Gateway API 及相容的實作；不要假設建立 API 物件本身就會安裝控制器或提供資料平面。

## 儲存與擴充

`PersistentVolumeClaim` 表達工作負載的儲存需求，PV 與 StorageClass 描述供應資源與配置方式。CSI 驅動程式負責將儲存系統整合至叢集；可用功能、拓樸、存取模式與快照支援取決於驅動程式及後端。

CustomResourceDefinition 可註冊自訂 API 資源，但僅定義 schema 不會實作控制行為；若資源需要協調邏輯，必須另行安裝相應控制器。擴充 API、授權、驗證與轉換功能時，應依當前版本文件確認相依元件與安全設定。

## 身分與隔離

Namespace 用於組織命名空間範圍內的資源，不是完整的安全邊界。RBAC 以 Role、ClusterRole 及其綁定授予 API 權限；網路隔離、Pod 安全及 Secret 加密還需要各自的策略與設定。ServiceAccount 為工作負載提供叢集身分，應依最小權限設定存取，並使用 Kubernetes 提供的短期憑證機制。

## 參考文件

- [Kubernetes API 概念](https://kubernetes.io/docs/reference/using-api/api-concepts/)
- [Pod](https://kubernetes.io/docs/concepts/workloads/pods/)
- [工作負載](https://kubernetes.io/docs/concepts/workloads/)
- [Services、Load Balancing 與 Networking](https://kubernetes.io/docs/concepts/services-networking/)
- [儲存](https://kubernetes.io/docs/concepts/storage/)
- [安全性](https://kubernetes.io/docs/concepts/security/)
