# API 扩展

Kubernetes 提供 API 聚合（API Aggregation）和 CustomResourceDefinition（CRD）两种主要方式扩展 Kubernetes API。扩展 API 不会自动获得权限；访问仍受 authentication、authorization（例如 RBAC）和 admission 控制。

* **CRD** 将声明式、自定义 API 类型注册到 kube-apiserver。资源数据使用 Kubernetes API/etcd 路径，通常配合 controller 处理业务逻辑。
* **API Aggregation** 通过 `APIService` 将 API group/version 路由到独立的 extension apiserver，适合需要自定义存储或不符合声明式资源模型的 API。

## 选择 CRD 或 API Aggregation

| 能力 | CRD | Aggregated API |
| :--- | :--- | :--- |
| 需要部署的服务 | CRD 本身由 kube-apiserver 提供；业务 controller 通常独立部署 | 需要可用的 extension apiserver，并用 APIService 注册 |
| Schema / OpenAPI | `apiextensions.k8s.io/v1` 中提供 structural OpenAPI schema；可校验、剪枝未知字段、生成 OpenAPI 文档 | 由 extension apiserver 定义并提供 |
| 默认值与 CEL validation | Schema 可声明 default 和 CEL validation；更复杂的准入逻辑可用 admission webhook | Extension apiserver 实现 |
| 多版本 | 支持多个 served versions、单一 storage version 和版本转换；需要正确配置转换与存储迁移 | Extension apiserver 实现 |
| Status / Scale 子资源 | 支持 CRD schema 中声明的 `/status` 和 `/scale` | 可自行实现 |
| 自定义存储 | 不支持替换 kube-apiserver 的存储后端 | 可自行实现 |
| 自定义子资源、Protobuf | 不提供任意子资源；CRD 使用 JSON API 表示 | 可自行实现 |
| Patch | 不支持 strategic merge patch；可用 JSON merge patch、JSON patch 和 server-side apply | Extension apiserver 实现 |

Kubernetes v1.37.1 中 CRD API 必须使用 `apiextensions.k8s.io/v1`，并为每个 served version 提供 structural schema；旧 `v1beta1` CRD API 已于 Kubernetes v1.22 移除。不要仅把旧清单的 `apiVersion` 改为 `v1`，因为 schema、版本和子资源字段布局也不同。

官方参考：[扩展 API](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/)、[Custom Resources / CRD](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)、[CRD schema 和验证](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/)。

## 使用方法

* [API Aggregation](aggregation.md)
* [CustomResourceDefinition](customresourcedefinition.md)
