# 历史 obsolete Flannel Docker/CNI integration（封存）

> 不适用于 Kubernetes v1.37.1 的历史示例；勿当作当前安装或诊断命令。

## Docker集成

```bash
source /run/flannel/subnet.env
docker daemon --bip=${FLANNEL_SUBNET} --mtu=${FLANNEL_MTU} &
```

## CNI集成

CNI flannel插件会将flannel网络配置转换为bridge插件配置，并调用bridge插件给容器netns配置网络。比如下面的flannel配置

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

会被cni flannel插件转换为

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

## 历史 Kubernetes 集成输出

> 旧教程使用 `coreos/flannel` 的 `master` 清单，且没有固定 Flannel 镜像版本。清单部署命令已移除；该旧输出只作原理参考。当前安装请使用本页上方固定版本的 Flannel v0.28.9 清单。
以下仅保留旧安装产生的进程与 CNI 配置样例，用于阅读历史日志：

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

flanneld自动连接kubernetes API，根据`node.Spec.PodCIDR`配置本地的flannel网络子网，并为容器创建vxlan和相关的子网路由。

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
