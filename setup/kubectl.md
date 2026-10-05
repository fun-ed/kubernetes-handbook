# 安装 kubectl

`kubectl` 是 Kubernetes 命令行客户端。本页示例固定到 v1.37.1；下载对应 OS/架构的官方二进制并校验 checksum。官方安装页提供 Windows、macOS、Linux 的包管理器与替代安装方法：<https://kubernetes.io/docs/tasks/tools/install-kubectl/>。

## Linux 示例

按目标主机架构设置 `ARCH`（常见为 `amd64` 或 `arm64`），再下载 v1.37.1：

```bash
VERSION=v1.37.1
ARCH=amd64
curl -LO "https://dl.k8s.io/release/${VERSION}/bin/linux/${ARCH}/kubectl"
curl -LO "https://dl.k8s.io/release/${VERSION}/bin/linux/${ARCH}/kubectl.sha256"
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
kubectl version --client
```

macOS 和 Windows 的官方二进制下载路径分别使用 `darwin`、`windows` 及相应 CPU 架构；完整命令见 [Install kubectl on macOS](https://kubernetes.io/docs/tasks/tools/install-kubectl-macos/) 和 [Install kubectl on Windows](https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/)。macOS 的校验命令与 Linux 不同，请按对应平台文档执行。

## 版本选择

kubectl 与 API server 通常保持同一 minor 版本。官方版本偏差策略允许 kubectl 比 API server 新或旧一个 minor，但高可用集群混跑多个 API server 版本时需同时满足混合版本限制。详见 [version-skew policy](https://kubernetes.io/releases/version-skew-policy/)。

## kubectl 插件

[krew](https://krew.sigs.k8s.io/) 是社区插件管理器，不属于 Kubernetes 核心工具。请依照 [Krew 当前安装步骤](https://krew.sigs.k8s.io/docs/user-guide/setup/install/)为当前 OS/架构安装，避免从旧的固定 `krew/v0.2.1` URL 下载。安装插件前应逐个审阅其维护状态、权限和供应链来源。
