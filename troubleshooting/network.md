# 网络排错

本章主要介绍各种常见的网络问题以及排错方法，包括 Pod 访问异常、Service 访问异常以及网络安全策略异常等。

说到 Kubernetes 的网络，其实无非就是以下三种情况之一

* Pod 访问容器外部网络
* 从容器外部访问 Pod 网络
* Pod 之间相互访问

当然，以上每种情况还都分别包括本地访问和跨主机访问两种场景，并且一般情况下都是通过 Service 间接访问 Pod。

排查网络问题基本上也是从这几种情况出发，定位出具体的网络异常点，再进而寻找解决方法。网络异常可能的原因比较多，常见的有

* CNI 网络插件配置错误，导致多主机网络不通，比如
  * IP 网段与现有网络冲突
  * 插件使用了底层网络不支持的协议
  * 忘记开启 IP 转发等
    * `sysctl net.ipv4.ip_forward`
    * `sysctl net.bridge.bridge-nf-call-iptables`
* Pod 网络路由丢失，比如
  * kubenet 要求网络中有 podCIDR 到主机 IP 地址的路由，这些路由如果没有正确配置会导致 Pod 网络通信等问题
  * 在公有云平台上，kube-controller-manager 会自动为所有 Node 配置路由，但如果配置不当（如认证授权失败、超出配额等），也有可能导致无法配置路由
