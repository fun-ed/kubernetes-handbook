# Argo Workflows

Argo Workflows 是 Kubernetes 原生工作流引擎。它使用 `Workflow` CRD 描述任务 DAG、并行步骤、产物和重试策略。Argo Workflows 与 Argo CD 是不同项目，本章只介绍 Workflows。

> **当前版本（2026-10-05）**：v4.1.4 是本手册资料截点前的最新稳定版。官方发布页提供对应版本的 CLI 和控制器安装文件：[v4.1.4 release](https://github.com/argoproj/argo-workflows/releases/tag/v4.1.4)。本次未找到官方材料明确声明该版本支持 Kubernetes v1.37；使用前请核对上游兼容说明。

## 安装测试环境

官方 Quick Start 明确说明下面是试用配置，不适合生产。它从固定版本发布页安装 controller，并只在 `argo` namespace 中创建资源：

```bash
ARGO_WORKFLOWS_VERSION=v4.1.4
kubectl create namespace argo
kubectl apply --namespace argo \
  --filename "https://github.com/argoproj/argo-workflows/releases/download/${ARGO_WORKFLOWS_VERSION}/quick-start-minimal.yaml"
```

安装 CLI（以下为 Linux/macOS amd64）：

```bash
ARGO_WORKFLOWS_VERSION=v4.1.4
ARGO_OS=linux
ARGO_ARCH=amd64
curl -fsSLO "https://github.com/argoproj/argo-workflows/releases/download/${ARGO_WORKFLOWS_VERSION}/argo-${ARGO_OS}-${ARGO_ARCH}.gz"
gunzip "argo-${ARGO_OS}-${ARGO_ARCH}.gz"
chmod +x "argo-${ARGO_OS}-${ARGO_ARCH}"
sudo install "argo-${ARGO_OS}-${ARGO_ARCH}" /usr/local/bin/argo
argo version
```

其他平台资产见发布页。生产安装前，按[官方安装文档](https://argo-workflows.readthedocs.io/en/latest/installation/)选择部署方式、持久化与身份验证配置，并为工作流配置专用 ServiceAccount 和最小 RBAC。不要给默认 ServiceAccount 绑定 `cluster-admin`。

## 提交和查看 Workflow

用与 controller 相同的 v4.1.4 tag 中的示例提交工作流：

```bash
argo submit --namespace argo --watch \
  https://raw.githubusercontent.com/argoproj/argo-workflows/v4.1.4/examples/hello-world.yaml
argo list --namespace argo
argo logs --namespace argo @latest
```

Workflow 是 Kubernetes 自定义资源。下面摘录自同一 tag 的 [hello-world.yaml](https://raw.githubusercontent.com/argoproj/argo-workflows/v4.1.4/examples/hello-world.yaml)：

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: hello-world-
spec:
  entrypoint: whalesay
  templates:
    - name: whalesay
      container:
        image: busybox:1.36.1
        command: [echo]
        args: ["hello world"]
```

样例镜像仅用于演示；生产工作流应使用组织批准、固定版本或 digest 的镜像，并按任务权限限制 ServiceAccount、Secret 与网络访问。

## 生产资料

- [Argo Workflows 安装指南](https://argo-workflows.readthedocs.io/en/latest/installation/)
- [Workflow 规范](https://argo-workflows.readthedocs.io/en/latest/workflow-concepts/)
- [Argo Workflows v4.1.4 发布说明](https://github.com/argoproj/argo-workflows/releases/tag/v4.1.4)

旧章中的 Argo 2.0/2.1 CLI、`argo-ci` chart、Tiller、`stable/minio` 和默认 ServiceAccount 的集群管理员绑定已移除，不再作为安装建议。
