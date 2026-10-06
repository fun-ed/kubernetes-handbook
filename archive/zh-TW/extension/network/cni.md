# CNI 本機手動實驗（封存）

> 歷史教學材料：以下手動建立 network namespace、介面和路由，使用 CNI spec 0.3.x；不是 Kubernetes v1.37.1 的安裝配置，且可能改變主機網路狀態。

# CNI

> **歷史本地實驗，不是 Kubernetes 叢集安裝指南。** 本頁命令手工呼叫 CNI 外掛，設定樣例使用 CNI spec 0.3.x；它們不能替代一個完整的多節點 Pod 網路實現。Kubernetes v1.37.1 原始碼將 [CNI plugins v1.9.1](https://github.com/containernetworking/plugins/releases/tag/v1.9.1) 固定為依賴版本，但應使用所選執行時和 CNI 專案的版本化安裝說明，不要將本頁舊設定直接應用到生產叢集。


Container Network Interface \(CNI\) 最早是由CoreOS發起的容器網路規範，是Kubernetes網路外掛的基礎。其基本思想為：Container Runtime在建立容器時，先建立好network namespace，然後呼叫CNI外掛為這個netns設定網路，其後再啟動容器內的程序。現已加入CNCF，成為CNCF主推的網路模型。

CNI外掛包括兩部分：

* CNI Plugin負責給容器設定網路，它包括兩個基本的介面
  * 設定網路: AddNetwork\(net _NetworkConfig, rt_ RuntimeConf\) \(types.Result, error\)
  * 清理網路: DelNetwork\(net _NetworkConfig, rt_ RuntimeConf\) error
* IPAM Plugin負責給容器分配IP位址，主要實現包括host-local和dhcp。

Kubernetes Pod 中的其他容器都是Pod所屬pause容器的網路，建立過程為：

1. kubelet 先建立pause容器生成network namespace
2. 呼叫網路CNI driver
3. CNI driver 根據設定呼叫具體的cni 外掛
4. cni 外掛給pause 容器設定網路
5. pod 中其他的容器都使用 pause 容器的網路

![](../../../.gitbook/assets/Chart_Container-Network-Interface-Drivers%20%283%29.png)

所有CNI外掛均支援透過環境變數和標準輸入傳入引數：

```bash
$ echo '{"cniVersion": "0.3.1","name": "mynet","type": "macvlan","bridge": "cni0","isGateway": true,"ipMasq": true,"ipam": {"type": "host-local","subnet": "10.244.1.0/24","routes": [{ "dst": "0.0.0.0/0" }]}}' | sudo CNI_COMMAND=ADD CNI_NETNS=/var/run/netns/a CNI_PATH=./bin CNI_IFNAME=eth0 CNI_CONTAINERID=a CNI_VERSION=0.3.1 ./bin/bridge

$ echo '{"cniVersion": "0.3.1","type":"IGNORED", "name": "a","ipam": {"type": "host-local", "subnet":"10.1.2.3/24"}}' | sudo CNI_COMMAND=ADD CNI_NETNS=/var/run/netns/a CNI_PATH=./bin CNI_IFNAME=a CNI_CONTAINERID=a CNI_VERSION=0.3.1 ./bin/host-local
```

常見的CNI網路外掛有

![](../../../.gitbook/assets/cni-plugins%20%282%29.png)

**CNI Plugin Chains**

CNI 也支援 Plugin Chains，也就是指定外掛清單，讓 Runtime 依序執行各外掛。這對支援連接埠映射（portmapping）、虛擬機器等功能很有幫助。設定方式請參閱後面的[連接埠映射範例](cni.md#端口映射示例)。

## Bridge

Bridge是最簡單的CNI網路外掛，它首先在Host建立一個網橋，然後再透過veth pair連線該網橋到container netns。

![](../../../.gitbook/assets/cni-bridge%20%281%29.png)

注意：**Bridge模式下，多主機網路通訊需要額外設定主機路由，或使用overlay網路**。可以藉助[Flannel](flannel.md)或者Quagga動態路由等來自動設定。比如overlay情況下的網路結構為

![](../../../.gitbook/assets/cni-overlay%20%281%29.png)

設定範例

```javascript
{
    "cniVersion": "0.3.0",
    "name": "mynet",
    "type": "bridge",
    "bridge": "mynet0",
    "isDefaultGateway": true,
    "forceAddress": false,
    "ipMasq": true,
    "hairpinMode": true,
    "ipam": {
        "type": "host-local",
        "subnet": "10.10.0.0/16"
    }
}
```

```text
# export CNI_PATH=/opt/cni/bin
# ip netns add ns
# /opt/cni/bin/cnitool add mynet /var/run/netns/ns
{
    "interfaces": [
        {
            "name": "mynet0",
            "mac": "0a:58:0a:0a:00:01"
        },
        {
            "name": "vethc763e31a",
            "mac": "66:ad:63:b4:c6:de"
        },
        {
            "name": "eth0",
            "mac": "0a:58:0a:0a:00:04",
            "sandbox": "/var/run/netns/ns"
        }
    ],
    "ips": [
        {
            "version": "4",
            "interface": 2,
            "address": "10.10.0.4/16",
            "gateway": "10.10.0.1"
        }
    ],
    "routes": [
        {
            "dst": "0.0.0.0/0",
            "gw": "10.10.0.1"
        }
    ],
    "dns": {}
}
# ip netns exec ns ip addr
1: lo: <LOOPBACK> mtu 65536 qdisc noop state DOWN group default qlen 1
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
9: eth0@if8: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default
    link/ether 0a:58:0a:0a:00:04 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 10.10.0.4/16 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::8c78:6dff:fe19:f6bf/64 scope link tentative dadfailed
       valid_lft forever preferred_lft forever
# ip netns exec ns ip route
default via 10.10.0.1 dev eth0
10.10.0.0/16 dev eth0  proto kernel  scope link  src 10.10.0.4
```

## IPAM

### DHCP

DHCP外掛是最主要的IPAM外掛之一，用來透過DHCP方式給容器分配IP位址，在macvlan外掛中也會用到DHCP外掛。

在使用DHCP外掛之前，需要先啟動dhcp daemon:

```bash
/opt/cni/bin/dhcp daemon &
```

然後設定網路使用dhcp作為IPAM外掛

```javascript
{
    ...
    "ipam": {
        "type": "dhcp",
    }
}
```

### host-local

host-local是最常用的CNI IPAM外掛，用來給container分配IP位址。

IPv4:

```javascript
{
    "ipam": {
        "type": "host-local",
        "subnet": "10.10.0.0/16",
        "rangeStart": "10.10.1.20",
        "rangeEnd": "10.10.3.50",
        "gateway": "10.10.0.254",
        "routes": [
            { "dst": "0.0.0.0/0" },
            { "dst": "192.168.0.0/16", "gw": "10.10.5.1" }
        ],
        "dataDir": "/var/my-orchestrator/container-ipam-state"
    }
}
```

IPv6:

```javascript
{
  "ipam": {
        "type": "host-local",
        "subnet": "3ffe:ffff:0:01ff::/64",
        "rangeStart": "3ffe:ffff:0:01ff::0010",
        "rangeEnd": "3ffe:ffff:0:01ff::0020",
        "routes": [
            { "dst": "3ffe:ffff:0:01ff::1/64" }
        ],
        "resolvConf": "/etc/resolv.conf"
    }
}
```

## ptp

ptp外掛透過veth pair給容器和host建立點對點連線：veth pair一端在container netns內，另一端在host上。可以透過設定host端的IP和路由來讓ptp連線的容器之前通訊。

```javascript
{
    "name": "mynet",
    "type": "ptp",
    "ipam": {
        "type": "host-local",
        "subnet": "10.1.1.0/24"
    },
    "dns": {
        "nameservers": [ "10.1.1.1", "8.8.8.8" ]
    }
}
```

## IPVLAN

IPVLAN 和 MACVLAN 類似，都是從一個主機介面虛擬出多個虛擬網路介面。一個重要的區別就是所有的虛擬介面都有相同的 mac 位址，而擁有不同的 ip 位址。因為所有的虛擬介面要共享 mac 位址，所以有些需要注意的地方：

* DHCP 協議分配 ip 的時候一般會用 mac 位址作為機器的標識。這個情況下，客戶端動態獲取 ip 的時候需要設定唯一的 ClientID 欄位，並且 DHCP server 也要正確設定使用該欄位作為機器標識，而不是使用 mac 位址

IPVLAN支援兩種模式：

* L2 模式：此時跟macvlan bridge 模式工作原理很相似，父介面作為交換機來轉發子介面的資料。同一個網路的子介面可以透過父介面來轉發資料，而如果想傳送到其他網路，報文則會透過父介面的路由轉發出去。
* L3 模式：此時ipvlan 有點像路由器的功能，它在各個虛擬網路和主機網路之間進行不同網路報文的路由轉發工作。只要父介面相同，即使虛擬機器/容器不在同一個網路，也可以互相 ping 通對方，因為 ipvlan 會在中間做報文的轉發工作。注意 L3 模式下的虛擬介面 不會接收到多播或者廣播的報文（這個模式下，所有的網路都會傳送給父介面，所有的 ARP 過程或者其他多播報文都是在底層的父介面完成的）。另外外部網路預設情況下是不知道 ipvlan 虛擬出來的網路的，如果不在外部路由器上設定好對應的路由規則，ipvlan 的網路是不能被外部直接存取的。

建立ipvlan的簡單方法為

```text
ip link add link <master-dev> <slave-dev> type ipvlan mode { l2 | L3 }
```

cni設定格式為

```text
{
    "name": "mynet",
    "type": "ipvlan",
    "master": "eth0",
    "ipam": {
        "type": "host-local",
        "subnet": "10.1.2.0/24"
    }
}
```

需要注意的是

* ipvlan外掛下，容器不能跟Host網路通訊
* 主機介面（也就是master interface）不能同時作為ipvlan和macvlan的master介面

## MACVLAN

MACVLAN可以從一個主機介面虛擬出多個macvtap，且每個macvtap裝置都擁有不同的mac位址（對應不同的linux字元裝置）。MACVLAN支援四種模式

* bridge模式：資料可以在同一master裝置的子裝置之間轉發
* vepa模式：VEPA 模式是對 802.1Qbg 標準中的 VEPA 機制的軟體實現，MACVTAP 裝置簡單的將資料轉發到master裝置中，完成資料匯聚功能，通常需要外部交換機支援 Hairpin 模式才能正常工作
* private模式：Private 模式和 VEPA 模式類似，區別是子 MACVTAP 之間相互隔離
* passthrough模式：核心的 MACVLAN 資料處理邏輯被跳過，硬體決定資料如何處理，從而釋放了 Host CPU 資源

建立macvlan的簡單方法為

```bash
ip link add link <master-dev> name macvtap0 type macvtap
```

cni設定格式為

```text
{
    "name": "mynet",
    "type": "macvlan",
    "master": "eth0",
    "ipam": {
        "type": "dhcp"
    }
}
```

需要注意的是

* macvlan需要大量 mac 位址，每個虛擬介面都有自己的 mac 位址
* 無法和 802.11\(wireless\) 網路一起工作
* 主機介面（也就是master interface）不能同時作為ipvlan和macvlan的master介面

## [Flannel](flannel.md)

[Flannel](https://github.com/coreos/flannel)透過給每臺宿主機分配一個子網的方式為容器提供虛擬網路，它基於Linux TUN/TAP，使用UDP封裝IP包來建立overlay網路，並藉助etcd維護網路的分配情況。

## [Weave Net（歷史教程，已封存）](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/extension/network/weave.md)

Weave Net是一個多主機容器網路方案，支援去中心化的控制平面，各個host上的wRouter間透過建立Full Mesh的TCP連結，並透過Gossip來同步控制資訊。這種方式省去了集中式的K/V Store，能夠在一定程度上減低部署的複雜性，Weave將其稱為“data centric”，而非RAFT或者Paxos的“algorithm centric”。

資料平面上，Weave透過UDP封裝實現L2 Overlay，封裝支援兩種模式，一種是執行在user space的sleeve mode，另一種是執行在kernal space的 fastpath mode。Sleeve mode透過pcap裝置在Linux bridge上截獲資料包並由wRouter完成UDP封裝，支援對L2 traffic進行加密，還支援Partial Connection，但是效能損失明顯。Fastpath mode即透過OVS的odp封裝VxLAN並完成轉發，wRouter不直接參與轉發，而是透過下發odp 流表的方式控制轉發，這種方式可以明顯地提升吞吐量，但是不支援加密等高階功能。

## [Contiv（歷史教程，已封存）](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/extension/network/contiv.md)

[Contiv](http://contiv.github.io)是思科開源的容器網路方案，主要提供基於Policy的網路管理，並與主流容器編排系統整合。Contiv最主要的優勢是直接提供了多租戶網路，並支援L2\(VLAN\), L3\(BGP\), Overlay \(VXLAN\)以及思科自家的ACI。

## [Calico](calico.md)

[Calico](https://www.projectcalico.org/) 是一個基於BGP的純三層的資料中心網路方案（不需要Overlay），並且與OpenStack、Kubernetes、AWS、GCE等IaaS和容器平臺都有良好的整合。

Calico在每一個計算節點利用Linux Kernel實現了一個高效的vRouter來負責資料轉發，而每個vRouter透過BGP協議負責把自己上執行的workload的路由資訊像整個Calico網路內傳播——小規模部署可以直接互聯，大規模下可透過指定的BGP route reflector來完成。 這樣保證最終所有的workload之間的資料流量都是透過IP路由的方式完成互聯的。Calico節點組網可以直接利用資料中心的網路結構（無論是L2或者L3），不需要額外的NAT，隧道或者Overlay Network。

此外，Calico基於iptables還提供了豐富而靈活的網路Policy，保證透過各個節點上的ACLs來提供Workload的多租戶隔離、安全組以及其他可達性限制等功能。

## [OVN](ovn-kubernetes.md)

[OVN (Open Virtual Network)](https://www.ovn.org/en/) 是OVS提供的原生虛擬化網路方案，旨在解決傳統SDN架構（比如Neutron DVR）的效能問題。

OVN為Kubernetes提供了兩種網路方案：

* Overaly: 透過ovs overlay連線容器
* Underlay: 將VM內的容器連到VM所在的相同網路（開發中）

其中，容器網路的設定是透過OVN的CNI外掛來實現。

## SR-IOV

Intel維護了一個SR-IOV的[CNI外掛](https://github.com/Intel-Corp/sriov-cni)，fork自[hustcat/sriov-cni](https://github.com/hustcat/sriov-cni)，並擴充套件了DPDK的支援。

專案主頁見[https://github.com/Intel-Corp/sriov-cni](https://github.com/Intel-Corp/sriov-cni)。

## [Romana](romana.md)

Romana是Panic Networks在2016年提出的開源專案，旨在借鑑 route aggregation的思路來解決Overlay方案給網路帶來的開銷。

## [OpenContrail](opencontrail.md)

OpenContrail是Juniper推出的開源網路虛擬化平臺，其商業版本為Contrail。其主要由控制器和vRouter組成：

* 控制器提供虛擬網路的設定、控制和分析功能
* vRouter提供分散式路由，負責虛擬路由器、虛擬網路的建立以及資料轉發

其中，vRouter支援三種模式

* Kernel vRouter：類似於ovs核心模組
* DPDK vRouter：類似於ovs-dpdk
* Netronome Agilio Solution \(商業產品\)：支援DPDK, SR-IOV and Express Virtio \(XVIO\)

[michaelhenkel/opencontrail-cni-plugin](https://github.com/michaelhenkel/opencontrail-cni-plugin)提供了一個OpenContrail的CNI外掛。

### Network Configuration Lists

[CNI spec v1.3.1](https://github.com/containernetworking/cni/blob/v1.3.1/SPEC.md#network-configuration-lists) 支援指定網路設定列表，包含多個網路外掛，由 Runtime 依次執行。注意

* ADD 操作，按順序依次呼叫每個外掛；而 DEL 操作呼叫順序相反
* ADD 操作，除最後一個外掛，前面每個外掛需要增加 `prevResult` 傳遞給其後的外掛
* 第一個外掛必須要包含 ipam 外掛

### 連接埠映射範例

下面的例子展示了 bridge+[portmap](https://github.com/containernetworking/plugins/tree/v1.9.1/plugins/meta/portmap) 外掛的用法。

首先，設定 CNI 網路使用 bridge+portmap 外掛：

```bash
# cat /root/mynet.conflist
{
  "name": "mynet",
  "cniVersion": "0.3.0",
  "plugins": [
    {
      "type": "bridge",
      "bridge": "mynet",
      "ipMasq": true,
      "isGateway": true,
      "ipam": {
      "type": "host-local",
      "subnet": "10.244.10.0/24",
      "routes": [
          {"dst": "0.0.0.0/0"}
      ]
      }
    },
    {
       "type": "portmap",
       "capabilities": {"portMappings": true}
    }
  ]
}
```

然後透過 `CAP_ARGS` 設定連接埠映射引數：

```bash
# export CAP_ARGS='{
    "portMappings": [
        {
            "hostPort":      9090,
            "containerPort": 80,
            "protocol":      "tcp",
            "hostIP":        "127.0.0.1"
        }
    ]
}'
```

測試新增網路介面：

```bash
# ip netns add test
# CNI_PATH=/opt/cni/bin NETCONFPATH=/root ./cnitool add mynet /var/run/netns/test
{
    "interfaces": [
        {
            "name": "mynet",
            "mac": "0a:58:0a:f4:0a:01"
        },
        {
            "name": "veth2cfb1d64",
            "mac": "4a:dc:1f:b7:56:b1"
        },
        {
            "name": "eth0",
            "mac": "0a:58:0a:f4:0a:07",
            "sandbox": "/var/run/netns/test"
        }
    ],
    "ips": [
        {
            "version": "4",
            "interface": 2,
            "address": "10.244.10.7/24",
            "gateway": "10.244.10.1"
        }
    ],
    "routes": [
        {
            "dst": "0.0.0.0/0"
        }
    ],
    "dns": {}
}
```

可以從 iptables 規則中看到新增的規則：

```bash
# iptables-save | grep 10.244.10.7
-A CNI-DN-be1eedf7a76853f303ebd -d 127.0.0.1/32 -p tcp -m tcp --dport 9090 -j DNAT --to-destination 10.244.10.7:80
-A CNI-SN-be1eedf7a76853f303ebd -s 127.0.0.1/32 -d 10.244.10.7/32 -p tcp -m tcp --dport 80 -j MASQUERADE
```

最後，清理網路介面：

```text
# CNI_PATH=/opt/cni/bin NETCONFPATH=/root ./cnitool del mynet /var/run/netns/test
```

## 其他

### [Canal](https://github.com/tigera/canal)

[Canal](https://github.com/tigera/canal)是Flannel和Calico聯合釋出的一個統一網路外掛，提供CNI網路外掛，並支援network policy。

### [kuryr-kubernetes](https://github.com/openstack/kuryr-kubernetes)

[kuryr-kubernetes](https://github.com/openstack/kuryr-kubernetes)是OpenStack推出的整合Neutron網路外掛，主要包括Controller和CNI外掛兩部分，並且也提供基於Neutron LBaaS的Service整合。

### [Cilium](https://github.com/cilium/cilium)

[Cilium](https://github.com/cilium/cilium)是一個基於eBPF和XDP的高效能容器網路方案，提供了CNI和CNM外掛。

專案主頁為[https://github.com/cilium/cilium](https://github.com/cilium/cilium)。

## [CNI-Genie](https://github.com/Huawei-PaaS/CNI-Genie)

[CNI-Genie](https://github.com/Huawei-PaaS/CNI-Genie)是華為PaaS團隊推出的同時支援多種網路外掛（支援calico, canal, romana, weave等）的CNI外掛。

專案主頁為[https://github.com/Huawei-PaaS/CNI-Genie](https://github.com/Huawei-PaaS/CNI-Genie)。
