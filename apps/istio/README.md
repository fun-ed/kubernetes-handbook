# Istio 服务网格

Istio 使用控制平面管理数据平面代理。当前控制平面由 `istiod` 提供；应用流量可以通过 sidecar 模式或 ambient 模式接入。

> **版本与 Kubernetes 支持范围**：截至 2026-10-05，Istio 1.31.1 是最新稳定版；官方支持表列出的 Kubernetes 版本为 1.32–1.36，没有列出 v1.37。因此本书目标集群 v1.37.1 尚无该版本的 Istio 官方兼容声明。不要将本章命令用于 v1.37.1 集群，除非上游支持表或平台供应商明确覆盖该组合。见 [Istio 1.31.1 发布页](https://github.com/istio/istio/releases/tag/1.31.1)和[支持版本表](https://istio.io/latest/docs/releases/supported-releases/)。

## 数据平面模式

- **Sidecar**：在每个 Pod 中注入 Envoy，适用于需要 Envoy L7 功能或现有 sidecar 工作流的服务。Namespace 标签 `istio-injection=enabled` 可启用自动注入。
- **Ambient**：不在每个 Pod 中注入代理。节点上的 `ztunnel` 提供 L4 连接与工作负载身份；按需部署的 waypoint proxy 提供 L7 功能。使用 namespace 标签 `istio.io/dataplane-mode=ambient` 将工作负载加入 ambient mesh。

同一应用不要同时通过注入标签和 ambient 标签加入两种数据平面。先确认 Kubernetes 版本、平台、CNI、策略和所需流量功能是否在当前 Istio 支持表中，再选择模式。见 [Istio ambient 文档](https://istio.io/latest/docs/ambient/)。

## 安装与日常检查

[安装章节](istio-deploy.md)使用 `istioctl` 安装 Istio，并给出两种模式的 namespace 标签。部署前应固定 Istio release、查看官方 Kubernetes 支持表，并检查所用安装 profile。

```bash
istioctl version
istioctl analyze --all-namespaces
istioctl proxy-status
```

`istioctl proxy-status` 用于检查 sidecar 与控制平面的同步状态；ambient 模式还应检查 `ztunnel` 和 waypoint 状态。不要通过检查已删除的 `Mixer`、`Galley` 或 `servicegraph` Deployment 来判断当前 Istio 是否健康。

## 旧版本章节

本目录中旧的 Mixer 指标、Mixer 策略、`RbacConfig`、`ServiceRole`、手工 `kube-inject` 与 Galley 部署步骤均属于早期 Istio 版本。它们在各自页面标记为历史内容，不能应用于当前 Istio。

当前流量管理与安全配置见 [Istio 官方文档](https://istio.io/latest/docs/)，不要把历史 CRD 示例改写成当前 API 而不先确认 schema 和版本。
