# Ingress

在本篇文章中你将会看到一些在其他地方被交叉使用的术语，为了防止产生歧义，我们首先来澄清下。

* 节点：Kubernetes 集群中的服务器；
* 集群：Kubernetes 管理的一组服务器集合；
* 边界路由器：为局域网和 Internet 路由数据包的路由器，执行防火墙保护局域网络；
* 集群网络：集群内通信的实现，例如 [Cilium](https://github.com/cilium/cilium)、[Calico](https://github.com/projectcalico/calico) 或其他符合需求的网络插件。

## 什么是 Ingress？

通常情况下，service 和 pod 的 IP 仅可在集群内部访问。集群外部的请求需要通过负载均衡转发到 service 在 Node 上暴露的 NodePort 上，然后再由 kube-proxy 通过边缘路由器 \(edge router\) 将其转发给相关的 Pod 或者丢弃。如下图所示

```text
   internet
        |
  ------------
  [Services]
```

而 Ingress 就是为进入集群的请求提供路由规则的集合，如下图所示

![image-20190316184154726](../../.gitbook/assets/image-20190316184154726%20%281%29.png)

Ingress 为 HTTP(S) 流量提供规则；规则由集群中安装的 Ingress controller 实现。创建 Ingress 资源本身不会自动提供外部入口，需先部署并配置兼容的 controller。

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

Ingress v1 要求每条 HTTP 路径设置 `pathType`，并使用 `backend.service.name` 与 `backend.service.port` 指向 Service。

## API 版本

| API version | 状态 |
| :--- | :--- |
| `networking.k8s.io/v1` | 当前版本 |
| `extensions/v1beta1`、`networking.k8s.io/v1beta1` | 自 v1.22 起不再提供 |

## Ingress 类型

根据 Ingress Spec 配置的不同，Ingress 可以分为以下几种类型：

### 单服务 Ingress

单服务 Ingress 即该 Ingress 仅指定一个没有任何规则的后端服务。

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

> 注：单个服务还可以通过设置 `Service.Type=NodePort` 或者 `Service.Type=LoadBalancer` 来对外暴露。

### 多服务的 Ingress

路由到多服务的 Ingress 即根据请求路径的不同转发到不同的后端服务上，比如

```text
foo.bar.com -> 178.91.123.132 -> / foo    s1:80
                                 / bar    s2:80
```

可以通过下面的 Ingress 来定义：

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

使用 `kubectl create -f` 创建完 ingress 后：

```bash
$ kubectl get ing
NAME      RULE          BACKEND   ADDRESS
test      -
          foo.bar.com
          /foo          s1:80
          /bar          s2:80
```

### 虚拟主机 Ingress

虚拟主机 Ingress 即根据名字的不同转发到不同的后端服务上，而他们共用同一个的 IP 地址，如下所示

```text
foo.bar.com --|                 |-> foo.bar.com s1:80
              | 178.91.123.132  |
bar.foo.com --|                 |-> bar.foo.com s2:80
```

下面是一个基于 [Host header](https://tools.ietf.org/html/rfc7230#section-5.4) 路由请求的 Ingress：

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

> 注：没有定义规则的后端服务称为默认后端服务，可以用来方便的处理 404 页面。

### TLS Ingress

TLS Ingress 通过 Secret 获取 TLS 私钥和证书 \(名为 `tls.crt` 和 `tls.key`\)，来执行 TLS 终止。如果 Ingress 中的 TLS 配置部分指定了不同的主机，则它们将根据通过 SNI TLS 扩展指定的主机名（假如 Ingress controller 支持 SNI）在多个相同端口上进行复用。

定义一个包含 `tls.crt` 和 `tls.key` 的 secret：

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

注意，不同 Ingress controller 支持的 TLS 功能不尽相同。 请参阅有关 [nginx](https://kubernetes.github.io/ingress-nginx/)，[GCE](https://github.com/kubernetes/ingress-gce) 或任何其他 Ingress controller 的文档，以了解 TLS 的支持情况。

## 更新 Ingress

可以通过 `kubectl edit ing name` 的方法来更新 ingress：

```bash
$ kubectl get ing
NAME      RULE          BACKEND   ADDRESS
test      -                       178.91.123.132
          foo.bar.com
          /foo          s1:80
$ kubectl edit ing test
```

这会弹出一个包含已有 IngressSpec yaml 文件的编辑器，修改并保存就会将其更新到 kubernetes API server，进而触发 Ingress Controller 重新配置负载均衡：

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

更新后：

```bash
$ kubectl get ing
NAME      RULE          BACKEND   ADDRESS
test      -                       178.91.123.132
          foo.bar.com
          /foo          s1:80
          bar.baz.com
          /foo          s2:80
```

当然，也可以通过 `kubectl replace -f new-ingress.yaml` 命令来更新，其中 new-ingress.yaml 是修改过的 Ingress yaml。

## Ingress Controller

Ingress controller 独立于 Kubernetes 控制平面部署。请选择仍受维护、与集群和网络实现兼容的 controller，并按其上游文档安装及配置；Helm chart、参数和支持周期因实现而异，不要照搬已过时的 chart 仓库命令。

其他 Ingress Controller 还有：

* [traefik ingress](../../extension/ingress/service-discovery-and-load-balancing.md) 提供了一个 Traefik Ingress Controller 的实践案例
* [kubernetes/ingress-nginx](https://github.com/kubernetes/ingress-nginx) 提供了一个详细的 Nginx Ingress Controller 示例
* [kubernetes/ingress-gce](https://github.com/kubernetes/ingress-gce) 提供了一个用于 GCE 的 Ingress Controller 示例

## Ingress Class

在 Ingress Class 之前，要给 Ingress 选择具体的 Controller，需要加上特殊的 annotation（如 kubernetes.io/ingress.class: nginx）。而有了 IngressClass，集群管理员就可以预先创建好支持的 Ingress 类型，并可以 Ingress 中直接引用。

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

## Gateway API - Ingress 的下一代演进

Gateway API 是一组用于配置集群流量路由的 API，提供比 Ingress 更丰富的角色与路由模型。其 API 版本、标准通道和实现支持情况会随发布演进，请查阅 [Gateway API 官方文档](https://gateway-api.sigs.k8s.io/)与所选 controller 的兼容性说明。

Ingress 仍是受支持的 API。新部署可以根据需求评估 Gateway API；迁移时应确认所选实现支持目标功能，并同时验证路由行为。

## 参考文档

* [Kubernetes Ingress Resource](https://kubernetes.io/docs/concepts/services-networking/ingress/)
* [Gateway API](https://gateway-api.sigs.k8s.io/)
* [Gateway API v1.3.0 Release](https://kubernetes.io/blog/2025/06/02/gateway-api-v1-3/)
* [Kubernetes Ingress Controller](https://github.com/kubernetes/ingress/tree/master)
* [使用 NGINX Plus 负载均衡 Kubernetes 服务](http://dockone.io/article/957)
* [使用 NGINX 和 NGINX Plus 的 Ingress Controller 进行 Kubernetes 的负载均衡](http://www.cnblogs.com/276815076/p/6407101.html)
* [Kubernetes Ingress Controller-Træfɪk](https://doc.traefik.io/traefik/providers/kubernetes-ingress/)
* [Kubernetes 1.2 and simplifying advanced networking with Ingress](https://kubernetes.io/blog/2016/03/kubernetes-1-2-and-simplifying-advanced-networking-with-ingress/)
