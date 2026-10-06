# Ingress 與入口控制器

Kubernetes Ingress API 宣告 HTTP(S) 路由規則；它本身不提供代理，叢集必須另行安裝與維護 Ingress controller。選擇控制器前，核對其當前 release、Kubernetes 支援表、維護狀態與安全公告。需要更豐富的流量路由能力時，也可評估 Gateway API 和相容實現。

> **歷史設定不可部署**：本頁原有的 Traefik v1 範例依賴已移除的 `extensions/v1beta1` Ingress、RBAC `v1beta1`、早期映像檔與 controller 引數。Kubernetes v1.22 已移除舊 Ingress API；不要執行本頁原清單。下面只給出當前 `networking.k8s.io/v1` Ingress API 形狀，不包含 controller 安裝配方。

## Kubernetes v1.37 Ingress 範例

先安裝受支援的 Ingress controller，並確認它建立了相應的 `IngressClass`。下面 `public-example`、Service 和 TLS Secret 是佔位名稱，應用前必須替換為叢集中真實資源：

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example
  namespace: default
spec:
  ingressClassName: public-example
  tls:
    - hosts:
        - app.example.com
      secretName: example-tls
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: example-service
                port:
                  number: 80
```

Ingress 與後端 Service 必須在同一 namespace。每條 HTTP path 都要宣告 `pathType`，後端使用 `service.name` 與 `service.port`。TLS Secret 應只包含所需證書，並按證書管理流程更新。

```bash
kubectl get ingressclass
kubectl describe ingress example
kubectl get ingress,service -n default
```

Controller 專用註解、負載平衡位址、健康檢查、TLS 解除安裝與存取日誌均由所選實現決定；使用其對應版本文件，不要從舊 Traefik 引數推斷當前行為。

## 參考

- [Kubernetes Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [Ingress controller](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/)
- [Gateway API](https://gateway-api.sigs.k8s.io/)
