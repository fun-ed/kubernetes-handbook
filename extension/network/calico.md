# Calico

[Calico](https://www.projectcalico.org/) 是一个纯三层的数据中心网络方案（不需要 Overlay），并且与 OpenStack、Kubernetes、AWS、GCE 等 IaaS 和容器平台都有良好的集成。

Calico 在每一个计算节点利用 Linux Kernel 实现了一个高效的 vRouter 来负责数据转发，而每个 vRouter 通过 BGP 协议负责把自己上运行的 workload 的路由信息像整个 Calico 网络内传播——小规模部署可以直接互联，大规模下可通过指定的 BGP route reflector 来完成。 这样保证最终所有的 workload 之间的数据流量都是通过 IP 路由的方式完成互联的。Calico 节点组网可以直接利用数据中心的网络结构（无论是 L2 或者 L3），不需要额外的 NAT，隧道或者 Overlay Network。

此外，Calico 基于 iptables 还提供了丰富而灵活的网络 Policy，保证通过各个节点上的 ACLs 来提供 Workload 的多租户隔离、安全组以及其他可达性限制等功能。

## 当前 Kubernetes 安装（2026-10-05）

Calico v3.33.0 是截至 2026-10-05 的稳定版本。官方支持矩阵明确列出 Kubernetes 1.35、1.36 和 1.37，节点还需要 Linux kernel 5.10 或更高版本。为 Kubernetes 1.37 安装时，先配置与集群一致且不重叠的 Pod CIDR，再执行 Calico 3.33.0 的版本化 CRD、Tigera Operator 和自定义资源清单：

```bash
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/v3_projectcalico_org.yaml
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/tigera-operator.yaml
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/custom-resources.yaml
```

默认自定义资源清单使用 `192.168.0.0/16`。如果创建集群时选了其他 Pod CIDR，先编辑对应的 `Installation` 自定义资源，不要照搬默认 CIDR。集群只能选择一个主 CNI；不要把 Calico 和另一种不兼容的网络实现并装。

来源：[Calico v3.33.0 release](https://github.com/projectcalico/calico/releases/tag/v3.33.0)、[Kubernetes 安装要求和兼容矩阵](https://docs.tigera.io/calico/latest/getting-started/kubernetes/requirements)、[Calico 安装指南](https://docs.tigera.io/calico/latest/getting-started/kubernetes/quickstart)。

> 以下 Calico 架构、etcd、Docker CNM、旧 CNI 配置和 `v3.1`/`v3.0` 命令是历史教学材料，不要用于当前 Kubernetes 安装。


## Calico 架构

![](../../.gitbook/assets/calico%20%281%29.png)

Calico 主要由 Felix、etcd、BGP client 以及 BGP Route Reflector 组成

1. Felix，Calico Agent，跑在每台需要运行 Workload 的节点上，主要负责配置路由及 ACLs 等信息来确保 Endpoint 的连通状态；
2. etcd，分布式键值存储，主要负责网络元数据一致性，确保 Calico 网络状态的准确性；
3. BGP Client（BIRD）, 主要负责把 Felix 写入 Kernel 的路由信息分发到当前 Calico 网络，确保 Workload 间的通信的有效性；
4. BGP Route Reflector（BIRD），大规模部署时使用，摒弃所有节点互联的 mesh 模式，通过一个或者多个 BGP Route Reflector 来完成集中式的路由分发。
5. calico/calico-ipam，主要用作 Kubernetes 的 CNI 插件

![](../../.gitbook/assets/calico2.png)

## IP-in-IP

Calico 控制平面的设计要求物理网络得是 L2 Fabric，这样 vRouter 间都是直接可达的，路由不需要把物理设备当做下一跳。为了支持 L3 Fabric，Calico 推出了 IPinIP 的选项。

## Calico CNI

见 [https://github.com/projectcalico/cni-plugin](https://github.com/projectcalico/cni-plugin)。

## Calico CNM

Calico 通过 Pool 和 Profile 的方式实现了 docker CNM 网络：

1. Pool，定义可用于 Docker Network 的 IP 资源范围，比如：10.0.0.0/8 或者 192.168.0.0/16；
2. Profile，定义 Docker Network Policy 的集合，由 tags 和 rules 组成；每个 Profile 默认拥有一个和 Profile 名字相同的 Tag，每个 Profile 可以有多个 Tag，以 List 形式保存。

具体实现见 [https://github.com/projectcalico/libnetwork-plugin](https://github.com/projectcalico/libnetwork-plugin)。

> 旧 etcd/Docker 集成、`v3.1` manifest、禁用 TLS 验证的 kubeconfig 与旧进程输出已封存；当前安装步骤见上方 Calico v3.33.0 指南。见[封存原始材料](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/extension/network/calico.md)。

**参考文档**

* [https://xuxinkun.github.io/2016/07/22/cni-cnm/](https://xuxinkun.github.io/2016/07/22/cni-cnm/)
* [https://www.projectcalico.org/](https://www.projectcalico.org/)
* [http://blog.dataman-inc.com/shurenyun-docker-133/](http://blog.dataman-inc.com/shurenyun-docker-133/)

