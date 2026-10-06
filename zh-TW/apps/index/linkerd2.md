# Linkerd

Linkerd 是 Kubernetes 服務網格。早期 Linkerd 2.x 章節中的 `linkerd install` 輸出、Controller workload、Dashboard 路徑、Emojivoto 清單與效能數字來自數年前的版本，不是當前安裝說明。

> **釋出狀態（截至 2026-10-05）**：獨立 Linkerd OSS 穩定版自 2024 年 2 月後沒有新的穩定 release；GitHub 的 `stable-2.20` 是 Git milestone/tag，不代表可下載的穩定發行包。當前可見的 OSS 發行線為 edge 26.9.3，不應稱為生產穩定版。需要生產支援時，核對官方當前釋出說明或單獨評估提供穩定發行版與支援服務的供應商；不要照抄本頁舊 `linkerd install` 命令。

來源：[Linkerd OSS releases](https://github.com/linkerd/linkerd2/releases)、[官方安裝文件](https://linkerd.io/2/getting-started/)、[官方概覽](https://linkerd.io/2/overview/)。本次沒有找到 OSS edge/stable 對 Kubernetes v1.37 的明確相容宣告，因此不推薦在本手冊目標叢集 v1.37.1 上部署。

## 評估前檢查

1. 確認所採用的發行版確實有可驗證的 release artifact；不要把 Git milestone 或 nightly/edge build 當作穩定版。
2. 逐項核對發行說明中的 Kubernetes、CNI、核心、代理注入和 upgrade 支援範圍。
3. 在測試叢集驗證 CLI、控制平面、資料平面代理、證書輪換和解除安裝流程，再製定生產升級及回復方案。

本頁舊的叢集清單、`deployment.extensions` 輸出、動態下載的 Emojivoto YAML、舊指標和 tap 範例只作為 Linkerd 2.x 歷史演示保留；不要對當前叢集執行。
