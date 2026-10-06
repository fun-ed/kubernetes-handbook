# Kubeflow：以 Kubernetes 建置機器學習平台

「Kubeflow」不是單一套件。Kubeflow manifests／AI Reference Platform 描述整合發行版；Pipelines、Trainer、Katib、Notebooks 等各有獨立版本、CRD 及控制器。安裝整合版會帶入大量控制器、webhook、RBAC、網路與外部依賴，不等於啟用一個 API。

## 發行版與支援邊界

截至 2026-10-05，官方 community-distribution 最新穩定 release 為 **26.03.1**，於 2026-06-15 發布；release notes 列出其元件包含 Pipelines 2.16.1、Trainer 2.2.0、Istio 1.30.1、cert-manager 1.20.2、Dex 2.45.1、Kubeflow Notebooks v1.11.0。這些個別元件版本不是同一個「Kubeflow 版本」。官方 26.03.1 說明提到其 CI 使用 Kubernetes 1.36；不能據此推論 Kubernetes v1.37.1 已受支援。本文以 v1.37 為基線，但整合相容性未知，須在隔離環境自行驗證。

此版本社群支援為 best-effort、約六個月；請查看上游支援政策與最新 release，不要把本文固定版本當成永久支援承諾。社群 manifests 與商業發行版的支援範圍可能不同。

## 架構與多租戶

控制器監看 CRD 或 Kubernetes 原生工作物件，建立 Pod、服務並回報狀態；CRD 存在不代表對應 controller/webhook 已健康。Notebook controller 管理 Notebook 工作負載；Pipelines 服務有自己的 API、資料庫與物件儲存需求；Trainer、Katib 也各有版本化 API 與控制器。依功能部署需要的元件，不要混用不同 release 的 CRD 與控制器。

完整多租戶平台還需要身份驗證及授權整合、TLS 憑證、Istio ingress/gateway 與使用者 namespace/Profile 管理。Profile 通常會建立 namespace 並配置服務帳號/RBAC，不能取代叢集身份系統、NetworkPolicy 或租戶資料隔離。不要用匿名登入或未加密方式公開 dashboard 作為快速安裝步驟；入口應限於可信網路並配置正式 OIDC/身份提供者及憑證。

## 前置條件與審查式安裝

完整安裝前需有受支援的 Linux Kubernetes 叢集、可用 StorageClass、叢集 DNS、時間同步、可連線至映像 registry、Istio/入口規劃、cert-manager 與有效 TLS 憑證，以及已設計的身份驗證、RBAC、網路隔離及備份。需要 GPU 時，另須相符的裝置外掛/驅動與資源配額。外部資料庫、物件儲存、郵件/身份提供者及雲端整合也須分別規劃。沒有可預設安全地公開至公網的設定。

僅在專用實驗叢集評估固定 release；以下先取得該 tag 原始碼供審查，**不代表可直接安裝**。不要套用 `main`、不要未審閱便對叢集套用遞迴遠端路徑，也不要假設一個命令就能完成安全的多租戶發行版：上游依安裝模式及環境需求分階段安裝，應依 tag 文件準備 overlay、身份及網路設定。

```bash
git clone --depth 1 --branch 26.03.1 https://github.com/kubeflow/manifests.git
cd manifests
# 檢查指定安裝方式、元件清單、身份/憑證與儲存設定；先渲染審查，不執行 apply。
kustomize build /path/to/reviewed-release-overlay | kubectl apply --dry-run=server -f -
```

此命令中的 overlay 路徑是明確佔位值，須以 tag 中官方安裝文件指定且已審查的完整 overlay 替換。server-side dry-run 僅檢查 API 是否接受，不會驗證 webhook、外部依賴、權限是否適切或 controller 能否運作。上游完整平台需依官方文件所列的安裝步驟與 overlays 操作，逐步驗收，不要以 magic patch loop 掩蓋失敗。

## Notebook 範例（須先安裝 v1.11 controller）

