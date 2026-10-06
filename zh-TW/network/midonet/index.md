# Midonet

> **歷史專案資料。** 本頁明確記錄的 Midonet `bees` 和 `k8s-midonet` 整合已不再更新；它們不是 Kubernetes v1.37.1 的受支援部署方案。不要將此頁架構說明當作當前 CNI 安裝教程。


[Midonet](https://www.midonet.org/)是Midokura公司開源的OpenStack網路虛擬化方案。

- 從元件來看，Midonet以Zookeeper+Cassandra建置分散式資料庫儲存VPC資源的狀態——Network State DB Cluster，並將controller分佈在轉發裝置（包括vswitch和L3 Gateway）本地——Midolman（L3 Gateway上還有quagga bgpd），裝置的轉發則保留了ovs kernel作為fast datapath。可以看到，Midonet和DragonFlow、OVN一樣，在架構的設計上都是沿著OVS-Neutron-Agent的思路，將controller分佈到裝置本地，並在neutron plugin和裝置agent間嵌入自己的資源資料庫作為super controller。
- 從介面來看，NSDB與Neutron間是REST API，Midolman與NSDB間是RPC，這倆沒什麼好說的。Controller的南向方面，Midolman並沒有用OpenFlow和OVSDB，它幹掉了user space中的vswitchd和ovsdb-server，直接透過linux netlink機制操作kernel space中的ovs datapath。

> 原始文件引用了 `1.png` 和 `2.png`，但來源檔未附這兩張圖。

## Docker/Kubernetes整合

Midonet作為[Kuryr](https://github.com/openstack/kuryr)的一個driver，透過[kuryr-libnetwork](https://github.com/openstack/kuryr-libnetwork)和[kuryr-kubernetes](https://github.com/openstack/kuryr-kubernetes)應用到容器中。

其他方法：

- Midonet 透過 [bees](https://github.com/midonet/bees) 整合，該專案已不再更新。
- Midonet 透過 [k8s-midonet](https://github.com/midonet/k8s-midonet) 與 Kubernetes 整合；該專案已不再更新。

**參考文件**

- [Midonet](https://www.midonet.org/)
- [SDNLab](http://www.sdnlab.com/16974.html)
- [MNS Overlay Network Models：Provider Router](https://blog.midonet.org/introduction-mns-overlay-network-models-part-1-provider-router/)
- [MNS Overlay Network Models：Tenant Routers and Bridges](https://blog.midonet.org/introduction-mns-overlay-network-models-part-2-tenant-routers-bridges/)
- [Midonet 參考架構](https://docs.midonet.org/docs/latest/reference-architecture/content/index.html)