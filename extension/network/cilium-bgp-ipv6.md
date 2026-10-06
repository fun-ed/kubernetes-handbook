# 使用 Cilium BGP 发布 IPv6 路由

本章使用 Cilium **v1.20.2** 与 BGP Control Plane v2 API。BGP 会将选定的丛集路由发布给邻接路由器。它不会取代 Cilium CNI 或 eBPF 资料平面、不会设定路由器，也不会提供 IPv6 邻居探索（NDP）。以下 `2001:db8::/32` 是文件保留网段，不可在真实网路路由。

Cilium BGP 控制平面会从选定节点建立 BGP 工作阶段，并发布设定的 PodCIDR 或 Service 位址。路由器仍须设定相符的 IPv6 介面、对等端位址、ASN、路由政策及回程路由。BGP 不负责配置位址，也不会发布 NDP 邻居项目。L2 announcement 与 BGP 是不同机制，不可互相替代。IPv6 路由网路须规划实际前缀、NDP、路由器广告及符合 IPAM 模式的 PodCIDR。

## 版本与先决条件

Cilium v1.20.2 使用 BGP v2 资源 `CiliumBGPClusterConfig`、`CiliumBGPPeerConfig` 与 `CiliumBGPAdvertisement`。新设定不可使用旧的 `CiliumBGPPeeringPolicy`。CRD 与 Cilium 必须来自同一版本。Cilium v1.20 文件的支援矩阵涵盖 Kubernetes v1.33 至 v1.36，不包含本手册基准 v1.37.1；因此此组合不是上游已支援的组合，仅能在隔离环境评估，不能宣称正式相容。请参阅 [Cilium 官方支援矩阵](https://docs.cilium.io/en/v1.20/operations/support/)。

启用前决定本地与远端 ASN、节点选择器、本地 IPv6 来源位址、对等端 IPv6 位址、位址系列及要发布的前缀。Cilium 预设依流量出口介面自动选出 BGP 来源位址；`CiliumBGPPeerConfig.spec.transport.sourceInterface` 可指定介面，该介面每个位址系列只能有一个符合条件的位址。不可在多节点共用同一个 IPv6 位址。TCP 179 必须符合网路防火墙规则。范例使用文件用途 ASN 与位址，不包含验证密码。

BGP 控制平面需在安装 Cilium 时设定 Helm 值 `bgpControlPlane.enabled=true`。套用 CRD 不会自行启用控制器。遵循 v1.20.2 的安装文件，保留现有 CNI/IPAM 设定；不可将下列资源直接套用至未确认版本的丛集。

## 最小 IPv6 对等端与广告设定

以下资源示范单节点实验室的栏位关系。节点标签刻意只选中一个节点，因 `2001:db8:100::10` 是单节点示例来源，不得复制到多节点。若选取多个节点，需为每个节点配置唯一且可路由的来源位址，并使用实际路由器端位址。文件网段不可在正式网路使用。

```yaml
apiVersion: cilium.io/v2
kind: CiliumBGPPeerConfig
metadata:
  name: lab-ipv6
spec:
  timers:
    holdTimeSeconds: 90
    keepAliveTimeSeconds: 30
  families:
    - afi: ipv6
      safi: unicast
      advertisements:
        matchLabels:
          advertise: lab-ipv6
---
apiVersion: cilium.io/v2
kind: CiliumBGPClusterConfig
metadata:
  name: lab-ipv6
spec:
  nodeSelector:
    matchLabels:
      kubernetes.io/hostname: bgp-lab-node
  bgpInstances:
    - name: ipv6
      localASN: 64512
      peers:
        - name: router
          peerASN: 64513
          peerAddress: 2001:db8:100::1
          peerConfigRef:
            name: lab-ipv6
---
apiVersion: cilium.io/v2
kind: CiliumBGPAdvertisement
metadata:
  name: lab-ipv6
  labels:
    advertise: lab-ipv6
spec:
  advertisements:
    - advertisementType: PodCIDR
      attributes:
        communities:
          standard:
            - 64512:100
    - advertisementType: Service
      service:
        addresses:
          - ClusterIP
      selector:
        matchLabels:
          bgp-advertise: "true"
      attributes:
        communities:
          standard:
            - 64512:200
```

此示例假设唯一选中的节点有来源位址 `2001:db8:100::10`，且可连线到路由器 `2001:db8:100::1`。位址依出口介面路由自动选取，范例没有设定不存在的 `localAddress` 栏位。套用前使用同版本 CRD 核对 [BGPPeerConfig API](https://docs.cilium.io/en/v1.20/network/bgp-control-plane/bgp-control-plane-configuration/#bgp-peer-config)、[ClusterConfig API](https://docs.cilium.io/en/v1.20/network/bgp-control-plane/bgp-control-plane-configuration/#bgp-cluster-config) 与 [Advertisement API](https://docs.cilium.io/en/v1.20/network/bgp-control-plane/bgp-control-plane-configuration/#bgp-advertisements)。PeerConfig family 的 `advertisements.matchLabels` 选取广告资源的 metadata 标签；Service 广告自己的 selector 再选取 Service。

PodCIDR 广告仅适用于支援的 Kubernetes PodCIDR IPAM 类型，例如 Kubernetes IPAM 或 cluster-pool；不得假设其他 IPAM 模式也能使用。路由器须有到 Pod 前缀的回程路由。Service 广告是另一项功能，只选择版本支援且符合网路设计的 Service 位址类型。`externalTrafficPolicy: Local` 时，只有具有本机端点的节点适合接收外部流量；请依 v1.20 文件确认广告条件与节点行为，并与路由器 ECMP 政策一并测试。不要将 ClusterIP 发布到无法路由这些位址的网路。

## 安装与检查

在采用 Cilium v1.20.2 chart 的隔离丛集中，依官方安装程序设定 BGP 控制平面，并保留现有 IPAM 与路由设定。不可将一般 Helm upgrade 命令视为正式环境安装指引。

以下为管理者完成安装与套用设定后的唯读检查：

```bash
cilium bgp peers
cilium bgp routes advertised ipv6 unicast
kubectl get ciliumbgpclusterconfigs,ciliumbgppeerconfigs,ciliumbgpadvertisements
kubectl describe ciliumbgpclusterconfig lab-ipv6
```

Cilium CLI 显示 BGP 对等端与广告路由状态；成功输出不代表上游路由器已接受或安装路由。请以路由器唯读命令检查 Adj-RIB-In 与转送表。若工作阶段不存在，检查 CRD/控制器、节点选择器、来源或对等端连线、TCP 179 与 ASN/位址系列。工作阶段存在但没有路由时，检查广告标签、IPAM 是否支援 PodCIDR 广告、Service 选择器及路由器汇入政策。

## 维运与回复

修改广告前记录 Cilium 设定、路由、节点标签与路由器政策。在隔离网路测试撤回与容错。路由器应限制可接受的前缀与 community。移除广告可能撤回路由并中断工作负载，须与路由器管理者协调，观察路由传播结果。停用 BGP 不会自动还原路由器政策。

主要来源：[Cilium v1.20 BGP Control Plane](https://docs.cilium.io/en/v1.20/network/bgp-control-plane/)、[BGP v2 设定](https://docs.cilium.io/en/v1.20/network/bgp-control-plane/bgp-control-plane-configuration/)、[Cilium v1.20 Kubernetes 支援矩阵](https://docs.cilium.io/en/v1.20/operations/support/)、[Cilium v1.20.2 发行版本](https://github.com/cilium/cilium/releases/tag/v1.20.2)、[Cilium Helm 参考](https://docs.cilium.io/en/v1.20/helm-reference/)。
