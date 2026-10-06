# Argo CD

Argo CD 是 Kubernetes 持續交付 controller。它會比較 Git revision 所產生的 manifest 與叢集中的 live object。Application controller 回報差異，並在收到要求或設定自動同步時執行同步作業。Argo CD 與 [Argo Workflows](argo.md) 是不同專案；Workflows 用來執行容器工作和 DAG。

> **版本快照（2026-10-05）：** 截點記錄的 Argo CD 最新穩定版為 v3.5.3，於 2026-09-14 發布。v3.5.3 固定版本的 Kubernetes 測試表列出 1.33 至 1.36，沒有 1.37。本章不宣稱支援 Kubernetes v1.37。請參閱[釋出頁](https://github.com/argoproj/argo-cd/releases/tag/v3.5.3)與[測試版本表](https://github.com/argoproj/argo-cd/blob/v3.5.3/docs/operator-manual/tested-kubernetes-versions.md)。

## Reconciliation 運作方式

`Application` 指定儲存庫、revision、manifest 路徑、目標叢集與命名空間，以及所屬的 `AppProject`。repo-server 取得儲存庫內容並產生 manifest，例如 Kustomize 或 Helm。application controller 比較期望物件與 live object，並記錄同步和健康狀態。API server 提供 UI 和 CLI、驗證使用者、套用 Argo CD RBAC 並協調操作。Diff 或 `OutOfSync` 狀態本身不代表已套用變更。

`AppProject` 是安全邊界，用來限制允許的來源儲存庫、目標叢集／命名空間和資源種類。內建的 `default` project 權限寬鬆。請建立明確列出允許項目的 project，並讓每個 Application 指定該 project；也要透過 Argo CD RBAC 與 Kubernetes RBAC 限制誰能建立或修改 Application 和 Project。Project 限制不能取代叢集授權，也不能取代對 controller Kubernetes 權限的檢視。

## 隔離環境安裝與評估

請使用拋棄式隔離叢集，以及不會指向正式環境的 kubeconfig context。標準非 HA 安裝僅供評估，不適用於正式環境。v3.5.3 上游安裝 manifest 授予 controller 廣泛的叢集存取權；除非先檢視 RBAC 和威脅模型，否則不要套用到共用或敏感叢集。

```bash
ARGOCD_VERSION=v3.5.3
kubectl create namespace argocd
kubectl apply -n argocd \
  -f "https://raw.githubusercontent.com/argoproj/argo-cd/${ARGOCD_VERSION}/manifests/install.yaml"
```

以下示範下載 macOS arm64 的同版 CLI（其他平台請替換資產名稱），並加入目前 shell 的 PATH：

```bash
curl -fsSLo argocd "https://github.com/argoproj/argo-cd/releases/download/v3.5.3/argocd-darwin-arm64"
chmod +x argocd
export PATH="$PWD:$PATH"
argocd version --client
```

只在 loopback 開啟 UI。請保持 port-forward 終端機執行中；此方式不會將服務公開至網際網路介面。

```bash
kubectl -n argocd port-forward svc/argocd-server 8080:443 --address 127.0.0.1
```

前往 `https://localhost:8080`。執行後續 CLI 操作前，必須依[官方登入文件](https://github.com/argoproj/argo-cd/blob/v3.5.3/docs/user-guide/commands/argocd_login.md)，將 CLI 設定為連線至此隔離環境，並使用可信任 TLS 設定及已驗證的使用者身分。命令範例假設 CLI 已完成此設定；不要略過 TLS 驗證，也不要複製或重用 bootstrap 管理員憑證。若本機 port-forward 的憑證名稱不符，應先設定可信任的 TLS 憑證，不要關閉驗證。

## 限制 Application

以下 manifest 建立範圍有限的 project，以及指向公開 Argo 範例儲存庫的 Application。經核對的 `guestbook` 路徑目前位於該儲存庫的 `master` 分支；`master` 是會移動的分支，不是固定 revision。此示範不宣稱其 revision 可重現；正式或需重現的環境應改為審核過的不可變 commit SHA。範例只部署至本機叢集中的專用命名空間。因為未啟用自動建立命名空間，請先建立目標命名空間。

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: guestbook-lab
  namespace: argocd
spec:
  sourceRepos:
    - https://github.com/argoproj/argocd-example-apps.git
  destinations:
    - server: https://kubernetes.default.svc
      namespace: guestbook-lab
  namespaceResourceWhitelist:
    - group: apps
      kind: Deployment
    - group: ""
      kind: Service
  clusterResourceWhitelist: []
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: guestbook-lab
  namespace: argocd
spec:
  project: guestbook-lab
  source:
    repoURL: https://github.com/argoproj/argocd-example-apps.git
    targetRevision: master
    path: guestbook
  destination:
    server: https://kubernetes.default.svc
    namespace: guestbook-lab
  # 僅手動同步。保持 prune 與 self-heal 關閉。
```

將 YAML 存為 `guestbook-application.yaml`。這是文件範例，不要直接套用到正式叢集。在隔離實驗環境 context 建立命名空間並套用，接著先檢視預計變更。

```bash
kubectl create namespace guestbook-lab
kubectl apply -f guestbook-application.yaml
argocd app get guestbook-lab
argocd app diff guestbook-lab
argocd app sync guestbook-lab --dry-run
```

第一個命令建立目標命名空間。讀取命令會顯示 Application 回報狀態和期望／live 差異。dry-run sync 預覽操作但不套用變更。只有在正確的實驗環境中檢視 diff 後，操作人員才應明確執行 `argocd app sync guestbook-lab`。

Health 是資源就緒狀態的摘要，不是安全或端對端應用程式檢查。`Synced` 表示依 Argo CD 的比較規則，追蹤的期望物件與 live 狀態相符，不代表工作負載已符合所有服務目標。遇到 `OutOfSync`、`Unknown` 或健康狀態降級時，先檢查儲存庫 manifest 產生錯誤、project 允許清單、目標叢集權限、controller 事件及工作負載狀態，再考慮變更政策。

## 同步政策與操作界線

自動同步、prune 和 self-heal 是不同的設定。自動同步會在 Git revision 改變並使 Application 不同步時套用變更。Prune 會刪除 Git 已移除的 live object，預設不會啟用。Self-heal 會嘗試在 live 狀態偏離 Git 時還原為 Git 狀態。只有在資源歸屬、審核、刪除保護和復原程序都已定義後，才啟用這些功能。不要輕率地同時啟用自動 prune 與 allow-empty；若產生的 manifest 為空，且允許刪除，可能會移除所有受管理物件。

正式環境請設定 SSO/OIDC、明確的最小權限 RBAC、可信任的儲存庫憑證、秘密資料管理、稽核軌跡、備份和監控。不要把明文秘密放進 Git。選擇 HA 安裝前，先評估 Redis、repository 和 controller 元件的容量，並驗證儲存、入口和復原方式。升級前檢視破壞性變更、CRD 與支援的 Kubernetes 版本矩陣；先在測試環境升級，並保留經測試的復原方式。v3.5.3 測試版本表並未證明支援 Kubernetes v1.37。

## 參考資料

- [Argo CD v3.5.3 安裝說明](https://github.com/argoproj/argo-cd/blob/v3.5.3/docs/operator-manual/installation.md)
- [架構](https://github.com/argoproj/argo-cd/blob/v3.5.3/docs/operator-manual/architecture.md)
- [Projects 與限制](https://github.com/argoproj/argo-cd/blob/v3.5.3/docs/user-guide/projects.md)
- [自動同步、prune 與 self-heal](https://github.com/argoproj/argo-cd/blob/v3.5.3/docs/user-guide/auto_sync.md)
- [CLI 登入](https://github.com/argoproj/argo-cd/blob/v3.5.3/docs/user-guide/commands/argocd_login.md)
- [v3.5.3 釋出頁](https://github.com/argoproj/argo-cd/releases/tag/v3.5.3)

## 唯讀檢查與常見錯誤

以下命令會檢查狀態、資源健康、歷史紀錄和 live／期望差異，不會同步資源。

```bash
argocd app get guestbook-lab
argocd app resources guestbook-lab
argocd app history guestbook-lab
argocd app diff guestbook-lab
kubectl -n guestbook-lab get deployments,services
kubectl -n guestbook-lab get events --sort-by=.metadata.creationTimestamp
```

比較錯誤常見原因包括 repo-server 無法取得或產生所選來源的 manifest、project 拒絕儲存庫或目的地，或 Argo CD 無法探索資源 API。先檢查 Application condition 訊息和 repo-server log，再考慮調整 project policy。若同步回報權限不足，請確認目的地憑證及 controller 的預期 RBAC。若應用程式為 `Synced` 但不健康，請檢查指定工作負載和 pod events；manifest 套用成功不代表已就緒。不要為了解決錯誤而全域放寬來源儲存庫、目的地或資源允許清單。

升級前記錄目前 manifest revision、CRD 版本和 controller 設定。在 staging 叢集套用目標版本文件要求的 CRD 與安裝變更，接著檢查 reconciliation 和回復行為。回復 controller 執行檔不會自動還原 schema 變更或已同步到目標叢集的應用程式變更。
