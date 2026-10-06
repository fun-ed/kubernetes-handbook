# Spinnaker

[Spinnaker](https://spinnaker.io/) 是持續交付平台，可將應用程式發布至多種雲端平台。上游發布資料截至 **2026-10-05** 的最高穩定版本為 **2026.3.0**（[官方 release](https://github.com/spinnaker/spinnaker/releases/tag/spinnaker-release-2026.3.0)）。本次未找到該版本明確支援 Kubernetes v1.37 的官方相容性聲明；版本發布不代表目標叢集已獲支援或測試。

Spinnaker 的元件、持續性儲存、驗證與雲端供應商設定，須依照[官方文件](https://spinnaker.io/docs/)及目標環境需求評估。本頁不提供通用安裝命令，也不宣稱已通過 v1.37 執行驗證。正式部署前應確認專案維護狀態、受支援的部署方式及相關雲端服務設定。

舊版 Helm 2 的 `stable` chart 安裝步驟使用已退役的 chart 儲存庫和舊版 Helm 語法，已移至[歷史封存](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/zh-TW/apps/devops/spinnaker.md)，不得作為目前的部署說明。
