# 集群 DNS

CoreDNS 是当前 Kubernetes 部署中的标准 DNS 扩展，kubeadm 集群也默认部署它。云服务和集群发行版可能会自行管理 DNS。Kubernetes v1.37 不要求使用已退役的 kube-dns。

不要照旧示例替换或删除集群的 DNS Deployment。检查和配置 DNS 时，请遵循集群服务商的流程。自定义搜索域、存根域和上游解析器时，请参考[自定义 DNS 服务](https://kubernetes.io/docs/tasks/administer-cluster/dns-custom-nameservers/)。

## 支持的 DNS 格式

* Service
  * A record：生成 `my-svc.my-namespace.svc.cluster.local`，解析 IP 分为两种情况
    * 普通 Service 解析为 Cluster IP
    * Headless Service 解析为指定的 Pod IP 列表
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
  - image: busybox
    command:
      - sleep
      - "3600"
    name: busybox
```

![](../../.gitbook/assets/dns-demo%20%283%29.png)

## 旧版 kube-dns 配置

以下 ConfigMap 格式和解析流程来自旧版 Kubernetes 的 kube-dns 扩展，不适用于 CoreDNS。新部署应使用 CoreDNS 的 `Corefile` 和当前 Kubernetes DNS 文档。

## kube-dns（历史内容）

本节介绍旧版由三个容器组成的 kube-dns 实现。这里的清单、镜像、端口和运维命令均与旧版本绑定，不要在 Kubernetes v1.37 集群中使用。当前 DNS 扩展为 CoreDNS。DNS 排错和配置请参考 [Kubernetes DNS 文档](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)。

### Ubuntu 18.04 的历史解析器问题

该案例适用于 Ubuntu 18.04 和旧版集群 DNS 设置，不代表通用修复方法。不要根据此例删除或替换 `/etc/resolv.conf`。请先检查节点当前使用的解析器配置，再按操作系统和集群服务商文档处理。

## 参考文档

* [dns-pod-service 介绍](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
* [coredns/coredns](https://github.com/coredns/coredns)

