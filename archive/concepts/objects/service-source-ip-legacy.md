> HISTORICAL: These source-address descriptions assume old kube-proxy/network-plugin behavior and are not universal. Check the current cluster network and load balancer documentation before relying on them. Preserved from `concepts/objects/service.md`.

## 保留源 IP

各种类型的 Service 对源 IP 的处理方法不同：

* ClusterIP Service：使用 iptables 模式，集群内部的源 IP 会保留（不做 SNAT）。如果 client 和 server pod 在同一个 Node 上，那源 IP 就是 client pod 的 IP 地址；如果在不同的 Node 上，源 IP 则取决于网络插件是如何处理的，比如使用 flannel 时，源 IP 是 node flannel IP 地址。
* NodePort Service：默认情况下，源 IP 会做 SNAT，server pod 看到的源 IP 是 Node IP。为了避免这种情况，可以给 service 设置 `spec.ExternalTrafficPolicy=Local` （1.6-1.7 版本设置 Annotation `service.beta.kubernetes.io/external-traffic=OnlyLocal`），让 service 只代理本地 endpoint 的请求（如果没有本地 endpoint 则直接丢包），从而保留源 IP。
* LoadBalancer Service：默认情况下，源 IP 会做 SNAT，server pod 看到的源 IP 是 Node IP。设置 `service.spec.ExternalTrafficPolicy=Local` 后可以自动从云平台负载均衡器中删除没有本地 endpoint 的 Node，从而保留源 IP。
