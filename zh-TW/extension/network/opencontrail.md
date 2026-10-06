# OpenContrail

> **歷史架構資料。** Juniper/Contrail 上游 release 頁面目前沒有可確認的帶日期穩定版本，本書也未找到 Kubernetes v1.37 相容矩陣；專案生命週期狀態尚未證實，不能稱為已退役。不要據此部署當前叢集；舊版 Kubernetes 整合依賴已移除的 exec network plugin。


OpenContrail 是 Juniper 推出的開源網路虛擬化平台，其商業版本為 Contrail。

## 架構

OpenContrail 主要由控制器和 vRouter 組成：

* 控制器提供虛擬網路的設定、控制和分析功能
* vRouter 提供分散式路由，負責虛擬路由器、虛擬網路的建立以及資料轉發

![](../../.gitbook/assets/Figure01%20%282%29.png)

vRouter 支援三種模式

* Kernel vRouter：類似於 ovs 核心模組
* DPDK vRouter：類似於 ovs-dpdk
* Netronome Agilio Solution \(商業產品 \)：支援 DPDK, SR-IOV and Express Virtio \(XVIO\)

![](../../.gitbook/assets/image05%20%282%29.png)

**參考文件**

* [http://www.opencontrail.org/opencontrail-architecture-documentation/](http://www.opencontrail.org/opencontrail-architecture-documentation/)
* [http://www.opencontrail.org/network-virtualization-architecture-deep-dive/](http://www.opencontrail.org/network-virtualization-architecture-deep-dive/)
