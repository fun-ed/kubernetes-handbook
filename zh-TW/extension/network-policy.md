# 網路策略

[Network Policy](../concepts/objects/network-policy.md) 提供了基於策略的網路控制，用於隔離應用並減少攻擊面。它使用標籤選擇器模擬傳統的分段網路，並透過策略控制它們之間的流量以及來自外部的流量。Network Policy 需要網路外掛來監測這些策略和 Pod 的變更，並為 Pod 設定流量控制。

## 如何開發 Network Policy 擴充套件

實現一個支援 Network Policy 的網路擴充套件需要至少包含兩個元件

* CNI 網路外掛：負責給 Pod 設定網路介面
* Policy controller：監聽 Network Policy 的變化，並將 Policy 應用到相應的網路介面

![](../.gitbook/assets/policy-controller%20%281%29.jpg)

## 支援 Network Policy 的網路外掛

* [Calico](https://www.projectcalico.org/)
* [Cilium](https://cilium.io/)
* [Romana](https://github.com/romana/romana)
* [Weave Net](https://www.weave.works/)

## Network Policy 使用方法

具體 Network Policy 的使用方法可以參考 [這裡](../concepts/objects/network-policy.md)。
