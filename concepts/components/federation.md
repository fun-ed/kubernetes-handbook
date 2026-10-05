# Federation（历史项目）

本页原先介绍的 Kubernetes Federation v1、`federation-apiserver`、`federation-controller-manager`、`kubefed`、Federated API 和 `federation.alpha.kubernetes.io/*` 注解属于旧版多集群方案，不是 Kubernetes v1.37 内置或受支持的组件。本页旧安装命令、API 清单、`--admission-control` 配置及公开 DNS/LoadBalancer 示例均已过时，**不要在当前集群中照此部署**。

Kubernetes 的单集群核心 API 不提供 Federation v1 的集群注册、资源复制或跨集群 DNS。多集群场景应先明确集群生命周期、身份权限、网络、安全和服务发现要求，再选择当前受维护并兼容目标集群版本的多集群管理或服务互联方案。不要将旧 Federation API 对象当作当前 Kubernetes 资源。

在维护旧集群时，应按旧项目的迁移及移除指南处理已有 Federation 控制平面和资源；不要仅删除命名空间来清理，因为它可能遗留 PV、云资源或成员集群中的副本。

当前多集群设计请参考 Kubernetes [架构与集群管理文档](https://kubernetes.io/docs/concepts/cluster-administration/)、所选方案的维护状态、安全文档及目标 Kubernetes 版本兼容矩阵。
