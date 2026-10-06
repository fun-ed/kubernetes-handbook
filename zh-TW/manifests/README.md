# 資訊清單狀態與 Kubernetes 相容性

此目錄包含個別資源的資訊清單和小型範例。**請勿**遞迴套用 `manifests/` 或含有無關資源的目錄。請檢視必要條件，並只套用為叢集選取的檔案。

目標基準版本為 Kubernetes v1.37.1。使用目前的 API 結構描述或映像檔標籤，本身並不能證明控制器或附加元件支援 Kubernetes 1.37。正式環境使用前，請先查閱連結的上游相容性指南。固定的專案版本和原始碼佐證彙整於 [`setup/component-versions.md`](../setup/component-versions.md)。

## 目前或已更新的範例

| 路徑 | 內容與必要條件 | 相容性注意事項 |
| --- | --- | --- |
| `kubedns/coredns.yaml` | 以 Kubernetes v1.37.1 kubeadm 附加元件原始碼為基礎的 CoreDNS v1.14.6。 | 使用 `clusterIP: 10.96.0.10`，也就是 kubeadm 預設值；若使用不同的 Service CIDR，請調整此設定。[上游原始碼](https://github.com/kubernetes/kubernetes/blob/v1.37.1/cluster/addons/dns/coredns/coredns.yaml.base)。 |
| `metrics-server/` | Metrics Server v0.9.0 版本元件；請一併套用這六份資訊清單。 | 上游文件指出相容於 Kubernetes v1.34 以上版本，包括 v1.37。會公開 `metrics.k8s.io/v1beta1`；這是供資源指標和 `kubectl top` 使用，不是完整的監控堆疊。[版本資訊清單](https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.9.0/components.yaml)。 |
| `node-problem-detector/npd.yaml` | Node Problem Detector v1.36.0 原始碼／設定；刻意以已發布的 v1.36.0 映像檔，覆寫版本部署 YAML 中過時的 v0.8.19 固定版本。 | v1.36.0 原始碼支援已設定的 `--config.system-log-monitor` 選項和 JSON 監控路徑；綁定使用 Kubernetes 內建的 `system:node-problem-detector` 角色。登錄中的 OCI 索引提供 linux/amd64 和 linux/arm64。尚未驗證與 Kubernetes v1.37 的相容性。[CLI 原始碼](https://github.com/kubernetes/node-problem-detector/blob/v1.36.0/cmd/options/options.go)、[登錄索引](https://registry.k8s.io/v2/node-problem-detector/node-problem-detector/manifests/v1.36.0)、[Kubernetes 角色原始碼](https://github.com/kubernetes/kubernetes/blob/v1.37.1/plugin/pkg/auth/authorizer/rbac/bootstrappolicy/policy.go)。 |
| `traefik-ingress/traefik-deployment.yaml`、`traefik-ingress/traefik-rbac.yaml` | 使用 Kubernetes Gateway 提供者的 Traefik v3.7.13。這些資訊清單不會公開 Dashboard/API。 | v3.7.13 標記版本的文件指定 Gateway API v1.6.1。在 kind Kubernetes v1.37.1 上使用 v1.6.2 CRD 進行的基本 HTTP/HTTPS冒煙測試已通過；這不代表擴大上游支援範圍，也不代表其他功能已獲得驗證。請參閱[驗證紀錄](../setup/kubernetes-v1.37.md)。Service 使用 `LoadBalancer`，因此需要可正常運作的外部／雲端負載平衡器實作。[提供者文件](https://raw.githubusercontent.com/traefik/traefik/v3.7.13/docs/content/reference/install-configuration/providers/kubernetes/kubernetes-gateway.md)。 |
| `gateway-api/` | 標準範例使用 Gateway API v1.6.2：`GatewayClass`、`Gateway`、`HTTPRoute` 和 `ListenerSet` 都是 `gateway.networking.k8s.io/v1`。安裝順序和各檔案的必要條件，請參閱[目錄 README](gateway-api/README.md)。 | CRD 是 API，不是控制器。請確認 Kubernetes 和控制器同時相容於 v1.36 與 v1.37，並確認各項功能均受支援。`retry-budget.yaml` 使用實驗性 `gateway.networking.x-k8s.io/v1alpha1 XBackendTrafficPolicy`；請安裝實驗性 CRD 以及實作該功能的控制器。已過時的 `CORSPolicy` 範例位於封存目錄。 |
| `ingress-nginx/cert-manager/cluster-issuer.yaml` | 目前的 `cert-manager.io/v1` `ClusterIssuer`，使用 Beta 版 Gateway API HTTP-01 解決器。使用前請替換 `user@example.com`。 | cert-manager 啟動前，需要先安裝 Gateway API CRD 和相容的 Gateway／控制器，並使用 `config.gatewayAPI.enabled=true` 設定 cert-manager。此範例以 `default/example-gateway` 為目標；其他命名空間中的 Certificate 需要 Gateway 監聽器允許來自那些路由命名空間的流量。cert-manager v1.21.2 文件指出支援至 Kubernetes v1.36；尚未驗證是否支援 v1.37。[版本套件](https://github.com/cert-manager/cert-manager/releases/download/v1.21.2/cert-manager.yaml)、[Gateway 解決器需求](https://cert-manager.io/docs/configuration/acme/http01/)。 |
| `test/my-nginx.yaml`、`test/nginx-pod.yaml` | 使用官方 `nginx:1.30.5-alpine3.24` 穩定映像檔標籤的目前 Deployment／Pod 範例。 | 簡單的工作負載範例；請依環境調整資源設定和映像檔原則。[官方映像檔標籤](https://hub.docker.com/_/nginx)。 |
| `test/rolling-update-test/rolling-update-test.yaml` | 目前的 Deployment 結構描述和 selector／標籤。 | 映像檔是私人登錄預留項目。套用前請先建置並發布映像檔，且設定映像檔存取權限；這不是可直接執行的公開映像檔範例。 |

## 歷史資源

已退役元件的資訊清單、過時 API 範例，以及標記為 `HISTORICAL:` 的獨立檔案，已移至 `archive/manifests/` 下，並保留其子目錄。這些檔案不納入目前的 `examples/` 和 `manifests/` 驗證根目錄，不應做為 Kubernetes v1.36/v1.37 的安裝資源。

[封存索引](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/index.md)列出每個舊路徑及其替代路徑，並附上佐證。目前的資源仍保留在此目錄中，包括衍生自 kubeadm 的 CoreDNS 範例，以及 cert-manager ClusterIssuer 範例；後者是否支援 Kubernetes v1.37，仍未經驗證。

## 上游原始碼參考資料

- [Kubernetes v1.37.1 CoreDNS 附加元件原始碼](https://github.com/kubernetes/kubernetes/blob/v1.37.1/cluster/addons/dns/coredns/coredns.yaml.base)
- [Metrics Server v0.9.0 版本](https://github.com/kubernetes-sigs/metrics-server/releases/tag/v0.9.0)
- [Node Problem Detector v1.36.0 部署](https://raw.githubusercontent.com/kubernetes/node-problem-detector/v1.36.0/deployment/node-problem-detector.yaml)、[設定](https://raw.githubusercontent.com/kubernetes/node-problem-detector/v1.36.0/deployment/node-problem-detector-config.yaml)、[RBAC](https://raw.githubusercontent.com/kubernetes/node-problem-detector/v1.36.0/deployment/rbac.yaml)、[CLI 選項](https://github.com/kubernetes/node-problem-detector/blob/v1.36.0/cmd/options/options.go)和[登錄 OCI 索引](https://registry.k8s.io/v2/node-problem-detector/node-problem-detector/manifests/v1.36.0)
- [Gateway API v1.6.2 版本](https://github.com/kubernetes-sigs/gateway-api/releases/tag/v1.6.2)
- [cert-manager v1.21.2 版本](https://github.com/cert-manager/cert-manager/releases/tag/v1.21.2)
- [Traefik v3.7.13 Gateway 提供者文件](https://raw.githubusercontent.com/traefik/traefik/v3.7.13/docs/content/reference/install-configuration/providers/kubernetes/kubernetes-gateway.md)