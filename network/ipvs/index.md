# kube-proxy 服务代理模式

本页原有 Kubernetes v1.8 IPVS alpha 本地实验会强制结束 kube-proxy 并手动改动主机网络，已移至[历史归档](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/network/ipvs/index.md)。请勿在当前集群运行归档示例。

在 Kubernetes v1.37 的 Linux 节点上，kube-proxy 可使用 iptables、IPVS 或 nftables 模式。Linux 上 nftables 模式要求 Linux 内核 5.13 或更新版本，自 v1.33 升为 GA，但不是默认模式；未指定模式时，Linux kube-proxy 默认使用 iptables。IPVS 自 v1.35 起弃用，但并非已从所有现有集群移除。Windows 节点仅提供 `kernelspace` 模式。选择模式前，核对节点内核／nftables 支持、发行版和 CNI 的兼容性，以及是否由 CNI/eBPF 实现取代 kube-proxy；不要在同一集群任意混用数据平面或手动复制另一模式的规则。详细模式限制与配置见 [Kubernetes v1.37 虚拟 IP 与 Service Proxy 文档](https://kubernetes.io/docs/reference/networking/virtual-ips/)。

目前 kube-proxy 配置与迁移要求，请依 [Kubernetes v1.37 虚拟 IP 与 Service Proxy 文档](https://kubernetes.io/docs/reference/networking/virtual-ips/)及 [kube-proxy 配置参考](https://kubernetes.io/docs/reference/config-api/kube-proxy-config.v1alpha1/)操作。更换代理模式是集群网络变更，须依发行版文档于维护流程中进行并验证 Service 流量；本页不提供可直接套用到任意集群的切换命令。
