# Spinnaker

[Spinnaker](https://spinnaker.io/) 是持续交付平台，可将应用发布到多种云平台。上游发布资料截至 **2026-10-05** 的最高稳定版本为 **2026.3.0**（[官方 release](https://github.com/spinnaker/spinnaker/releases/tag/spinnaker-release-2026.3.0)）。本次未找到该版本明确支持 Kubernetes v1.37 的官方兼容声明；版本发布不代表目标集群已获支持或测试。

Spinnaker 的组件、持久化、认证与云提供者配置须依照[官方文档](https://spinnaker.io/docs/)及目标环境要求评估。本页不提供通用安装命令，也不宣称对 v1.37 的运行认证。生产部署前应确认项目维护状态、受支持的部署方式及相关云服务配置。

旧版 Helm 2 的 `stable` chart 安装步骤使用已退役的 chart 仓库和旧 Helm 语法，已移至[历史归档](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/apps/devops/spinnaker.md)，不得作为当前部署说明。
