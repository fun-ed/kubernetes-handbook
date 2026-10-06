# API Aggregation

API Aggregation 透過 kube-apiserver 的 aggregation layer 將額外 API group/version 路由到 extension API server。與 CRD 不同，APIService 代理外部 API 服務；適用於需要自定義 API 伺服器邏輯、儲存或不適合宣告式 CRD 的場景。普通宣告式資源通常優先使用 CRD。

## Kubernetes v1.37.1 設定要點

* `APIService` 使用穩定 API `apiregistration.k8s.io/v1`，名稱格式為 `<version>.<group>`。
* Extension API server 透過 Service 暴露 HTTPS 服務；`APIService.spec.caBundle` 必須信任該服務證書的簽發 CA。確保 Service 有可用 Endpoints，且 kube-apiserver 到服務的網路可達。
* 自託管 kube-apiserver 需正確設定 front-proxy/requestheader 證書與信任鏈；託管叢集通常由平台管理這些元件級設定，不要照抄任意控制平面 flags。
* 資源的認證、授權和 admission 仍由 API server / extension API server 各自的設定決定；APIService 不會自動給使用者授予權限。

下面的例子演示一個 `example.com/v1` APIService。將 `caBundle` 替換為 extension API server CA 證書 PEM 內容的 base64 編碼，並確認服務的 SAN 與 Kubernetes Service DNS 名稱匹配。

```yaml
apiVersion: apiregistration.k8s.io/v1
kind: APIService
metadata:
  name: v1.example.com
spec:
  group: example.com
  version: v1
  groupPriorityMinimum: 1000
  versionPriority: 15
  service:
    namespace: example
    name: example-apiserver
    port: 443
  caBundle: BASE64_ENCODED_CA_CERT
```

```bash
kubectl apply -f apiservice.yaml
kubectl get apiservice v1.example.com
kubectl get --raw /apis/example.com/v1
```

APIService 必須顯示 `Available=True`，並能透過 discovery endpoint 返回 API resource list。完整步驟見 [設定 API Aggregation layer](https://kubernetes.io/docs/tasks/extend-kubernetes/configure-aggregation-layer/) 和 [部署 extension API server](https://kubernetes.io/docs/tasks/extend-kubernetes/setup-extension-api-server/)。

## API 伺服器開發

API server 與控制器應使用符合目標 Kubernetes 版本的 client-go / apimachinery 依賴和 Go 工具鏈。可參考上游 [sample-apiserver](https://github.com/kubernetes/sample-apiserver)；不要直接複製舊 apiserver-builder、glide 依賴和已歸檔 incubator 範例作為當前建置流程。

> 歷史說明：早期 Aggregation 設定會在自託管 kube-apiserver 上設定 `--requestheader-*` 與 proxy-client 證書 flags。當前部署必須遵循對應發行版的 aggregation layer 設定指南，正確建立 front-proxy 證書信任鏈後再註冊 APIService；不能只憑一個 Service 和 `APIService` 清單完成安全設定。
