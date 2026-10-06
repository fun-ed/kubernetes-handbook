# Ingress Controller 和 Gateway API 控制器

[Ingress](../../concepts/objects/ingress.md) 是穩定的 Kubernetes HTTP 路由 API，但其功能已凍結；新功能應優先評估 [Gateway API](https://gateway-api.sigs.k8s.io/)。二者都需要叢集中安裝並設定控制器，Kubernetes 不會自動建立外部負載平衡器。

## Kubernetes v1.37.1 當前版本（2026-10-05）

| 元件 | 當前穩定版本 | Kubernetes v1.37.1 相容性 |
| :--- | :--- | :--- |
| [Traefik Proxy](https://github.com/traefik/traefik/releases/tag/v3.7.13) | v3.7.13；[Helm chart 41.6.1](https://github.com/traefik/traefik-helm-chart/releases/tag/v41.6.1) | [v3.7.13 要求](https://raw.githubusercontent.com/traefik/traefik/v3.7.13/docs/content/includes/kubernetes-requirements.md)說明遵循 Kubernetes 版本偏差策略並支援至少最新三個次版本；未找到獨立的 v1.37 e2e 矩陣。 |
| [Gateway API](https://github.com/kubernetes-sigs/gateway-api/releases/tag/v1.6.2) | v1.6.2（2026-09-03） | Traefik v3.7.13 釋出文件明確支援的 Standard CRD 版本是 v1.6.1；不要將 v1.6.2 表述為該 Traefik 版本已驗證的組合。 |
| [Envoy Gateway](https://github.com/envoyproxy/gateway/releases/tag/v1.9.2) | v1.9.2 | [官方相容矩陣](https://gateway.envoyproxy.io/news/releases/matrix/)僅列 v1.9 支援 Kubernetes 1.33–1.36；未列出 v1.37。 |
| [cert-manager](https://github.com/cert-manager/cert-manager/releases/tag/v1.21.2) | v1.21.2 | [官方支援/測試矩陣](https://cert-manager.io/docs/releases/#currently-supported-releases)僅列 Kubernetes 1.33–1.36；未列出 v1.37。 |
| [ingress-nginx](https://github.com/kubernetes/ingress-nginx) | 已歸檔 | 上游於 2026-03-24 歸檔，維護與安全修復已結束；不要在新叢集部署。 |

### Traefik + Gateway API（已釋出並有版本匹配的組合）

Traefik v3.7.13 文件支援 Standard Gateway API v1.6.1，並說明 Gateway API CRD 不再隨 Helm chart 安裝。先安裝與 Traefik 文件相符的 CRD，再安裝固定 chart 版本：

```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.6.1/standard-install.yaml
helm repo add traefik https://traefik.github.io/charts
helm repo update
helm upgrade --install traefik traefik/traefik \
  --version 41.6.1 \
  --namespace traefik \
  --create-namespace \
  --set providers.kubernetesGateway.enabled=true
```

chart v41.6.1 的預設值會建立名為 `traefik` 的 `GatewayClass` 和名為 `traefik-gateway` 的預設 `Gateway`。預設 HTTP listener 只接受同一 namespace 的 Routes；需要跨 namespace 時，顯式審查並設定 `allowedRoutes`，不要無條件開放整個叢集。版本細節見[當前 Traefik 範例](service-discovery-and-load-balancing.md)。

Gateway API v1.6.2 是截至 2026-10-05 的最新發布，但與 Traefik v3.7.13 組合時應按其 v3.7.13 文件使用 v1.6.1。驗證新的 Traefik 釋出說明後再升級 CRD。

## 歷史控制器目錄

本目錄中基於 Helm `stable` 儲存庫、舊 NGINX/Traefik annotations、`extensions/v1beta1` Ingress、Ingress v1beta1 後端欄位及 `xip.io` 的舊教程不適用於 Kubernetes v1.37.1。相關頁面保留的內容均有本地歷史說明；不要只改 API 字串後直接部署。

* [Ingress 基礎用法](../../concepts/objects/ingress.md)
* [Traefik Gateway API 範例](service-discovery-and-load-balancing.md)
* [Let's Encrypt / cert-manager 相容性說明](ingress_letsencrypt.md)
* [Minikube 網路入口說明](minikube-ingress.md)
* [Keepalived VIP 歷史實驗已歸檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/index.md)
