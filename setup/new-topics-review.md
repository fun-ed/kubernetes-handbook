# 新主题整合复核记录

**Kubernetes 基线：** v1.37.1。**来源截点：** 2026-10-05。本记录涵盖七组新增章节和安装顺序指南。它补充先前的现行内容复核，不取代或改写该记录。

## 范围与来源证据

| 主题 | 版本证据与兼容性限制 |
| --- | --- |
| Argo CD | v3.5.3 于 2026-09-14 发布。该版本固定的测试表列出 Kubernetes 1.33 至 1.36，未列 1.37。[发布](https://github.com/argoproj/argo-cd/releases/tag/v3.5.3) · [测试版本](https://github.com/argoproj/argo-cd/blob/v3.5.3/docs/operator-manual/tested-kubernetes-versions.md) |
| Argo Workflows | v4.1.4 于 2026-09-18 发布。未找到肯定的官方 Kubernetes v1.37 兼容矩阵。版本化 RBAC 指南记载，Workflow executor 规则需要对 `workflowtaskresults` 授予 `create` 和 `patch`。[发布](https://github.com/argoproj/argo-workflows/releases/tag/v4.1.4) · [RBAC](https://github.com/argoproj/argo-workflows/blob/v4.1.4/docs/workflow-rbac.md) |
| KubeVirt | v1.9.0 是截点时查到的最高稳定版，于 2026-07-30 发布。排除预发布版 v1.10.0-alpha.0；已查阅的官方资料没有声明支持 Kubernetes v1.37。[发布](https://github.com/kubevirt/kubevirt/releases/tag/v1.9.0) |
| Kubeflow | Community Distribution 26.03.1 于 2026-06-15 发布。它包含各自独立版本化的项目，例如 Pipelines 2.16.1、Trainer 2.2.0、Istio 1.30.1、cert-manager 1.20.2、Dex 2.45.1 和 Notebooks v1.11.0。发布说明提及 Kubernetes 1.36 CI，但未说明支持 v1.37。本记录未将采用 CalVer 的发行版当作单一 SemVer 组件加入自动发布追踪清单。[发布](https://github.com/kubeflow/community-distribution/releases/tag/26.03.1) |
| Longhorn | v1.13.0 与 chart 1.13.0 于 2026-09-29 发布。发布说明列出 Kubernetes v1.34 为最低版本；这不是对完整 v1.37.1 平台组合的认证。[发布](https://github.com/longhorn/longhorn/releases/tag/v1.13.0) · [chart](https://github.com/longhorn/longhorn/blob/v1.13.0/chart/Chart.yaml) |
| Cilium BGP 与 IPv6 | 指南使用现有 Cilium v1.20.2 基线。其版本化 Kubernetes 矩阵列出 1.33 至 1.36，未列 v1.37。本主题章节沿用既有版本基线，不将 BGP 专题当作新版本审计。[矩阵](https://docs.cilium.io/en/v1.20/operations/support/) · [BGP v2 配置](https://docs.cilium.io/en/v1.20/network/bgp-control-plane/bgp-control-plane-configuration/) |
| nftables | 指南记载 Kubernetes v1.37 kube-proxy 行为：nftables 模式已 GA，但不是默认模式；Linux 内核最低版本为 5.13。[Kubernetes 文档](https://kubernetes.io/docs/reference/networking/virtual-ips/#nftables-proxy-mode) |
| Istio Ambient | 指南沿用现有 Istio 1.31.1 基线。官方支持表列到 Kubernetes 1.36，因此本记录不宣称兼容 v1.37。[Istio 1.31 Ambient 安装](https://istio.io/v1.31/docs/ambient/install/) · [支持表](https://istio.io/latest/docs/releases/supported-releases/) |

## 整合与验证状态

七组新增章节为 `apps/devops/argo-cd.md`、`apps/kubevirt.md`、`apps/kubeflow.md`、`extension/volume/longhorn.md`、`extension/network/cilium-bgp-ipv6.md`、`network/nftables.md` 和 `apps/istio/ambient.md`，各有 `zh-TW/` 对应版本。`apps/devops/argo.md` 现已明确标示 Argo Workflows。`setup/component-installation-order.md` 及繁体中文版本说明按需安装依赖顺序、工具安装和数据安全边界。
两份目录都已链接新章节，相关本地索引也提供入口。繁体中文涵盖清单记录实际存在的 Markdown 成对文件。组件追踪清单新增 Argo Workflows、Longhorn 和 KubeVirt；没有肯定 v1.37 支持证据时，支持状态仍为未确认。Kubeflow 按多项目 CalVer 发行版记录，不视为单一 SemVer 追踪项。Cilium 与 Istio 的既有版本基线未升级。

先前的 178 组文件复核仍是历史快照。未改写其来源哈希与结论，也未将这些新章节或 Cilium、kube-proxy 的少量交叉链接修改追溯纳入。先前复核未覆盖这些新页面。

主整合者记录的验证命令、结果、来源指纹与未覆盖范围见[验证报告](new-topics-review.json)。本主题内容负责人未执行安装器或集群命令。
