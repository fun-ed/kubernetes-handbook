# Helm 4

[Helm](https://helm.sh/) 是 Kubernetes 應用包管理與釋出工具。Helm Chart 包含 Kubernetes 資源模板及其預設值，Release 跟蹤 Chart 在指定 namespace 中的安裝設定。

> **當前版本（2026-10-05）**：Helm v4.3.0 是本手冊資料截點前的最新穩定版。Helm 官方相容表列出 v4.3.x 支援 Kubernetes v1.34–v1.37。Helm 4 是客戶端工具，不需要安裝 Tiller。參見[官方釋出頁](https://github.com/helm/helm/releases/tag/v4.3.0)和[版本偏差策略](https://helm.sh/docs/topics/version_skew/)。

## 使用 OCI Chart

安裝 Helm 後確認客戶端版本，並從 OCI registry 安裝固定版本的 Chart。下面的範例參考 [Helm 官方 Quickstart](https://helm.sh/docs/intro/quickstart/)；`podinfo` chart 版本為 6.11.2：

```bash
helm version
helm show values oci://ghcr.io/stefanprodan/charts/podinfo --version 6.11.2
helm upgrade --install my-podinfo \
  oci://ghcr.io/stefanprodan/charts/podinfo \
  --version 6.11.2 \
  --namespace demos --create-namespace
helm list --namespace demos
helm history my-podinfo --namespace demos
```

將經過稽核的自定義設定寫入 `values.yaml` 並與部署原始碼一起管理。更新 Release 前檢查 Chart metadata、依賴、渲染結果、RBAC、映像檔與 namespace：

```bash
helm template my-podinfo \
  oci://ghcr.io/stefanprodan/charts/podinfo \
  --version 6.11.2 --namespace demos -f values.yaml
helm upgrade my-podinfo \
  oci://ghcr.io/stefanprodan/charts/podinfo \
  --version 6.11.2 --namespace demos -f values.yaml
```

需要回復時先檢查歷史 revision，再指定期望版本；解除安裝會刪除 Release 管理的資源：

```bash
helm history my-podinfo --namespace demos
helm rollback my-podinfo <REVISION> --namespace demos
helm uninstall my-podinfo --namespace demos
```

Chart 可來自 OCI registry、傳統 Helm repository、本地目錄或 `.tgz` 包。來源與 Chart 版本應寫入部署設定並經過審查；`helm search hub` 用於發現 Chart，不能替代對維護狀態、權限和渲染結果的稽核。確保 Chart 輸出的是目標 Kubernetes 版本仍支援的 API；Helm 客戶端相容並不代表任意 Chart 都與 v1.37 相容。

## Helm 2 歷史背景

Helm 2 把客戶端與叢集內 Tiller server 分離，由 Tiller 儲存 Release 狀態並以叢集權限建立、更新資源。該架構讓服務端元件持有高權限憑證，也使客戶端和 server release 版本需要協同管理。Helm 3 移除 Tiller，以 Kubernetes Secret 儲存 Release 狀態；Helm 4 延續無 Tiller 的客戶端架構並更新 Chart/API 支援。

舊版教程中的 `helm init`、Tiller RBAC/Deployment、`helm install --name` 以及 `stable/`、`incubator/` repository 均屬 Helm 2 歷史材料，**不要用於新叢集**。舊 Chart 還可能包含已刪除的 Kubernetes API，應按當前 Chart 文件重新評估，不要僅替換 Helm 命令後繼續部署。
