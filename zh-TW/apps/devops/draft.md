# Draft

[Draft](https://github.com/Azure/draft) 是 Azure 維護的 Kubernetes 應用開發 CLI，可生成容器建置檔案、Kubernetes manifest 或 Helm/Kustomize 專案檔案，並為 GitHub Actions 建立工作流。

> **當前版本（2026-10-05）**：Draft v0.17.15 是本手冊資料截點前的最新穩定版：[官方釋出頁](https://github.com/Azure/draft/releases/tag/v0.17.15)。官方 README 目前列出 `brew install draft` 與安裝指令碼兩種方式。使用前請在釋出頁檢查目標平台和驗證資訊。

## 建立應用腳手架

在應用原始碼目錄中安裝 Draft 後，執行互動式生成器：

```bash
brew install draft
draft version
draft create
```

`draft create` 會詢問應用語言、映像檔和 Kubernetes 部署型別，並在目錄中生成所選專案檔案。檢查 Dockerfile 的基礎映像檔、Kubernetes 清單中的映像檔、權限、資源設定與 Secret 後再提交。不要把生成器輸出直接應用到生產叢集。

## 生成 CI 工作流與驗證

Draft 可以生成 GitHub Actions 工作流，也可以按其包含的規則檢查部分 Kubernetes 部署實踐：

```bash
draft generate-workflow
draft validate
```

`draft generate-workflow` 生成的 workflow 仍需人工審查權限、OIDC 信任、部署環境、映像檔釋出和 Secret 設定。`draft validate` 的規則來源於 Azure AKS deployment safeguards，不能替代 Kubernetes API 驗證、策略引擎、安全掃描或叢集相容性測試。

## 舊版 Draft 教程說明

本章舊版範例曾介紹 `draft init`、`draft up`、叢集內 `draftd`、Helm 2/Tiller 和 `stable/nginx-ingress`。當前 Azure Draft CLI 已採用不同的命令和工作流，舊命令不屬於 v0.17.15 的安裝步驟；請以 [Draft 官方 README](https://github.com/Azure/draft)和[釋出頁](https://github.com/Azure/draft/releases/tag/v0.17.15)為準。
