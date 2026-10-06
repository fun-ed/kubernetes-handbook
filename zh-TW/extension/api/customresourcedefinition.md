# CustomResourceDefinition

CustomResourceDefinition（CRD）允許透過宣告式 schema 將自定義資源註冊到 Kubernetes API，而無需修改 kube-apiserver。Kubernetes v1.37.1 中建立 CRD 的 API 為 `apiextensions.k8s.io/v1`；CRD 不會自動授予資源權限，必須另行設定 RBAC。

| CRD API | Kubernetes 版本 | 約束 |
| :--- | :--- | :--- |
| `apiextensions.k8s.io/v1` | 穩定版，自 v1.16 起；v1.22+ 唯一可用版本 | 每個 served version 都必須有 structural OpenAPI schema。 |
| `apiextensions.k8s.io/v1beta1` | v1.22 起移除 | 不能在 Kubernetes v1.37.1 使用。 |

## Kubernetes v1.37.1 CRD 範例

CRD 的 `spec.versions[]` 包含每個 API 版本的 `schema` 和可選 `subresources`。下面的結構化 schema 保留 `spec`/`status` 欄位型別，提供 `/status` 和 `/scale` 子資源；至少一個 served version 必須設為 `storage: true`。

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
            required:
            - cronSpec
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

```yaml
apiVersion: stable.example.com/v1
kind: CronTab
metadata:
  name: example
spec:
  cronSpec: "*/5 * * * *"
  image: registry.example.com/cron
  replicas: 2
```

多版本 CRD 還需要選擇 storage version、實現版本轉換並制定舊資料遷移/移除計劃；不要把新增 `served: true` 當作自動的欄位轉換。需要 webhook 轉換時，按當前 CRD API 文件設定 `spec.conversion` 和 TLS 服務。

```bash
kubectl apply -f crontab-crd.yaml
kubectl get crd crontabs.stable.example.com
kubectl apply -f crontab.yaml
kubectl get crontabs
```

官方參考：[擴充套件 API 與自定義資源](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)、[宣告式 CRD schema / validation](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/)。

> **歷史 API 說明：** 以下舊的 CRD 定義清單使用 Kubernetes v1.22 起已移除的 `apiextensions.k8s.io/v1beta1`，且不包含 v1 必需的 structural schema，不能在 v1.37.1 部署。Validation、Subresources 和 Categories 章節中的舊欄位佈局僅供版本沿革參考；當前結構請使用上方 `apiextensions.k8s.io/v1` 範例。Finalizer 機制本身仍適用於當前 CRD。

> 舊版 `apiextensions.k8s.io/v1beta1` manifest、validation/subresource/categories 舊欄位範例及 Kubebuilder 1.0.1 安裝流程已封存，不能部署到 v1.37.1。當前 CRD schema 與子資源範例見本頁上方；[封存的原始 CRD 範例與舊工具鏈](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/zh-TW/extension/api/customresourcedefinition.md)。

## Finalizer（當前仍適用）

Finalizer 用於實現控制器的非同步預刪除鉤子，可以透過 `metadata.finalizers` 來指定 Finalizer。

```yaml
apiVersion: "stable.example.com/v1"
kind: CronTab
metadata:
  finalizers:
  - finalizer.stable.example.com
```

Finalizer 指定後，客戶端刪除物件的操作會先設定 `metadata.deletionTimestamp` 而不是立即刪除。這會觸發監聽 CRD 的控制器；控制器完成清理後移除自己的 finalizer。所有 finalizer 移除後，API server 才會最終刪除物件。


## 參考文件

* [Extend the Kubernetes API with CustomResourceDefinitions](https://kubernetes.io/docs/tasks/access-kubernetes-api/extend-api-custom-resource-definitions/#validation)
* [CRD schema / validation](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/)
