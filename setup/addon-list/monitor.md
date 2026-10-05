# Kubernetes 集群监控

截至 2026-10-05，Prometheus 社区 chart 仓库发布的 `kube-prometheus-stack` 最新稳定 chart 为 **91.9.0**（2026-10-02 发布）。它打包 Prometheus Operator、Prometheus、Alertmanager、node-exporter、kube-state-metrics 及默认 Grafana 配置，是需要 Prometheus 生态时可评估的一种方案；chart 版本并不等同于 Kubernetes 兼容认证。

使用 Helm 4.3.0 客户端、固定 chart 版本安装：

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --version 91.9.0 --namespace monitoring --create-namespace
```

来源：[chart 91.9.0 release](https://github.com/prometheus-community/helm-charts/releases/tag/kube-prometheus-stack-91.9.0)、[chart README](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)、[Helm 安装与版本说明](https://helm.sh/docs/intro/install/)。部署前检查该 chart release 对 Kubernetes v1.37 的支持状态、Helm 4 兼容性、CRD 变更和存储配置；本仓库不把 chart 最新发布误称为已验证的 Kubernetes 兼容组合。生产环境先阅读 chart 的 values、资源需求、认证、持久化、网络暴露和升级/回滚文档。

metrics-server 不是该监控栈的替代品：它面向 `kubectl top` 和 HPA 的即时 Metrics API。Prometheus/长期指标、日志、trace 及告警各需独立的数据保留与安全设计。

> **历史说明：** Heapster 已退役并归档，旧页面内 Heapster、cAdvisor、Docker daemon flag、早期 Kubernetes Dashboard 及过期 chart 示例均不适用于 v1.37.1。本页不保留可以误执行的旧安装命令。