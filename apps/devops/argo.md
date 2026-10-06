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
        image: busybox:1.37.0
        command: [echo]
        args: ["hello world"]
```

样例镜像仅用于演示；生产工作流应使用组织批准、固定版本或 digest 的镜像，并按任务权限限制 ServiceAccount、Secret 与网络访问。

## 生产资料

- [Argo Workflows 安装指南](https://argo-workflows.readthedocs.io/en/latest/installation/)
- [Workflow 规范](https://argo-workflows.readthedocs.io/en/latest/workflow-concepts/)
- [Argo Workflows v4.1.4 发布说明](https://github.com/argoproj/argo-workflows/releases/tag/v4.1.4)

旧章中的 Argo 2.0/2.1 CLI、`argo-ci` chart、Tiller、`stable/minio` 和默认 ServiceAccount 的集群管理员绑定已移除，不再作为安装建议。

## Dedicated workflow identity and permissions

The quick-start bundle is explicitly for evaluation, not production. Workflow pods use `spec.serviceAccountName`; if omitted, they use the namespace's `default` ServiceAccount. Production workflows should name a dedicated ServiceAccount and bind only the permissions their tasks require. The v4.1.4 executor minimum is namespace-scoped permission to create and patch `workflowtaskresults` in API group `argoproj.io`.

This example is a minimal dedicated task identity for the namespace where the Workflow runs. It does not grant permission to deploy arbitrary Kubernetes objects.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: workflow-task
  namespace: argo
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: workflow-task-executor
  namespace: argo
rules:
  - apiGroups: [argoproj.io]
    resources: [workflowtaskresults]
    verbs: [create, patch]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: workflow-task-executor
  namespace: argo
subjects:
  - kind: ServiceAccount
    name: workflow-task
    namespace: argo
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: workflow-task-executor
```

The workflow controller has its own permissions to observe and manage Workflow resources; do not confuse those controller permissions with permissions granted to user task pods. Add task-specific permissions only when a task needs Kubernetes API access, and scope them to the needed resource, namespace and verbs. Do not bind `cluster-admin` or rely on the shared default ServiceAccount.

## Steps and DAG example

A Workflow is both the specification and recorded state of one run. Templates define task execution; the entrypoint names the starting template. In a `steps` template, each nested list runs in sequence and items in the same list can run in parallel. A DAG expresses explicit dependencies. The example below runs `prepare`, then `left` and `right` concurrently, then `finish` after both succeed. The `busybox:1.37.0` tag is the pinned image used in the upstream v4.1.4 hello-world example; for higher supply-chain assurance, select an approved image and immutable digest.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: small-dag-
spec:
  serviceAccountName: workflow-task
  entrypoint: pipeline
  templates:
    - name: pipeline
      dag:
        tasks:
          - name: prepare
            template: say
            arguments:
              parameters: [{name: message, value: prepare}]
          - name: left
            depends: prepare
            template: say
            arguments:
              parameters: [{name: message, value: left}]
          - name: right
            depends: prepare
            template: say
            arguments:
              parameters: [{name: message, value: right}]
          - name: finish
            depends: "left && right"
            template: say
            arguments:
              parameters: [{name: message, value: finish}]
    - name: say
      inputs:
        parameters:
          - name: message
      container:
        image: busybox:1.37.0
        command: [echo]
        args: ["{{inputs.parameters.message}}"]
```

To try it, first install the v4.1.4 quick-start manifest only in a disposable cluster and namespace, then apply the ServiceAccount, Role and RoleBinding above. Save the Workflow as `small-dag.yaml`; the following submits and observes it without exposing a server endpoint:

```bash
argo submit -n argo --watch small-dag.yaml
argo list -n argo
argo get -n argo @latest
argo logs -n argo @latest
```

The submitter needs authority to create Workflows in `argo`; the commands assume CLI access is already configured. `--watch` waits for completion. `list`, `get` and `logs` inspect runs. The optional Argo Server UI can be reached through an explicitly local port-forward; see the [v4.1.4 Quick Start](https://github.com/argoproj/argo-workflows/blob/v4.1.4/docs/quick-start.md). Do not make the server public as a shortcut.

Retries may repeat task side effects. Make tasks idempotent or use external deduplication/locking before configuring retries. Artifacts need a configured artifact repository and suitable credentials; a Workflow manifest alone does not configure storage. Set an appropriate TTL only after deciding how long logs, outputs and run metadata must remain available. Deleting old Workflow objects does not guarantee external artifact cleanup.

## Diagnose and operate safely

If submission is forbidden, check the submitter's namespace RBAC. These CLI examples assume an authenticated CLI context with access to the isolated `argo` namespace. If a pod cannot report its task result, verify that the Workflow's named ServiceAccount has the `workflowtaskresults` RoleBinding in the Workflow namespace and that the CRD/controller installation is healthy. If pods remain pending or image pulls fail, inspect pod events, scheduler capacity, image reference and registry access before changing Workflow privileges. For failed DAG nodes, inspect `argo get` and logs; a retry should not be used to hide a deterministic input or permission error.

The v4.1.4 official release was published 2026-09-18. Its existence and API documentation do not establish Kubernetes v1.37 compatibility; the handbook's baseline is v1.37.1, and no affirmative upstream v1.37 matrix was found for this release. Check the [release](https://github.com/argoproj/argo-workflows/releases/tag/v4.1.4), [RBAC guidance](https://github.com/argoproj/argo-workflows/blob/v4.1.4/docs/workflow-rbac.md), [Workflow concepts](https://github.com/argoproj/argo-workflows/blob/v4.1.4/docs/workflow-concepts.md) and [installation guide](https://github.com/argoproj/argo-workflows/blob/v4.1.4/docs/installation.md) before a production deployment. Stage upgrades, verify CRDs and controller compatibility, preserve workflow and artifact data, and rehearse rollback without deleting persistent data.
