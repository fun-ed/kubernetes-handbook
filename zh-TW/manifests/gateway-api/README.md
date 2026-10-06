# Gateway API 範例

本目錄中的範例是依據 Gateway API v1.6.2 編寫（截至 2026-10-05 的最新穩定版本）。Gateway API CRD 是 API 定義，不是流量控制器；每個控制器對標準、實驗性資源和欄位的支援情況，都需要個別確認。儲存庫中的基本 HTTP/HTTPS 流程已在隔離的 Kubernetes v1.37.1 kind 叢集中驗證，請參閱[相容性驗證記錄](../../setup/kubernetes-v1.37.md)；這不代表所有功能或生產環境都通過相容性認證。

## CRD 與控制器

安裝標準資源時，請使用官方 v1.6.2 release bundle：

```bash
kubectl apply --server-side -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.6.2/standard-install.yaml
```

只有在需要實驗性 API（例如 `retry-budget.yaml`）時，才安裝實驗性 bundle：

```bash
kubectl apply --server-side -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.6.2/experimental-install.yaml
```

必須另外安裝能實作所需 API／功能的 Gateway 控制器。儲存庫中的 Traefik 範例來自 v3.7.13；該 release tag 的文件指定使用 Gateway API v1.6.1。本次 v1.6.2 組合僅通過下述基本路由的本機 smoke test，不代表上游正式支援範圍擴大，也不證明其他控制器、`ListenerSet` 或實驗性策略可用。

## 範例

- `basic/`：標準 `GatewayClass`、`Gateway` 和 `HTTPRoute`；先部署控制器，再視需要套用。預設命名空間中必須先有 `api-service:8080`、`app-service:3000` 和 `default-service:80` 這三個後端 Service。
- `migration/ingress-to-gateway.yaml`：標準 v1 資源的遷移範例；需預先建立後端 Service 和 `default/example-com-tls` Secret。Gateway API v1.6.2 沒有標準 `CORSPolicy`，CORS 必須使用控制器明確支援的實作專屬設定。
- `v1.3-features/request-mirroring.yaml`：`HTTPRoute` 標準 v1 請求鏡像欄位；目標 Service 必須存在，控制器也必須支援 `RequestMirror`。
- `v1.3-features/xlistenersets.yaml`：使用已進入標準 channel 的 `ListenerSet` v1，而非不存在的 `XListenerSet`。這是需要相應控制器支援的功能範例；GatewayClass 中的 controller name 是佔位值，必須替換成實際值。HTTPS 範例還需要 `gateway-system/wildcard-tls` Secret。
- `v1.3-features/retry-budget.yaml`：實驗性 `gateway.networking.x-k8s.io/v1alpha1 XBackendTrafficPolicy`，依據 v1.6.2 experimental CRD 編寫。它會限制由其他機制發起的重試流量，本身不會設定重試次數或條件；必須使用實作此策略的控制器。Traefik v3.7.13 文件未確認是否支援此功能。
- `cors-policy.yaml` 已移至歷史封存，因為 Gateway API v1.6.2 不會提供 `CORSPolicy`；請參閱[封存索引](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/index.md)。

只套用上述清單中符合您控制器與前置條件的檔案。目前的 `v1.3-features/` 目錄包含標準與實驗性範例；除非需要實驗性 API，否則不要安裝實驗性 bundle。

```bash
# 本仓库 Traefik 示例；LoadBalancer Service 还需要云端或集群外部负载均衡实现。
kubectl apply -f ../traefik-ingress/traefik-rbac.yaml -f ../traefik-ingress/traefik-deployment.yaml
kubectl apply -f basic/gatewayclass.yaml
kubectl apply -f basic/gateway.yaml -f basic/httproute.yaml
```

官方來源：[Gateway API v1.6.2 release](https://github.com/kubernetes-sigs/gateway-api/releases/tag/v1.6.2)、[Traefik v3.7.13 Gateway provider 文件](https://raw.githubusercontent.com/traefik/traefik/v3.7.13/docs/content/reference/install-configuration/providers/kubernetes/kubernetes-gateway.md)。