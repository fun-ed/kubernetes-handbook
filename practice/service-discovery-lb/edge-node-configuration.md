# 集群入口与外部 VIP

> **旧示例不可照抄**：本页后面的原始 Keepalived、IPVS、手工修改 Traefik DaemonSet、测试网段 IP 与 hostPort 配置来自旧集群，不是 Kubernetes v1.37 的可部署高可用方案。不要在生产节点照搬这些地址、systemd 配置或 `ipvsadm` 操作。

## 选择入口架构

- 云平台通常优先使用受支持的 `Service` type `LoadBalancer` 或平台 Ingress/Gateway 实现，由云控制面分配并维护入口地址。
- 裸机集群可评估受维护且与当前 Kubernetes/CNI 兼容的 LoadBalancer 实现，或由平台网络团队提供外部 VIP/负载均衡。确认地址池、路由公告、健康检查、故障切换与防火墙规则。
- 若在集群外运行代理并转发到 NodePort/LoadBalancer，应将节点维护、后端健康检查、源地址保留和安全策略作为基础设施配置管理。

选择方案时同时考虑故障域、L2/L3 网络拓扑、Pod CIDR 可达性、CNI、kube-proxy 模式与云/机房责任边界。VIP 漂移不是服务高可用本身；必须验证代理到各节点的健康检查、成员变更时的摘除行为和客户端重试策略。

## Kubernetes 侧检查

```bash
kubectl get nodes -o wide
kubectl get services --all-namespaces -o wide
kubectl get ingressclass
```

Kubernetes v1.35 起 IPVS kube-proxy 模式已弃用；nftables backend 已 GA，但不会自动成为默认值。升级或改用 nftables 前，应核对节点内核、CNI、发行版 kube-proxy 配置和官方迁移指南；不要为实现 VIP 而直接在节点上操作 IPVS 表。

原文的 Keepalived 三节点实验、Traefik 旧 RBAC/Deployment、IPVS 与 `hostPort` 细节仅供理解旧架构。实际部署请使用当前平台和入口控制器各自维护的配置方式，不要把旧实验地址视为默认方案。
