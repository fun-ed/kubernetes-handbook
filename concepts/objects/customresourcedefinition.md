# CustomResourceDefinition

CustomResourceDefinition（CRD）是 v1.7 新增的无需改变代码就可以扩展 Kubernetes API 的机制，用来管理自定义对象。它实际上是 ThirdPartyResources（TPR）的升级版本，而 TPR 已经在 v1.8 中弃用。

## API version

Kubernetes v1.37 使用 `apiextensions.k8s.io/v1` 创建 CustomResourceDefinition。v1 API 要求明确提供 `spec.scope`，每个版本都必须有结构化的 `openAPIV3Schema`。

| API version | 历史状态 |
| :--- | :--- |
| `apiextensions.k8s.io/v1` | 当前版本 |
| `apiextensions.k8s.io/v1beta1` | v1.22 起不再提供 |
## CRD 示例

下面的 v1 CRD 定义 namespaced `CronTab` 资源，并为其 API 版本提供结构化 schema：

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

使用 `kubectl apply -f my-crontab.yaml` 创建自定义资源，再用 `kubectl get crontabs` 查看。

## Finalizer

Finalizer 用于实现控制器的异步预删除钩子，可以通过 `metadata.finalizers` 来指定 Finalizer。

```yaml
apiVersion: "stable.example.com/v1"
kind: CronTab
metadata:
  finalizers:
  - finalizer.stable.example.com
```

Finalizer 指定后，客户端删除对象的操作只会设置 `metadata.deletionTimestamp` 而不是直接删除。这会触发正在监听 CRD 的控制器，控制器执行一些删除前的清理操作，从列表中删除自己的 finalizer，然后再重新发起一个删除操作。此时，被删除的对象才会真正删除。

## Validation

CRD v1 使用结构化 OpenAPI schema 验证自定义资源。字段的类型和约束放在 `.spec.versions[*].schema.openAPIV3Schema` 中，不需要启用旧版 feature gate。

下面的例子要求 `spec.cronSpec` 符合 cron 表达式格式，并将 `spec.replicas` 限制在 1 到 10：

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

CRD schema 校验会拒绝格式不匹配的对象以及超出范围的副本数。

下面的对象同时违反 cron 表达式和副本数量限制，因此 API Server 会拒绝它：

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

CRD v1 可在对应版本的 `spec.versions[*].subresources` 中开启 `/status` 和 `/scale`。Scale 子资源使用 schema 中定义的副本数和标签选择器路径：

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

`spec.names.categories` 可将 CRD 注册到 `kubectl get <category>` 查询的资源类别中。以下 CRD 使用同样的 v1 结构化 schema：

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

在使用 CRD 扩展 Kubernetes API 时，通常还需要实现一个新建资源的控制器，监听新资源的变化情况，并作进一步的处理。

[https://github.com/kubernetes/sample-controller](https://github.com/kubernetes/sample-controller) 提供了一个 CRD 控制器的示例，包括

* 如何注册资源 `Foo`
* 如何创建、删除和查询 `Foo` 对象
* 如何监听 `Foo` 资源对象的变化情况

## 建置 CRD 控制器

手動建置 CRD 控制器時，需維護 API types、程式碼產生、RBAC、測試及部署資源。新專案可評估 [Kubebuilder](https://book.kubebuilder.io/)；請依所選 Kubebuilder 版本的官方文件初始化專案、產生 API、執行測試及建置部署資源。Kubebuilder 指令和產生的目錄結構會隨版本更新，不要沿用本頁舊版 1.0.1 安裝方式、`dep`、beta API 或舊的 Makefile targets。

本頁舊 Kubebuilder 1.0.1 工作流程及其錯誤修復方式已移至[歷史歸檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/concepts/kubebuilder-v1-workflow.md)。不要直接修改 CRD status 欄位來繞過 API 驗證。

## 参考文档

* [Extend the Kubernetes API with CustomResourceDefinitions](https://kubernetes.io/docs/tasks/access-kubernetes-api/extend-api-custom-resource-definitions/#validation)
* [CustomResourceDefinition API](https://kubernetes.io/docs/reference/kubernetes-api/apiextensions/custom-resource-definition-v1/)

