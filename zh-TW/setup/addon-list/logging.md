# 叢集日誌

Kubernetes 不會自動部署集中式日誌後端，也不會預設在每個節點安裝 Fluentd。應用通常把日誌寫到標準輸出/錯誤，再由節點級日誌代理收集並轉發到叢集外或集中的日誌儲存與查詢系統。選擇代理、後端和部署方式時，應核對其當前 Kubernetes、節點作業系統及執行時支援，並依照該專案的官方文件設定存取權限和保留策略。

- [Kubernetes 叢集日誌架構](https://kubernetes.io/docs/concepts/cluster-administration/logging/)
- [Kubernetes 日誌文件](https://kubernetes.io/docs/tasks/debug/)

> **歷史說明：** 本頁舊版曾介紹 `cluster/kube-up.sh`、由 Kubernetes 儲存庫提供的 Fluentd/Elasticsearch/Kibana manifests、`beta.kubernetes.io/fluentd-ds-ready` 標籤，以及將 `kubectl proxy` 綁定到 `0.0.0.0` 的存取方法。這些指令碼、標籤和設定並非 v1.37.1 的受支援部署方案；不要應用舊 manifest 或公開 API 代理。舊 ELK 介紹只作歷史背景。

部署前確認日誌代理需要的節點權限、Secret/RBAC、資料出口和資源限制，並驗證日誌中不含不應收集的敏感資訊。不要將日誌後端直接暴露到不可信網路。
