# 安裝 kubectl

`kubectl` 是 Kubernetes 命令列用戶端。本頁範例固定使用 v1.37.1；下載對應作業系統及架構的官方二進位檔，並驗證 checksum。官方[安裝說明](https://kubernetes.io/docs/tasks/tools/install-kubectl/)提供 Windows、macOS、Linux 的套件管理器及替代安裝方式。

## Linux 範例

按目標主機架構設定 `ARCH`（常見為 `amd64` 或 `arm64`），再下載 v1.37.1：

```bash
VERSION=v1.37.1
ARCH=amd64
curl -LO "https://dl.k8s.io/release/${VERSION}/bin/linux/${ARCH}/kubectl"
curl -LO "https://dl.k8s.io/release/${VERSION}/bin/linux/${ARCH}/kubectl.sha256"
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
kubectl version --client
```

macOS 和 Windows 的官方二進位下載路徑分別使用 `darwin`、`windows` 及相應 CPU 架構；完整命令見 [Install kubectl on macOS](https://kubernetes.io/docs/tasks/tools/install-kubectl-macos/) 和 [Install kubectl on Windows](https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/)。macOS 的驗證命令與 Linux 不同，請按對應平台文件執行。

## 版本選擇

kubectl 與 API server 通常保持同一 minor 版本。官方版本偏差策略允許 kubectl 比 API server 新或舊一個 minor，但高可用叢集混跑多個 API server 版本時需同時滿足混合版本限制。詳見 [version-skew policy](https://kubernetes.io/releases/version-skew-policy/)。

## kubectl 外掛

[krew](https://krew.sigs.k8s.io/) 是社群外掛管理器，不屬於 Kubernetes 核心工具。請依照 [Krew 當前安裝步驟](https://krew.sigs.k8s.io/docs/user-guide/setup/install/)為當前 OS/架構安裝，避免從舊的固定 `krew/v0.2.1` URL 下載。安裝外掛前應逐個審閱其維護狀態、權限和供應鏈來源。
