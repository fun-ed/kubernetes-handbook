# 网络插件

## 网络模型

* IP-per-Pod，每个 Pod 都拥有一个独立 IP 地址，Pod 内所有容器共享一个网络命名空间
* 集群内所有 Pod 都在一个直接连通的扁平网络中，可通过 IP 直接访问
  * 所有容器之间无需 NAT 就可以直接互相访问
  * 所有 Node 和所有容器之间无需 NAT 就可以直接互相访问
  * 容器自己看到的 IP 跟其他容器看到的一样
* Service ClusterIP 仅供集群内访问；外部请求可通过 NodePort、LoadBalancer 或 Gateway/Ingress 暴露

## 网络插件和版本（2026-10-05）

Kubernetes 不提供一个可通用于所有集群的默认 Pod 网络实现。每个集群必须配置一个符合 CNI 要求的网络实现。选定并安装一种主 CNI；不要把多个互不兼容的 CNI 当作并列安装步骤。CNI 插件二进制包不是完整的多节点 Kubernetes 网络方案，须按网络实现的部署说明配置 IPAM、路由、策略和运行时。

| 网络实现或组件 | 稳定版本 | Kubernetes v1.37.1 兼容性证据 |
| :--- | :--- | :--- |
| [Cilium](https://github.com/cilium/cilium/releases/tag/v1.20.2) | v1.20.2（2026-09-16） | Cilium v1.20 官方矩阵只保证 Kubernetes 1.33–1.36；未列出 v1.37。 |
| [Calico](https://github.com/projectcalico/calico/releases/tag/v3.33.0) | v3.33.0（2026-10-01） | 官方测试 Kubernetes 1.35、1.36 和 1.37。 |
| [Flannel](https://github.com/flannel-io/flannel/releases/tag/v0.28.9) | v0.28.9（2026-08-07） | 未找到该版本针对 v1.37 的官方兼容矩阵；不可据此宣称受支持。 |
| [OVN-Kubernetes](https://github.com/ovn-kubernetes/ovn-kubernetes/releases/tag/v1.4.0) | v1.4.0（2026-09-04） | 发布说明提到 Kubernetes v1.36.2；未找到 v1.37 兼容声明。 |
| [CNI plugins](https://github.com/containernetworking/plugins/releases/tag/v1.9.1) | v1.9.1（2026-03-16） | Kubernetes v1.37.1 源码依赖清单固定此版本；它是 CNI 插件二进制包，不是完整集群网络。 |
| [SR-IOV Network Operator](https://github.com/k8snetworkplumbingwg/sriov-network-operator/releases/tag/v1.6.0) | v1.6.0（2025-08-13） | 发布说明提到 OpenShift 4.18；未声明支持 Kubernetes v1.37.1。它是硬件/设备运营组件，不是通用主 CNI。 |

安装前应检查网络实现的兼容矩阵、内核和平台前提，并确认 Pod CIDR、Service CIDR、节点网络和防火墙规则互不冲突。具体的版本化安装命令见 [Cilium](cilium.md)、[Calico](calico.md) 和 [Flannel](flannel.md)。

## 历史网络插件接口

下文的 kubenet 和 exec 插件文字用于解释旧集群的实现背景，不代表 Kubernetes v1.37.1 的通用默认值或可用的安装方式。exec 网络插件接口早已移除。当前集群应按发行版文档配置 CNI。

* CNI（Container Network Interface）是运行时与网络插件之间的接口和配置格式；它本身不是一种网络实现。
* kubenet 是历史上的一种简单网络实现，是否提供以及如何配置取决于 Kubernetes 发行版。不要把它写成通用推荐默认值。
* exec：Kubernetes 已移除的旧 kubelet 网络插件接口。需要扩展网络时使用 CNI 实现。


## kubenet（历史实现）
> 本节保留旧版 kubenet 工作方式说明，不是 Kubernetes v1.37.1 的安装方法。


kubenet 是一个基于 CNI bridge 的网络插件，它为每个容器建立一对 veth pair 并连接到 cbr0 网桥上。kubenet 在 bridge 插件的基础上拓展了很多功能，包括

* 使用 host-local IPAM 插件为容器分配 IP 地址， 并定期释放已分配但未使用的 IP 地址
* 设置 sysctl `net.bridge.bridge-nf-call-iptables = 1`
* 为 Pod IP 创建 SNAT 规则
  * `-A POSTROUTING ! -d 10.0.0.0/8 -m comment --comment "kubenet: SNAT for outbound traffic from cluster" -m addrtype ! --dst-type LOCAL -j MASQUERADE`
* 开启网桥的 hairpin 和 promisc 模式，允许 Pod 访问它自己所在的 Service IP（即通过 NAT 后再访问 Pod 自己）

  ```bash
  -A OUTPUT -j KUBE-DEDUP
  -A KUBE-DEDUP -p IPv4 -s a:58:a:f4:2:1 -o veth+ --ip-src 10.244.2.1 -j ACCEPT
  -A KUBE-DEDUP -p IPv4 -s a:58:a:f4:2:1 -o veth+ --ip-src 10.244.2.0/24 -j DROP
  ```

* HostPort 管理以及设置端口映射
* Traffic shaping，支持通过 `kubernetes.io/ingress-bandwidth` 和 `kubernetes.io/egress-bandwidth` 等 Annotation 设置 Pod 网络带宽限制

下图是一个 Kubernetes on Azure 多节点的 Pod 之间相互通信的原理：

![image-20190316183639488](../../.gitbook/assets/image-20190316183639488%20%281%29.png)

跨节点 Pod 之间相互通信时，会通过云平台或者交换机配置的路由转发到正确的节点中：

![image-20190316183650404](../../.gitbook/assets/image-20190316183650404.png)

未来 kubenet 插件会迁移到标准的 CNI 插件（如 ptp），具体计划见 [这里](https://docs.google.com/document/d/1glJLMHrE2eqwRrAN4fdsz4Vg3R1Iqt6bm5GJQ4GdjlQ/edit#)。

## CNI bridge 示例（历史本地实验）

> 本节的 bridge 配置演示单机 CNI 行为，不是适用于 Kubernetes 集群的完整网络方案。旧仓库地址已退役，CNI 0.3.0 示例也不是 Kubernetes v1.37.1 的安装配置。当前 CNI 二进制版本见上表；请按你选定的 CNI 项目文档安装和配置。

更多 CNI 网络插件接口和本地实验细节见 [CNI 网络插件](cni.md)。

## [Flannel](flannel.md)

[Flannel](https://github.com/flannel-io/flannel) 是使用 overlay 或主机路由为 Pod 提供连通性的 CNI 实现。2026-10-05 的稳定版本为 [v0.28.9](https://github.com/flannel-io/flannel/releases/tag/v0.28.9)。本书未找到官方针对 Kubernetes v1.37 的兼容矩阵；安装前核对上游发布说明和集群前提。按 [Flannel 版本化指南](flannel.md)安装，不要使用 `master` 清单。

## Weave Net 历史架构

Weave Net 曾使用 Gossip 控制平面和 UDP overlay。上游仓库已归档，旧 Kubernetes 安装端点与清单不能用于当前集群。历史技术细节见[归档索引](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/index.md)。

## [Calico](calico.md)

Calico 是 CNI 网络实现，也提供网络策略功能。2026-10-05 的稳定版本为 [v3.33.0](https://github.com/projectcalico/calico/releases/tag/v3.33.0)。官方要求说明此版本测试 Kubernetes 1.35、1.36 和 1.37。按 [Calico 版本化指南](calico.md)安装；不要使用旧版本清单。


## [OVN Kubernetes](ovn-kubernetes.md)
> OVN-Kubernetes v1.4.0 发布说明提到 Kubernetes v1.36.2，但没有验证 v1.37.1 的兼容性声明。见[固定版本的架构和历史示例](ovn-kubernetes.md)。


[OVN (Open Virtual Network)](https://www.ovn.org/en/) 是 OVS 提供的原生虚拟化网络方案，旨在解决传统 SDN 架构（比如 Neutron DVR）的性能问题。

OVN 为 Kubernetes 提供了两种网络方案：

* Overaly: 通过 ovs overlay 连接容器
* Underlay: 将 VM 内的容器连到 VM 所在的相同网络（开发中）

其中，容器网络的配置是通过 OVN 的 CNI 插件来实现。

## Contiv 历史架构

Contiv 曾提供多租户容器网络与策略管理。上游仓库已归档，旧安装步骤不能用于当前集群。历史技术细节见[归档索引](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/index.md)。

## Romana

> 历史架构简介；本书未核实可用于 Kubernetes v1.37.1 的当前发行版或兼容矩阵。

Romana 是 Panic Networks 在 2016 年提出的开源项目，旨在借鉴 route aggregation 的思路来解决 Overlay 方案给网络带来的开销。

## OpenContrail / Contrail

Juniper/Contrail 提供网络虚拟化控制器和 vRouter。上游 release 页面没有可确认的带日期稳定版本，且本书未找到 Kubernetes v1.37 兼容矩阵；生命周期状态未证实，不能据此称其已退役。旧 Kubernetes 集成依赖已移除的 exec network plugin，不适用于当前集群。见[上游发布信息](https://github.com/Juniper/contrail-controller/releases)。

## Midonet

> 历史 OpenStack 网络架构简介，不是 Kubernetes v1.37.1 的 CNI 部署指南。

Midonet 曾由 Zookeeper 和 Cassandra 保存 VPC 资源状态，并将控制器分布到转发设备。其资料不应直接套用到当前 Kubernetes 集群。

## Host network

最简单的网络模型就是让容器共享 Host 的 network namespace，使用宿主机的网络协议栈。这样，不需要额外的配置，容器就可以共享宿主的各种网络资源。

优点

* 简单，不需要任何额外配置
* 高效，没有 NAT 等额外的开销

缺点

* 没有任何的网络隔离
* 容器和 Host 的端口号容易冲突
* 容器内任何网络配置都会影响整个宿主机

> 注意：HostNetwork 只让 Pod 使用宿主机的网络命名空间，不会代替集群 Pod 网络。节点仍需要由发行版提供或安装一个主 CNI；Kubernetes v1.37.1 不会默认配置 kubenet。

## 其他

### ipvs（历史模式）

Kubernetes v1.8 起支持过 ipvs kube-proxy 模式。当前 IPVS 模式已弃用；nftables kube-proxy 模式已 GA，但不是默认值。选择并配置服务代理模式时，按 v1.37 文档核对内核前提；不要照搬下面的旧版 alpha 说明。

### [Canal](https://github.com/tigera/canal)

Canal 组合 Calico 网络策略和 Flannel 网络实现。该旧简介未记录与 Kubernetes v1.37.1 匹配的 Canal 发行版及兼容矩阵；如使用，应确认供应方明确支持所选 Flannel 和 Calico 版本，不要把它当作额外主 CNI 叠加安装。

### Kuryr-Kubernetes（已退役）

> OpenStack Kuryr-Kubernetes 的 [2024.1-eom 发布](https://github.com/openstack/kuryr-kubernetes/releases/tag/2024.1-eom)明确标记项目为 **RETIRED**（2025-10-31）。不要用于新集群；旧教程与配置见[归档索引](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/index.md)。

### [Cilium](https://github.com/cilium/cilium)

Cilium 是基于 eBPF 和 XDP 的网络实现，提供 CNI 和网络策略功能。截至 2026-10-05，其稳定版为 [v1.20.2](https://github.com/cilium/cilium/releases/tag/v1.20.2)；[v1.20 官方矩阵](https://docs.cilium.io/en/v1.20/network/kubernetes/compatibility/)只保证 Kubernetes 1.33–1.36，没有列出 v1.37。安装见[Cilium 当前指南](cilium.md)，不要使用旧教程的 `HEAD` 清单或历史部署步骤。

### kope

> 历史路由项目简介；本书未核实 Kubernetes v1.37.1 支持状态或当前安装指南。

### [Kube-router](https://github.com/cloudnativelabs/kube-router)

[Kube-router](https://github.com/cloudnativelabs/kube-router) 是一个基于 BGP 的网络插件，并提供了可选的 ipvs 服务发现（替代 kube-proxy）以及网络策略功能。

> **历史安装说明（不可执行）**：本页旧例使用 `master` 清单、删除 kube-proxy DaemonSet 和 Docker Engine 命令，均不是当前 Kubernetes v1.37.1 的安全部署步骤。本书未确认 Kube-router 的当前稳定版本或 v1.37 兼容性；不要运行旧命令，须先查项目发行说明和支持矩阵。

Cilium 的 BGP 控制平面与 IPv6 路由场景另见 [Cilium BGP 与 IPv6](cilium-bgp-ipv6.md)。如使用 nftables kube-proxy 模式，请参阅 [nftables 专章](../../network/nftables.md)；模式兼容性取决于集群环境与版本，不应视为默认值。
