# Ingress

在本篇文章中你將會看到一些在其他地方被交叉使用的術語，為了防止產生歧義，我們首先來澄清下。

* 節點：Kubernetes 叢集中的伺服器；
* 叢集：Kubernetes 管理的一組伺服器集合；
* 邊界路由器：為區域網和 Internet 路由資料包的路由器，執行防火牆保護區域網絡；
* 叢集網路：叢集內通訊的實現，例如 [Cilium](https://github.com/cilium/cilium)、[Calico](https://github.com/projectcalico/calico) 或其他符合需求的網路外掛。

## 什麼是 Ingress？

通常情況下，service 和 pod 的 IP 僅可在叢集內部存取。叢集外部的請求需要透過負載平衡轉發到 service 在 Node 上暴露的 NodePort 上，然後再由 kube-proxy 透過邊緣路由器 \(edge router\) 將其轉發給相關的 Pod 或者丟棄。如下圖所示

```text
   internet
        |
  ------------
  [Services]
```

而 Ingress 就是為進入叢集的請求提供路由規則的集合，如下圖所示

![image-20190316184154726](../../.gitbook/assets/image-20190316184154726%20%281%29.png)

Ingress 為 HTTP(S) 流量提供規則；規則由叢集中安裝的 Ingress controller 實現。建立 Ingress 資源本身不會自動提供外部入口，需先部署並設定相容的 controller。

## Ingress 格式

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: test-ingress
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /testpath
        pathType: Prefix
        backend:
          service:
            name: test
            port:
              number: 80
```

Ingress v1 要求每條 HTTP 路徑設定 `pathType`，並使用 `backend.service.name` 與 `backend.service.port` 指向 Service。

## API 版本

| API version | 狀態 |
| :--- | :--- |
| `networking.k8s.io/v1` | 當前版本 |
| `extensions/v1beta1`、`networking.k8s.io/v1beta1` | 自 v1.22 起不再提供 |

## Ingress 型別

根據 Ingress Spec 設定的不同，Ingress 可以分為以下幾種型別：

### 單服務 Ingress

單服務 Ingress 即該 Ingress 僅指定一個沒有任何規則的後端服務。

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: test-ingress
spec:
  ingressClassName: nginx
  defaultBackend:
    service:
      name: testsvc
      port:
        number: 80
```

> 注：單個服務還可以透過設定 `Service.Type=NodePort` 或者 `Service.Type=LoadBalancer` 來對外暴露。

### 多服務的 Ingress

路由到多服務的 Ingress 即根據請求路徑的不同轉發到不同的後端服務上，比如

```text
foo.bar.com -> 178.91.123.132 -> / foo    s1:80
                                 / bar    s2:80
```

可以透過下面的 Ingress 來定義：

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
      - path: /foo
        pathType: Prefix
        backend:
          service:
            name: s1
            port:
              number: 80
      - path: /bar
        pathType: Prefix
        backend:
          service:
            name: s2
            port:
              number: 80
```

使用 `kubectl create -f` 建立完 ingress 後：

```bash
$ kubectl get ing
NAME      RULE          BACKEND   ADDRESS
test      -
          foo.bar.com
          /foo          s1:80
          /bar          s2:80
```

### 虛擬主機 Ingress

虛擬主機 Ingress 即根據名字的不同轉發到不同的後端服務上，而他們共用同一個的 IP 位址，如下所示

```text
foo.bar.com --|                 |-> foo.bar.com s1:80
              | 178.91.123.132  |
bar.foo.com --|                 |-> bar.foo.com s2:80
```

下面是一個基於 [Host header](https://tools.ietf.org/html/rfc7230#section-5.4) 路由請求的 Ingress：

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

> 注：沒有定義規則的後端服務稱為預設後端服務，可以用來方便的處理 404 頁面。

### TLS Ingress

TLS Ingress 透過 Secret 獲取 TLS 私鑰和證書 \(名為 `tls.crt` 和 `tls.key`\)，來執行 TLS 終止。如果 Ingress 中的 TLS 設定部分指定了不同的主機，則它們將根據透過 SNI TLS 擴充套件指定的主機名（假如 Ingress controller 支援 SNI）在多個相同連接埠上進行復用。

定義一個包含 `tls.crt` 和 `tls.key` 的 secret：

```yaml
apiVersion: v1
data:
  tls.crt: base64 encoded cert
  tls.key: base64 encoded key
kind: Secret
metadata:
  name: testsecret
  namespace: default
type: Opaque
```

Ingress 中引用 secret：

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: no-rules-map
spec:
  ingressClassName: nginx
  tls:
  - secretName: testsecret
  defaultBackend:
    service:
      name: s1
      port:
        number: 80
```

注意，不同 Ingress controller 支援的 TLS 功能不盡相同。 請參閱有關 [nginx](https://kubernetes.github.io/ingress-nginx/)，[GCE](https://github.com/kubernetes/ingress-gce) 或任何其他 Ingress controller 的文件，以瞭解 TLS 的支援情況。

## 更新 Ingress

可以透過 `kubectl edit ing name` 的方法來更新 ingress：

```bash
$ kubectl get ing
NAME      RULE          BACKEND   ADDRESS
test      -                       178.91.123.132
          foo.bar.com
          /foo          s1:80
$ kubectl edit ing test
```

這會彈出一個包含已有 IngressSpec yaml 檔案的編輯器，修改並儲存就會將其更新到 kubernetes API server，進而觸發 Ingress Controller 重新設定負載平衡：

```yaml
spec:
  rules:
  - host: foo.bar.com
    http:
      paths:
      - path: /foo
        pathType: Prefix
        backend:
          service:
            name: s1
            port:
              number: 80
  - host: bar.baz.com
    http:
      paths:
      - path: /foo
        pathType: Prefix
        backend:
          service:
            name: s2
            port:
              number: 80
```

更新後：

```bash
$ kubectl get ing
NAME      RULE          BACKEND   ADDRESS
test      -                       178.91.123.132
          foo.bar.com
          /foo          s1:80
          bar.baz.com
          /foo          s2:80
```

當然，也可以透過 `kubectl replace -f new-ingress.yaml` 命令來更新，其中 new-ingress.yaml 是修改過的 Ingress yaml。

## Ingress Controller

Ingress controller 獨立於 Kubernetes 控制平面部署。請選擇仍受維護、與叢集和網路實現相容的 controller，並按其上游文件安裝及設定；Helm chart、引數和支援週期因實現而異，不要照搬已過時的 chart 儲存庫命令。

其他 Ingress Controller 還有：

* [traefik ingress](../../extension/ingress/service-discovery-and-load-balancing.md) 提供了一個 Traefik Ingress Controller 的實踐案例
* [kubernetes/ingress-nginx](https://github.com/kubernetes/ingress-nginx) 提供了一個詳細的 Nginx Ingress Controller 範例
* [kubernetes/ingress-gce](https://github.com/kubernetes/ingress-gce) 提供了一個用於 GCE 的 Ingress Controller 範例

## Ingress Class

在 Ingress Class 之前，要給 Ingress 選擇具體的 Controller，需要加上特殊的 annotation（如 kubernetes.io/ingress.class: nginx）。而有了 IngressClass，叢集管理員就可以預先建立好支援的 Ingress 型別，並可以 Ingress 中直接引用。

```yaml
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: external-lb
spec:
  controller: example.com/ingress-controller
  parameters:
    apiGroup: k8s.example.com
    kind: IngressParameters
    name: external-lb
```

## Gateway API - Ingress 的下一代演進

Gateway API 是一組用於設定叢集流量路由的 API，提供比 Ingress 更豐富的角色與路由模型。其 API 版本、標準通道和實現支援情況會隨釋出演進，請查閱 [Gateway API 官方文件](https://gateway-api.sigs.k8s.io/)與所選 controller 的相容性說明。

Ingress 仍是受支援的 API。新部署可以根據需求評估 Gateway API；遷移時應確認所選實現支援目標功能，並同時驗證路由行為。

## 參考文件

* [Kubernetes Ingress Resource](https://kubernetes.io/docs/concepts/services-networking/ingress/)
* [Gateway API](https://gateway-api.sigs.k8s.io/)
* [Gateway API v1.3.0 Release](https://kubernetes.io/blog/2025/06/02/gateway-api-v1-3/)
* [Kubernetes Ingress Controller](https://github.com/kubernetes/ingress/tree/master)
* [使用 NGINX Plus 負載平衡 Kubernetes 服務](http://dockone.io/article/957)
* [使用 NGINX 和 NGINX Plus 的 Ingress Controller 進行 Kubernetes 的負載平衡](http://www.cnblogs.com/276815076/p/6407101.html)
* [Kubernetes Ingress Controller-Træfɪk](https://doc.traefik.io/traefik/providers/kubernetes-ingress/)
* [Kubernetes 1.2 and simplifying advanced networking with Ingress](https://kubernetes.io/blog/2016/03/kubernetes-1-2-and-simplifying-advanced-networking-with-ingress/)
