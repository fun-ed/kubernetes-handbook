# Argo Workflows

Argo Workflows 是 Kubernetes 原生工作流引擎。它使用 `Workflow` CRD 描述任務 DAG、並行步驟、產物和重試策略。Argo Workflows 與 Argo CD 是不同專案，本章只介紹 Workflows。

> **當前版本（2026-10-05）**：v4.1.4 是本手冊資料截點前的最新穩定版。官方釋出頁提供對應版本的 CLI 和控制器安裝檔案：[v4.1.4 release](https://github.com/argoproj/argo-workflows/releases/tag/v4.1.4)。本次未找到官方材料明確宣告該版本支援 Kubernetes v1.37；使用前請核對上游相容說明。

## 安裝測試環境

官方 Quick Start 明確說明下面是試用設定，不適合生產。它從固定版本釋出頁安裝 controller，並只在 `argo` namespace 中建立資源：

```bash
ARGO_WORKFLOWS_VERSION=v4.1.4
kubectl create namespace argo
kubectl apply --namespace argo \
  --filename "https://github.com/argoproj/argo-workflows/releases/download/${ARGO_WORKFLOWS_VERSION}/quick-start-minimal.yaml"
```

安裝 CLI（以下為 Linux/macOS amd64）：

```bash
ARGO_WORKFLOWS_VERSION=v4.1.4
ARGO_OS=linux
ARGO_ARCH=amd64
curl -fsSLO "https://github.com/argoproj/argo-workflows/releases/download/${ARGO_WORKFLOWS_VERSION}/argo-${ARGO_OS}-${ARGO_ARCH}.gz"
gunzip "argo-${ARGO_OS}-${ARGO_ARCH}.gz"
chmod +x "argo-${ARGO_OS}-${ARGO_ARCH}"
sudo install "argo-${ARGO_OS}-${ARGO_ARCH}" /usr/local/bin/argo
argo version
```

其他平台資產見釋出頁。生產安裝前，按[官方安裝文件](https://argo-workflows.readthedocs.io/en/latest/installation/)選擇部署方式、持久化與身分驗證設定，並為工作流設定專用 ServiceAccount 和最小 RBAC。不要給預設 ServiceAccount 綁定 `cluster-admin`。

## 提交和檢視 Workflow

用與 controller 相同的 v4.1.4 tag 中的範例提交工作流：

```bash
argo submit --namespace argo --watch \
  https://raw.githubusercontent.com/argoproj/argo-workflows/v4.1.4/examples/hello-world.yaml
argo list --namespace argo
argo logs --namespace argo @latest
```

Workflow 是 Kubernetes 自定義資源。下面摘錄自同一 tag 的 [hello-world.yaml](https://raw.githubusercontent.com/argoproj/argo-workflows/v4.1.4/examples/hello-world.yaml)：

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: hello-world-
spec:
  entrypoint: whalesay
  templates:
    - name: whalesay
      container:
        image: busybox:1.37.0
        command: [echo]
        args: ["hello world"]
```

樣例映像檔僅用於演示；生產工作流應使用組織批准、固定版本或 digest 的映像檔，並按任務權限限制 ServiceAccount、Secret 與網路存取。

## 生產資料

- [Argo Workflows 安裝指南](https://argo-workflows.readthedocs.io/en/latest/installation/)
- [Workflow 規範](https://argo-workflows.readthedocs.io/en/latest/workflow-concepts/)
- [Argo Workflows v4.1.4 釋出說明](https://github.com/argoproj/argo-workflows/releases/tag/v4.1.4)

舊章中的 Argo 2.0/2.1 CLI、`argo-ci` chart、Tiller、`stable/minio` 和預設 ServiceAccount 的叢集管理員綁定已移除，不再作為安裝建議。

## 專用工作流程身分與權限

Quick Start 套件明確供評估使用，不適用於正式環境。Workflow pod 使用 `spec.serviceAccountName`；若未指定，則使用該命名空間的 `default` ServiceAccount。正式工作流程應指定專用 ServiceAccount，並只綁定任務需要的權限。v4.1.4 executor 的最低需求是在命名空間範圍內，允許對 API group `argoproj.io` 的 `workflowtaskresults` 執行 create 與 patch。

以下範例是在 Workflow 執行所在命名空間建立最小專用任務身分，不授予任意建立 Kubernetes 物件的權限。

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: workflow-task
  namespace: argo
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: workflow-task-executor
  namespace: argo
rules:
  - apiGroups: [argoproj.io]
    resources: [workflowtaskresults]
    verbs: [create, patch]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: workflow-task-executor
  namespace: argo
subjects:
  - kind: ServiceAccount
    name: workflow-task
    namespace: argo
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: workflow-task-executor
```

Workflow controller 有自己觀察及管理 Workflow 資源的權限；不要將這些 controller 權限與授予使用者任務 pod 的權限混為一談。只有在任務確實需要 Kubernetes API 存取時，才增加任務專用權限，並將資源、命名空間和 verbs 限制在必要範圍。不要綁定 `cluster-admin`，也不要依賴共用的 default ServiceAccount。

## Steps 與 DAG 範例

Workflow 同時是規格和單次執行的狀態紀錄。Template 定義任務內容，entrypoint 指定起始 template。在 `steps` template 中，每個巢狀清單依序執行，同一清單中的項目可平行執行。DAG 會明確列出相依關係。以下範例先執行 `prepare`，接著平行執行 `left` 和 `right`，兩者成功後再執行 `finish`。`busybox:1.37.0` 是 v4.1.4 上游 hello-world 範例使用的固定 tag；若需更高供應鏈保證，請選用核准映像檔與不可變 digest。

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: small-dag-
spec:
  serviceAccountName: workflow-task
  entrypoint: pipeline
  templates:
    - name: pipeline
      dag:
        tasks:
          - name: prepare
            template: say
            arguments:
              parameters: [{name: message, value: prepare}]
          - name: left
            depends: prepare
            template: say
            arguments:
              parameters: [{name: message, value: left}]
          - name: right
            depends: prepare
            template: say
            arguments:
              parameters: [{name: message, value: right}]
          - name: finish
            depends: "left && right"
            template: say
            arguments:
              parameters: [{name: message, value: finish}]
    - name: say
      inputs:
        parameters:
          - name: message
      container:
        image: busybox:1.37.0
        command: [echo]
        args: ["{{inputs.parameters.message}}"]
```

先在拋棄式叢集與命名空間安裝 v4.1.4 Quick Start manifest，再套用上述 ServiceAccount、Role 和 RoleBinding。將 Workflow 存為 `small-dag.yaml`；以下命令會提交並觀察執行狀態，不需公開 server endpoint：

```bash
argo submit -n argo --watch small-dag.yaml
argo list -n argo
argo get -n argo @latest
argo logs -n argo @latest
```

提交者需有權在 `argo` 建立 Workflow，且假設已設定好 CLI 存取方式。`--watch` 會等候執行完成。`list`、`get` 和 `logs` 用來檢視執行結果。選用 Argo Server UI 時，可使用明確綁定本機的 port-forward；請參閱[v4.1.4 Quick Start](https://github.com/argoproj/argo-workflows/blob/v4.1.4/docs/quick-start.md)。不要為了方便而公開 server。

重試可能重複執行任務副作用。設定重試前，請讓任務具備冪等性，或使用外部去重／鎖定機制。產物需要已設定 artifact repository 和適當憑證，單靠 Workflow manifest 不會設定儲存空間。設定 TTL 前，先決定 log、輸出和執行中繼資料要保留多久。刪除過期 Workflow 物件不保證外部產物也會清除。

## 安全操作與診斷

這些 CLI 範例假設已設定具備隔離環境 `argo` 命名空間存取權的已驗證 CLI context。若提交被拒絕，請檢查提交者在命名空間中的 RBAC。若 pod 無法回報任務結果，請確認 Workflow 指定的 ServiceAccount 在 Workflow 命名空間有 `workflowtaskresults` RoleBinding，並確認 CRD/controller 安裝正常。若 pod 一直 Pending 或無法取得映像檔，先檢查 pod events、排程容量、映像檔參照和 registry 存取，不要先擴大 Workflow 權限。DAG 節點失敗時，透過 `argo get` 和 log 檢查原因；不要用重試掩蓋固定的輸入或權限錯誤。

v4.1.4 官方釋出於 2026-09-18。該版本存在及其 API 文件並不能證明支援 Kubernetes v1.37；本手冊基準為 v1.37.1，未找到此版本肯定支援 v1.37 的上游矩陣。正式部署前請檢視[釋出頁](https://github.com/argoproj/argo-workflows/releases/tag/v4.1.4)、[RBAC 指引](https://github.com/argoproj/argo-workflows/blob/v4.1.4/docs/workflow-rbac.md)、[Workflow 概念](https://github.com/argoproj/argo-workflows/blob/v4.1.4/docs/workflow-concepts.md)及[安裝指南](https://github.com/argoproj/argo-workflows/blob/v4.1.4/docs/installation.md)。升級前先在測試環境驗證 CRD 與 controller 相容性，保留 Workflow 和產物資料，並在不刪除持久資料的情況下演練復原。
