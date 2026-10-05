# Service

Kubernetes 在设计之初就充分考虑了针对容器的服务发现与负载均衡机制，提供了 Service 资源，并通过 kube-proxy 配合 cloud provider 来适应不同的应用场景。随着 kubernetes 用户的激增，用户场景的不断丰富，又产生了一些新的负载均衡机制。目前，kubernetes 中的负载均衡大致可以分为以下几种机制，每种机制都有其特定的应用场景：

* Service：直接用 Service 提供 cluster 内部的负载均衡，并借助 cloud provider 提供的 LB 提供外部访问
* Ingress Controller：还是用 Service 提供 cluster 内部的负载均衡，但是通过自定义 Ingress Controller 提供外部访问
* Service Load Balancer：把 load balancer 直接跑在容器中，实现 Bare Metal 的 Service Load Balancer
* Custom Load Balancer：自定义负载均衡，并替代 kube-proxy，一般在物理部署 Kubernetes 时使用，方便接入公司已有的外部服务

## Service

![](../../.gitbook/assets/14735737093456%20%284%29.jpg)

Service 是对一组提供相同功能的 Pod 的抽象，并为它们提供统一入口。Service 通过标签选择器关联后端；kube-proxy 或兼容的替代实现根据控制面维护的 EndpointSlices 转发流量。

> **API 迁移：** Endpoints API 自 Kubernetes v1.33 起弃用。新工具和排障流程应读取 `discovery.k8s.io/v1` 的 EndpointSlices。

Service 有四种类型：

* ClusterIP：默认类型，自动分配一个仅 cluster 内部可以访问的虚拟 IP
* NodePort：在 ClusterIP 基础上为 Service 在每台机器上绑定一个端口，这样就可以通过 `<NodeIP>:NodePort` 来访问该服务。如果 kube-proxy 设置了 `--nodeport-addresses=10.240.0.0/16`（v1.10 支持），那么仅该 NodePort 仅对设置在范围内的 IP 有效。
* LoadBalancer：在 NodePort 的基础上，借助 cloud provider 创建一个外部的负载均衡器，并将请求转发到 `<NodeIP>:NodePort`
* ExternalName：将服务通过 DNS CNAME 记录转发到指定域名（通过 `spec.externalName` 设定）；解析由集群 DNS 实现提供。

另外，也可以将已有的服务以 Service 的形式加入到 Kubernetes 集群中来，只需要在创建 Service 的时候不指定 Label selector，而是在 Service 创建好后手动为其添加 endpoint。

### Service 定义

Service 的定义也是通过 yaml 或 json，比如下面定义了一个名为 nginx 的服务，将服务的 80 端口转发到 default namespace 中带有标签 `run=nginx` 的 Pod 的 80 端口

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

当服务需要多个端口时，每个端口都必须设置一个名字

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

### 协议

Service、Endpoints（已弃用，建议使用 EndpointSlices）和 Pod 支持三种类型的协议：

* TCP（Transmission Control Protocol，传输控制协议）是一种面向连接的、可靠的、基于字节流的传输层通信协议。
* UDP（User Datagram Protocol，用户数据报协议）是一种无连接的传输层协议，用于不可靠信息传送服务。
* SCTP（Stream Control Transmission Protocol，流控制传输协议），用于通过IP网传输SCN（Signaling Communication Network，信令通信网）窄带信令消息。

### API 版本

Service 使用核心 API 组的 `v1`（`apiVersion: v1`）。
### 不指定 Selectors 的服务

在创建 Service 的时候，也可以不指定 Selectors，用来将 service 转发到 kubernetes 集群外部的服务（而不是 Pod）。目前支持两种方法

（1）自定义 endpoint，即创建同名的 service 和 endpoint，在 endpoint 中设置外部服务的 IP 和端口

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
# 兼容旧客户端的 Endpoints API（v1.33 起弃用，不建议新增）
kind: Endpoints
apiVersion: v1
metadata:
  name: my-service
subsets:
  - addresses:
      - ip: 1.2.3.4
    ports:
      - port: 9376

