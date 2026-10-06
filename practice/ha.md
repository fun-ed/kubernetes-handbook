# 集群高可用

本页概述 Kubernetes 控制平面高可用（HA）的当前设计要点，目标为 Kubernetes v1.37.1。部署须采用 kubeadm v1.37 文档或发行版维护的流程；本页不是完整安装手册，也不构成生产认证。

## 控制平面拓扑

kubeadm HA 支持 stacked-etcd（每个控制平面节点运行 etcd 成员）与 external-etcd 两种拓扑。两者都需要规划稳定且冗余的 API server endpoint（通常由负载均衡器提供）、控制平面节点故障域、API server 健康检查、证书生命周期和恢复方案。外部负载均衡器、DNS、网络连通性与防火墙是平台前置条件，应由相应团队独立配置和验证。

选择拓扑时，按故障域、运维能力、节点数量、资源预算和 etcd 延迟权衡。多个 API server 不会自动提供高可用入口；客户端、负载均衡器与控制平面节点都须能在故障时转移。避免把控制平面服务地址、证书或测试 IP 当成通用配置。

## etcd 与备份

- kubeadm v1.37.1 的 etcd 默认镜像为 **3.7.0**；这是 Kubernetes 固定值，不是上游最新版本或第三方兼容声明。
- stacked-etcd 将 etcd 成员与控制平面节点放在相同故障域；external-etcd 将数据层与控制平面分离，但增加独立节点、网络和证书管理要求。
- 保持 etcd 成员数量为奇数，并为选举和多数派 quorum 保留足够资源与低延迟网络。丢失多数派时，不能靠增加 API server 恢复 etcd 写入能力。
- 采用受支持的快照与恢复流程，保护快照、加密传输并定期在隔离环境演练恢复。备份成功不代表已验证数据一致性或可恢复性。

恢复和升级须遵循 etcd 与集群发行版的精确版本顺序；不可只替换镜像、复制旧证书脚本或跨版本复用旧配置。

## kubeadm 部署前检查

1. 选择并测试可靠的 `controlPlaneEndpoint`，确认所有控制平面与工作节点可达。
2. 按 [Kubernetes v1.37 kubeadm HA 指南](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)准备节点、CRI v1 运行时、cgroup driver、网络与负载均衡器。
3. 使用与 kubeadm v1.37 匹配的 `kubeadm.k8s.io/v1beta4` 配置格式；逐项校验证书分发、SAN、RBAC、API server health check 及控制平面 join 顺序。共享证书密钥应通过安全渠道传递并设定有效期限。
4. 部署后检查 etcd 成员健康、API endpoint 故障切换、控制平面组件状态、DNS、CNI、持久化与告警；在维护窗口演练节点替换和 etcd 恢复。

详细流程和拓扑清单见 [kubeadm 高可用集群](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)、[etcd 集群操作指南](https://etcd.io/docs/v3.7/op-guide/)及本手册[组件版本矩阵](../setup/component-versions.md)。

本页早期的 cfssl R1.2 下载、手工 etcd 3.1 Pod/systemd 配置、旧 kubeadm `MasterConfiguration` 与 `kubeadm alpha phase` 操作已移至[历史归档](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/practice/ha.md)。请勿执行归档中的脚本或清单。
