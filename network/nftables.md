# kube-proxy 的 nftables 模式

Kubernetes kube-proxy 原生 nftables 模式从 v1.33 起稳定，要求 Linux kernel 5.13 或更高版本。Kubernetes v1.37 的 Linux kube-proxy 默认仍使用 `iptables`；IPVS 模式从 v1.35 起弃用。原生 nftables 模式不同于 `iptables-nft` 兼容后端，后者由 iptables 命令在底层操作 nftables。它也不同于 Cilium eBPF Service 实现。应选择一种 Service 数据平面，除非 CNI 官方集成明确要求，否则不要同时运行相互竞争的 kube-proxy 与 eBPF Service 实现。

原生模式通过 nftables 建立 Service、端点和 NodePort 规则，而非调用 iptables 接口。它不会配置主机防火墙、IPv6 路由或 CNI 网络策略。内核版本、nft 用户空间工具、kube-proxy 配置、防火墙策略和网络接口布局都会影响结果。

## 配置片段

以下是 kube-proxy 配置文件片段，不是 Kubernetes API 对象。它使用 `kubeproxy.config.k8s.io/v1alpha1` 配置结构，应合并到集群安装工具管理的配置中，不能用 `kubectl apply`。

```yaml
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
mode: nftables
clusterCIDR: fd00:10:244::/56
# 双栈集群应填写实际 Pod CIDR，使用逗号分隔。
```

`clusterCIDR` 必须符合实际 Pod 网络，供 kube-proxy 判断哪些流量需要 masquerade。双栈集群填写两个真实 CIDR，例如 `10.244.0.0/16,fd00:10:244::/56`。文档示例网段不能用于实际网络。保留发行版生成的其他字段；这个片段不是完整配置。

## 在隔离实验室迁移

先确认 Linux 内核、kube-proxy 版本及集群管理方式。在一次性测试集群备份当前配置及其所属 ConfigMap 或安装器参数。检查当前模式、节点地址、Service CIDR、Pod CIDR、NodePort 范围、防火墙规则及现有 kube-proxy 规则。修改配置源后，按该集群管理工具文档进行 rollout。kubeadm 管理的集群通常将 kube-proxy 配置存放在 `kube-proxy` ConfigMap，但仍须确认当前版本与生命周期工具如何管理它。不要清空主机规则集或盲目替换 ConfigMap。

切换前后都从测试工作负载检查 Service 与 DNS。以下命令只读取状态：

```bash
kubectl -n kube-system get daemonset kube-proxy
kubectl -n kube-system get pods -l k8s-app=kube-proxy -o wide
kubectl get services,endpointslices -A
nft list ruleset
iptables --version
```

`nft list ruleset` 会显示当前主机规则，应由具备节点权限的管理者检查。`iptables --version` 可帮助识别 iptables 前端，但无法证明 kube-proxy 使用哪种模式。请同时检查生效配置与日志。成功表示 proxy Pod 使用预期配置，且所需网络中的测试 ClusterIP、DNS、NodePort 路径正常；这不能证明所有防火墙或外部地址路径都已验证。

## 地址与故障检查

根据 v1.37 kube-proxy 配置参考检查实际配置中的 `nodePortAddresses`、`iptablesLocalhostNodePorts` 与 `detectLocalMode` 等字段。nftables 模式不支持与 iptables 模式相同的 localhost NodePort 行为。迁移时 NodePort 过滤与来源地址行为可能改变。检查主机防火墙是否允许目标 NodePort 流量。IPv6 还需确认节点地址、路由及防火墙规则；启用 nftables 不会建立 IPv6 连通性。

Service 不通时，比对各节点规则与 kube-proxy 日志，确认 EndpointSlice 有就绪端点，检查是否有其他 Service proxy 同时处理流量，并分别测试 DNS 与 ClusterIP。仅查看规则列表不能证明流量正常。

## 正式环境与回退

先在隔离集群迁移，保存生效配置、节点规则集与流量测试结果。回退会更改 proxy 配置并重启节点规则管理，应按集群安装器流程验证，并保留旧配置。不要运行 `nft flush ruleset` 或大范围 iptables flush 命令回退，它们可能删除其他主机防火墙与容器规则。

主要来源：[Kubernetes v1.37 nftables proxy mode](https://kubernetes.io/docs/reference/networking/virtual-ips/#nftables-proxy-mode)、[kube-proxy 配置 API](https://kubernetes.io/docs/reference/config-api/kube-proxy-config.v1alpha1/)、[v1.37 kube-proxy 配置源码](https://github.com/kubernetes/kubernetes/blob/v1.37.1/pkg/proxy/apis/config/types.go)、[Kubernetes v1.37 变更记录](https://github.com/kubernetes/kubernetes/blob/v1.37.1/CHANGELOG/CHANGELOG-1.37.md)。
