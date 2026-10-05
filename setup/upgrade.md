# Kubernetes 升级与版本偏差

本页以 Kubernetes v1.37.1（截至 2026-10-05）为当前手册版本。具体升级前，逐项检查官方[版本偏差策略](https://kubernetes.io/releases/version-skew-policy/)、[kubeadm 升级指南](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/)和所用发行版或云厂商的支持政策。

## v1.37 集群的组件版本约束

版本偏差按 **minor** 版本计算，不等于“任意较新/较旧版本都兼容”。同一组件也应尽量保持相同 patch 版本。

- **kube-apiserver：** 高可用集群中各 API server 最多相差一个 minor 版本，例如升级期间可暂时同时运行 v1.36 和 v1.37。
- **kubelet：** 不得比任何 API server 新；单一 v1.37 API server 时，最多可旧三个 minor（v1.34–v1.37）。如果 API server 混跑 v1.36/v1.37，kubelet 不得高于较旧的 v1.36 API server。
- **kube-proxy：** 不得比任何 API server 新，最多可比 API server 旧三个 minor；它与所在节点 kubelet 也最多相差三个 minor。高可用滚动升级时同时满足两项限制。
- **kube-controller-manager、kube-scheduler、cloud-controller-manager：** 不得比它们通信的 API server 新，最多旧一个 minor。API server 混跑时不得高于其中最旧的 API server。
- **kubectl：** 通常允许比 API server 旧或新一个 minor；高可用 API server 混跑期间需遵守官方策略对混合版本的额外限制。

具体矩阵和边界条件以[官方版本偏差策略](https://kubernetes.io/releases/version-skew-policy/)为准。kubeadm 有额外的工具版本规则，也必须遵守。

## 升级顺序

Kubernetes 不支持跳过 minor 版本升级。逐 minor 完成升级，例如 v1.35 → v1.36 → v1.37；在每一跳中先把 control plane 升到目标 minor，再逐节点升级 kubelet。单控制平面集群也不得跳级。

使用 kubeadm 的集群按官方流程升级：

1. 阅读目标版本的发行说明和 API 弃用指南；确认 admission webhook、CRD、operator 和应用可以处理新资源版本及字段。
2. 把 kubeadm 的软件包仓库切换到目标 minor 专属的 `pkgs.k8s.io` 仓库，并按 kubeadm 升级文档操作。v1.37 软件包仓库不是跨 minor 的滚动通道。
3. 高可用集群按 kubeadm 官方流程逐台升级 control-plane 节点。kubeadm 会在各节点一并升级该节点的 kube-apiserver、controller-manager 和 scheduler，并通过本地 API endpoint 操作；不需要等所有 API server 升完后再把这些静态 Pod 作为独立阶段升级。外部部署的 cloud-controller-manager 及负载均衡/API endpoint 切换须按其独立部署和云厂商流程处理；涉及目标版本的迁移应等所有 API server 都已升级到目标版本后进行。
4. 每个节点升级 kubelet 前先 drain；按官方节点升级流程执行。不要把旧文档中的 kubelet 原地跨 minor 升级命令照搬到新版本。
5. 按各插件上游说明单独检查并升级 CNI、CSI、CoreDNS 外部定制项和自定义扩展。kubeadm 不会替所有插件自动升级。
6. 检查节点、系统 Pod、API discovery、控制器与应用，再解除维护。

升级 etcd、发行版内核、containerd 或云 provider 时，还需各自使用对应项目的兼容与备份恢复流程。对 etcd 等持久化数据先验证可恢复备份，不要把集群升级当作可逆操作。

## Kubernetes v1.37 的注意事项

- kubeadm v1.37.1 默认使用 etcd 3.7.0、CoreDNS 1.14.6 和 pause 3.10.2。这些是 kubeadm 默认值；不要仅因外部项目有更新版本就直接替换镜像。
- kubelet 的 `KubeletCgroupDriverFromCRI` 在运行时支持 `RuntimeConfig` 时可自动读取 cgroup driver；v1.37 对旧 runtime 的兼容回退仍存在，移除已延后至 v1.38。新部署应优先让 containerd/CRI-O 与 kubelet 使用 `systemd`，不要依赖旧式回退行为。
- kube-proxy 的 IPVS 模式已弃用；nftables 模式已 GA，但 v1.37 并非默认模式。切换代理模式须单独评估内核、规则管理及回滚策略。
- `metrics.k8s.io/v1` 的 API 稳定状态不表示所有 metrics API 后端都已实现该版本。使用 metrics-server 时先检查其兼容矩阵和 APIService discovery；例如 v0.9.0 上游 manifest 注册 `metrics.k8s.io/v1beta1`。

## API 与 feature gate 检查

- 对每个升级源版本，按官方[弃用指南](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)检查被移除的 API。API 迁移可能需要调整 schema、selector、字段类型或 webhook，而不只是替换 API 字符串。
- 按集群实际版本和组件查看 [Feature Gates](feature-gates.md) 及[官方表格](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/)。不要继续设置已经 GA 或已移除的 gate；Alpha/Beta gate 的启用范围、默认值可能每个 minor 改变。
- 查阅 [Kubernetes v1.37.1 发行说明](https://raw.githubusercontent.com/kubernetes/kubernetes/v1.37.1/CHANGELOG/CHANGELOG-1.37.md)及[迁移说明](kubernetes-v1.37.md)，逐项检查应用和插件行为变化。

## 参考

- [Kubernetes version and version-skew support policy](https://kubernetes.io/releases/version-skew-policy/)
- [升级 Kubernetes 集群（kubeadm）](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/)
- [安装 kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)
- [API deprecation guide](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)
- [Feature Gates](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/)