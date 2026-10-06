# Service

Kubernetes 在設計之初，就充分考量了容器的服務探索與負載平衡機制，提供 Service 資源，並透過 kube-proxy 搭配 cloud provider，以因應不同的應用情境。隨著 Kubernetes 使用者大幅增加，使用情境日益豐富，也因此出現了一些新的負載平衡機制。目前，Kubernetes 中的負載平衡大致可分為以下幾種機制，每種機制都有其特定的應用情境：

* Service：直接使用 Service 提供叢集內部的負載平衡，並借助 cloud provider 提供的 LB 開放外部存取
* Ingress Controller：仍使用 Service 提供叢集內部的負載平衡，但透過自訂 Ingress Controller 開放外部存取
* Service Load Balancer：直接在容器中執行 load balancer，實作裸機環境的 Service Load Balancer
* Custom Load Balancer：自訂負載平衡並取代 kube-proxy，通常用於實體部署 Kubernetes，方便介接公司既有的外部服務

## Service

![](../../.gitbook/assets/14735737093456%20%284%29.jpg)

Service 是一組提供相同功能之 Pod 的抽象表示，並為它們提供統一的入口。Service 透過標籤選取器關聯後端；kube-proxy 或相容的替代實作，會根據控制平面維護的 EndpointSlices 轉送流量。

> **API 遷移：** Endpoints API 自 Kubernetes v1.33 起已棄用。新工具和疑難排解流程應讀取 `discovery.k8s.io/v1` 的 EndpointSlices。

Service 有四種類型：

* ClusterIP：預設類型，自動指派一個僅供叢集內部存取的虛擬 IP
* NodePort：在 ClusterIP 的基礎上，為 Service 在每台機器上綁定一個連接埠，讓使用者可以透過 `<NodeIP>:NodePort` 存取該服務。如果 kube-proxy 設定了 `--nodeport-addresses=10.240.0.0/16`（v1.10 支援），則該 NodePort 僅對設定範圍內的 IP 有效。
* LoadBalancer：在 NodePort 的基礎上，借助 cloud provider 建立外部負載平衡器，並將要求轉送到 `<NodeIP>:NodePort`
* ExternalName：透過 DNS CNAME 記錄，將服務轉送到指定網域名稱（透過 `spec.externalName` 設定）；解析由叢集 DNS 實作提供。

此外，也可以將既有服務以 Service 的形式加入 Kubernetes 叢集，只要在建立 Service 時不指定 Label selector，並在 Service 建立後手動為其新增 endpoint 即可。

### Service 定義

Service 的定義也使用 YAML 或 JSON，例如，以下定義了一個名為 nginx 的服務，將服務的 80 連接埠轉送到 default namespace 中帶有標籤 `run=nginx` 的 Pod 的 80 連接埠

```yaml
apiVersion: v1
kind: Service
metadata:
  labels:
    run: nginx
  name: nginx
  namespace: default
spec:
  ports:
  - port: 80
    protocol: TCP
    targetPort: 80
  selector:
    run: nginx
  sessionAffinity: None
  type: ClusterIP
```

```bash
kubectl get service nginx
kubectl get endpointslices -l kubernetes.io/service-name=nginx
kubectl describe service nginx
```

服務需要多個連接埠時，每個連接埠都必須設定名稱

```yaml
kind: Service
apiVersion: v1
metadata:
  name: my-service
spec:
  selector:
    app: MyApp
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 9376
  - name: https
    protocol: TCP
    port: 443
    targetPort: 9377
```

### 通訊協定

Service、Endpoints（已棄用，建議使用 EndpointSlices）和 Pod 支援三種通訊協定：

* TCP（Transmission Control Protocol，傳輸控制協定）是一種具連線導向、可靠且以位元組串流為基礎的傳輸層通訊協定。
* UDP（User Datagram Protocol，使用者資料包協定）是一種無連線的傳輸層協定，用於不可靠的資訊傳送服務。
* SCTP（Stream Control Transmission Protocol，串流控制傳輸協定）用於透過 IP 網路傳輸 SCN（Signaling Communication Network，信令通訊網路）窄頻信令訊息。

### API 版本

Service 使用核心 API 群組的 `v1`（`apiVersion: v1`）。

### 未指定選取器的服務

建立 Service 時，也可以不指定選取器，藉此將 Service 轉送到 Kubernetes 叢集外部的服務（而非 Pod）。目前支援兩種方法：

