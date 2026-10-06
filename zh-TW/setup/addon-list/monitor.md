# Kubernetes 叢集監控

截至 2026-10-05，Prometheus 社群 chart 儲存庫釋出的 `kube-prometheus-stack` 最新穩定 chart 為 **91.9.0**（2026-10-02 釋出）。它打包 Prometheus Operator、Prometheus、Alertmanager、node-exporter、kube-state-metrics 及預設 Grafana 設定，是需要 Prometheus 生態時可評估的一種方案；chart 版本並不等同於 Kubernetes 相容認證。

使用 Helm 4.3.0 客戶端、固定 chart 版本安裝：

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --version 91.9.0 --namespace monitoring --create-namespace
```

來源：[chart 91.9.0 release](https://github.com/prometheus-community/helm-charts/releases/tag/kube-prometheus-stack-91.9.0)、[chart README](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)、[Helm 安裝與版本說明](https://helm.sh/docs/intro/install/)。部署前檢查該 chart release 對 Kubernetes v1.37 的支援狀態、Helm 4 相容性、CRD 變更和儲存設定；本儲存庫不把 chart 最新發布誤稱為已驗證的 Kubernetes 相容組合。生產環境先閱讀 chart 的 values、資源需求、認證、持久化、網路暴露和升級/回復文件。

metrics-server 不是該監控棧的替代品：它面向 `kubectl top` 和 HPA 的即時 Metrics API。Prometheus/長期指標、日誌、trace 及告警各需獨立的資料保留與安全設計。

> **歷史說明：** Heapster 已退役並歸檔，舊頁面內 Heapster、cAdvisor、Docker daemon flag、早期 Kubernetes Dashboard 及過期 chart 範例均不適用於 v1.37.1。本頁不保留可以誤執行的舊安裝命令。