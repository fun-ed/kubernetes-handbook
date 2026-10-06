# Kubernetes v1.37 相容性指南

本章的版本快照截止於 **2026-10-05**，目標為 **Kubernetes v1.37.1**。只選擇截止日期前釋出的穩定版本，不使用 v1.38 alpha 或元件的預釋出版本。元件的最新版本、kubeadm 內建版本與 Kubernetes 相容宣告是不同資訊，見[元件版本清單](component-versions.md)。

版本依據為 [Kubernetes 釋出列表](https://kubernetes.io/releases/)、[v1.37.1 釋出記錄](https://github.com/kubernetes/kubernetes/releases/tag/v1.37.1)和 [v1.37 原始碼變更記錄](https://github.com/kubernetes/kubernetes/blob/v1.37.1/CHANGELOG/CHANGELOG-1.37.md)。這些頁面的釋出時間資訊可能不同，本書以版本標籤及截止日期為篩選依據，不把釋出時間差異解釋為不同版本。

## 部署基線

- 控制平面、kubelet、kube-proxy、kubeadm、kubectl 使用 v1.37.1；映像檔登錄站使用 `registry.k8s.io`。
- 節點使用支援 CRI v1 的執行時，優先選擇 containerd 2.x 或同次版本的 CRI-O。Docker Engine 本身不是 CRI 實現；cri-dockerd 路徑還有 exec/attach 的已知相容性問題，不作為本章新部署基線。
- Linux 新節點使用 cgroup v2，執行時與 kubelet 的 cgroup 驅動保持一致。在 systemd 系統中使用 `systemd` 驅動。
- kubeadm v1.37.1 原始碼的元件基線包括 etcd 3.7.0、CoreDNS 1.14.6 和 pause 3.10.2。它們不是所有第三方元件的通用相容性保證。安裝時用 `kubeadm config images list --kubernetes-version v1.37.1` 核對具體映像檔標籤。
- 使用維護中的 CNI、CSI 和 Gateway API 控制器。只安裝 CRD 不會產生網路或儲存實現。

基線依賴見 [v1.37.1 dependencies.yaml](https://github.com/kubernetes/kubernetes/blob/v1.37.1/build/dependencies.yaml)。執行時設定見[官方執行時指南](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)。containerd 2.x 的外掛路徑與 1.x 不同，應從所安裝版本生成預設設定再修改，不直接複製舊版 `config.toml`。

如必須沿用 Docker Engine，先核對 [cri-dockerd 的流式請求問題](https://github.com/Mirantis/cri-dockerd/issues/569)。Kubernetes v1.36 起預設啟用 `ExtendWebSocketsToKubelet`，舊配接器的相對 streaming URL 可能導致 `kubectl exec`、`attach` 失敗。上游部署工具採用過在 kube-apiserver 暫時關閉該開關的規避方式，但這不是本書已經驗證的 v1.37 設定；優先遷移到 containerd 或 CRI-O，而不是繞過錯誤後宣稱 Docker 路徑相容。

## 升級前檢查

不能從本書早期的 v1.6、v1.13 或 v1.33 教程直接跨次版本升級到 v1.37。先升級到當前次版本的最新補丁，再逐次升級；每一步都遵循部署工具和元件的升級說明。

1. 備份 etcd、叢集設定與工作負載資料，並在隔離環境驗證恢復。etcd 跨次版本遷移按 etcd 官方順序執行，不能僅替換二進位。
2. 核對 CNI、CSI、執行時、雲控制器、准入 webhook、監控和 ingress/Gateway 控制器的支援矩陣。最新 release 不等於已透過 v1.37 驗證。
3. 清理已移除的 API、特性開關和元件啟動引數。檢查實際 API discovery、審計記錄以及 `apiserver_requested_deprecated_apis` 指標。
4. 在測試叢集驗證網路、DNS、持久卷、准入策略、證書與監控告警，然後逐節點 drain、升級並 uncordon。

### v1.37 的特殊升級風險

以下內容來自[官方 v1.37 變更記錄](https://github.com/kubernetes/kubernetes/blob/v1.37.1/CHANGELOG/CHANGELOG-1.37.md)。

| 專案 | 遷移要求 |
| --- | --- |
| SELinux 卷標籤 | `SELinuxMount` 升級為 GA 並預設啟用。啟用 SELinux 的叢集應在 v1.36 階段檢查共享卷與工作負載的標籤衝突，見[官方遷移說明](https://kubernetes.io/blog/2026/04/22/breaking-changes-in-selinux-volume-labeling/)。 |
| 工作負載感知排程 | 升級前清除 `scheduling.k8s.io/v1alpha2` 物件；核心 Workload/PodGroup 使用 `v1beta1`，CompositePodGroup 使用 `v1alpha3`。這些 API 的啟用仍取決於相應特性開關，不能批次替換所有 alpha API。 |
| 特性開關 | 移除 `GangScheduling`、`WorkloadAwarePreemption`、`AnyVolumeDataSource` 和 kubeadm 的 `NodeLocalCRISocket` 舊設定；`DeclarativeValidationTakeover` 已鎖定，不能繼續顯式設定。 |
| kubelet 事件限流 | `eventRecordQPS: 0` 表示不限流。需要限流時設定明確的非零值，例如 `50`。 |
| kubelet 日誌權限 | kubelet 啟動日誌會記錄有效設定。限制 `nodes/log` 子資源權限，僅授予可信管理者，避免洩露設定。 |
| cAdvisor | 除 `--housekeeping-interval` 外，舊的 cAdvisor 啟動引數已移除。自定義應用指標、CPU load 和 tasks-state 等舊指標不再匯出，升級後要調整採集和告警。 |
| kube-proxy | 顯式設定 `mode`。IPVS 自 v1.35 起棄用；新 Linux 核心可選擇 nftables，舊核心可使用 iptables。v1.37 的預設模式仍不是 nftables。 |
| 執行時 cgroup 檢測 | 支援 CRI `RuntimeConfig` 的執行時可提供 cgroup 驅動。舊執行時的回復行為在 v1.37 尚未移除，移除延期到 v1.38；新部署仍應選擇支援該介面的執行時。 |

## API 與安全遷移

常見舊範例按[官方 API 遷移指南](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)修改欄位，不能只修改 `apiVersion`。

| 物件 | v1.37 使用方式 |
| --- | --- |
| Deployment、DaemonSet、ReplicaSet、StatefulSet | `apps/v1`，顯式 selector，且與 Pod template 標籤一致。 |
| CronJob | `batch/v1`。 |
| Ingress | `networking.k8s.io/v1`，設定 `pathType`，後端為 `service.name` 與 `service.port`。新入口優先評估 Gateway API。 |
| RBAC | `rbac.authorization.k8s.io/v1`，按實際權限使用最小授權。 |
| HPA | `autoscaling/v2` 支援多指標與可設定容差；`autoscaling/v1` 仍可用於簡單 CPU 範例。 |
| PDB | `policy/v1`，必須檢查 selector。空 selector 會選擇命名空間全部 Pod。 |
| CRD | `apiextensions.k8s.io/v1`，使用 `spec.versions` 和結構化 schema。 |
| APIService | `apiregistration.k8s.io/v1`，版本宣告必須與後端實際服務一致。 |
| CSR | `certificates.k8s.io/v1`，顯式指定 `signerName`、`usages`。 |
| PodSecurityPolicy | 已移除，遷移到 Pod Security Admission 或維護中的准入策略實現。 |
| ServiceAccount 憑證 | 使用投射的短期權杖或 `kubectl create token`，不依賴自動生成永久 token Secret。 |

v1.37 的 `metrics.k8s.io/v1` 已穩定，`kubectl top` 支援該版本並可回復到 v1beta1。但 [Metrics Server v0.9.0 的官方清單](https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.9.0/components.yaml)仍註冊 `v1beta1.metrics.k8s.io`，v1.37 的 HPA 資源指標客戶端也使用 v1beta1。保留後端的 v1beta1 服務，不要僅把 APIService 名稱改為 v1 就假設實現已升級。聚合 API 的實際版本必須與後端匹配。

## v1.37 功能重點

- Pod Certificates、ClusterTrustBundle 與投射功能升級為 GA。PodCertificateRequest 的 v1 API 不再接受舊 `PKIXPublicKey` 和 `ProofOfPossession` 欄位。
- DRA 擴充套件資源、裝置汙點/容忍和裝置狀態升級為 GA；驅動仍須匹配 CRI、節點核心與相應 DRA 介面。
- `HPAConfigurableTolerance` 和 `StorageVersionMigration` 升級為 GA。
- `MemoryQoS` 為 Beta；預設不設定 `memory.high`，需要顯式設定 `memoryThrottlingFactor`。
- PVC 的 unused-since 狀態為 Beta 並預設啟用，可輔助識別未使用卷，但不能據此自動刪除業務資料。

完整特性與預設值以該版本原始碼及[特性開關說明](feature-gates.md)為準，不把歷史特性表作為當前可設定開關清單。

## 驗證與回復邊界

先確認命令指向預期的測試叢集。下面命令不建立工作負載，但會存取所選叢集。

```bash
kubectl version
kubectl get nodes -o wide
kubectl get --raw='/readyz?verbose'
kubectl api-resources
kubectl get pods -A
kubectl get apiservices
kubectl top nodes
```

對修改過的清單，在相容的測試叢集執行 `kubectl apply --dry-run=server --validate=strict -f <file>`。服務端 dry-run 需要可用的 API、CRD 和 admission webhook，不能代替真實的 DNS、網路、卷與業務驗證。CRD 控制器與雲資源也需單獨驗證。

本書保留明確標記的歷史教程，供理解舊架構及遷移使用；其中已退役的 Heapster、舊 ingress-nginx、Tiller、Mixer、PodPreset、dockershim、GlusterFS in-tree 卷等不是 v1.37 的部署路徑。歷史清單不應納入當前元件的安裝命令。

Kubernetes 不支援把升級後的控制平面直接降級作為通用回復。回復方案應由部署工具、etcd 快照恢復流程及業務資料恢復共同定義，在升級前完成驗證。

## 本次相容性驗證記錄

以下保留原有相容性驗收的範圍與結果，包括當時的 GitBook 建置失敗。後續網站工具鏈與可重跑驗證分別見[網站建置](site-build.md)和[最小回歸](verification.md)；這些新流程不改變本節歷史驗證的計數或範圍。

驗證使用隔離的 kind v0.33.0 叢集。先用官方 v1.37.0 節點映像檔進行排錯，再從官方 v1.37.1 服務端釋出包建置節點，重新驗證 **API server 與 kubelet 均為 v1.37.1**。該測試節點執行 containerd **2.3.4**；這不是元件清單中 containerd 2.4.1 的執行認證。

| 檢查 | 實際結果與邊界 |
| --- | --- |
| kubeadm 設定 | v1.37.1 `kubeadm config validate` 接受範例的四段設定；映像檔列表核實 etcd 3.7.0、CoreDNS 1.14.6、pause 3.10.2。 |
| 獨立清單 | 113 個當前資源透過嚴格 server-side dry-run；其中 96 個內建物件透過 v1.37.1 嚴格 schema，17 個自定義物件另按 Gateway API 1.6.2、cert-manager 1.21.2、Calico 3.33 CRD 檢查。41 個歷史檔案只檢查 YAML，不宣稱可部署。 |
| 文件內清單 | 126 個符合測試前提的內建資源在 v1.37.1 實際提交 dry-run，其中 3 個證書佔位範例僅在記憶體中替換為臨時測試證書。歷史 alpha 註解及 10 個外部控制器、Kata 等前提不滿足的範例不計入透過數。 |
| client-go | v0.37.1 範例透過 Go 編譯、`go test ./...`、`go vet ./...`；包沒有單元測試檔案。實際驗證首次快取、Pod 增刪改事件、SIGTERM 退出與缺失 kubeconfig 的錯誤路徑。 |
| Gateway | Traefik 3.7.13 與 Gateway API 1.6.2 的 80/443 listener、HTTPRoute 條件及實際 HTTP/HTTPS 請求透過。HTTPS 只信任臨時測試證書；沒有驗證外部 LoadBalancer、ACME 或全部 Gateway 特性。 |
| DNS 與指標 | CoreDNS 1.14.6 的 API/業務 Service DNS 查詢透過；Metrics Server 0.9.0 提供 v1beta1 指標，kubectl 1.37.1 `top nodes` 透過。kind 的 kubelet serving 證書不受信任，因此僅臨時測試 Deployment 加過 `--kubelet-insecure-tls`，儲存庫清單沒有放寬 TLS。 |
| Node Problem Detector | v1.36.0 釋出映像檔接受清單啟動引數，包括幫助頁不列出的 `--logtostderr`。這是 CLI 檢查，不是核心、宿主日誌或特權 DaemonSet 的執行認證。 |
| 文件與建置 | YAML 圍欄、變更引入的相對連結及 diff 空白檢查透過；保留 4 個原有失效相對連結，不計為新增問題。完整 GitBook 渲染未透過：本機缺少 CLI，隔離驗證又遇到舊 npm 外掛安裝錯誤和 github 外掛要求 GitBook 4 alpha 的版本衝突。沒有把靜態檢查當成渲染成功，也未把舊 Node/GitBook 工具鏈作為生產推薦。 |

支援矩陣不包含 v1.37 的 Istio、Cilium、Envoy Gateway、cert-manager，以及尚無同次版本穩定釋出的 Cluster Autoscaler，仍按[元件清單](component-versions.md)標註限制。上述結果不是全元件、雲環境、持久卷、SELinux/GPU 或生產升級的認證。

本次更新由 AI 輔助調查與修改，並經過分域 review 和實際驗證；未宣稱已經完成人類逐行審查。調查、排錯、維護與釋出步驟分別記錄於 [.agents/skill-investigate.md](../.agents/skill-investigate.md)、[.agents/skill-debug.md](../.agents/skill-debug.md)、[.agents/skill-maintenance.md](../.agents/skill-maintenance.md)。
