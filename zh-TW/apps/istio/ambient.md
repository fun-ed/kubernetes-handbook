# Istio ambient 模式

本章固定使用 Istio **v1.31.1**。Ambient 模式無需在每個應用 Pod 注入 sidecar，即可提供網格功能。節點上的 ztunnel 處理 L4 連線與 HBONE 通道上的網格 mTLS。可選的 waypoint proxy 基於 Envoy，為選定工作負載處理 L7 功能。Ambient 不會讓應用公開，也不能替代 Kubernetes NetworkPolicy、入口閘道器或 CNI。

Istio ambient CNI 外掛會為加入網格的 Pod 設定流量捕獲。CNI 安裝順序與 chart 配置很重要，尤其是 Cilium 等其他 CNI 已負責 Pod 網路時。依 v1.31.1 安裝說明及 Cilium 整合文件確認 CNI 串接配置。不要讓兩個外掛爭用同一責任，也不要假設控制平面安裝成功就代表流量捕獲正常。

Istio v1.31 支援矩陣包含 Kubernetes v1.32 至 v1.36，不包含本手冊基準 v1.37.1。因此本章組合不屬於上游宣告支援的組合，僅能在隔離實驗室評估，不可聲稱相容。平臺、核心和主機網路限制取決於安裝路徑，須查閱對應版本的 ambient 要求。

## 安裝與名稱空間加入

依 [Istio ambient 安裝指南](https://istio.io/v1.31/docs/ambient/install/)順序安裝 v1.31.1 base chart、`istiod`、ambient profile/ztunnel 和 CNI 元件。所有 chart 固定為 v1.31.1，並按現有 CNI 核對設定。本章不提供對現有叢集執行安裝的命令。

控制平面與資料平面已在一次性實驗環境部署後，可為測試名稱空間新增 ambient 標籤：

```bash
kubectl label namespace sample istio.io/dataplane-mode=ambient
```

此標籤表示使用 ambient，不是 `istio-injection=enabled`，也不會注入 sidecar。已有 Pod 可能需要重新建立才能加入網格。操作前確認名稱空間只含預期工作負載。

## L4 與 waypoint 策略

以下 L4 AuthorizationPolicy 是不使用 waypoint L7 AuthorizationPolicy 時的獨立方案。它只允許 `sample` 名稱空間的 `frontend` ServiceAccount 連線到標籤為 `app: backend`、TCP 8080 的 Pod。

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: backend-l4
  namespace: sample
spec:
  selector:
    matchLabels:
      app: backend
  action: ALLOW
  rules:
    - from:
        - source:
            principals:
              - cluster.local/ns/sample/sa/frontend
      to:
        - operation:
            ports: ["8080"]
```

使用 waypoint L7 策略時，不要同時保留上述 L4 策略。經 waypoint 轉送後，目的工作負載看到的是 waypoint 身分；只允許原始客戶端 ServiceAccount 的 L4 `ALLOW` 策略會阻擋 waypoint。若應用另有 L4 限制，應明確允許 waypoint 身分並在隔離環境驗證。

先安裝 Istio v1.31 要求的 Gateway API CRD，然後在 `sample` 名稱空間建立 waypoint Gateway。以下 Gateway 使用官方支援的 `istio-waypoint` GatewayClass、HBONE listener 15008，並設定 waypoint 處理 Service 流量：

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: sample-waypoint
  namespace: sample
  labels:
    istio.io/waypoint-for: service
spec:
  gatewayClassName: istio-waypoint
  listeners:
    - name: mesh
      port: 15008
      protocol: HBONE
```

Gateway 就緒後，使用 namespace 標籤將名稱空間內的 Service 流量導向 waypoint：

```bash
kubectl label namespace sample istio.io/use-waypoint=sample-waypoint
```

`istio.io/use-waypoint` 指定 Gateway 名稱，不是 `istio-injection=enabled`，也不會注入 sidecar。該標籤宣告路由意圖，不保證 waypoint 不存在或流量型別不匹配時請求失敗。若 L7 策略是安全邊界，須按 Istio 文件配置強制流量經過 waypoint 的 L4 授權，並驗證繞過失敗路徑。`istio.io/waypoint-for: service` 表示處理 Service 目的流量；若要處理 Pod IP 工作負載流量，須依版本文件設定對應值。

以下 L7 AuthorizationPolicy 透過 `targetRefs` 指向 `sample-waypoint` Gateway，只允許 HTTP GET `/health`。此策略是 waypoint L7 方案，不能與上面只允許客戶端 principal 的 L4 策略直接疊加。

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: backend-http
  namespace: sample
spec:
  targetRefs:
    - group: gateway.networking.k8s.io
      kind: Gateway
      name: sample-waypoint
  action: ALLOW
  rules:
    - to:
        - operation:
            methods: ["GET"]
            paths: ["/health"]
```

建立 Gateway 前安裝該 Istio 版本要求的 Gateway API CRD。按版本檔案檢查 GatewayClass 與 Gateway 狀態。混合 Istio revision 時，較舊控制平面可能不識別 `targetRefs`，並錯誤解釋策略目標，產生 fail-open 風險。相關 proxy 與控制平面應使用相容版本；滾動升級前遵循對應版本的防護說明。

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: backend-l4
  namespace: sample
spec:
  selector:
    matchLabels:
      app: backend
  action: ALLOW
  rules:
    - from:
        - source:
            principals:
              - cluster.local/ns/sample/sa/frontend
      to:
        - operation:
            ports: ["8080"]
```


## 只讀檢查與故障排查

```bash
istioctl version
istioctl proxy-status
istioctl ztunnel-config workloads
kubectl get pods -n istio-system -o wide
kubectl get gatewayclass,gateway -A
kubectl get authorizationpolicy -A
```

這些命令檢查版本、proxy 同步狀態、ztunnel 工作負載及 Gateway/策略資源；它們本身不能證明流量已加密或授權結果正確。使用專用實驗工作負載分別測試允許和拒絕的請求。若 ztunnel 未列出工作負載，檢查名稱空間加入標籤、Pod 是否重建、CNI 安裝、節點位置及 ztunnel 日誌。若 L7 策略未生效，檢查 waypoint 就緒狀態、use-waypoint 標籤、流量是否經過 waypoint、Gateway API 版本及所有相關 revision 是否支援 `targetRefs`。

## 適用邊界與回退

未確認 v1.31 文件前，不要讓 `hostNetwork` 工作負載或不支援的 runtime/OS 組合加入 ambient。不要將 waypoint 或 Istio 控制平面服務公開到公網。Ambient mTLS 只適用於被網格捕獲的流量，不會自動加密所有主機或外部連線。

實驗室回退時，先按文件移除或修改名稱空間加入標籤，再檢查流量策略，最後才移除資料平面元件。正式環境須先規劃策略遷移、節點覆蓋、CNI 串接和控制平面 revision 順序。解除安裝 CNI 元件可能中斷全部 Pod 網路，不是通用安全回退方法。

主要來源：[Istio v1.31 ambient 概覽](https://istio.io/v1.31/docs/ambient/overview/)、[ambient 安裝](https://istio.io/v1.31/docs/ambient/install/)、[waypoint](https://istio.io/v1.31/docs/ambient/usage/waypoint/)、[ambient 授權](https://istio.io/v1.31/docs/ambient/usage/l7-features/)、[Istio v1.31.1 釋出版本](https://github.com/istio/istio/releases/tag/1.31.1)、[支援狀態](https://istio.io/latest/docs/releases/supported-releases/)、[Cilium-Istio 整合](https://docs.cilium.io/en/stable/network/servicemesh/istio/)。
