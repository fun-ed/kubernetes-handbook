# Kubeflow：以 Kubernetes 建置机器学习平台

「Kubeflow」不是单一套件。Kubeflow manifests／AI Reference Platform 描述整合发行版；Pipelines、Trainer、Katib、Notebooks 等各有独立版本、CRD 与控制器。安装整合版会带入大量控制器、webhook、RBAC、网路与外部依赖，不等于启用一个 API。

## 发行版与支援边界

截至 2026-10-05，官方 community-distribution 最新稳定 release 为 **26.03.1**，2026-06-15 发布；release notes 列明其元件包含 Pipelines 2.16.1、Trainer 2.2.0、Istio 1.30.1、cert-manager 1.20.2、Dex 2.45.1、Kubeflow Notebooks v1.11.0。这些各自的版本不是同一个「Kubeflow 版本」。官方 26.03.1 说明提及其 CI 使用 Kubernetes 1.36；不可由此推断 Kubernetes v1.37.1 已受支援。本文基线 v1.37 的整合相容性未知，须在隔离环境自行验证。

此版本 community support 为 best-effort、约六个月；请查看上游支援政策与最新 release，而非将本文的固定版本当永久支援承诺。社群 manifests 与商业发行版支援范围可能不同。

## 架构与多租户

控制器监看 CRD 或 Kubernetes 原生工作物件，建立 Pod、服务及状态；CRD 存在不代表对应 controller/webhook 已健康。Notebook controller 管理 Notebook 工作负载；Pipelines 服务则有自己的 API、资料库与物件储存需求；Trainer、Katib 也各自有版本化 API 和控制器。依功能部署所需组件，不要混用不同 release 的 CRD 与控制器。

Full multi-user 平台还需身份验证与授权整合、TLS 凭证、Istio ingress/gateway 与使用者 namespace/Profile 管理。Profile 常建立 namespace 并配置服务帐号/RBAC，不会自动替代丛集身份系统、NetworkPolicy 或租户资料隔离。不要以匿名登入或未加密公开 dashboard 作为快速安装步骤；入口应限制在可信网路并配置正式 OIDC/身份供应者与凭证。

## 前置条件与审查式安装

完整安装前需有受支援的 Linux Kubernetes 丛集、可用 StorageClass、丛集 DNS、时间同步、出站映像 registry 存取、Istio/入口规划、cert-manager 与有效 TLS 凭证，以及已设计的身份验证、RBAC、网路隔离与备份。需要 GPU 时，另需相符的装置外挂/驱动与资源配额。外部资料库、物件储存、邮件/身份提供者及云端整合也需分别规划。没有预设可安全暴露到公网的配置。

只在专用实验丛集评估固定 release；下列先取得该 tag 原始码以审查，**不代表可直接安装**。不要套用 `main`、不审阅就对丛集套用递回远端路径，也不要假设一次命令能完成安全的 multi-user 发行版：上游依安装模式及环境要求分阶段安装，应照 tag 文件准备 overlay/身份/网路配置。

```bash
git clone --depth 1 --branch 26.03.1 https://github.com/kubeflow/manifests.git
cd manifests
# 检查指定安装方式、元件清单、身分/凭证与储存设定；先渲染审查，不执行 apply。
kustomize build /path/to/reviewed-release-overlay | kubectl apply --dry-run=server -f -
```

`example` 是上游范例路径，不应盲目当成符合任何环境的安全设定；请以 tag 中当前 README/安装指引所列 overlay 替换并完整检视。server-side dry-run 仅检查 API 接受度，不会验证 webhook、外部依赖、权限是否合适或 controller 能否运作。上游针对完整平台列出安装步骤与 overlays，依序依官方文件执行并在每步验收，不以 magic patch loop 遮蔽失败。

## Notebook 范例（需先有 v1.11 controller）

以下使用 Kubeflow Notebooks v1 API，必须在已安装并确认 `kubeflow/notebooks` v1.11.0 controller/CRD 的丛集，以及预先存在的 `ml-work` namespace 和 StorageClass/PVC。不要在只安装 Kubernetes 的丛集直接套用：伺服器未知 CRD 时会拒绝它。映像为明确参数，需选择经组织核准、支援 Notebook 的映像，不虚构版本标签。先确认 CRD schema 与 pinned release 范例一致。

```yaml
apiVersion: kubeflow.org/v1
kind: Notebook
metadata:
  name: research
  namespace: ml-work
spec:
  template:
    spec:
      containers:
        - name: research
          image: REPLACE_WITH_APPROVED_NOTEBOOK_IMAGE
          resources:
            requests:
              cpu: "1"
              memory: 2Gi
            limits:
              cpu: "2"
              memory: 4Gi
          volumeMounts:
            - name: workspace
              mountPath: /home/jovyan
      volumes:
        - name: workspace
          persistentVolumeClaim:
            claimName: research-workspace
```

PVC 需事先建立并符合 CSI/StorageClass 存取模式；Notebook 会使用其资料，删除 PVC 可能永久毁损资料。此范例没有配置 GPU；GPU 工作负载须使用丛集实际提供的 extended resource 名称并配置 device plugin，不能仅增加任意 `nvidia.com/gpu` 栏位。

唯读检查：

```bash
kubectl get crd notebooks.kubeflow.org
kubectl get notebooks -n ml-work
kubectl describe notebook research -n ml-work
kubectl get pods,pvc -n ml-work -o wide
kubectl get events -n ml-work --sort-by=.lastTimestamp
```

Notebook 建立成功只代表 API 接受物件；Pod Ready、卷挂载、映像拉取、使用者认证及资料存取需分别验证。需额外确认该 release 的 CRD/controller 实际安装并查阅 [Notebooks v1 文件](https://www.kubeflow.org/docs/components/notebooks/)。

## 营运、备份与故障

`kubectl get pods -A`、`kubectl get events -A --sort-by=.lastTimestamp` 可先定位控制器、webhook、Pod 排程或映像拉取问题；`kubectl get crd`、API discovery 可辨识缺少 CRD。Notebook Pod Pending 常与 PVC 未绑定、配额或资源不足有关；API 建立失败则检查 webhook、schema、namespace 与 RBAC。不可用跳过 TLS 验证或删除 webhook 的方式消除错误。

正式使用前记录整合版与每个元件的版本、CRD 变更、映像 digest、overlay 与身份设定；保护并备份 etcd、Pipelines metadata DB/object store、PVC、Notebook 资料、凭证与 OIDC/外部服务设定。升级先查该 release 的 breaking changes，依顺序备份与演练；回退 controller 不一定能读取已迁移资料或 CRD。检查租户隔离、Profile 权限、服务帐号、Secret 存取、资源配额及网路出口。多元件版本或外部资料库/身份供应者不相容，是常见部署限制；以 pinned release 测试验证而非推测。

## 官方来源

- [Kubeflow manifests 26.03.1 release](https://github.com/kubeflow/community-distribution/releases/tag/26.03.1)
- [Kubeflow manifests 固定 release 原始码](https://github.com/kubeflow/manifests/tree/26.03.1)
- [安装 Kubeflow 平台](https://www.kubeflow.org/docs/started/installing-kubeflow/)
- [官方支援政策](https://www.kubeflow.org/docs/started/support/)
- [Kubeflow Notebooks 文件](https://www.kubeflow.org/docs/components/notebooks/)
- [Kubeflow Trainer 文件](https://www.kubeflow.org/docs/components/trainer/)
- [Kubeflow Pipelines 文件](https://www.kubeflow.org/docs/components/pipelines/)
