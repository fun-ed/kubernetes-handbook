# Istio 服務網格

Istio 使用控制平面管理資料平面代理。當前控制平面由 `istiod` 提供；應用流量可以透過 sidecar 模式或 ambient 模式接入。

> **版本與 Kubernetes 支援範圍**：截至 2026-10-05，Istio 1.31.1 是最新穩定版；官方支援表列出的 Kubernetes 版本為 1.32–1.36，沒有列出 v1.37。因此本書目標叢集 v1.37.1 尚無該版本的 Istio 官方相容宣告。不要將本章命令用於 v1.37.1 叢集，除非上游支援表或平台供應商明確覆蓋該組合。見 [Istio 1.31.1 釋出頁](https://github.com/istio/istio/releases/tag/1.31.1)和[支援版本表](https://istio.io/latest/docs/releases/supported-releases/)。

## 資料平面模式

- **Sidecar**：在每個 Pod 中注入 Envoy，適用於需要 Envoy L7 功能或現有 sidecar 工作流的服務。Namespace 標籤 `istio-injection=enabled` 可啟用自動注入。
- **Ambient**：不在每個 Pod 中注入代理。節點上的 `ztunnel` 提供 L4 連線與工作負載身分；按需部署的 waypoint proxy 提供 L7 功能。使用 namespace 標籤 `istio.io/dataplane-mode=ambient` 將工作負載加入 ambient mesh。

同一應用不要同時透過注入標籤和 ambient 標籤加入兩種資料平面。先確認 Kubernetes 版本、平台、CNI、策略和所需流量功能是否在當前 Istio 支援表中，再選擇模式。見 [Istio ambient 文件](https://istio.io/latest/docs/ambient/)。

## 安裝與日常檢查

[安裝章節](istio-deploy.md)使用 `istioctl` 安裝 Istio，並給出兩種模式的 namespace 標籤。部署前應固定 Istio release、檢視官方 Kubernetes 支援表，並檢查所用安裝 profile。

```bash
istioctl version
istioctl analyze --all-namespaces
istioctl proxy-status
```

`istioctl proxy-status` 用於檢查 sidecar 與控制平面的同步狀態；ambient 模式還應檢查 `ztunnel` 和 waypoint 狀態。不要透過檢查已刪除的 `Mixer`、`Galley` 或 `servicegraph` Deployment 來判斷當前 Istio 是否健康。

## 舊版本章節

本目錄中的舊 Mixer 指標、Mixer 策略、`RbacConfig`、`ServiceRole`、手工 `kube-inject` 與 Galley 部署教程已移入[歷史歸檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/index.md)。它們的 API 和安裝步驟不適用於當前 Istio。當前 API schema、安裝方式和 Kubernetes 支援範圍應以 Istio 對應 release 的官方文件為準。
