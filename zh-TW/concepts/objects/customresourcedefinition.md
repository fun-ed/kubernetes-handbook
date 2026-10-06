# CustomResourceDefinition

CustomResourceDefinition（CRD）是 v1.7 新增的無需改變程式碼就可以擴充套件 Kubernetes API 的機制，用來管理自定義物件。它實際上是 ThirdPartyResources（TPR）的升級版本，而 TPR 已經在 v1.8 中棄用。

## API version

Kubernetes v1.37 使用 `apiextensions.k8s.io/v1` 建立 CustomResourceDefinition。v1 API 要求明確提供 `spec.scope`，每個版本都必須有結構化的 `openAPIV3Schema`。

| API version | 歷史狀態 |
| :--- | :--- |
| `apiextensions.k8s.io/v1` | 當前版本 |
| `apiextensions.k8s.io/v1beta1` | v1.22 起不再提供 |
## CRD 範例

下面的 v1 CRD 定義 namespaced `CronTab` 資源，並為其 API 版本提供結構化 schema：

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: crontabs.stable.example.com
spec:
  group: stable.example.com
  scope: Namespaced
  names:
    plural: crontabs
    singular: crontab
    kind: CronTab
    shortNames:
    - ct
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              cronSpec:
                type: string
              image:
                type: string
              replicas:
                type: integer
```

`stable.example.com` 是保留作示例的網域。這個自訂資源只測試 schema；CRD 本身不會啟動 CronTab 工作或拉取 `image` 欄位的映像檔。若要實作排程行為，必須另外部署支援此自訂 API 的控制器。

```yaml
apiVersion: stable.example.com/v1
kind: CronTab
metadata:
  name: my-new-cron-object
spec:
  cronSpec: "*/5 * * * *"
  image: my-awesome-cron-image
```

使用 `kubectl apply -f my-crontab.yaml` 建立自定義資源，再用 `kubectl get crontabs` 檢視。

## Finalizer

Finalizer 用於實現控制器的非同步預刪除鉤子，可以透過 `metadata.finalizers` 來指定 Finalizer。

```yaml
apiVersion: "stable.example.com/v1"
kind: CronTab
metadata:
  finalizers:
  - finalizer.stable.example.com
```

Finalizer 指定後，客戶端刪除物件的操作只會設定 `metadata.deletionTimestamp` 而不是直接刪除。這會觸發正在監聽 CRD 的控制器，控制器執行一些刪除前的清理操作，從列表中刪除自己的 finalizer，然後再重新發起一個刪除操作。此時，被刪除的物件才會真正刪除。

## Validation

CRD v1 使用結構化 OpenAPI schema 驗證自定義資源。欄位的型別和約束放在 `.spec.versions[*].schema.openAPIV3Schema` 中，不需要啟用舊版 feature gate。

下面的例子要求 `spec.cronSpec` 符合 cron 表示式格式，並將 `spec.replicas` 限制在 1 到 10：

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: crontabs.stable.example.com
spec:
  group: stable.example.com
  scope: Namespaced
  names:
    plural: crontabs
    singular: crontab
    kind: CronTab
    shortNames:
    - ct
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              cronSpec:
                type: string
                pattern: '^(\d+|\*)(/\d+)?(\s+(\d+|\*)(/\d+)?){4}$'
              image:
                type: string
              replicas:
                type: integer
                minimum: 1
                maximum: 10
```

CRD schema 驗證會拒絕格式不匹配的物件以及超出範圍的副本數。

下面的物件同時違反 cron 表示式和副本數量限制，因此 API Server 會拒絕它：

```yaml
apiVersion: stable.example.com/v1
kind: CronTab
metadata:
  name: invalid-cron-object
spec:
  cronSpec: "* * * *"
  image: my-awesome-cron-image
  replicas: 15
```

## Subresources

CRD v1 可在對應版本的 `spec.versions[*].subresources` 中開啟 `/status` 和 `/scale`。Scale 子資源使用 schema 中定義的副本數和標籤選擇器路徑：

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: crontabs.stable.example.com
spec:
  group: stable.example.com
  scope: Namespaced
  names:
    plural: crontabs
    singular: crontab
    kind: CronTab
    shortNames:
    - ct
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              cronSpec:
                type: string
              image:
                type: string
              replicas:
                type: integer
          status:
            type: object
            properties:
              replicas:
                type: integer
              labelSelector:
                type: string
    subresources:
      status: {}
      scale:
        specReplicasPath: .spec.replicas
        statusReplicasPath: .status.replicas
        labelSelectorPath: .status.labelSelector
```

```bash
$ kubectl create -f resourcedefinition.yaml
$ kubectl create -f- <<EOF
apiVersion: "stable.example.com/v1"
kind: CronTab
metadata:
  name: my-new-cron-object
spec:
  cronSpec: "* * * * */5"
  image: my-awesome-cron-image
  replicas: 3
EOF

$ kubectl scale --replicas=5 crontabs/my-new-cron-object
crontabs "my-new-cron-object" scaled

$ kubectl get crontabs my-new-cron-object -o jsonpath='{.spec.replicas}'
5
```

## Categories

`spec.names.categories` 可將 CRD 註冊到 `kubectl get <category>` 查詢的資源類別中。以下 CRD 使用同樣的 v1 結構化 schema：

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: crontabs.stable.example.com
spec:
  group: stable.example.com
  scope: Namespaced
  names:
    plural: crontabs
    singular: crontab
    kind: CronTab
    shortNames:
    - ct
    categories:
    - all
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              cronSpec:
                type: string
              image:
                type: string
              replicas:
                type: integer
```

```yaml
# my-crontab.yaml
apiVersion: "stable.example.com/v1"
kind: CronTab
metadata:
  name: my-new-cron-object
spec:
  cronSpec: "* * * * */5"
  image: my-awesome-cron-image
```

```bash
$ kubectl create -f resourcedefinition.yaml
$ kubectl create -f my-crontab.yaml
$ kubectl get all
NAME                          AGE
crontabs/my-new-cron-object   3s
```

## CRD 控制器

在使用 CRD 擴充套件 Kubernetes API 時，通常還需要實現一個新建資源的控制器，監聽新資源的變化情況，並作進一步的處理。

[https://github.com/kubernetes/sample-controller](https://github.com/kubernetes/sample-controller) 提供了一個 CRD 控制器的範例，包括

* 如何註冊資源 `Foo`
* 如何建立、刪除和查詢 `Foo` 物件
* 如何監聽 `Foo` 資源物件的變化情況

## 建置 CRD 控制器

手動建置 CRD 控制器時，需維護 API types、程式碼產生、RBAC、測試及部署資源。新專案可評估 [Kubebuilder](https://book.kubebuilder.io/)；請依所選 Kubebuilder 版本的官方文件初始化專案、產生 API、執行測試及建置部署資源。Kubebuilder 指令和產生的目錄結構會隨版本更新，不要沿用本頁舊版 1.0.1 安裝方式、`dep`、beta API 或舊的 Makefile targets。

本頁舊 Kubebuilder 1.0.1 工作流程及其錯誤修復方式已移至[歷史歸檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/concepts/kubebuilder-v1-workflow.md)。不要直接修改 CRD status 欄位來繞過 API 驗證。

## 參考文件

* [Extend the Kubernetes API with CustomResourceDefinitions](https://kubernetes.io/docs/tasks/access-kubernetes-api/extend-api-custom-resource-definitions/#validation)
* [CustomResourceDefinition API](https://kubernetes.io/docs/reference/kubernetes-api/apiextensions/custom-resource-definition-v1/)
