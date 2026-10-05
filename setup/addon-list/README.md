# 集群附加组件

Kubernetes 核心发行版不替你自动安装所有网络、指标、可观测性和扩缩容组件。每个插件应按其官方支持矩阵、集群 minor 版本、容器运行时和网络要求单独选型；这里的“最新稳定版”不等于已经认证支持 Kubernetes v1.37。

- [Pod 网络 / CNI](https://kubernetes.io/docs/concepts/cluster-administration/addons/#networking-and-network-policy)：kubeadm 集群必须安装 CNI 后节点才会 Ready。当前本手册示例为 Calico 3.33.0，官方资料明确支持 Kubernetes 1.35–1.37。
- [CoreDNS](kube-dns.md)：kubeadm 默认安装 CoreDNS。历史 kube-dns 文件仅作背景，旧 YAML 不应重新应用。
- [metrics-server](metrics.md)：仅向 Metrics API 提供即时资源用量，非长期指标存储系统。当前上游 0.9.0 仍注册 `metrics.k8s.io/v1beta1`。
- [监控](monitor.md)：可评估 Prometheus 社区 `kube-prometheus-stack`，安装前核对 chart、CRD 和 Kubernetes 支持范围。
- [Cluster Autoscaler](cluster-autoscaler.md)：版本通常需与 Kubernetes control plane minor 对齐；截至 2026-10-05，上游尚无经核实的 Kubernetes 1.37 匹配发布/兼容条目，本手册不提供 v1.37 安装命令。
- [Dashboard 状态](dashboard.md)：Kubernetes Dashboard 已归档，不是可部署的当前组件；参见 Headlamp 项目。
- [GPU 工作负载](gpu.md)：NVIDIA GPU Operator 26.7.1 的 26.7 支持矩阵覆盖 Kubernetes v1.33–v1.37，但仍应核对完整的平台组合。
- [日志](logging.md)：Kubernetes 不会默认安装集中式日志后端或节点日志代理，需按当前架构选择并固定日志组件。
- [Pod 出站 SNAT](ip-masq-agent.md)：masquerade 行为依赖 CNI/云平台，不要照用旧版 beta 标签或 `master` manifest。

本页面过去列出的 Heapster、早期 kube-dns、Kubernetes Dashboard 安装包及旧 chart 只保留为历史背景。不要用旧仓库、旧镜像或未固定版本的 `master` YAML 部署新集群。

## 参考

- [Kubernetes Addons](https://kubernetes.io/docs/concepts/cluster-administration/addons/)
- [组件版本清单](../component-versions.md)
- [版本偏差与升级策略](../upgrade.md)
