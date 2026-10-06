# Gateway API 示例

本目录示例按 Gateway API v1.6.2 编写（截至 2026-10-05 的最新稳定版本）。Gateway API CRD 是 API 定义，不是流量控制器；每个控制器对标准、实验性资源及字段的支持均需单独确认。仓库的基础 HTTP/HTTPS 流程已在隔离的 Kubernetes v1.37.1 kind 集群中验证，见[适配验证记录](../../setup/kubernetes-v1.37.md)；这不是所有功能或生产环境的兼容认证。

## CRD 与控制器

安装标准资源时使用官方 v1.6.2 release bundle：

```bash
kubectl apply --server-side -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.6.2/standard-install.yaml
```

只有需要实验性 API（例如 `retry-budget.yaml`）时才安装实验性 bundle：

```bash
kubectl apply --server-side -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.6.2/experimental-install.yaml
```

必须另行安装实现所需 API/功能的 Gateway 控制器。仓库内的 Traefik 示例来自 v3.7.13；该 release tag 的文档指定 Gateway API v1.6.1。本次 v1.6.2 组合仅通过下述基础路由的本地 smoke test，不扩大上游正式支持范围，也不证明其他控制器、`ListenerSet` 或实验性策略可用。

## 示例

- `basic/`：标准 `GatewayClass`、`Gateway` 和 `HTTPRoute`；先部署控制器，再按需应用。默认命名空间中必须先存在 `api-service:8080`、`app-service:3000` 和 `default-service:80` 三个后端 Service。
- `migration/ingress-to-gateway.yaml`：标准 v1 资源的迁移示例；需预先创建后端 Service 和 `default/example-com-tls` Secret。Gateway API v1.6.2 没有标准 `CORSPolicy`，CORS 必须使用控制器明确支持的实现专属配置。
- `v1.3-features/request-mirroring.yaml`：`HTTPRoute` 标准 v1 请求镜像字段；目标 Service 必须存在，控制器也必须支持 `RequestMirror`。
- `v1.3-features/xlistenersets.yaml`：使用已进入标准 channel 的 `ListenerSet` v1，而非不存在的 `XListenerSet`。这是需要相应控制器支持的功能示例；GatewayClass 中的 controller name 是占位值，须换成实际值。HTTPS 示例另需 `gateway-system/wildcard-tls` Secret。
- `v1.3-features/retry-budget.yaml`：实验性 `gateway.networking.x-k8s.io/v1alpha1 XBackendTrafficPolicy`，按 v1.6.2 experimental CRD 编写。它限制已由其他机制发起的重试流量，本身不配置重试次数或条件；必须使用实现该策略的控制器。Traefik v3.7.13 文档未确认支持它。
- `cors-policy.yaml` was moved to the historical archive because Gateway API v1.6.2 does not serve `CORSPolicy`; see the [archive index](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/index.md).

Apply only the files listed above that match your controller and prerequisites. The current `v1.3-features/` directory contains standard and experimental examples; do not install the experimental bundle unless you need an experimental API.

```bash
# 本仓库 Traefik 示例；LoadBalancer Service 还需要云端或集群外部负载均衡实现。
kubectl apply -f ../traefik-ingress/traefik-rbac.yaml -f ../traefik-ingress/traefik-deployment.yaml
kubectl apply -f basic/gatewayclass.yaml
kubectl apply -f basic/gateway.yaml -f basic/httproute.yaml
```

官方来源：[Gateway API v1.6.2 release](https://github.com/kubernetes-sigs/gateway-api/releases/tag/v1.6.2)、[Traefik v3.7.13 Gateway provider 文档](https://raw.githubusercontent.com/traefik/traefik/v3.7.13/docs/content/reference/install-configuration/providers/kubernetes/kubernetes-gateway.md)。