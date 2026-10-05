# Helm 4

[Helm](https://helm.sh/) 是 Kubernetes 应用包管理与发布工具。Helm Chart 包含 Kubernetes 资源模板及其默认值，Release 跟踪 Chart 在指定 namespace 中的安装配置。

> **当前版本（2026-10-05）**：Helm v4.3.0 是本手册资料截点前的最新稳定版。Helm 官方兼容表列出 v4.3.x 支持 Kubernetes v1.34–v1.37。Helm 4 是客户端工具，不需要安装 Tiller。参见[官方发布页](https://github.com/helm/helm/releases/tag/v4.3.0)和[版本偏差策略](https://helm.sh/docs/topics/version_skew/)。

## 使用 OCI Chart

安装 Helm 后确认客户端版本，并从 OCI registry 安装固定版本的 Chart。下面的示例参考 [Helm 官方 Quickstart](https://helm.sh/docs/intro/quickstart/)；`podinfo` chart 版本为 6.11.2：

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

将经过审核的自定义配置写入 `values.yaml` 并与部署源码一起管理。更新 Release 前检查 Chart metadata、依赖、渲染结果、RBAC、镜像与 namespace：

```bash
helm template my-podinfo \
  oci://ghcr.io/stefanprodan/charts/podinfo \
  --version 6.11.2 --namespace demos -f values.yaml
helm upgrade my-podinfo \
  oci://ghcr.io/stefanprodan/charts/podinfo \
  --version 6.11.2 --namespace demos -f values.yaml
```

需要回滚时先检查历史 revision，再指定期望版本；卸载会删除 Release 管理的资源：

```bash
helm history my-podinfo --namespace demos
helm rollback my-podinfo <REVISION> --namespace demos
helm uninstall my-podinfo --namespace demos
```

Chart 可来自 OCI registry、传统 Helm repository、本地目录或 `.tgz` 包。来源与 Chart 版本应写入部署配置并经过审查；`helm search hub` 用于发现 Chart，不能替代对维护状态、权限和渲染结果的审核。确保 Chart 输出的是目标 Kubernetes 版本仍支持的 API；Helm 客户端兼容并不代表任意 Chart 都与 v1.37 兼容。

## Helm 2 历史背景

Helm 2 把客户端与集群内 Tiller server 分离，由 Tiller 保存 Release 状态并以集群权限创建、更新资源。该架构让服务端组件持有高权限凭据，也使客户端和 server release 版本需要协同管理。Helm 3 移除 Tiller，以 Kubernetes Secret 存储 Release 状态；Helm 4 延续无 Tiller 的客户端架构并更新 Chart/API 支持。

旧版教程中的 `helm init`、Tiller RBAC/Deployment、`helm install --name` 以及 `stable/`、`incubator/` repository 均属 Helm 2 历史材料，**不要用于新集群**。旧 Chart 还可能包含已删除的 Kubernetes API，应按当前 Chart 文档重新评估，不要仅替换 Helm 命令后继续部署。
