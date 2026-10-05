# Pod egress SNAT 与 IP masquerading

Pod 出站流量的 SNAT 行为由集群网络实现和云平台配置共同决定；Kubernetes 核心并未提供一套适用于所有 CNI 的通用安装步骤。变更 masquerade/SNAT 前，先确认 Pod、Service 和节点网段、流量出口、返回路由，以及由 CNI、节点规则还是云网络负责转换。按照所选网络插件和平台针对目标版本的官方文档配置，并在测试环境验证。

- [Kubernetes 网络模型](https://kubernetes.io/docs/concepts/services-networking/)
- [Kubernetes SIG Network 的 ip-masq-agent 项目](https://github.com/kubernetes-sigs/ip-masq-agent)
- [Calico 网络文档](https://docs.tigera.io/calico/latest/networking)

> **历史说明：** 旧版本页使用了 `kubernetes-incubator/ip-masq-agent` 的 `master` manifest、`beta.kubernetes.io/masq-agent-ds-ready` 标签及 2018 年的 iptables/CNI 示例。不要将旧 YAML、标签或 Windows CNI 配置用于 v1.37.1；按当前项目发布说明和实际 CNI/平台支持矩阵选择并固定版本。`ip-masq-agent` 是独立网络组件，不是 Kubernetes v1.37 内置插件。

排查时比较 Pod 出口前后的源地址，检查节点上的实际 SNAT 规则和路由，并确认返回路径。避免在不知道规则所有者和作用范围时直接修改节点防火墙或 NAT 规则。
