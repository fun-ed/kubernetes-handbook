# Flannel

[Flannel](https://github.com/coreos/flannel) 透過為每台主機分配一個子網路，為容器提供虛擬網路。它以 Linux TUN/TAP 為基礎，使用 UDP 封裝 IP 封包來建立覆疊網路，並透過 etcd 維護網路分配資訊。

## 目前的安裝方式（2026-10-05）

Flannel v0.28.9 是本書查到的最新穩定版。官方發布說明未提供 Kubernetes v1.37 相容性矩陣，因此不要將此版本標示為已驗證支援 v1.37.1。安裝前請檢查發行版、節點核心、CIDR 和 Flannel 發布說明。此清單會部署一個主要 CNI，請勿與其他不相容的 CNI 一起安裝。

如果叢集使用範例中的 `10.244.0.0/16` Pod CIDR，建立叢集時也必須使用相同範圍；如果是現有叢集，請先確認實際的 Pod CIDR。清單使用 `apps/v1`、`rbac.authorization.k8s.io/v1`，並固定 Flannel 和 CNI 二進位映像檔的版本：

```bash
kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/v0.28.9/Documentation/kube-flannel.yml
```

來源：[Flannel v0.28.9 發布](https://github.com/flannel-io/flannel/releases/tag/v0.28.9)、[版本化清單](https://raw.githubusercontent.com/flannel-io/flannel/v0.28.9/Documentation/kube-flannel.yml)。該版本對 Kubernetes v1.37 的支援狀態尚未在上游矩陣中確認。

## 歷史原理與設定範例

> 以下 etcd、Docker 整合、CNI bridge 轉換及舊版 Kubernetes 部署輸出，都是用來說明歷史實作的內容，不是上方的目前安裝方法。舊版 `coreos/flannel` `master` 清單已無法使用。

## Flannel 原理

控制平面上主機本機的 flanneld，負責從遠端 ETCD 叢集同步本機與其他主機上的子網路資訊，並為 Pod 分配 IP 位址。資料平面的 flannel 透過 Backend（例如 UDP 封裝）實作 L3 Overlay；既可以選擇一般的 TUN 裝置，也可以選擇 VxLAN 裝置。

```javascript
{
    "Network": "10.0.0.0/8",
    "SubnetLen": 20,
    "SubnetMin": "10.10.0.0",
    "SubnetMax": "10.99.0.0",
    "Backend": {
        "Type": "udp",
        "Port": 7890
    }
}
```

![](../../.gitbook/assets/flannel%20%282%29.png)

除了 UDP，Flannel 也支援許多其他 Backend：

* udp：使用使用者空間的 UDP 封裝，預設使用 8285 連接埠。由於封裝和解封裝都在使用者空間進行，效能會大幅降低。
* vxlan：使用 VxLAN 封裝，需設定 VNI、連接埠（預設為 8472）和 [GBP](https://github.com/torvalds/linux/commit/3511494ce2f3d3b77544c79b87511a4ddb61dc89)。
* host-gw：採用直接路由的方式，將容器網路的路由資訊直接更新至主機的路由表中；僅適用於第二層可直接連通的網路。
* aws-vpc：使用 Amazon VPC 路由表建立路由，適用於在 AWS 上執行的容器。
* gce：使用 Google Compute Engine Network 建立路由。所有執行個體都必須啟用 IP forwarding，適用於在 GCE 上執行的容器。
* ali-vpc：使用阿里雲 VPC 路由表建立路由，適用於在阿里雲上執行的容器。

> 舊 Docker daemon、CNI 整合及未固定版本的 Kubernetes 輸出已封存；目前 Flannel 安裝狀態與限制見上方。見[封存原始材料](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/zh-TW/extension/network/flannel.md)。

## 優點

* 設定與安裝簡單，使用方便。
* 與雲端平台整合良好，採用 VPC 的方式不會造成額外的效能損失。

## 缺點

* VXLAN 模式對零停機重新啟動的支援不佳。

> 使用 udp 以外的 Backend 時，資料路徑由核心提供，flanneld 則負責控制平面。因此，即使重新啟動 flanneld（包括為了升級而重新啟動），也不會影響現有連線。不過，若使用 vxlan Backend，就必須在幾秒內完成重新啟動，因為 ARP 項目可能會開始逾時，屆時需要由 flannel 精靈程式重新整理。此外，若要避免重新啟動期間發生中斷，就不得變更設定（例如 VNI、--iface 值）。

**參考文件**

* [https://github.com/coreos/flannel](https://github.com/coreos/flannel)
* [https://coreos.com/flannel/docs/latest/](https://coreos.com/flannel/docs/latest/)