```

推荐使用 EndpointSlices 替代 Endpoints：

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

（2）通过 DNS 转发，在 service 定义中指定 externalName。此时 DNS 服务会给 `<service-name>.<namespace>.svc.cluster.local` 创建一个 CNAME 记录，其值为 `my.database.example.com`。并且，该服务不会自动分配 Cluster IP，需要通过 service 的 DNS 来访问。

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

注意：Endpoints 的 IP 地址不能是 127.0.0.0/8、169.254.0.0/16 和 224.0.0.0/24，也不能是 Kubernetes 中其他服务的 clusterIP。

### Headless 服务

Headless 服务即不需要 Cluster IP 的服务，即在创建服务的时候指定 `spec.clusterIP=None`。包括两种类型

* 不指定 Selectors，但设置 externalName，即上面的（2），通过 CNAME 记录处理
* 指定 Selectors，通过 DNS A 记录设置后端 endpoint 列表

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

## 保留源 IP

各种类型的 Service 对源 IP 的处理方法不同：

* ClusterIP Service：使用 iptables 模式，集群内部的源 IP 会保留（不做 SNAT）。如果 client 和 server pod 在同一个 Node 上，那源 IP 就是 client pod 的 IP 地址；如果在不同的 Node 上，源 IP 则取决于网络插件是如何处理的，比如使用 flannel 时，源 IP 是 node flannel IP 地址。
* NodePort Service：默认情况下，源 IP 会做 SNAT，server pod 看到的源 IP 是 Node IP。为了避免这种情况，可以给 service 设置 `spec.ExternalTrafficPolicy=Local` （1.6-1.7 版本设置 Annotation `service.beta.kubernetes.io/external-traffic=OnlyLocal`），让 service 只代理本地 endpoint 的请求（如果没有本地 endpoint 则直接丢包），从而保留源 IP。
* LoadBalancer Service：默认情况下，源 IP 会做 SNAT，server pod 看到的源 IP 是 Node IP。设置 `service.spec.ExternalTrafficPolicy=Local` 后可以自动从云平台负载均衡器中删除没有本地 endpoint 的 Node，从而保留源 IP。

## 内部网络策略

默认情况下，Kubernetes 把集群中所有 Endpoints 的 IP 作为 Service 的后端。你可以通过设置 `.spec.internalTrafficPolicy=Local` 让 kube-proxy 只为 Node 本地的 Endpoints 做负载均衡。

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

注意，开启内网网络策略之后，即使其他 Node 上面有正常工作的 Endpoints，只要 Node 本地没有正常运行的 Pod，该 Service 就无法访问。

## 工作原理

kube-proxy 负责将 service 负载均衡到后端 Pod 中，如下图所示

![](../../.gitbook/assets/service-flow%20%284%29.png)

## Ingress

Service provides network reachability and transport-level balancing. For HTTP(S) routing, use an Ingress resource with a compatible Ingress controller or Gateway API implementation; creating an Ingress alone does not install a controller.

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

Ingress 和 Ingress controller 的介绍参见[专章](ingress.md)。

## Service Load Balancer（历史项目）

本节原先介绍的 `kubernetes/contrib/service-loadbalancer` 是已归档的旧项目，不应作为当前部署建议。根据集群类型选择受维护的云负载均衡集成、MetalLB 等实现，或受支持的 Ingress/Gateway controller，并遵循其当前文档。

## Custom Load Balancer

虽然 Kubernetes 提供了丰富的负载均衡机制，但在实际使用的时候，还是会碰到一些复杂的场景是它不能支持的，比如

* 接入已有的负载均衡设备
* 多租户网络情况下，容器网络和主机网络是隔离的，这样 `kube-proxy` 就不能正常工作

自定义负载均衡实现应使用 EndpointSlices 等当前 API 发现 Service 后端，并按所选网络架构配置流量转发；实现、可用性与升级方式取决于所选项目。
## 集群外部访问服务

Service 对外暴露方式取决于平台与网络实现：

* `NodePort` 在节点地址上开放所分配的端口；应限制防火墙允许来源，不要默认将端口暴露到公网。
* `LoadBalancer` 由云平台或已安装的负载均衡实现提供外部地址，流量路径可能因实现而异。
* Ingress controller 或 Gateway controller 适用于 HTTP(S) 路由。
* 裸金属环境可评估受维护的负载均衡实现，例如 [MetalLB](https://metallb.io/)。
## Endpoints 迁移到 EndpointSlices

从 Kubernetes v1.33 起，Endpoints API 已弃用。新客户端应读取 EndpointSlices；Service 控制器会维护其选择器对应的 EndpointSlices。

### 主要差异

1. **多个 EndpointSlices vs 单个 Endpoints**：
   - 一个 Service 可以对应多个 EndpointSlices
   - 需要使用标签选择器 `kubernetes.io/service-name=<servicename>` 来查找相关的 EndpointSlices

2. **API 结构差异**：
   - EndpointSlices 使用 `discovery.k8s.io/v1` API 组
   - 明确指定 `addressType`（IPv4 或 IPv6）
   - 每个 endpoint 通常包含单个地址

### 代码迁移示例

**旧的 Endpoints API 用法**：

```go
endpoints, err := clientset.CoreV1().Endpoints(namespace).Get(ctx, serviceName, metav1.GetOptions{})
```

**新的 EndpointSlices API 用法**：

```go
endpointSlices, err := clientset.DiscoveryV1().EndpointSlices(namespace).List(ctx, metav1.ListOptions{
    LabelSelector: fmt.Sprintf("kubernetes.io/service-name=%s", serviceName),
})
```

### EndpointSlices 的优势

- **支持双栈网络**：可同时支持 IPv4 和 IPv6 地址
- **更好的性能**：在大规模集群中减少资源开销
- **流量分发**：支持更灵活的流量分发策略
- **简化实现**：简化了服务代理和控制器的实现

### 迁移建议

1. **逐步迁移**：在现有代码中同时支持两种 API，然后逐步切换
2. **测试验证**：确保新的 EndpointSlices 逻辑在生产环境中正常工作
3. **监控告警**：设置监控来跟踪 Endpoints API 的使用情况

## 参考资料

* [https://kubernetes.io/docs/concepts/services-networking/service/](https://kubernetes.io/docs/concepts/services-networking/service/)
* [https://kubernetes.io/docs/concepts/services-networking/ingress/](https://kubernetes.io/docs/concepts/services-networking/ingress/)
* [https://kubernetes.io/blog/2025/04/24/endpoints-deprecation/](https://kubernetes.io/blog/2025/04/24/endpoints-deprecation/)
* [https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/)
* [https://github.com/kubernetes/contrib/tree/master/service-loadbalancer](https://github.com/kubernetes/contrib/tree/master/service-loadbalancer)
* [https://www.nginx.com/blog/load-balancing-kubernetes-services-nginx-plus/](https://www.nginx.com/blog/load-balancing-kubernetes-services-nginx-plus/)
* [https://github.com/weaveworks/flux](https://github.com/weaveworks/flux)
* [https://github.com/AdoHe/kube2haproxy](https://github.com/AdoHe/kube2haproxy)
* [Accessing Kubernetes Services Without Ingress, NodePort, or LoadBalancer](https://medium.com/@kyralak/accessing-kubernetes-services-without-ingress-nodeport-or-loadbalancer-de6061b42d72)