建立不含選取器的 Service 時，可搭配手動維護的 EndpointSlice 將流量轉送至外部端點。新實作請使用 `discovery.k8s.io/v1`，不要建立已棄用的 Endpoints 物件；舊版範例和 client-go 呼叫見[歷史歸檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/concepts/endpoints-legacy.md)。

建議使用 EndpointSlices 取代 Endpoints：

```yaml
kind: Service
apiVersion: v1
metadata:
  name: my-service
spec:
  ports:
    - protocol: TCP
      port: 80
      targetPort: 9376
---
# EndpointSlice 属于 discovery.k8s.io/v1
kind: EndpointSlice
apiVersion: discovery.k8s.io/v1
metadata:
  name: my-service-abc123
  labels:
    kubernetes.io/service-name: my-service
addressType: IPv4
endpoints:
- addresses:
  - "1.2.3.4"
ports:
- port: 9376
  protocol: TCP

```

（2）透過 DNS 轉送，在 Service 定義中指定 externalName。此時 DNS 服務會為 `<service-name>.<namespace>.svc.cluster.local` 建立一筆 CNAME 記錄，其值為 `my.database.example.com`。而且，該服務不會自動取得 Cluster IP，必須透過 Service 的 DNS 存取。

```yaml
kind: Service
apiVersion: v1
metadata:
  name: my-service
  namespace: default
spec:
  type: ExternalName
  externalName: my.database.example.com
```

注意：Endpoints 的 IP 位址不能是 127.0.0.0/8、169.254.0.0/16 或 224.0.0.0/24，也不能是 Kubernetes 中其他服務的 clusterIP。

### Headless 服務

Headless 服務是不需要 Cluster IP 的服務，也就是建立服務時指定 `spec.clusterIP=None`。包含兩種類型：

* 不指定選取器，但設定 externalName，即上述的（2），透過 CNAME 記錄處理
* 指定選取器，透過 DNS A 記錄設定後端 endpoint 清單

```yaml
apiVersion: v1
kind: Service
metadata:
  labels:
    app: nginx
  name: nginx
spec:
  clusterIP: None
  ports:
  - name: tcp-80-80-3b6tl
    port: 80
    protocol: TCP
    targetPort: 80
  selector:
    app: nginx
  sessionAffinity: None
  type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: nginx
  name: nginx
  namespace: default
spec:
  replicas: 2
  revisionHistoryLimit: 5
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - image: nginx:1.30.5
        name: nginx
        ports:
        - containerPort: 80
```

```bash
kubectl get services -A
kubectl get pods -l app=nginx
```

## Service 來源 IP

來源 IP 是否保留，取決於 Service 類型、`externalTrafficPolicy`、kube-proxy 或替代資料平面、CNI 路由，以及雲端負載平衡器的設定；不能只根據 Service 類型推定。

