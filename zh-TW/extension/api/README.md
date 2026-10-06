# API 擴充套件

Kubernetes 提供 API 聚合（API Aggregation）和 CustomResourceDefinition（CRD）兩種主要方式擴充套件 Kubernetes API。擴充套件 API 不會自動獲得權限；存取仍受 authentication、authorization（例如 RBAC）和 admission 控制。

* **CRD** 將宣告式、自定義 API 型別註冊到 kube-apiserver。資源資料使用 Kubernetes API/etcd 路徑，通常配合 controller 處理業務邏輯。
* **API Aggregation** 透過 `APIService` 將 API group/version 路由到獨立的 extension apiserver，適合需要自定義儲存或不符合宣告式資源模型的 API。

## 選擇 CRD 或 API Aggregation

| 能力 | CRD | Aggregated API |
| :--- | :--- | :--- |
| 需要部署的服務 | CRD 本身由 kube-apiserver 提供；業務 controller 通常獨立部署 | 需要可用的 extension apiserver，並用 APIService 註冊 |
| Schema / OpenAPI | `apiextensions.k8s.io/v1` 中提供 structural OpenAPI schema；可驗證、剪枝未知欄位、生成 OpenAPI 文件 | 由 extension apiserver 定義並提供 |
| 預設值與 CEL validation | Schema 可宣告 default 和 CEL validation；更復雜的准入邏輯可用 admission webhook | Extension apiserver 實現 |
| 多版本 | 支援多個 served versions、單一 storage version 和版本轉換；需要正確設定轉換與儲存遷移 | Extension apiserver 實現 |
| Status / Scale 子資源 | 支援 CRD schema 中宣告的 `/status` 和 `/scale` | 可自行實現 |
| 自定義儲存 | 不支援替換 kube-apiserver 的儲存後端 | 可自行實現 |
| 自定義子資源、Protobuf | 不提供任意子資源；CRD 使用 JSON API 表示 | 可自行實現 |
| Patch | 不支援 strategic merge patch；可用 JSON merge patch、JSON patch 和 server-side apply | Extension apiserver 實現 |

Kubernetes v1.37.1 中 CRD API 必須使用 `apiextensions.k8s.io/v1`，並為每個 served version 提供 structural schema；舊 `v1beta1` CRD API 已於 Kubernetes v1.22 移除。不要僅把舊清單的 `apiVersion` 改為 `v1`，因為 schema、版本和子資源欄位佈局也不同。

官方參考：[擴充套件 API](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/)、[Custom Resources / CRD](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)、[CRD schema 和驗證](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/)。

## 使用方法

* [API Aggregation](aggregation.md)
* [CustomResourceDefinition](customresourcedefinition.md)
