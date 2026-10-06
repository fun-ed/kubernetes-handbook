# Flux GitOps

Flux 是 Kubernetes 的 GitOps 持續交付工具，使用 Kubernetes 自定義資源持續協調 Git、OCI、Helm 等來源中的期望狀態。

> **當前版本（2026-10-05）**：Flux CLI v2.9.6 是本手冊資料截點前的最新穩定版。釋出頁：[fluxcd/flux2 v2.9.6](https://github.com/fluxcd/flux2/releases/tag/v2.9.6)。本次未找到官方相容矩陣明確宣告 v2.9.6 支援 Kubernetes v1.37；部署前請核對[官方安裝文件](https://fluxcd.io/flux/installation/)和目標叢集支援範圍。

## 安裝固定版本 CLI

macOS Apple Silicon 範例。Linux、Intel macOS 與 Windows 的資產名稱及雜湊值見同一釋出頁：

```bash
curl -fsSLo flux.tar.gz \
  https://github.com/fluxcd/flux2/releases/download/v2.9.6/flux_2.9.6_darwin_arm64.tar.gz
# 下载并按发布页公布的值验证 SHA-256 后，再安装。
tar -xzf flux.tar.gz flux
sudo install flux /usr/local/bin/flux
flux version
```

## Bootstrap GitOps

設定好 `kubectl` 後，先檢查叢集和 CRD，再按 Git 平台的[官方 Bootstrap 指南](https://fluxcd.io/flux/installation/bootstrap/)將控制器引導到專用基礎設施儲存庫：

```bash
flux check --pre
flux bootstrap github \
  --owner=<github-user-or-org> \
  --repository=<cluster-config-repo> \
  --branch=main \
  --path=clusters/production
flux check
```

透過受控的 Secret store 或安全 shell 注入 GitHub token 和儲存庫寫入權限；不要把 token 寫入文件、命令歷史或 Git。`flux bootstrap` 會在叢集中安裝控制器，並把叢集設定提交到儲存庫。修改儲存庫前，確認 `--path` 與環境隔離方式符合團隊策略。

## 檢查與升級

```bash
flux get all --all-namespaces
flux logs --all-namespaces --level=error
kubectl get gitrepositories,kustomizations,helmreleases --all-namespaces
```

升級時遵循 [Flux 官方升級流程](https://fluxcd.io/flux/installation/upgrade/)，不要只替換 CLI 而忽略叢集控制器。
