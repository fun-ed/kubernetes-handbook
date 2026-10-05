# Cluster Autoscaler

Cluster Autoscaler 会调用云平台或基础设施 provider 的 API 扩缩节点组；安装方案与权限、节点组模板、调度约束和云平台强相关，不能使用一个通用 manifest 代替 provider 文档。

上游建议 Cluster Autoscaler 与 Kubernetes control plane **minor 版本匹配**。截至 2026-10-05，最新稳定 Cluster Autoscaler release 为 **1.36.1**；上游 compatibility README 表格尚未列出 Kubernetes v1.37，且没有经核实的 CA v1.37 稳定发布。因此本手册不把 CA 1.36.1 镜像用于 Kubernetes 1.37，也不编造 v1.37 pin。请检查[上游 releases](https://github.com/kubernetes/autoscaler/releases)、[兼容矩阵](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/README.md)以及云厂商当前支持矩阵；只有确认存在匹配 v1.37 的 release 后才部署。

旧教程中的 CA v1.3 manifest、手动 RBAC 和 HPA sample 不是当前可用配置。生产环境应按所用 provider 的官方安装说明生成最小权限策略，并先在非生产集群验证 scale-up、scale-down、drain 保护和节点组边界。
