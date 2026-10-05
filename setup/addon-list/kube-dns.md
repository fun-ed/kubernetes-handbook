# CoreDNS 与历史 kube-dns

Kubernetes v1.37.1 的 kubeadm 默认部署 CoreDNS **1.14.6**。新建集群时不要另行套用本页早期 kube-dns Deployment 或重复安装第二套 DNS。kubeadm 创建的 CoreDNS 在 CNI 安装前不会正常工作；先完成 Pod network，再检查：

```bash
kubectl -n kube-system get deploy,pods -l k8s-app=kube-dns
kubectl -n kube-system rollout status deployment/coredns
```

kubeadm 镜像列表、配置和 CoreDNS Corefile 可从官方 [kubeadm 文档](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)与 [CoreDNS 文档](https://coredns.io/manual/toc/)查阅。变更副本数、插件或转发目标前，备份并检查现有 Corefile；修改默认镜像版本时先核实 Kubernetes 与 CoreDNS 的兼容性。验证服务发现时可从实际 workload namespace 查询集群 Service 的 DNS 名称。

> **历史说明：** 旧版 Kubernetes 使用 kube-dns，并由独立的 Deployment/Service 及早期 addon-manager YAML 管理。该历史配置不适用于 v1.37.1；本手册不保留旧 YAML 和下载命令，避免误部署重复 DNS 服务。