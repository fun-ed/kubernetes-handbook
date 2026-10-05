# Traefik + Kubernetes Gateway API

Ingress 是仍受支持但功能冻结的 API；本页将旧 Traefik Helm `stable` 仓库、旧 Dashboard 部署和 `extensions/v1beta1` Ingress 示例替换为固定版本的 Gateway API 部署。不要把旧 Traefik v1/v2 annotations 或旧 chart values 直接移植到 v3。

## Kubernetes v1.37.1 版本组合（2026-10-05）

* Traefik Proxy v3.7.13，Helm chart v41.6.1。
* Traefik v3.7.13 的 Gateway provider 文档支持 Gateway API Standard v1.6.1；Gateway API CRD 由用户单独安装，chart 不再包含 CRD。
* Gateway API v1.6.2 已发布，但不是 Traefik v3.7.13 文档验证的组合。本文固定使用 v1.6.1。
* Traefik 文档说明其遵循 Kubernetes 版本偏差策略并支持至少最新三个次版本；截至本文日期 Kubernetes v1.37 属于该支持窗口，但上游没有单独列出的 v1.37 e2e 矩阵。

来源：[Traefik v3.7.13 发布](https://github.com/traefik/traefik/releases/tag/v3.7.13)、[Traefik chart v41.6.1](https://github.com/traefik/traefik-helm-chart/releases/tag/v41.6.1)、[Traefik v3.7.13 Gateway API provider 要求](https://raw.githubusercontent.com/traefik/traefik/v3.7.13/docs/content/reference/install-configuration/providers/kubernetes/kubernetes-gateway.md)、[Gateway API v1.6.1 发布](https://github.com/kubernetes-sigs/gateway-api/releases/tag/v1.6.1)。

## 安装

下面先安装 Traefik 文档验证的 Gateway API Standard CRD，再用固定 chart 版本启用 Kubernetes Gateway provider。Helm chart 自动创建 Gateway API 所需 RBAC，并创建默认 `GatewayClass` 和 `Gateway`。

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

该 chart 默认创建名为 `traefik` 的 `GatewayClass`、名为 `traefik-gateway` 的 `Gateway`，并在 `traefik` namespace 建立 HTTP listener。默认仅允许 Gateway 同 namespace 的 Route；这样可以避免无意间授权其他 namespace。检查部署结果：

```bash
kubectl get gatewayclass traefik
kubectl -n traefik get gateway traefik-gateway
kubectl -n traefik get service traefik
```

`Gateway` 是否获得外部地址取决于集群的 `LoadBalancer` 实现。没有云负载均衡器时，需要为环境配置 LoadBalancer 实现或使用受控的 NodePort/外部入口；Helm 安装本身不会分配公共 IP。

## 将 HTTPRoute 绑定到应用 Service

将 `whoami` 和 `80` 替换为已经部署在 `traefik` namespace 的应用 Service 名称和端口。若 Route 在其他 namespace，需有意配置 listener 的 `allowedRoutes.namespaces`，并确认授权范围。

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: whoami
  namespace: traefik
spec:
  parentRefs:
  - name: traefik-gateway
  hostnames:
  - whoami.example.com
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: whoami
      port: 80
```

```bash
kubectl apply -f httproute.yaml
kubectl -n traefik get httproute whoami
kubectl -n traefik describe gateway traefik-gateway
```

请求路由状态应为 `Accepted=True`，Gateway listener 应报告 `Programmed=True`。确认 DNS 解析到 Gateway 的外部地址后，再通过 `http://whoami.example.com/` 测试应用服务。

## 历史教程

原页面中基于 `stable/traefik`、旧 ACME values、旧 Ingress annotations 和 `extensions/v1beta1` 的安装与路由步骤不适用于 Traefik v3 或 Kubernetes v1.37.1，已移除。HTTPS/ACME 另见[证书与兼容性说明](ingress_letsencrypt.md)。
