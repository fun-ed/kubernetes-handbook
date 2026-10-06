# Romana

> **歷史專案，安裝範例已移除。** 原教程使用 `romana/romana` 儲存庫 `master` 中的可變 Kubernetes manifests。本書未核實專案當前穩定版本、維護狀態或 Kubernetes v1.37.1 相容矩陣；不要把舊清單應用到當前叢集。


Romana是Panic Networks在2016年提出的開源專案，旨在解決Overlay方案給網路帶來的開銷。

## 歷史 Kubernetes 部署說明

舊教程曾分別描述 kubeadm 和 kops 清單，以及透過 CNI、AWS 路由元件進行設定。原始 manifests 指向可變 `master` 分支，已不作為可複製命令保留。

## 工作原理

![](../../.gitbook/assets/romana%20%282%29.png)

![](../../.gitbook/assets/routeagg%20%282%29.png)

* layer 3 networking，消除overlay帶來的開銷
* 基於iptables ACL的網路隔離
* 基於hierarchy CIDR管理Host/Tenant/Segment ID

![](../../.gitbook/assets/cidr%20%282%29.png)

## 優點

* 純三層網路，效能好

## 缺點

* 基於IP管理租戶，有規模上的限制
* 物理裝置變更或位址規劃變更麻煩

**參考文件**

* [http://romana.io/](http://romana.io/)
* [Romana basics](http://romana.io/how/romana_basics/)
* [Romana Github](https://github.com/romana/romana)
* [Romana 2.0](http://romana.readthedocs.io/en/latest/index.html)
