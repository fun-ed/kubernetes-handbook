# Skaffold

[Skaffold](https://skaffold.dev/) 在本地开发循环中构建镜像、部署 Kubernetes 资源并观察代码变化。它没有常驻的集群端控制器。

> **当前版本（2026-10-05）**：v2.25.0 是本手册资料截点前的最新稳定版。官方发布页提供各平台二进制和 SHA-256 校验信息：[Skaffold v2.25.0](https://github.com/GoogleContainerTools/skaffold/releases/tag/v2.25.0)。本次未核实到明确覆盖 Kubernetes v1.37 的官方兼容矩阵。

Linux/macOS 安装示例：

```bash
# Linux amd64
curl -fsSLo skaffold https://storage.googleapis.com/skaffold/releases/v2.25.0/skaffold-linux-amd64
# Apple Silicon macOS: https://storage.googleapis.com/skaffold/releases/v2.25.0/skaffold-darwin-arm64
# 下载后按发布页公布的 SHA-256 值验证对应资产。
chmod +x skaffold
sudo install skaffold /usr/local/bin/skaffold
skaffold version
```

先准备包含 Dockerfile 和 Kubernetes manifest 的应用目录，并确认 `kubectl` 指向可用于开发的集群。运行 `skaffold init` 可根据本地文件生成配置；检查生成的 builder、镜像仓库和部署器设置后，再启动开发循环：

```bash
skaffold init
skaffold dev
```

`skaffold dev` 会监听文件变化并在退出时清理资源。要执行一次构建和部署，可运行 `skaffold run`；先检查 `skaffold.yaml` 中的 namespace、镜像仓库、构建器与 manifest 列表。不要在生产集群中运行开发循环。

本页旧示例使用 Skaffold 早期仓库路径、GCR 测试镜像、Golang 1.9 和未固定的 `latest` 下载地址；这些输出只代表历史测试，不是当前安装或镜像建议。
