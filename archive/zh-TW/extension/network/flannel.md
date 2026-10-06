# 歷史 obsolete Flannel Docker/CNI integration（封存）

> 不適用於 Kubernetes v1.37.1 的歷史範例；勿當作目前安裝或診斷指令。

## Docker 整合

```bash
source /run/flannel/subnet.env
docker daemon --bip=${FLANNEL_SUBNET} --mtu=${FLANNEL_MTU} &
```

## CNI 整合

CNI flannel 外掛程式會將 flannel 網路設定轉換為 bridge 外掛程式設定，並呼叫 bridge 外掛程式，為容器的 netns 設定網路。例如，以下 flannel 設定：

```javascript
{
    "name": "mynet",
    "type": "flannel",
    "delegate": {
        "bridge": "mynet0",
        "mtu": 1400
    }
}
```

會由 CNI flannel 外掛程式轉換為：

```javascript
{
    "name": "mynet",
    "type": "bridge",
    "mtu": 1472,
    "ipMasq": false,
    "isGateway": true,
    "ipam": {
        "type": "host-local",
        "subnet": "10.1.17.0/24"
    }
}
```

## 歷史 Kubernetes 整合輸出

> 舊版教學使用 `coreos/flannel` 的 `master` 清單，且未固定 Flannel 映像檔版本。部署清單的指令已移除；此處保留的舊版輸出僅供參考原理。若要進行目前的安裝，請使用本頁上方固定版本的 Flannel v0.28.9 清單。
以下僅保留舊版安裝產生的程序與 CNI 設定範例，供閱讀歷史記錄時參考：

```bash
$ ps -ef | grep flannel | grep -v grep
root      3625  3610  0 13:57 ?        00:00:00 /opt/bin/flanneld --ip-masq --kube-subnet-mgr
root      9640  9619  0 13:51 ?        00:00:00 /bin/sh -c set -e -x; cp -f /etc/kube-flannel/cni-conf.json /etc/cni/net.d/10-flannel.conf; while true; do sleep 3600; done

$ cat /etc/cni/net.d/10-flannel.conf
{
  "name": "cbr0",
  "type": "flannel",
  "delegate": {
    "isDefaultGateway": true
  }
}
```

![](../../../.gitbook/assets/flannel-components.png)

flanneld 會自動連線至 Kubernetes API，根據 `node.Spec.PodCIDR` 設定本機 flannel 網路子網路，並為容器建立 VxLAN 和相關的子網路路由。

```bash
$ cat /run/flannel/subnet.env
FLANNEL_NETWORK=10.244.0.0/16
FLANNEL_SUBNET=10.244.0.1/24
FLANNEL_MTU=1410
FLANNEL_IPMASQ=true

$ ip -d link show flannel.1
12: flannel.1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1410 qdisc noqueue state UNKNOWN mode DEFAULT group default
    link/ether 8e:5a:0d:07:0f:0d brd ff:ff:ff:ff:ff:ff promiscuity 0
    vxlan id 1 local 10.146.0.2 dev ens4 srcport 0 0 dstport 8472 nolearning ageing 300 udpcsum addrgenmode eui64
```

![](../../../.gitbook/assets/flannel-network%20%281%29.png)
