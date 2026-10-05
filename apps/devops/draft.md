# Draft

[Draft](https://github.com/Azure/draft) 是 Azure 维护的 Kubernetes 应用开发 CLI，可生成容器构建文件、Kubernetes manifest 或 Helm/Kustomize 项目文件，并为 GitHub Actions 建立工作流。

> **当前版本（2026-10-05）**：Draft v0.17.15 是本手册资料截点前的最新稳定版：[官方发布页](https://github.com/Azure/draft/releases/tag/v0.17.15)。官方 README 目前列出 `brew install draft` 与安装脚本两种方式。使用前请在发布页检查目标平台和校验信息。

## 创建应用脚手架

在应用源码目录中安装 Draft 后，运行交互式生成器：

```bash
brew install draft
draft version
draft create
```

`draft create` 会询问应用语言、镜像和 Kubernetes 部署类型，并在目录中生成所选项目文件。检查 Dockerfile 的基础镜像、Kubernetes 清单中的镜像、权限、资源配置与 Secret 后再提交。不要把生成器输出直接应用到生产集群。

## 生成 CI 工作流与验证

Draft 可以生成 GitHub Actions 工作流，也可以按其包含的规则检查部分 Kubernetes 部署实践：

```bash
draft generate-workflow
draft validate
```

`draft generate-workflow` 生成的 workflow 仍需人工审查权限、OIDC 信任、部署环境、镜像发布和 Secret 配置。`draft validate` 的规则来源于 Azure AKS deployment safeguards，不能替代 Kubernetes API 校验、策略引擎、安全扫描或集群兼容性测试。

## 旧版 Draft 教程说明

本章旧版示例曾介绍 `draft init`、`draft up`、集群内 `draftd`、Helm 2/Tiller 和 `stable/nginx-ingress`。当前 Azure Draft CLI 已采用不同的命令和工作流，旧命令不属于 v0.17.15 的安装步骤；请以 [Draft 官方 README](https://github.com/Azure/draft)和[发布页](https://github.com/Azure/draft/releases/tag/v0.17.15)为准。
