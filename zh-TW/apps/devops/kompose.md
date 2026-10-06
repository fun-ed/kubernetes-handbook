# Kompose

Kompose 將 Docker Compose 檔案轉換為 Kubernetes manifest。它能幫助遷移基礎設定，但不會自動保留 Compose 與 Kubernetes 的所有語義；轉換結果必須審查。

> **當前版本（2026-10-05）**：Kompose v1.38.0 是官方釋出頁在本手冊截點前列出的最新穩定版。該釋出頁提供二進位、各架構下載位址和 SHA-256 雜湊值：[Kompose v1.38.0](https://github.com/kubernetes/kompose/releases/tag/v1.38.0)。該版本未據此宣稱支援 Kubernetes v1.37。

macOS Apple Silicon 安裝範例：

```bash
curl -fsSLo kompose \
  https://github.com/kubernetes/kompose/releases/download/v1.38.0/kompose-darwin-arm64
# 下载后按发布页的 SHA-256 值验证资产。
chmod +x kompose
sudo install kompose /usr/local/bin/kompose
kompose version
```

Linux 與 Windows 資產及雜湊值見官方釋出頁。下載後先驗證對應資產的 SHA-256，再安裝。

## 轉換 Compose 專案

在含有 `compose.yaml` 的目錄中執行 `kompose convert`，先檢查生成的 Service、Deployment、ConfigMap、Secret、探針和儲存定義，再將輸出提交到 Git：

```bash
kompose convert --out manifests/
```

轉換器不會替你建立映像檔、資料庫持久化、Secret 管理、網路策略或雲負載平衡。必須先檢查生成 YAML 的 API、選擇器、映像檔、權限和儲存，再在測試叢集中使用 `kubectl apply -f manifests/`。`kompose up` 會直接向當前 `kubectl` context 部署生成資源，不適合作為無審查的遷移步驟。

舊範例引用 kubernetes-incubator 的下載位址和已經歸檔的 GCR 測試映像檔。它們只用於識別歷史 Kompose 輸出，不是當前可用的安裝或映像檔說明。