下例採用 Kubeflow Notebooks v1 API，必須在已安裝且確認 `kubeflow/notebooks` v1.11.0 controller/CRD 的叢集，以及事先建立的 `ml-work` namespace 和 StorageClass/PVC 中使用。不要直接套用到只安裝 Kubernetes 的叢集：API server 不認得 CRD 時會拒絕此物件。映像為明確參數，須選用組織核准且支援 Notebook 的映像，不虛構版本標籤。先確認 CRD schema 與指定 release 範例一致。

```yaml
apiVersion: kubeflow.org/v1
kind: Notebook
metadata:
  name: research
  namespace: ml-work
spec:
  template:
    spec:
      containers:
        - name: research
          image: REPLACE_WITH_APPROVED_NOTEBOOK_IMAGE
          resources:
            requests:
              cpu: "1"
              memory: 2Gi
            limits:
              cpu: "2"
              memory: 4Gi
          volumeMounts:
            - name: workspace
              mountPath: /home/jovyan
      volumes:
        - name: workspace
          persistentVolumeClaim:
            claimName: research-workspace
```

PVC 須事先建立，且符合 CSI/StorageClass 存取模式；Notebook 會使用其中資料，刪除 PVC 可能造成永久資料遺失。此例未配置 GPU；GPU 工作負載須採用叢集實際提供的 extended resource 名稱並配置 device plugin，不能只增加任意 `nvidia.com/gpu` 欄位。

唯讀檢查：

```bash
kubectl get crd notebooks.kubeflow.org
kubectl get notebooks -n ml-work
kubectl describe notebook research -n ml-work
kubectl get pods,pvc -n ml-work -o wide
kubectl get events -n ml-work --sort-by=.lastTimestamp
```

Notebook 建立成功只代表 API 接受物件；Pod Ready、磁碟掛載、映像下載、使用者認證及資料存取仍須分別驗證。另須確認該 release 的 CRD/controller 確實已安裝，並查閱 [Notebooks v1 文件](https://www.kubeflow.org/docs/components/notebooks/)。

## 營運、備份與故障

`kubectl get pods -A`、`kubectl get events -A --sort-by=.lastTimestamp` 可先定位控制器、webhook、Pod 排程或映像下載問題；`kubectl get crd`、API discovery 可辨識缺少 CRD。Notebook Pod Pending 常見原因為 PVC 尚未綁定、配額或資源不足；API 建立失敗則檢查 webhook、schema、namespace 與 RBAC。不可透過略過 TLS 驗證或刪除 webhook 排除錯誤。

正式使用前記錄整合版及每個元件版本、CRD 變更、映像 digest、overlay 與身份設定；保護並備份 etcd、Pipelines metadata DB/object store、PVC、Notebook 資料、憑證及 OIDC/外部服務設定。升級前查閱該 release 的 breaking changes，依序備份並演練；回退 controller 不一定能讀取已遷移的資料或 CRD。檢查租戶隔離、Profile 權限、服務帳號、Secret 存取、資源配額及網路出口。多元件版本或外部資料庫/身份提供者不相容，是常見部署限制；應以 pinned release 測試驗證，而非推測。

## 官方來源

- [Kubeflow manifests 26.03.1 release](https://github.com/kubeflow/community-distribution/releases/tag/26.03.1)
- [Kubeflow manifests 固定 release 原始碼](https://github.com/kubeflow/manifests/tree/26.03.1)
- [安裝 Kubeflow 平台](https://www.kubeflow.org/docs/started/installing-kubeflow/)
- [官方支援政策](https://www.kubeflow.org/docs/started/support/)
- [Kubeflow Notebooks 文件](https://www.kubeflow.org/docs/components/notebooks/)
- [Kubeflow Trainer 文件](https://www.kubeflow.org/docs/components/trainer/)
- [Kubeflow Pipelines 文件](https://www.kubeflow.org/docs/components/pipelines/)
