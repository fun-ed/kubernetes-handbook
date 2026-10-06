# 搭建 Kubernetes 集群

本手册当前部署路径以 **Kubernetes v1.37.1** 为目标，版本资料截至 2026-10-05。v1.37.1 发布于 2026-09-15；请在升级和生产变更前重新核对 [Kubernetes 发布周期](https://kubernetes.io/releases/) 与发行说明。

- **新建集群：** [使用 kubeadm 部署 v1.37.1](cluster/kubeadm.md)
- **从旧版本迁移：** [Kubernetes v1.37 迁移说明](kubernetes-v1.37.md)
- **兼容版本与上游来源：** [组件版本清单](component-versions.md)
- **现行版本与示例核对：** [组件及 sample YAML 版本核对](component-current-status.md)
- **发行版部署：** [k0s](cluster/k0s.md) 与 [RKE2](cluster/rke2.md)。使用发行版自身的 Kubernetes 与依赖组合，不直接套用 kubeadm 的组件版本。
- **版本偏差与升级顺序：** [升级和版本偏差](upgrade.md)
- **功能门控：** [Feature Gates](feature-gates.md)

## Kubernetes v1.37.1 的 kubeadm 默认依赖

下列镜像版本来自 Kubernetes v1.37.1 的 kubeadm 默认值，并非这些项目在截稿日的最新发布。升级或替换它们需先检查上游兼容性，不能把“最新版本”直接替换进现有集群。

| 组件 | kubeadm v1.37.1 默认版本 | 说明 |
| --- | --- | --- |
| etcd | 3.7.0 | kubeadm 使用的默认 etcd 镜像 |
| CoreDNS | 1.14.6 | kubeadm 使用的默认 DNS 镜像 |
| pause | 3.10.2 | Pod sandbox 镜像；containerd/CRI-O 配置需匹配 |

[Kubernetes v1.37.1 kubeadm 镜像默认值](https://raw.githubusercontent.com/kubernetes/kubernetes/v1.37.1/cmd/kubeadm/app/constants/constants.go)；最新稳定组件与单独维护的版本兼容证据见[组件版本清单](component-versions.md)。

## 组件边界

- Kubernetes 的 Debian/RPM 软件包使用 `pkgs.k8s.io` 的 **v1.37 专属**仓库；不要再使用已冻结的 `apt.kubernetes.io` 或 `yum.kubernetes.io`。
- Kubernetes 需要实现 CRI v1 的容器运行时。当前清单记录 containerd 2.4.1；在 systemd/cgroup v2 主机上使用 systemd cgroup driver。Docker Engine 不能直接作为 CRI runtime；若有迁移需求，先阅读官方 [Dockershim 迁移指南](https://kubernetes.io/docs/tasks/administer-cluster/migrating-from-dockershim/)。
- kubeadm 不会替你安装 Pod 网络。CNI provider 必须单独选型并安装；例如 Calico 3.33.0 的上游兼容资料明确列出 Kubernetes 1.35–1.37。Pod CIDR 必须与所选 provider 配置一致，且不能与节点网络重叠。
- CNI 插件、`crictl`、监控组件、Helm chart 和云厂商自动扩缩器有各自的发布周期，不能把 Kubernetes 源码中的依赖版本误当成整套集群的自动安装版本。
- 即使 Kubernetes 将 `metrics.k8s.io/v1` 标为 GA，聚合 API 仍须由实际后端提供相应版本。上游 metrics-server 0.9.0 manifest 注册的是 `metrics.k8s.io/v1beta1`，应以所部署后端的 discovery 结果为准。

## 旧教程归档

针对旧 Kubernetes 版本、已移除 API 或已退役组件的安装教程与清单已移出当前导航。归档目录保留原始内容，仅供历史参考；其中的命令和资源不能用于 Kubernetes v1.36/v1.37 部署。

查看[归档索引](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/index.md)。当前自建集群入口是 [kubeadm v1.37.1 指南](cluster/kubeadm.md)；云托管 Kubernetes 请使用云厂商针对目标版本的官方文档。