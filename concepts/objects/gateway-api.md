# Gateway API

Gateway API 是 Kubernetes SIG Network 維護的可擴充網路 API。它提供比 Ingress 更細緻的角色分工及路由資源；API 物件本身不會安裝資料平面或控制器，也不保證叢集支援特定功能。

截至 Kubernetes v1.37，本章依 Gateway API v1.6.2 的標準 API 文件說明。必須先安裝相容的 Gateway API CRD，再部署支援所需 API 版本與功能的 Gateway Controller。請先檢查控制器實作清單及安裝指南；不同實作支援的資源、欄位、政策和功能通道可能不同。

## 核心資源

- `GatewayClass` 由基礎設施提供者建立，識別管理 Gateway 的控制器。
- `Gateway` 表達一個或多個監聽器及其所屬的 GatewayClass。
- `HTTPRoute`、`GRPCRoute` 等 Route 資源描述如何將協定流量導向後端。跨 Namespace 引用及附加仍受各資源的權限與政策限制。

例如，以下 `HTTPRoute` 參照名為 `example-gateway` 的 Gateway，並將符合條件的請求送至同一 Namespace 的 `web` Service：

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: web
  namespace: default
spec:
  parentRefs:
    - name: example-gateway
  hostnames:
    - www.example.test
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: web
          port: 80
```

`.test` 是保留作測試用途的網域；範例不含可直接使用的外部 IP、憑證或叢集專屬設定。部署前請確認對應的 Gateway、Service、HTTPRoute CRD 及控制器功能均已安裝且相容，再以 `kubectl get gatewayclass,gateway,httproute -A` 及狀態條件確認控制器已接受設定並完成程式化。

## 角色與相容性

基礎設施提供者通常管理 `GatewayClass`，叢集操作人員管理 `Gateway`，應用團隊建立 Route。`allowedRoutes`、ReferenceGrant 及其他政策可限制 Route 附加與跨 Namespace 參照；請依信任邊界授予所需權限，不要假設所有 Namespace 都可任意附加路由。

Gateway API 會以標準通道和實驗通道發佈功能。只有標準通道的 API 保證已標準化；實驗通道資源需使用對應的 CRD 發行包，且可能變更。API 版本與功能支援會因控制器版本而異，請核對[相容性矩陣](https://gateway-api.sigs.k8s.io/implementations/)和所選控制器文件。

## 參考文件

- [Gateway API v1.6.2 文件](https://gateway-api.sigs.k8s.io/)
- [安裝 Gateway API](https://gateway-api.sigs.k8s.io/guides/)
- [Gateway API 實作與相容性](https://gateway-api.sigs.k8s.io/implementations/)
- [Kubernetes Gateway API 概念](https://kubernetes.io/docs/concepts/services-networking/gateway/)

舊版功能通道摘要及特定控制器範例已移至[歷史歸檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/concepts/objects/gateway-api-legacy.md)。
