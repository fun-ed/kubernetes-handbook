# 集群部署

## 自建集群

需要自行管理 Linux control plane 和 worker 节点时，使用本仓库针对 Kubernetes v1.37.1 编写的 [kubeadm 部署指南](kubeadm.md)。先核对[组件版本清单](../component-versions.md)、[版本偏差策略](../upgrade.md)和目标网络插件官方兼容矩阵。

kubeadm 用于引导最小可用集群，不是基础设施自动化平台。生产部署还需规划 control-plane 高可用 endpoint、证书备份、etcd 备份恢复、网络和防火墙、存储、访问控制、监控、升级及灾难恢复。

本仓库也提供 [k0s](k0s.md) 和 [RKE2](rke2.md) 指南及版本固定的配置示例。它们是包含 Kubernetes、运行时和附加组件的发行版；发行版本、所带 Kubernetes 版本及默认组件组合需分别核对，不能仅因发行版更新就认为已支持本书的 v1.37 基线。具体版本与来源见[现行组件与示例版本核对](../component-current-status.md)。

如使用其他集群自动化工具，请核对其当前文档、目标 Kubernetes minor 的支持声明及升级路径。本目录不再保留旧版集群创建教程。历史 Azure、Windows、LinuxKit、kOps、Kubespray 和其他部署流程见[归档索引](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/index.md)；归档步骤不适用于 Kubernetes v1.36/v1.37。

## 托管集群

对于 GKE、EKS、AKS 等托管产品，使用对应云厂商官方文档、支持的 Kubernetes 版本列表、升级说明和其受支持的网络/存储插件。不要运行历史 kube-up、acs-engine 或本仓库旧脚本来创建云资源。

## Kubernetes 官方文档

- [kubeadm 安装](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)
- [kubeadm 创建集群](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)
- [生产环境部署工具](https://kubernetes.io/docs/setup/production-environment/tools/)
- [集群高可用](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)
