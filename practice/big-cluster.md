# 大规模 Kubernetes 集群

Kubernetes 官方大规模集群指南说明，v1.37 设计目标包括不超过 5,000 个节点、每节点不超过 110 个 Pod、全群不超过 150,000 个 Pod 与 300,000 个容器。这些是官方规模边界，不是对任意云平台、CNI、工作负载或扩展组合的性能保证。请参阅[官方大规模集群指南](https://kubernetes.io/docs/setup/best-practices/cluster-large/)并针对目标环境进行容量测试。

## 规划与扩展

- 先定义工作负载与故障域，测量 API Server 请求负载、etcd 延迟/磁盘、节点资源、Pod 密度、DNS、网络、存储及日志/监控负载。扩容前设定批次和速率限制，避免云供应商配额、实例创建限速或控制平面瞬时负载成为瓶颈。
- 控制平面需跨故障区域提供冗余 API endpoint；官方指南建议每个故障区域至少有一个控制平面实例。先垂直扩充控制平面，再以观测到的瓶颈决定是否横向增加实例。负载均衡器、健康检查、跨区流量成本与故障转移需依平台单独验证。
- 持续监控并调整附加组件资源：每节点运行的 DaemonSet、单副本或分区级服务、可水平扩展的控制器有不同容量模型。可使用 VPA recommender 等工具辅助估算请求与限制，但应审查建议并逐步发布。
- 为 CoreDNS、metrics-server 等集群关键附加组件评估合适的 PriorityClass；优先级不会创造节点容量，仍须留出资源并测试抢占影响。

## etcd 与事件负载

大规模集群可评估把 Event 对象写入专用 etcd 实例，以隔离事件负载。它需要额外 etcd 节点和 API Server 配置，不是通用的默认优化；先量测事件速率、存储与 API Server 负载，再按官方 etcd 操作指南设计备份、监控、TLS 与恢复流程。kubeadm v1.37.1 的默认 etcd 3.7.0 仅是 kubeadm 固定值，不等同于大规模集群设计或 etcd 上游最新版本。

## 容量验证

在隔离且与生产拓扑相近的环境中逐步增加节点与负载，记录 Kubernetes/runtime/CNI 版本、节点规格、插件、请求速率、资源使用量、错误率及恢复行为。验证云端配额、API Server 与 etcd 延迟、控制平面故障切换、DNS、网络和存储；一次基准测试结果不构成容量承诺。性能参数应依 v1.37 官方指南、发行版说明与实际测量调整，不要复制旧版固定 kube-apiserver/kubelet 参数或 Docker 专属设置。

本章早期资料包含 etcd 3.2/3.1、Docker 专用参数、已移除 addon 路径、过期性能数字与未经验证的通用 API Server 参数，已移至[历史归档](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/practice/big-cluster.md)。请勿将归档中的命令、资源片段或数值作为当前容量配置。
