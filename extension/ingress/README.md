# Ingress Controller 和 Gateway API 控制器

[Ingress](../../concepts/objects/ingress.md) 是稳定的 Kubernetes HTTP 路由 API，但其功能已冻结；新功能应优先评估 [Gateway API](https://gateway-api.sigs.k8s.io/)。二者都需要集群中安装并配置控制器，Kubernetes 不会自动创建外部负载均衡器。

## Kubernetes v1.37.1 当前版本（2026-10-05）

| 组件 | 当前稳定版本 | Kubernetes v1.37.1 兼容性 |
| :--- | :--- | :--- |
| [Traefik Proxy](https://github.com/traefik/traefik/releases/tag/v3.7.13) | v3.7.13；[Helm chart 41.6.1](https://github.com/traefik/traefik-helm-chart/releases/tag/v41.6.1) | [v3.7.13 要求](https://raw.githubusercontent.com/traefik/traefik/v3.7.13/docs/content/includes/kubernetes-requirements.md)说明遵循 Kubernetes 版本偏差策略并支持至少最新三个次版本；未找到独立的 v1.37 e2e 矩阵。 |
| [Gateway API](https://github.com/kubernetes-sigs/gateway-api/releases/tag/v1.6.2) | v1.6.2（2026-09-03） | Traefik v3.7.13 发布文档明确支持的 Standard CRD 版本是 v1.6.1；不要将 v1.6.2 表述为该 Traefik 版本已验证的组合。 |
| [Envoy Gateway](https://github.com/envoyproxy/gateway/releases/tag/v1.9.2) | v1.9.2 | [官方兼容矩阵](https://gateway.envoyproxy.io/news/releases/matrix/)仅列 v1.9 支持 Kubernetes 1.33–1.36；未列出 v1.37。 |
| [cert-manager](https://github.com/cert-manager/cert-manager/releases/tag/v1.21.2) | v1.21.2 | [官方支持/测试矩阵](https://cert-manager.io/docs/releases/#currently-supported-releases)仅列 Kubernetes 1.33–1.36；未列出 v1.37。 |
| [ingress-nginx](https://github.com/kubernetes/ingress-nginx) | 已归档 | 上游于 2026-03-24 归档，维护与安全修复已结束；不要在新集群部署。 |

### Traefik + Gateway API（已发布并有版本匹配的组合）

Traefik v3.7.13 文档支持 Standard Gateway API v1.6.1，并说明 Gateway API CRD 不再随 Helm chart 安装。先安装与 Traefik 文档相符的 CRD，再安装固定 chart 版本：

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

chart v41.6.1 的默认值会创建名为 `traefik` 的 `GatewayClass` 和名为 `traefik-gateway` 的默认 `Gateway`。默认 HTTP listener 只接受同一 namespace 的 Routes；需要跨 namespace 时，显式审查并配置 `allowedRoutes`，不要无条件开放整个集群。版本细节见[当前 Traefik 示例](service-discovery-and-load-balancing.md)。

Gateway API v1.6.2 是截至 2026-10-05 的最新发布，但与 Traefik v3.7.13 组合时应按其 v3.7.13 文档使用 v1.6.1。验证新的 Traefik 发布说明后再升级 CRD。

## 历史控制器目录

本目录中基于 Helm `stable` 仓库、旧 NGINX/Traefik annotations、`extensions/v1beta1` Ingress、Ingress v1beta1 后端字段及 `xip.io` 的旧教程不适用于 Kubernetes v1.37.1。相关页面保留的内容均有本地历史说明；不要只改 API 字符串后直接部署。

* [Ingress 基础用法](../../concepts/objects/ingress.md)
* [Traefik Gateway API 示例](service-discovery-and-load-balancing.md)
* [Let's Encrypt / cert-manager 兼容性说明](ingress_letsencrypt.md)
* [Minikube 网络入口说明](minikube-ingress.md)
* [Keepalived VIP 历史实验已归档](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/index.md)
