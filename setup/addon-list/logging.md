# 集群日志

Kubernetes 不会自动部署集中式日志后端，也不会默认在每个节点安装 Fluentd。应用通常把日志写到标准输出/错误，再由节点级日志代理收集并转发到集群外或集中的日志存储与查询系统。选择代理、后端和部署方式时，应核对其当前 Kubernetes、节点操作系统及运行时支持，并依照该项目的官方文档配置访问权限和保留策略。

- [Kubernetes 集群日志架构](https://kubernetes.io/docs/concepts/cluster-administration/logging/)
- [Kubernetes 日志文档](https://kubernetes.io/docs/tasks/debug/)

> **历史说明：** 本页旧版曾介绍 `cluster/kube-up.sh`、由 Kubernetes 仓库提供的 Fluentd/Elasticsearch/Kibana manifests、`beta.kubernetes.io/fluentd-ds-ready` 标签，以及将 `kubectl proxy` 绑定到 `0.0.0.0` 的访问方法。这些脚本、标签和配置并非 v1.37.1 的受支持部署方案；不要应用旧 manifest 或公开 API 代理。旧 ELK 介绍只作历史背景。

部署前确认日志代理需要的节点权限、Secret/RBAC、数据出口和资源限制，并验证日志中不含不应收集的敏感信息。不要将日志后端直接暴露到不可信网络。
