# Metrics API 与 metrics-server

metrics-server 收集 kubelet 的资源指标并向 Kubernetes Metrics API 提供短期、近实时用量，主要服务 `kubectl top` 和基于资源指标的 HPA。它不是长期时序数据库、日志平台或生产可观测性系统。长期监控请看[监控方案](monitor.md)。

## 安装 metrics-server 0.9.0

截至 2026-10-05，上游稳定版为 **0.9.0**，兼容矩阵列明支持 Kubernetes 1.34+。先确认节点可从 metrics-server 连接 kubelet，证书和地址符合上游要求，再安装固定 release manifest：

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.9.0/components.yaml
kubectl -n kube-system rollout status deployment/metrics-server
kubectl get apiservice v1beta1.metrics.k8s.io
kubectl get --raw /apis/metrics.k8s.io
kubectl top nodes
kubectl top pods -A
```

发布源：[metrics-server v0.9.0 release](https://github.com/kubernetes-sigs/metrics-server/releases/tag/v0.9.0)、[上游安装与兼容矩阵](https://github.com/kubernetes-sigs/metrics-server#readme)。升级前逐项检查证书、kubelet TLS、网络可达性及 HA 配置，不要为了让 APIService 变为 Available 而关闭 TLS 验证或复制旧的 Docker 防火墙修改。

## `metrics.k8s.io/v1` 与后端

Kubernetes Metrics API 的版本生命周期与具体 metrics-server backend 的实现是两件事。即使集群/API 文档中的 `metrics.k8s.io/v1` 已 GA，聚合 API server 也不会替后端自动转换或生成该版本。metrics-server 0.9.0 上游 `components.yaml` 注册的是 `v1beta1.metrics.k8s.io`，兼容矩阵也只承诺 `metrics.k8s.io/v1beta1`。因此这里的 v0.9.0 部署应按实际服务的 v1beta1 discovery 使用；若应用要求 v1，必须先确认所用 backend 明确实现并发布了该版本。

验证 APIService 后可检查 discovery：

```bash
kubectl get --raw /apis/metrics.k8s.io/v1beta1
kubectl get apiservice v1beta1.metrics.k8s.io -o wide
```

metrics-server 官方明确指出其设计目标不是通用监控解决方案；不要将 Heapster 或旧版 metrics-server 的安装教程当作当前生产指标管道。