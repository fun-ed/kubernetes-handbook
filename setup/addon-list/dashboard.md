# Kubernetes Dashboard 状态

**Kubernetes Dashboard 上游项目已于 2026-01-21 归档**，仓库位于 `kubernetes-retired` 组织下，不再是应安装到新 Kubernetes v1.37 集群的维护中组件。参见[归档仓库](https://github.com/kubernetes-retired/dashboard)。本页不提供旧版本 manifest、静态 ServiceAccount token 或 Helm 安装命令。

如果需要 Web UI，可评估仍维护的 [Headlamp](https://headlamp.dev/) 项目，并按它的当前安装指南、版本兼容资料和组织的认证/授权要求部署。访问集群管理 UI 应通过正式身份认证并遵守最小权限；不要使用历史教程中长期有效的管理员 bearer token，也不要向公网暴露未受保护的 Dashboard。

> **历史说明：** 本仓库旧页面所记录的 Dashboard v2.0.0-beta8 是多年以前的预览版说明。它仅解释旧集群管理界面的历史，不适用于 Kubernetes v1.37.1。