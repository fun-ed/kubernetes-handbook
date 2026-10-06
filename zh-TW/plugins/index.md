# Kubernetes外掛

Kubernetes在設計之初就充分考慮了[可擴充套件性](https://kubernetes.io/docs/concepts/overview/extending/)，很多資源或操作都可以透過外掛來[自由擴充套件](https://kubernetes.io/docs/concepts/overview/extending/)，比如認證授權、網路、Volume、容器執行引擎、排程等。

## Kubernetes v1.37.1 部署注意事項

本目錄保留的外掛資料橫跨多個 Kubernetes 版本。部署前先檢查相關外掛的維護狀態、發行版相容矩陣以及其所依賴的 Kubernetes API；舊設定中的 beta API、舊 CRD schema、舊 Admission 設定或外掛端點不能僅透過改版本號繼續使用。

容器執行時和 CNI 有獨立的當前版本及設定邊界，分別見 [CRI 執行時概覽](../extension/cri/README.md)和[網路外掛概覽](../extension/network/README.md)。認證、授權、准入和擴充套件 API 也應優先按 v1.37 官方文件設定。
