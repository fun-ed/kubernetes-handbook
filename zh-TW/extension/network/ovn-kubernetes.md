# OVN

> **版本與相容性（2026-10-05）。** OVN-Kubernetes 最新穩定釋出為 [v1.4.0](https://github.com/ovn-kubernetes/ovn-kubernetes/releases/tag/v1.4.0)（2026-09-04）；其釋出說明提到 Kubernetes v1.36.2，但沒有驗證 v1.37.1 的相容性宣告。以下 `ovnkube` 直接程序和發行版包命令是舊式整合範例，不適用於當前叢集；請按固定版本的上游釋出說明選擇部署方式。


[ovn-kubernetes](https://github.com/openvswitch/ovn-kubernetes) 提供了一個ovs OVN 網路外掛，支援 underlay 和 overlay 兩種模式。

* underlay：容器執行在虛擬機器中，而ovs則執行在虛擬機器所在的物理機上，OVN將容器網路和虛擬機器網路連線在一起
* overlay：OVN透過logical overlay network連線所有節點的容器，此時ovs可以直接執行在物理機或虛擬機器上

## 歷史 overlay 程序範例（非 v1.37 部署指南）

![](../../.gitbook/assets/ovn_kubernetes.png)

### 歷史 master 啟動引數範例（不可直接執行）

```bash
# start ovn
/usr/share/openvswitch/scripts/ovn-ctl start_northd
/usr/share/openvswitch/scripts/ovn-ctl start_controller

# start ovnkube
nohup sudo ovnkube -k8s-kubeconfig kubeconfig.yaml -net-controller \
 -loglevel=4 \
 -k8s-apiserver="http://$CENTRAL_IP:8080" \
 -logfile="/var/log/openvswitch/ovnkube.log" \
 -init-master=$NODE_NAME -cluster-subnet="$CLUSTER_IP_SUBNET" \
 -service-cluster-ip-range=$SERVICE_IP_SUBNET \
 -nodeport \
 -nb-address="tcp://$CENTRAL_IP:6631" \
 -sb-address="tcp://$CENTRAL_IP:6632" 2>&1 &
```

### 歷史 Node 啟動引數範例（不可直接執行）

```bash
nohup sudo ovnkube -k8s-kubeconfig kubeconfig.yaml -loglevel=4 \
    -logfile="/var/log/openvswitch/ovnkube.log" \
    -k8s-apiserver="http://$CENTRAL_IP:8080" \
    -init-node="$NODE_NAME"  \
    -nodeport \
    -nb-address="tcp://$CENTRAL_IP:6631" \
    -sb-address="tcp://$CENTRAL_IP:6632" -k8s-token="$TOKEN" \
    -init-gateways \
    -service-cluster-ip-range=$SERVICE_IP_SUBNET \
    -cluster-subnet=$CLUSTER_IP_SUBNET 2>&1 &
```

### CNI外掛原理

#### ADD操作

* 從`ovn` annotation獲取ip/mac/gateway
* 在容器netns中設定介面和路由
* 新增ovs連接埠

```bash
ovs-vsctl add-port br-int veth_outside \
  --set interface veth_outside \
    external_ids:attached_mac=mac_address \
    external_ids:iface-id=namespace_pod \
    external_ids:ip_address=ip_address
```

#### DEL操作

```bash
ovs-vsctl del-port br-int port
```

## 歷史安裝步驟（已移除）

舊步驟依賴發行版儲存庫中的未固定版本 Open vSwitch/OVN 套件、舊 apt keyrings 和全域性 pip 安裝；它不構成受支援的 OVN-Kubernetes v1.4.0 安裝流程，不能用於 Kubernetes v1.37.1。

## 參考文件

* [https://github.com/openvswitch/ovn-kubernetes](https://github.com/openvswitch/ovn-kubernetes)
