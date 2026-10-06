# CustomResourceDefinition

CustomResourceDefinition（CRD）允许通过声明式 schema 将自定义资源注册到 Kubernetes API，而无需修改 kube-apiserver。Kubernetes v1.37.1 中创建 CRD 的 API 为 `apiextensions.k8s.io/v1`；CRD 不会自动授予资源权限，必须另行配置 RBAC。

| CRD API | Kubernetes 版本 | 约束 |
| :--- | :--- | :--- |
| `apiextensions.k8s.io/v1` | 稳定版，自 v1.16 起；v1.22+ 唯一可用版本 | 每个 served version 都必须有 structural OpenAPI schema。 |
| `apiextensions.k8s.io/v1beta1` | v1.22 起移除 | 不能在 Kubernetes v1.37.1 使用。 |

## Kubernetes v1.37.1 CRD 示例

CRD 的 `spec.versions[]` 包含每个 API 版本的 `schema` 和可选 `subresources`。下面的结构化 schema 保留 `spec`/`status` 字段类型，提供 `/status` 和 `/scale` 子资源；至少一个 served version 必须设为 `storage: true`。

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

多版本 CRD 还需要选择 storage version、实现版本转换并制定旧数据迁移/移除计划；不要把新增 `served: true` 当作自动的字段转换。需要 webhook 转换时，按当前 CRD API 文档配置 `spec.conversion` 和 TLS 服务。

```bash
kubectl apply -f crontab-crd.yaml
kubectl get crd crontabs.stable.example.com
kubectl apply -f crontab.yaml
kubectl get crontabs
```

官方参考：[扩展 API 与自定义资源](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)、[声明式 CRD schema / validation](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/)。

> **历史 API 说明：** 以下旧的 CRD 定义清单使用 Kubernetes v1.22 起已移除的 `apiextensions.k8s.io/v1beta1`，且不包含 v1 必需的 structural schema，不能在 v1.37.1 部署。Validation、Subresources 和 Categories 章节中的旧字段布局仅供版本沿革参考；当前结构请使用上方 `apiextensions.k8s.io/v1` 示例。Finalizer 机制本身仍适用于当前 CRD。

> 旧版 `apiextensions.k8s.io/v1beta1` manifest、validation/subresource/categories 旧字段示例及 Kubebuilder 1.0.1 安装流程已封存，不能部署到 v1.37.1。当前 CRD schema 与子资源示例见本页上方；[封存的原始 CRD 示例与旧工具链](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/extension/api/customresourcedefinition.md)。

## Finalizer（当前仍适用）

Finalizer 用于实现控制器的异步预删除钩子，可以通过 `metadata.finalizers` 来指定 Finalizer。

```yaml
apiVersion: "stable.example.com/v1"
kind: CronTab
metadata:
  finalizers:
  - finalizer.stable.example.com
```

Finalizer 指定后，客户端删除对象的操作会先设置 `metadata.deletionTimestamp` 而不是立即删除。这会触发监听 CRD 的控制器；控制器完成清理后移除自己的 finalizer。所有 finalizer 移除后，API server 才会最终删除对象。

## 参考文档

* [Extend the Kubernetes API with CustomResourceDefinitions](https://kubernetes.io/docs/tasks/access-kubernetes-api/extend-api-custom-resource-definitions/#validation)
* [CRD schema / validation](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/)

