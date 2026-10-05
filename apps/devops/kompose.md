# Kompose

Kompose 将 Docker Compose 文件转换为 Kubernetes manifest。它能帮助迁移基础配置，但不会自动保留 Compose 与 Kubernetes 的所有语义；转换结果必须审查。

> **当前版本（2026-10-05）**：Kompose v1.38.0 是官方发布页在本手册截点前列出的最新稳定版。该发布页提供二进制、各架构下载地址和 SHA-256 校验值：[Kompose v1.38.0](https://github.com/kubernetes/kompose/releases/tag/v1.38.0)。该版本未据此宣称支持 Kubernetes v1.37。

macOS Apple Silicon 安装示例：

```bash
curl -fsSLo kompose \
  https://github.com/kubernetes/kompose/releases/download/v1.38.0/kompose-darwin-arm64
# 下载后按发布页的 SHA-256 值验证资产。
chmod +x kompose
sudo install kompose /usr/local/bin/kompose
kompose version
```

Linux 与 Windows 资产及校验值见官方发布页。下载后先验证对应资产的 SHA-256，再安装。

## 转换 Compose 项目

在含有 `compose.yaml` 的目录中运行 `kompose convert`，先检查生成的 Service、Deployment、ConfigMap、Secret、探针和存储定义，再将输出提交到 Git：

```bash
kompose convert --out manifests/
```

转换器不会替你创建镜像、数据库持久化、Secret 管理、网络策略或云负载均衡。必须先检查生成 YAML 的 API、选择器、镜像、权限和存储，再在测试集群中使用 `kubectl apply -f manifests/`。`kompose up` 会直接向当前 `kubectl` context 部署生成资源，不适合作为无审查的迁移步骤。

旧示例引用 kubernetes-incubator 的下载地址和已经归档的 GCR 测试镜像。它们只用于识别历史 Kompose 输出，不是当前可用的安装或镜像说明。
