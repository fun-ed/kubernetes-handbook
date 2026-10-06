# Skaffold

[Skaffold](https://skaffold.dev/) 在本地開發迴圈中建置映像檔、部署 Kubernetes 資源並觀察程式碼變化。它沒有常駐的叢集端控制器。

> **當前版本（2026-10-05）**：v2.25.0 是本手冊資料截點前的最新穩定版。官方釋出頁提供各平台的二進位檔和 SHA-256 雜湊值：[Skaffold v2.25.0](https://github.com/GoogleContainerTools/skaffold/releases/tag/v2.25.0)。本次未核實到明確覆蓋 Kubernetes v1.37 的官方相容矩陣。

Linux/macOS 安裝範例：

```bash
# Linux amd64
curl -fsSLo skaffold https://storage.googleapis.com/skaffold/releases/v2.25.0/skaffold-linux-amd64
# Apple Silicon macOS: https://storage.googleapis.com/skaffold/releases/v2.25.0/skaffold-darwin-arm64
# 下载后按发布页公布的 SHA-256 值验证对应资产。
chmod +x skaffold
sudo install skaffold /usr/local/bin/skaffold
skaffold version
```

先準備包含 Dockerfile 和 Kubernetes manifest 的應用目錄，並確認 `kubectl` 指向可用於開發的叢集。執行 `skaffold init` 可根據本地檔案生成設定；檢查生成的 builder、映像檔登錄站和部署器設定後，再啟動開發迴圈：

```bash
skaffold init
skaffold dev
```

`skaffold dev` 會監聽檔案變化並在退出時清理資源。要執行一次建置和部署，可執行 `skaffold run`；先檢查 `skaffold.yaml` 中的 namespace、映像檔登錄站、建置器與 manifest 列表。不要在生產叢集中執行開發迴圈。

本頁舊範例使用 Skaffold 早期儲存庫路徑、GCR 測試映像檔、Golang 1.9 和未固定的 `latest` 下載位址；這些輸出只代表歷史測試，不是當前安裝或映像檔建議。
