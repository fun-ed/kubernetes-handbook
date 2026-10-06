> HISTORICAL: This chapter is frozen at an older Gateway API release. Its API versions, feature channel labels, fields, and inference-routing claims may be outdated or non-standard. Do not apply its examples without checking the current Gateway API implementation and documentation.

# Gateway API

Gateway API 是 Kubernetes 社群推出的用於設定和管理閘道器的新一代 API，它是 Ingress 資源的演進版本，提供了更強大、更靈活和更具表達力的流量管理能力。

## 什麼是 Gateway API？

Gateway API 是一個由 Kubernetes 網路特殊興趣小組 (SIG-NETWORK) 維護的開源專案，旨在透過提供表達性強、可擴充套件和麵向角色的介面來改進服務網路。

Gateway API 解決了傳統 Ingress 的以下限制：

- **表達能力有限**：Ingress 只能處理簡單的 HTTP 路由
- **可擴充套件性差**：依賴於特定控制器的註解來擴充套件功能
- **角色混亂**：缺乏清晰的角色分離和權限邊界

## 核心概念

Gateway API 引入了以下核心資源：

### Gateway

Gateway 描述瞭如何將流量轉換為叢集內的服務。它定義了監聽器，每個監聽器定義一個連接埠、協議和主機名。

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: example-gateway
  namespace: default
spec:
  gatewayClassName: example-class
  listeners:
  - name: http
    port: 80
    protocol: HTTP
    hostname: "*.example.com"
```

### GatewayClass

GatewayClass 定義了一組閘道器，這些閘道器共享公共設定和行為。它類似於 StorageClass，但用於閘道器。

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: example-class
spec:
  controllerName: example.com/gateway-controller
```

### HTTPRoute

HTTPRoute 定義了 HTTP 請求如何路由到後端服務。

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: example-route
  namespace: default
spec:
  parentRefs:
  - name: example-gateway
  hostnames:
  - "api.example.com"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api/v1
    backendRefs:
    - name: api-service
      port: 8080
```

## Gateway API v1.3.0 新特性

### 標準通道特性

#### 基於百分比的請求映像檔

v1.3.0 引入了基於百分比的請求映像檔功能，允許將指定百分比的請求映像檔到另一個後端：

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: example-route
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: production-service
      port: 8080
    filters:
    - type: RequestMirror
      requestMirror:
        backendRef:
          name: test-service
          port: 8080
        percent: 10  # 镜像 10% 的请求
```

### 實驗性通道特性

#### CORS 過濾

新增的 CORS 過濾器支援跨域資源共享設定：

```yaml
apiVersion: gateway.networking.x-k8s.io/v1alpha1
kind: HTTPRoute
metadata:
  name: cors-example
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
    filters:
    - type: ExtensionRef
      extensionRef:
        group: gateway.networking.x-k8s.io
        kind: CORSPolicy
        name: cors-policy
    backendRefs:
    - name: api-service
      port: 8080
---
apiVersion: gateway.networking.x-k8s.io/v1alpha1
kind: CORSPolicy
metadata:
  name: cors-policy
spec:
  allowOrigins:
  - "https://example.com"
  - "https://*.example.com"
  allowMethods:
  - GET
  - POST
  - PUT
  allowHeaders:
  - "Content-Type"
  - "Authorization"
  allowCredentials: true
  maxAge: "24h"
```

#### 重試預算 (XBackendTrafficPolicy)

重試預算功能限制客戶端在服務端點間的重試行為：

```yaml
apiVersion: gateway.networking.x-k8s.io/v1alpha1
kind: XBackendTrafficPolicy
metadata:
  name: retry-budget
spec:
  targetRefs:
  - group: ""
    kind: Service
    name: api-service
  retry:
    attempts: 3
    backoff: "1s"
    budget:
      percentage: 20  # 最多 20% 的请求可以重试
      interval: "10s"
```

#### XListenerSets

XListenerSets 提供了標準化的 Gateway 監聽器合併機制：

```yaml
apiVersion: gateway.networking.x-k8s.io/v1alpha1
kind: XListenerSet
metadata:
  name: shared-listeners
  namespace: gateway-system
spec:
  listeners:
  - name: http
    port: 80
    protocol: HTTP
  - name: https
    port: 443
    protocol: HTTPS
    tls:
      mode: Terminate
      certificateRefs:
      - name: wildcard-cert
```

#### Inference Extension（AI/ML 推理擴充套件）

