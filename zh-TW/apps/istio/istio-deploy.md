# Istio 安裝與資料平面選擇

截至 2026-10-05，Istio **1.31.1** 是本手冊資料截點前的最新穩定版。Istio 官方支援表只列出 Kubernetes **1.32–1.36**，沒有列出 Kubernetes v1.37。由於本手冊目標為 Kubernetes v1.37.1，當前沒有上游相容證據支援在該叢集安裝 Istio 1.31.1。以下命令只供受支援版本的測試叢集評估；請等待 Istio 官方支援表覆蓋 v1.37 或取得平台供應商的明確相容宣告。

來源：[Istio 1.31.1 釋出頁](https://github.com/istio/istio/releases/tag/1.31.1)、[支援版本表](https://istio.io/latest/docs/releases/supported-releases/)。

## 下載固定版本並檢查客戶端

Istio 官方 release archive 包含 `istioctl`、設定 profile 和範例。下面將下載器固定到 1.31.1，而不是自動跟隨未來的最新版本：

```bash
ISTIO_VERSION=1.31.1
curl -L https://istio.io/downloadIstio | ISTIO_VERSION="$ISTIO_VERSION" sh -
cd "istio-${ISTIO_VERSION}"
export PATH="$PWD/bin:$PATH"
istioctl version
```

首次在任何目標叢集安裝前，檢視該版本支援表、平台說明和 profile。不要把當前 Kubernetes v1.37.1 叢集當作上述受支援測試環境。

## Sidecar 模式

在官方支援的測試叢集中安裝 Istio 後，為要注入 Envoy 的 namespace 設定標籤。`istioctl install` 會安裝控制平面與所選 profile 的元件：

```bash
istioctl install --set profile=demo --skip-confirmation
kubectl label namespace default istio-injection=enabled
```

後續在 `default` namespace 建立的適用 Pod 會由 webhook 注入 Envoy sidecar。應用部署前確認映像檔、探針、連接埠命名和資源請求；啟用注入不會替代服務身分、授權策略或網路策略設定。`demo` profile 只用於評估，不是生產 profile。

## Ambient 模式

在支援的叢集中使用 ambient profile 安裝節點代理 `ztunnel` 和 CNI 元件，然後顯式標記 namespace：

```bash
istioctl install --set profile=ambient --skip-confirmation
kubectl label namespace default istio.io/dataplane-mode=ambient
```

Ambient 模式不向每個 Pod 注入 sidecar。`ztunnel` 提供 L4 mesh 功能；需要 L7 路由或策略的服務還需部署 waypoint。按[ambient 指南](https://istio.io/latest/docs/ambient/getting-started/)安裝和設定 waypoint，並核對當前 release 的支援範圍。

## 檢查與清理

```bash
istioctl analyze --all-namespaces
istioctl proxy-status
kubectl get pods -n istio-system
```

評估結束後按當前版本的官方[解除安裝說明](https://istio.io/latest/docs/setup/install/istioctl/#uninstall-istio)清理。不要直接刪除 `istio-system` 中單個控制平面元件來完成解除安裝。

舊的 Helm 2/Tiller 安裝命令、Mixer、Galley、`istioctl kube-inject`、servicegraph 和舊 ServiceGraph 頁面已從當前安裝流程移除；對應技術說明只作為早期 Istio 歷史材料保留在各自頁面。
