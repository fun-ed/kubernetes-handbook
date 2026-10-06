# 叢集 DNS

CoreDNS 是當前 Kubernetes 部署中的標準 DNS 擴充套件，kubeadm 叢集也預設部署它。雲服務和叢集發行版可能會自行管理 DNS。Kubernetes v1.37 不要求使用已退役的 kube-dns。

不要照舊範例替換或刪除叢集的 DNS Deployment。檢查和設定 DNS 時，請遵循叢集服務商的流程。自定義搜尋域、存根域和上游解析器時，請參考[自定義 DNS 服務](https://kubernetes.io/docs/tasks/administer-cluster/dns-custom-nameservers/)。

## 支援的 DNS 格式

* Service
  * A record：生成 `my-svc.my-namespace.svc.cluster.local`，解析 IP 分為兩種情況
    * 普通 Service 解析為 Cluster IP
    * Headless Service 解析為指定的 Pod IP 列表
  * SRV record：生成 `_my-port-name._my-port-protocol.my-svc.my-namespace.svc.cluster.local`
* Pod
  * A record：`pod-ip-address.my-namespace.pod.cluster.local`
  * 指定 hostname 和 subdomain：`hostname.custom-subdomain.default.svc.cluster.local`，如下所示

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: busybox2
  labels:
    name: busybox
spec:
  hostname: busybox-2
  subdomain: default-subdomain
  containers:
  - image: busybox:1.37.0
    command:
      - sleep
      - "3600"
    name: busybox
```

![](../../.gitbook/assets/dns-demo%20%283%29.png)

## 舊版 kube-dns 設定

以下 ConfigMap 格式和解析流程來自舊版 Kubernetes 的 kube-dns 擴充套件，不適用於 CoreDNS。新部署應使用 CoreDNS 的 `Corefile` 和當前 Kubernetes DNS 文件。

## kube-dns（歷史內容）

本節介紹舊版由三個容器組成的 kube-dns 實現。這裡的清單、映像檔、連接埠和運維命令均與舊版本綁定，不要在 Kubernetes v1.37 叢集中使用。當前 DNS 擴充套件為 CoreDNS。DNS 排錯和設定請參考 [Kubernetes DNS 文件](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)。

### Ubuntu 18.04 的歷史解析器問題

該案例適用於 Ubuntu 18.04 和舊版叢集 DNS 設定，不代表通用修復方法。不要根據此例刪除或替換 `/etc/resolv.conf`。請先檢查節點當前使用的解析器設定，再按作業系統和叢集服務商文件處理。

## 參考文件

* [dns-pod-service 介紹](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
* [coredns/coredns](https://github.com/coredns/coredns)
