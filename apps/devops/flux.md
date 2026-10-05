# Flux GitOps

Flux 是 Kubernetes 的 GitOps 持续交付工具，使用 Kubernetes 自定义资源持续协调 Git、OCI、Helm 等来源中的期望状态。

> **当前版本（2026-10-05）**：Flux CLI v2.9.6 是本手册资料截点前的最新稳定版。发布页：[fluxcd/flux2 v2.9.6](https://github.com/fluxcd/flux2/releases/tag/v2.9.6)。本次未找到官方兼容矩阵明确声明 v2.9.6 支持 Kubernetes v1.37；部署前请核对[官方安装文档](https://fluxcd.io/flux/installation/)和目标集群支持范围。

## 安装固定版本 CLI

macOS Apple Silicon 示例。Linux、Intel macOS 与 Windows 的资产名称及校验值见同一发布页：

```bash
curl -fsSLo flux.tar.gz \
  https://github.com/fluxcd/flux2/releases/download/v2.9.6/flux_2.9.6_darwin_arm64.tar.gz
# 下载并按发布页公布的值验证 SHA-256 后，再安装。
tar -xzf flux.tar.gz flux
sudo install flux /usr/local/bin/flux
flux version
```

## Bootstrap GitOps

配置好 `kubectl` 后，先检查集群和 CRD，再按 Git 平台的[官方 Bootstrap 指南](https://fluxcd.io/flux/installation/bootstrap/)将控制器引导到专用基础设施仓库：

```bash
flux check --pre
flux bootstrap github \
  --owner=<github-user-or-org> \
  --repository=<cluster-config-repo> \
  --branch=main \
  --path=clusters/production
flux check
```

通过受控的 Secret store 或安全 shell 注入 GitHub token 和仓库写权限；不要把 token 写入文档、命令历史或 Git。`flux bootstrap` 会在集群中安装控制器，并把集群配置提交到仓库。修改仓库前，确认 `--path` 与环境隔离方式符合团队策略。

## 检查与升级

```bash
flux get all --all-namespaces
flux logs --all-namespaces --level=error
kubectl get gitrepositories,kustomizations,helmreleases --all-namespaces
```

升级时遵循 [Flux 官方升级流程](https://fluxcd.io/flux/installation/upgrade/)，不要只替换 CLI 而忽略集群控制器。