`externalTrafficPolicy: Local` 會將外部流量限制為接收流量之節點上的本機端點。這可能保留來源 IP，但若該節點沒有可用端點，流量可能無法轉送；負載平衡器的健康檢查與節點選擇也須依平台實作確認。請查閱[目前的流量政策文件](https://kubernetes.io/docs/reference/networking/virtual-ips/#traffic-policies)。舊版 kube-proxy 與網路外掛的逐類型說明已移至[歷史歸檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/concepts/objects/service-source-ip-legacy-zh-TW.md)。

## 內部網路政策

根據預設，Kubernetes 會將叢集中所有 Endpoints 的 IP 做為 Service 的後端。你可以設定 `.spec.internalTrafficPolicy=Local`，讓 kube-proxy 只對節點本機的 Endpoints 進行負載平衡。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: MyApp
  ports:
    - protocol: TCP
      port: 80
      targetPort: 9376
  internalTrafficPolicy: Local
```

請注意，啟用內部網路政策後，即使其他節點上有正常運作的 Endpoints，只要節點本機沒有正常執行的 Pod，就無法存取該 Service。

## 運作原理

kube-proxy 負責將 Service 的負載平衡到後端 Pod，如下圖所示

![](../../.gitbook/assets/service-flow%20%284%29.png)

## Ingress

Service 提供網路連線能力和傳輸層的負載平衡。若要進行 HTTP(S) 路由，請使用 Ingress 資源搭配相容的 Ingress 控制器或 Gateway API 實作；單獨建立 Ingress 並不會安裝控制器。

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: test
spec:
  ingressClassName: nginx
  rules:
  - host: foo.bar.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: s1
            port:
              number: 80
  - host: bar.foo.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: s2
            port:
              number: 80
```

Ingress 和 Ingress 控制器的介紹請參閱[專章](ingress.md)。

## Service Load Balancer（歷史專案）

本節先前介紹的 `kubernetes/contrib/service-loadbalancer` 是已封存的舊專案，不應做為目前的部署建議。請依據叢集類型選擇受維護的雲端負載平衡整合、MetalLB 等實作，或受支援的 Ingress/Gateway 控制器，並遵循其現行文件。

## Custom Load Balancer

雖然 Kubernetes 提供了豐富的負載平衡機制，但實際使用時，仍會遇到一些無法支援的複雜情境，例如：

* 介接既有的負載平衡設備
* 在多租戶網路環境中，容器網路與主機網路彼此隔離，因此 `kube-proxy` 無法正常運作

自訂負載平衡實作應使用 EndpointSlices 等目前的 API 探索 Service 後端，並依所選的網路架構設定流量轉送；實作方式、可用性與升級方式則取決於所選專案。

## 從叢集外部存取服務

Service 對外開放的方式取決於平台與網路實作：

* `NodePort` 會在節點位址上開放所指派的連接埠；應限制防火牆允許的來源，不要預設將連接埠暴露至公網。
* `LoadBalancer` 由雲端平台或已安裝的負載平衡實作提供外部位址，流量路徑可能因實作而異。
* Ingress 控制器或 Gateway 控制器適用於 HTTP(S) 路由。
* 裸機環境可評估受維護的負載平衡實作，例如 [MetalLB](https://metallb.io/)。

## 從 Endpoints 遷移至 EndpointSlices

從 Kubernetes v1.33 起，Endpoints API 已棄用。新的用戶端應讀取 EndpointSlices；Service 控制器會維護與其選取器對應的 EndpointSlices。

### 主要差異

1. **多個 EndpointSlices 與單一 Endpoints**：
   - 一個 Service 可以對應多個 EndpointSlices
   - 需要使用標籤選取器 `kubernetes.io/service-name=<servicename>` 來尋找相關的 EndpointSlices

2. **API 結構差異**：
   - EndpointSlices 使用 `discovery.k8s.io/v1` API 群組
   - 明確指定 `addressType`（IPv4 或 IPv6）
   - 每個 endpoint 通常只包含一個位址

### 程式碼遷移範例

舊版 `CoreV1().Endpoints(...)` 呼叫已移至[歷史歸檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/concepts/endpoints-legacy.md)。新 client-go 程式應列出 EndpointSlices，並用 `kubernetes.io/service-name` 標籤篩選：

**新版 EndpointSlices API 用法**：

```go
endpointSlices, err := clientset.DiscoveryV1().EndpointSlices(namespace).List(ctx, metav1.ListOptions{
    LabelSelector: fmt.Sprintf("kubernetes.io/service-name=%s", serviceName),
})
```

### EndpointSlices 的優勢

- **支援雙堆疊網路**：可同時支援 IPv4 和 IPv6 位址
- **效能更佳**：在大型叢集中減少資源開銷
- **流量分配**：支援更靈活的流量分配策略
- **簡化實作**：簡化服務代理和控制器的實作

### 遷移建議

1. **逐步遷移**：在現有程式碼中同時支援兩種 API，然後逐步切換
2. **測試驗證**：確保新的 EndpointSlices 邏輯在正式環境中正常運作
3. **監控與警示**：設定監控，以追蹤 Endpoints API 的使用情況

## 參考資料

* [https://kubernetes.io/docs/concepts/services-networking/service/](https://kubernetes.io/docs/concepts/services-networking/service/)
* [https://kubernetes.io/docs/concepts/services-networking/ingress/](https://kubernetes.io/docs/concepts/services-networking/ingress/)
* [https://kubernetes.io/blog/2025/04/24/endpoints-deprecation/](https://kubernetes.io/blog/2025/04/24/endpoints-deprecation/)
* [https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/)
* [https://github.com/kubernetes/contrib/tree/master/service-loadbalancer](https://github.com/kubernetes/contrib/tree/master/service-loadbalancer)
* [https://www.nginx.com/blog/load-balancing-kubernetes-services-nginx-plus/](https://www.nginx.com/blog/load-balancing-kubernetes-services-nginx-plus/)
* [https://github.com/weaveworks/flux](https://github.com/weaveworks/flux)
* [https://github.com/AdoHe/kube2haproxy](https://github.com/AdoHe/kube2haproxy)
* [不使用 Ingress、NodePort 或 LoadBalancer 存取 Kubernetes 服務](https://medium.com/@kyralak/accessing-kubernetes-services-without-ingress-nodeport-or-loadbalancer-de6061b42d72)