# 集群部署

## 自建集群

需要自行管理 Linux control plane 和 worker 节点时，使用本仓库针对 Kubernetes v1.37.1 编写的 [kubeadm 部署指南](kubeadm.md)。先核对[组件版本清单](../component-versions.md)、[版本偏差策略](../upgrade.md)和目标网络插件官方兼容矩阵。

kubeadm 用于引导最小可用集群，不是基础设施自动化平台。生产部署还需规划 control-plane 高可用 endpoint、证书备份、etcd 备份恢复、网络和防火墙、存储、访问控制、监控、升级及灾难恢复。

如使用其他集群自动化工具，请只按其当前 upstream 文档和明确支持的 Kubernetes release 执行。本目录保留的旧案例不代表工具或云厂商的当前能力：

- [kops 旧操作笔记](kops.md)（已加历史说明；kops 新版本支持范围以其当前文档为准）
- [Kubespray v1.7.3 示例](kubespray.md)，仅历史参考
- [LinuxKit 早期案例](k8s-linuxkit.md)，仅历史参考
- [Azure ACS/AKS 预览期示例](azure.md)，请改用 Azure 当前 AKS 文档
- [Windows 节点笔记](windows.md)，需按目标 Kubernetes minor 与平台当前支持矩阵核验

## 托管集群

对于 GKE、EKS、AKS 等托管产品，使用对应云厂商官方文档、支持的 Kubernetes 版本列表、升级说明和其受支持的网络/存储插件。不要运行历史 kube-up、acs-engine 或本仓库旧脚本来创建云资源。

## Kubernetes 官方文档

- [kubeadm 安装](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)
- [kubeadm 创建集群](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)
- [生产环境部署工具](https://kubernetes.io/docs/setup/production-environment/tools/)
- [集群高可用](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)
