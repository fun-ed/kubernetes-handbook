# Traefik + Kubernetes Gateway API

Ingress 是仍受支援但功能凍結的 API；本頁將舊 Traefik Helm `stable` 儲存庫、舊 Dashboard 部署和 `extensions/v1beta1` Ingress 範例替換為固定版本的 Gateway API 部署。不要把舊 Traefik v1/v2 annotations 或舊 chart values 直接移植到 v3。

## Kubernetes v1.37.1 版本組合（2026-10-05）

* Traefik Proxy v3.7.13，Helm chart v41.6.1。
* Traefik v3.7.13 的 Gateway provider 文件支援 Gateway API Standard v1.6.1；Gateway API CRD 由使用者單獨安裝，chart 不再包含 CRD。
* Gateway API v1.6.2 已釋出，但不是 Traefik v3.7.13 文件驗證的組合。本文固定使用 v1.6.1。
* Traefik 文件說明其遵循 Kubernetes 版本偏差策略並支援至少最新三個次版本；截至本文日期 Kubernetes v1.37 屬於該支援視窗，但上游沒有單獨列出的 v1.37 e2e 矩陣。

來源：[Traefik v3.7.13 釋出](https://github.com/traefik/traefik/releases/tag/v3.7.13)、[Traefik chart v41.6.1](https://github.com/traefik/traefik-helm-chart/releases/tag/v41.6.1)、[Traefik v3.7.13 Gateway API provider 要求](https://raw.githubusercontent.com/traefik/traefik/v3.7.13/docs/content/reference/install-configuration/providers/kubernetes/kubernetes-gateway.md)、[Gateway API v1.6.1 釋出](https://github.com/kubernetes-sigs/gateway-api/releases/tag/v1.6.1)。

## 安裝

下面先安裝 Traefik 文件驗證的 Gateway API Standard CRD，再用固定 chart 版本啟用 Kubernetes Gateway provider。Helm chart 自動建立 Gateway API 所需 RBAC，並建立預設 `GatewayClass` 和 `Gateway`。

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

該 chart 預設建立名為 `traefik` 的 `GatewayClass`、名為 `traefik-gateway` 的 `Gateway`，並在 `traefik` namespace 建立 HTTP listener。預設僅允許 Gateway 同 namespace 的 Route；這樣可以避免無意間授權其他 namespace。檢查部署結果：

```bash
kubectl get gatewayclass traefik
kubectl -n traefik get gateway traefik-gateway
kubectl -n traefik get service traefik
```

`Gateway` 是否獲得外部位址取決於叢集的 `LoadBalancer` 實現。沒有云負載平衡器時，需要為環境設定 LoadBalancer 實現或使用受控的 NodePort/外部入口；Helm 安裝本身不會分配公共 IP。

## 將 HTTPRoute 綁定到應用 Service

將 `whoami` 和 `80` 替換為已經部署在 `traefik` namespace 的應用 Service 名稱和連接埠。若 Route 在其他 namespace，需有意設定 listener 的 `allowedRoutes.namespaces`，並確認授權範圍。

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

請求路由狀態應為 `Accepted=True`，Gateway listener 應報告 `Programmed=True`。確認 DNS 解析到 Gateway 的外部位址後，再透過 `http://whoami.example.com/` 測試應用服務。

## 歷史教程

原頁面中基於 `stable/traefik`、舊 ACME values、舊 Ingress annotations 和 `extensions/v1beta1` 的安裝與路由步驟不適用於 Traefik v3 或 Kubernetes v1.37.1，已移除。HTTPS/ACME 另見[證書與相容性說明](ingress_letsencrypt.md)。
