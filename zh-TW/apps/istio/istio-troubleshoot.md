# Istio 排錯

遇到故障時先確認 Istio release 和 Kubernetes 版本是否在[官方支援表](https://istio.io/latest/docs/releases/supported-releases/)中，再使用 [Istio 官方排錯指南](https://istio.io/latest/docs/ops/diagnostic-tools/istioctl-analyze/)與 `istioctl`。

```bash
istioctl version
istioctl analyze --all-namespaces
istioctl proxy-status
kubectl get pods -n istio-system
```

`istioctl proxy-status` 可檢查 sidecar 與控制平面的同步；Ambient 模式還要核對 `ztunnel` 和 waypoint 狀態。當前版本資料見[安裝章節](istio-deploy.md)。本目錄保留的早期診斷輸出涉及 Mixer、servicegraph 和已刪除的 API，不能用於當前版本。