* Service NodePort 和 health probe 端口冲突
  * 在 1.10.4 版本之前的集群中，多个不同的 Service 之间的 NodePort 和 health probe 端口有可能会有重合 （已经在 [kubernetes\#64468](https://github.com/kubernetes/kubernetes/pull/64468) 修复）
* 主机内或者云平台的安全组、防火墙或者安全策略等阻止了 Pod 网络，比如
  * 非 Kubernetes 管理的 iptables 规则禁止了 Pod 网络
  * 公有云平台的安全组禁止了 Pod 网络（注意 Pod 网络有可能与 Node 网络不在同一个网段）
  * 交换机或者路由器的 ACL 禁止了 Pod 网络

## CNI 插件无法启动

网络插件的 DaemonSet、镜像和配置由集群发行版或网络供应商维护。不要直接应用分支上的未固定版本清单；先检查相关 Pod Events 和容器日志：

```bash
kubectl -n kube-system get pods -o wide
CNI_POD='<cni-pod>'
kubectl -n kube-system describe pod "$CNI_POD"
kubectl -n kube-system logs "$CNI_POD" --all-containers=true --tail=100
```

如果日志提示 SELinux 拒绝访问，应查看节点审计日志并按所选网络插件的当前文档修正策略。不要通过禁用 SELinux 或改成 permissive 来绕过问题。
## Pod 无法分配 IP

先查看 Pod Events、Node Pod CIDR 与节点资源，确认问题属于 IP 地址耗尽、CNI 初始化失败还是运行时 sandbox 创建失败：

```bash
NODE='<node-name>'
kubectl describe pod '<pod-name>' -n '<namespace>'
kubectl describe node "$NODE"
kubectl get pods --all-namespaces -o wide --field-selector="spec.nodeName=$NODE"
```

在 Node 上可用 `crictl` 对照当前 runtime 的容器与 Pod sandbox；确保 `crictl` 使用该 Node 实际 CRI socket。IPAM 状态文件的位置和恢复方式由具体 CNI/IPAM 插件决定：

```bash
sudo crictl info
sudo crictl pods
sudo crictl ps -a
```

IPAM 地址池显示耗尽或状态不一致时，先检查插件日志、地址池容量和已分配 Pod，再按 CNI 供应商文档处理。不要停止 kubelet、直接删除 IPAM 分配文件、虚拟网卡或网络命名空间；这些操作可能破坏仍在使用的地址并造成更大范围网络中断。

## Pod 无法解析 DNS

先查看 CoreDNS Pod、Service 与 EndpointSlices，再从 Pod 内测试集群域名：

```bash
kubectl -n kube-system get pods
kubectl -n kube-system get services
# Replace with the DNS Service name shown above
DNS_SERVICE='<dns-service-name>'
kubectl -n kube-system get endpointslices -l "kubernetes.io/service-name=$DNS_SERVICE"
kubectl run dns-check --image=busybox:1.37.0 --restart=Never --rm -it -- \
  nslookup kubernetes.default.svc.cluster.local
```

若集群 DNS 的 Service 或 EndpointSlices 异常，查看 DNS Pod 日志、Corefile、NetworkPolicy 及 Pod 到 DNS Service 的网络路径。DNS Service 名称可能因发行版而异；不要直接创建或替换一个硬编码 ClusterIP 的 kube-dns Service。

CoreDNS 配置语法与插件支持依赖实际 CoreDNS 版本。遇到 `proxy`、`forward` 等插件问题时，先核对当前 Corefile 和所用 CoreDNS 版本文档；本页旧版 proxy 迁移配置不应直接用于生产环境。检查 Service 网络时请同时确认 kube-proxy 或替代实现是否正常。

## DNS 解析缓慢

DNS 延迟可能来自上游 DNS、CoreDNS 资源限制、节点网络或 conntrack 压力。先比较集群 Service 域名和外部域名的查询结果，检查 CoreDNS 与 CNI 日志，再按内核、容器运行时和集群网络实现的版本文档定位。

旧版 `single-request-reopen` 与特定内核 conntrack 问题的 workaround 并非通用修复；不要通过容器启动脚本修改 `/etc/resolv.conf` 或盲目增加 DNS 参数。对于需要本地缓存的集群，可评估受维护且与目标版本兼容的 NodeLocal DNSCache 部署文档。

更多 DNS 配置方法见 [Customizing DNS Service](https://kubernetes.io/docs/tasks/administer-cluster/dns-custom-nameservers/)。

## Service 无法访问

先确认 Service selector 匹配到预期 Pod，并使用 EndpointSlices 检查后端地址与端口：

```bash
SERVICE='<service-name>'
kubectl get service "$SERVICE" -o yaml
kubectl get pods -l '<key1=value1,key2=value2>' -o wide
kubectl get endpointslices -l "kubernetes.io/service-name=$SERVICE" -o yaml
```

如果没有后端，检查 selector、Pod readiness 与端口配置。若 EndpointSlices 正常，再分别从客户端 Pod 测试 Service DNS、ClusterIP 和后端 Pod IP，并检查 NetworkPolicy、CNI 路由、防火墙与 kube-proxy（或其替代实现）的日志。数据平面规则因 iptables、nftables、IPVS 或 eBPF 等实现而异，不要照搬另一种模式的静态规则。

## Pod 无法通过 Service 访问自己

Pod 访问指向自身的 Service 时，行为取决于 Service 流量策略、CNI 与 kube-proxy 或替代实现。先确认 Service 后端 EndpointSlices 与 Pod readiness，再查看所用网络插件的 hairpin/loopback 文档；不要依赖旧版 `cbr0`、`--hairpin-mode` 或固定网桥的命令。

## Pod 无法访问 Kubernetes API

先确认控制平面与 `kubernetes` Service 状态，再分别检查网络连通性和 RBAC 授权：

```bash
kubectl get service kubernetes
kubectl get endpointslices -l kubernetes.io/service-name=kubernetes
NAMESPACE='<namespace>'
SERVICE_ACCOUNT='<service-account>'
kubectl auth can-i list pods --as="system:serviceaccount:${NAMESPACE}:${SERVICE_ACCOUNT}" -n "$NAMESPACE"
```

EndpointSlice 检查控制平面后端发现，`kubectl auth can-i` 检查授权；两者都不能代替从故障 Pod 到 API Server 的实际网络测试。不要在交互式 shell 或日志中打印 ServiceAccount token。如需应用级验证，应使用可信诊断工具并避免暴露凭据。

## 内核或 Service 数据平面问题

连接超时可能与内核、conntrack、CNI 或 Service 代理配置有关。旧文章中的 iptables/SNAT workaround 针对特定内核和数据平面实现，不应当作通用修复。先确认集群的 kube-proxy 模式或替代实现，再按其当前文档和节点发行版定位。

## 参考文档

* [Troubleshoot Applications](https://kubernetes.io/docs/tasks/debug-application-cluster/debug-application/)
* [Debug Services](https://kubernetes.io/docs/tasks/debug-application-cluster/debug-service/)

