# Istio 排错

遇到故障时先确认 Istio release 和 Kubernetes 版本是否在[官方支持表](https://istio.io/latest/docs/releases/supported-releases/)中，再使用 [Istio 官方排错指南](https://istio.io/latest/docs/ops/diagnostic-tools/istioctl-analyze/)与 `istioctl`。

```bash
istioctl version
istioctl analyze --all-namespaces
istioctl proxy-status
kubectl get pods -n istio-system
```

`istioctl proxy-status` 可检查 sidecar 与控制平面的同步；Ambient 模式还要核对 `ztunnel` 和 waypoint 状态。当前版本资料见[安装章节](istio-deploy.md)。本目录保留的早期诊断输出涉及 Mixer、servicegraph 和已删除的 API，不能用于当前版本。
