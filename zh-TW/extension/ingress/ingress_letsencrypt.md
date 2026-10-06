# HTTPS 證書與 ACME（Let's Encrypt）

> **本頁舊版安裝教程已停用。** 原例使用已歸檔的 ingress-nginx、Helm `stable` 儲存庫、`extensions/v1beta1` Ingress、舊 cert-manager annotations 和舊 CRD 安裝方式；這些命令和清單不適用於 Kubernetes v1.37.1，不能只改 API 字串後繼續使用。

## Kubernetes v1.37.1 相容性（2026-10-05）

* ingress-nginx 已於 2026-03-24 歸檔，維護和安全修復已結束；不要用於新叢集。
* 當前 cert-manager 穩定版為 [v1.21.2](https://github.com/cert-manager/cert-manager/releases/tag/v1.21.2)，但其官方支援/測試矩陣只列 Kubernetes 1.33–1.36，沒有列出 v1.37。本文不提供在 v1.37.1 上安裝該版本的生產命令。
* 新的 HTTPS 入口可評估 [Traefik v3.7.13 + Gateway API Standard v1.6.1](service-discovery-and-load-balancing.md)。Traefik 與 Gateway API 的版本組合必須按該釋出版的官方文件固定。

相容性來源：[cert-manager 支援版本矩陣](https://cert-manager.io/docs/releases/#currently-supported-releases)、[Traefik Gateway API 當前部署範例](service-discovery-and-load-balancing.md)、[Gateway API v1.6.1](https://github.com/kubernetes-sigs/gateway-api/releases/tag/v1.6.1)。

## ACME 和 cert-manager 的當前介面

在 cert-manager 明確支援的 Kubernetes 版本上，使用 `cert-manager.io/v1` 的 `Issuer`/`ClusterIssuer`、`Certificate` 和當前 Gateway API solver 設定；不要使用舊的 `certmanager.k8s.io` annotations、`kubernetes.io/tls-acme` 或手動下載舊 CRD 的步驟。

cert-manager 的 Gateway API solver 自 v1.15 起可用。當前官方安裝指南使用 OCI Helm chart，Gateway API CRD 應先安裝，再設定 controller 的 `config.gatewayAPI.enabled: true`；CRD 變更後，若 cert-manager 已執行，應按文件重啟相關 controller。完整設定和範例見 [cert-manager HTTP-01 文件](https://cert-manager.io/docs/configuration/acme/http01/)。

ACME HTTP-01 要求公網 DNS 指向入口位址、TCP 80 能到達 challenge route，並且 Gateway listener 允許 route 所在 namespace。HTTPS 服務還需要讓 Gateway 引用同 namespace 中的 TLS Secret。請按實際 Gateway listener 和 cert-manager 支援矩陣驗證這些條件；測試時先使用 Let's Encrypt staging endpoint，避免觸及生產簽發限額。

## 歷史範例

舊 NGINX Ingress、Dashboard Basic Auth、`extensions/v1beta1` 後端欄位及動態 `master` ClusterIssuer YAML 已移除。Ingress API v1 的欄位形狀並不足以證明某個舊 Controller、annotation 或 cert-manager 版本相容 Kubernetes v1.37。