Gateway API Inference Extension 是專為生成式 AI 和大語言模型 (LLM) 推理工作負載設計的擴充套件，提供了智慧路由和負載平衡能力。

**核心元件：**

**InferencePool** - 定義執行模型伺服器的 Pod 池：
```yaml
apiVersion: gateway.networking.x-k8s.io/v1alpha1
kind: InferencePool
metadata:
  name: llama2-pool
spec:
  deployment:
    replicas: 3
    template:
      spec:
        containers:
        - name: model-server
          image: vllm/vllm-openai:latest
          resources:
            limits:
              nvidia.com/gpu: 1
```

**InferenceModel** - 使用者面向的模型端點：
```yaml
apiVersion: gateway.networking.x-k8s.io/v1alpha1
kind: InferenceModel
metadata:
  name: llama2-7b
spec:
  poolRef:
    name: llama2-pool
  routing:
    priority: high
    trafficSplit:
    - weight: 90
      version: stable
    - weight: 10
      version: canary
```

**主要特性：**
- **模型感知路由**：基於模型型別和狀態進行智慧路由
- **請求優先順序**：支援每請求的重要性級別設定
- **安全模型釋出**：支援金絲雀釋出和 A/B 測試
- **最佳化負載平衡**：基於實時指標進行 GPU 資源最佳化

**效能優勢：**
- 降低 AI/ML 工作負載延遲
- 提高 GPU 利用率
- 標準化 AI 服務路由方式
- 支援字首快取感知的負載平衡

## 角色分離

Gateway API 設計了清晰的角色分離：

- **基礎設施提供者**：管理 GatewayClass 和基礎設施
- **叢集操作員**：管理 Gateway 資源和網路策略
- **應用開發者**：管理 Route 資源和應用流量

## 支援的協議

Gateway API 支援多種協議：

- **HTTP/HTTPS**：透過 HTTPRoute 資源
- **TLS**：透過 TLSRoute 資源
- **TCP**：透過 TCPRoute 資源
- **UDP**：透過 UDPRoute 資源
- **gRPC**：透過 GRPCRoute 資源

## 與 Ingress 的對比

| 特性 | Ingress | Gateway API |
|------|---------|-------------|
| 協議支援 | 僅 HTTP/HTTPS | HTTP/HTTPS/TCP/UDP/TLS/gRPC |
| 角色分離 | 無 | 清晰的角色分離 |
| 可擴充套件性 | 透過註解 | 原生 API 擴充套件 |
| 表達能力 | 有限 | 豐富的流量管理能力 |
| 型別安全 | 部分 | 完全型別安全 |

## 相容性

- **Kubernetes 版本**：要求 Kubernetes 1.26 或更高版本
- **API 穩定性**：標準通道功能已達到 v1 穩定版本
- **實現**：Envoy Gateway、Istio、Cilium、Airlock 等多個實現

## 遷移指南

### 從 Ingress 遷移

1. **安裝 Gateway API CRDs**：
```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.3.0/standard-install.yaml
```

2. **建立 GatewayClass**：
```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: nginx
spec:
  controllerName: nginx.org/nginx-gateway-controller
```

3. **建立 Gateway**：
```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: nginx-gateway
spec:
  gatewayClassName: nginx
  listeners:
  - name: http
    port: 80
    protocol: HTTP
```

4. **將 Ingress 轉換為 HTTPRoute**：
```yaml
# 原 Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example-ingress
spec:
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: example-service
            port:
              number: 80

# 转换为 HTTPRoute
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: example-route
spec:
  parentRefs:
  - name: nginx-gateway
  hostnames:
  - "example.com"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: example-service
      port: 80
```

## 最佳實踐

1. **漸進式遷移**：先在測試環境驗證，再逐步遷移生產環境
2. **角色分離**：明確定義不同角色的職責和權限
3. **監控觀察**：部署適當的監控和日誌記錄
4. **安全設定**：使用 TLS 終止和適當的安全策略
5. **效能測試**：驗證新設定的效能表現

## 參考文件

* [Gateway API 官方文件](https://gateway-api.sigs.k8s.io/)
* [Gateway API v1.3.0 釋出說明](https://kubernetes.io/blog/2025/06/02/gateway-api-v1-3/)
* [Gateway API Inference Extension 介紹](https://kubernetes.io/blog/2025/06/05/introducing-gateway-api-inference-extension/)
* [Gateway API GitHub 倉庫](https://github.com/kubernetes-sigs/gateway-api)
* [Gateway API 實現列表](https://gateway-api.sigs.k8s.io/implementations/)