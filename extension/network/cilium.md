# Cilium

[Cilium ](https://github.com/cilium/cilium)是一个基于 eBPF 和 XDP 的高性能容器网络方案，代码开源在 [https://github.com/cilium/cilium](https://github.com/cilium/cilium)。其主要功能特性包括

* 安全上，支持 L3/L4/L7 安全策略，这些策略按照使用方法又可以分为
  * 基于身份的安全策略（security identity）
  * 基于 CIDR 的安全策略
  * 基于标签的安全策略
* 网络上，支持三层平面网络（flat layer 3 network），如
  * 覆盖网络（Overlay），包括 VXLAN 和 Geneve 等
  * Linux 路由网络，包括原生的 Linux 路由和云服务商的高级网络路由等
* 提供基于 BPF 的负载均衡
* 提供便利的监控和排错能力

![](../../.gitbook/assets/cilium.png)

## 当前安装（2026-10-05）

Cilium v1.20.2 是截至 2026-10-05 的最新稳定版本。其 Helm chart 版本与 Cilium 版本一致。官方安装文档要求配置 Kubernetes CNI 网络，并要求 Linux kernel 5.10 或更高版本。安装前确认集群没有另一个不兼容的主 CNI。

```bash
helm repo add cilium https://helm.cilium.io/
helm repo update
helm install cilium cilium/cilium \
  --version 1.20.2 \
  --namespace kube-system
```

截至 2026-10-05，Cilium v1.20 官方兼容矩阵仅列 Kubernetes 1.33、1.34、1.35 和 1.36 为端到端测试并保证兼容的版本；未列出 Kubernetes v1.37，因此不要宣称 Cilium v1.20.2 已验证支持 Kubernetes v1.37.1。其策略示例使用 Cilium CRD 的 `cilium.io/v2` API，不要仅凭 CRD API 版本推断控制器兼容性。

来源：[Cilium v1.20.2 release](https://github.com/cilium/cilium/releases/tag/v1.20.2)、[Cilium v1.20 Kubernetes 兼容矩阵](https://docs.cilium.io/en/v1.20/network/kubernetes/compatibility/)、[Cilium v1.20 Helm 安装指南](https://docs.cilium.io/en/v1.20/installation/k8s-install-helm/)。

如需深入了解 Cilium 的 BGP 控制平面与 IPv6 路由场景，请参阅 [Cilium BGP 与 IPv6](cilium-bgp-ipv6.md)；本页的版本兼容性限制仍然适用。

[eBPF](https://docs.cilium.io/en/v1.20/reference-guides/bpf/) 和 XDP 背景介绍如下。


## eBPF 和 XDP

eBPF（extended Berkeley Packet Filter）起源于BPF，它提供了内核的数据包过滤机制。BPF的基本思想是对用户提供两种SOCKET选项：`SO_ATTACH_FILTER`和`SO_ATTACH_BPF`，允许用户在sokcet上添加自定义的filter，只有满足该filter指定条件的数据包才会上发到用户空间。`SO_ATTACH_FILTER`插入的是cBPF代码，`SO_ATTACH_BPF`插入的是eBPF代码。eBPF是对cBPF的增强，目前用户端的tcpdump等程序还是用的cBPF版本，其加载到内核中后会被内核自动的转变为eBPF。Linux 3.15 开始引入 eBPF。其扩充了 BPF 的功能，丰富了指令集。它在内核提供了一个虚拟机，用户态将过滤规则以虚拟机指令的形式传递到内核，由内核根据这些指令来过滤网络数据包。

![](../../.gitbook/assets/bpf%20%282%29.png)

XDP（eXpress Data Path）为Linux内核提供了高性能、可编程的网络数据路径。由于网络包在还未进入网络协议栈之前就处理，它给Linux网络带来了巨大的性能提升。XDP 看起来跟 DPDK 比较像，但它比 DPDK 有更多的优点，如

* 无需第三方代码库和许可
* 同时支持轮询式和中断式网络
* 无需分配大页
* 无需专用的CPU
* 无需定义新的安全网络模型

当然，XDP的性能提升是有代价的，它牺牲了通用型和公平性：（1）不提供缓存队列（qdisc），TX设备太慢时直接丢包，因而不要在RX比TX快的设备上使用XDP；（2）XDP程序是专用的，不具备网络协议栈的通用性。

## 历史部署材料

> 本节原有部署步骤使用 Cilium 1.0、Kubernetes 1.10、`HEAD` 清单、etcd 和 cluster-admin ServiceAccount 绑定。它们不适用于当前集群，不能安全地通过只替换 URL 或 API 版本升级。请使用本页上方固定为 Cilium v1.20.2 的 Helm 命令，并检查上游兼容矩阵。

旧教程中的 Minikube 和 Istio 步骤不再保留为可复制命令。策略示例仍在下方，使用 `cilium.io/v2` 自定义资源。


## 安全策略

TCP 策略：

```yaml
apiVersion: "cilium.io/v2"
kind: CiliumNetworkPolicy
description: "L3-L4 policy to restrict deathstar access to empire ships only"
metadata:
  name: "rule1"
spec:
  endpointSelector:
    matchLabels:
      org: empire
      class: deathstar
  ingress:
  - fromEndpoints:
    - matchLabels:
        org: empire
    toPorts:
    - ports:
      - port: "80"
        protocol: TCP
```

CIDR 策略

```yaml
apiVersion: "cilium.io/v2"
kind: CiliumNetworkPolicy
metadata:
  name: "cidr-rule"
spec:
  endpointSelector:
    matchLabels:
      app: myService
  egress:
  - toCIDR:
    - 20.1.1.1/32
  - toCIDRSet:
    - cidr: 10.0.0.0/8
      except:
      - 10.96.0.0/12
```

L7 HTTP 策略：

```bash
apiVersion: "cilium.io/v2"
kind: CiliumNetworkPolicy
description: "L7 policy to restrict access to specific HTTP call"
metadata:
  name: "rule1"
spec:
  endpointSelector:
    matchLabels:
      org: empire
      class: deathstar
  ingress:
  - fromEndpoints:
    - matchLabels:
        org: empire
    toPorts:
    - ports:
      - port: "80"
        protocol: TCP
      rules:
        http:
        - method: "POST"
          path: "/v1/request-landing"
```

## 历史监控工具

旧的 `microscope` 项目和其可变 `master` manifest 没有经过 Cilium v1.20 或 Kubernetes v1.37.1 验证；安装命令不再提供。诊断当前 Cilium 流量时，可使用与部署版本匹配的 `cilium monitor` CLI。

## 参考资料

* [Cilium documentation](http://cilium.readthedocs.io/)

