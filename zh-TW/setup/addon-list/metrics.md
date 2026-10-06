# Metrics API 與 metrics-server

metrics-server 收集 kubelet 的資源指標並向 Kubernetes Metrics API 提供短期、近實時用量，主要服務 `kubectl top` 和基於資源指標的 HPA。它不是長期時序資料庫、日誌平台或生產可觀測性系統。長期監控請看[監控方案](monitor.md)。

## 安裝 metrics-server 0.9.0

截至 2026-10-05，上游穩定版為 **0.9.0**，相容矩陣列明支援 Kubernetes 1.34+。先確認節點可從 metrics-server 連線 kubelet，證書和位址符合上游要求，再安裝固定 release manifest：

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.9.0/components.yaml
kubectl -n kube-system rollout status deployment/metrics-server
kubectl get apiservice v1beta1.metrics.k8s.io
kubectl get --raw /apis/metrics.k8s.io
kubectl top nodes
kubectl top pods -A
```

釋出源：[metrics-server v0.9.0 release](https://github.com/kubernetes-sigs/metrics-server/releases/tag/v0.9.0)、[上游安裝與相容矩陣](https://github.com/kubernetes-sigs/metrics-server#readme)。升級前逐項檢查證書、kubelet TLS、網路可達性及 HA 設定，不要為了讓 APIService 變為 Available 而關閉 TLS 驗證或複製舊的 Docker 防火牆修改。

## `metrics.k8s.io/v1` 與後端

Kubernetes Metrics API 的版本生命週期與 metrics-server 後端的實作情況不同。即使叢集/API 文件中的 `metrics.k8s.io/v1` 已 GA，聚合 API server 也不會替後端自動轉換或產生該版本。metrics-server 0.9.0 上游 `components.yaml` 註冊的是 `v1beta1.metrics.k8s.io`，相容矩陣也只承諾 `metrics.k8s.io/v1beta1`。因此，部署 v0.9.0 時應以實際提供的 v1beta1 API discovery 為準；若應用要求 v1，必須先確認所用後端明確實作並發布該版本。

驗證 APIService 後可檢查 discovery：

```bash
kubectl get --raw /apis/metrics.k8s.io/v1beta1
kubectl get apiservice v1beta1.metrics.k8s.io -o wide
```

metrics-server 官方明確指出其設計目標不是通用監控解決方案；不要將 Heapster 或舊版 metrics-server 的安裝教程當作當前生產指標管道。