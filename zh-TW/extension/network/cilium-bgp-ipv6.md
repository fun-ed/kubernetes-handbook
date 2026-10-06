# 使用 Cilium BGP 釋出 IPv6 路由

本章使用 Cilium **v1.20.2** 與 BGP Control Plane v2 API。BGP 會將選定的叢集路由釋出給鄰接路由器。它不會取代 Cilium CNI 或 eBPF 資料平面、不會設定路由器，也不會提供 IPv6 鄰居探索（NDP）。以下 `2001:db8::/32` 是檔案保留網段，不可在真實網路路由。

Cilium BGP 控制平面會從選定節點建立 BGP 工作階段，併釋出設定的 PodCIDR 或 Service 位址。路由器仍須設定相符的 IPv6 介面、對等端位址、ASN、路由政策及回程路由。BGP 不負責配置位址，也不會發布 NDP 鄰居專案。L2 announcement 與 BGP 是不同機制，不可互相替代。IPv6 路由網路須規劃實際字首、NDP、路由器廣告及符合 IPAM 模式的 PodCIDR。

## 版本與先決條件

Cilium v1.20.2 使用 BGP v2 資源 `CiliumBGPClusterConfig`、`CiliumBGPPeerConfig` 與 `CiliumBGPAdvertisement`。新設定不可使用舊的 `CiliumBGPPeeringPolicy`。CRD 與 Cilium 必須來自同一版本。Cilium v1.20 檔案的支援矩陣涵蓋 Kubernetes v1.33 至 v1.36，不包含本手冊基準 v1.37.1；因此此組合不是上游已支援的組合，僅能在隔離環境評估，不能宣稱正式相容。請參閱 [Cilium 官方支援矩陣](https://docs.cilium.io/en/v1.20/operations/support/)。

啟用前決定本地與遠端 ASN、節點選擇器、本地 IPv6 來源位址、對等端 IPv6 位址、位址系列及要釋出的字首。Cilium 預設依流量出口介面自動選出 BGP 來源位址；`CiliumBGPPeerConfig.spec.transport.sourceInterface` 可指定介面，該介面每個位址系列只能有一個符合條件的位址。不可在多節點共用同一個 IPv6 位址。TCP 179 必須符合網路防火牆規則。範例使用檔案用途 ASN 與位址，不包含驗證密碼。

BGP 控制平面需在安裝 Cilium 時設定 Helm 值 `bgpControlPlane.enabled=true`。套用 CRD 不會自行啟用控制器。遵循 v1.20.2 的安裝檔案，保留現有 CNI/IPAM 設定；不可將下列資源直接套用至未確認版本的叢集。

## 最小 IPv6 對等端與廣告設定

以下資源示範單節點實驗室的欄位關係。節點標籤刻意只選中一個節點，因 `2001:db8:100::10` 是單節點示例來源，不得複製到多節點。若選取多個節點，需為每個節點配置唯一且可路由的來源位址，並使用實際路由器端位址。檔案網段不可在正式網路使用。

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

此示例假設唯一選中的節點有來源位址 `2001:db8:100::10`，且可連線到路由器 `2001:db8:100::1`。位址依出口介面路由自動選取，範例沒有設定不存在的 `localAddress` 欄位。套用前使用同版本 CRD 核對 [BGPPeerConfig API](https://docs.cilium.io/en/v1.20/network/bgp-control-plane/bgp-control-plane-configuration/#bgp-peer-config)、[ClusterConfig API](https://docs.cilium.io/en/v1.20/network/bgp-control-plane/bgp-control-plane-configuration/#bgp-cluster-config) 與 [Advertisement API](https://docs.cilium.io/en/v1.20/network/bgp-control-plane/bgp-control-plane-configuration/#bgp-advertisements)。PeerConfig family 的 `advertisements.matchLabels` 選取廣告資源的 metadata 標籤；Service 廣告自己的 selector 再選取 Service。

PodCIDR 廣告僅適用於支援的 Kubernetes PodCIDR IPAM 型別，例如 Kubernetes IPAM 或 cluster-pool；不得假設其他 IPAM 模式也能使用。路由器須有到 Pod 字首的回程路由。Service 廣告是另一項功能，只選擇版本支援且符合網路設計的 Service 位址型別。`externalTrafficPolicy: Local` 時，只有具有本機端點的節點適合接收外部流量；請依 v1.20 檔案確認廣告條件與節點行為，並與路由器 ECMP 政策一併測試。不要將 ClusterIP 釋出到無法路由這些位址的網路。

## 安裝與檢查

在採用 Cilium v1.20.2 chart 的隔離叢集中，依官方安裝程式設定 BGP 控制平面，並保留現有 IPAM 與路由設定。不可將一般 Helm upgrade 命令視為正式環境安裝指引。

以下為管理者完成安裝與套用設定後的唯讀檢查：

```bash
cilium bgp peers
cilium bgp routes advertised ipv6 unicast
kubectl get ciliumbgpclusterconfigs,ciliumbgppeerconfigs,ciliumbgpadvertisements
kubectl describe ciliumbgpclusterconfig lab-ipv6
```

Cilium CLI 顯示 BGP 對等端與廣告路由狀態；成功輸出不代表上游路由器已接受或安裝路由。請以路由器唯讀命令檢查 Adj-RIB-In 與轉送表。若工作階段不存在，檢查 CRD/控制器、節點選擇器、來源或對等端連線、TCP 179 與 ASN/位址系列。工作階段存在但沒有路由時，檢查廣告標籤、IPAM 是否支援 PodCIDR 廣告、Service 選擇器及路由器匯入政策。

## 維運與回覆

修改廣告前記錄 Cilium 設定、路由、節點標籤與路由器政策。在隔離網路測試撤回與容錯。路由器應限制可接受的字首與 community。移除廣告可能撤回路由並中斷工作負載，須與路由器管理者協調，觀察路由傳播結果。停用 BGP 不會自動還原路由器政策。

主要來源：[Cilium v1.20 BGP Control Plane](https://docs.cilium.io/en/v1.20/network/bgp-control-plane/)、[BGP v2 設定](https://docs.cilium.io/en/v1.20/network/bgp-control-plane/bgp-control-plane-configuration/)、[Cilium v1.20 Kubernetes 支援矩陣](https://docs.cilium.io/en/v1.20/operations/support/)、[Cilium v1.20.2 發行版本](https://github.com/cilium/cilium/releases/tag/v1.20.2)、[Cilium Helm 參考](https://docs.cilium.io/en/v1.20/helm-reference/)。
