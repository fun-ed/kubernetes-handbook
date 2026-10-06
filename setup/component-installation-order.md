# 组件按需安装顺序

本手册介绍多个可选组件，不代表应将它们全部安装到同一集群。先确认要解决的问题、目标 Kubernetes 版本、发行版与现有网络、存储和身份认证方案。只安装本次需要的组件，并固定到经过审查的版本；各组件章节中的版本和兼容性限制优先于通用顺序。

## 先检查，再安装

1. 确认 Kubernetes 与发行版版本、节点操作系统和内核、可用 CPU／内存／磁盘、网络范围，以及现有 CNI、DNS、CSI、Ingress 或 Gateway 实现。
2. 确认该组件的官方 Kubernetes 支持声明、前置条件、数据持久性和升级／回滚方式。没有正式兼容矩阵时，不要把它描述成已支持目标版本。
3. 规划 Namespace、ServiceAccount、RBAC、Secret、网络策略、资源请求与配额。用单独的身份运行控制器，不要默认授予 `cluster-admin`。
4. 先准备必要的底层服务，再安装控制器。先检查 API 与 CRD 已就绪，最后再创建自定义资源和工作负载。
5. 每次只引入一项变更，在隔离环境验证健康状态、网络路径、存储行为和恢复流程，再决定是否推广。

先确认主网络与 Pod 连通性，再准备必要的 DNS 和存储服务。之后安装控制器及其 CRD 与平台 API，最后再部署应用工作负载。集群发行版已提供的服务不要重复安装或替换。

## 本手册主题的安装顺序

以下是依赖顺序，不是把所有主题堆叠到同一集群的清单。详细安装命令、版本限制和故障处理请以链接章节及对应版本的官方文档为准。

### 网络基础

- [Cilium](../extension/network/cilium.md) 作为主 CNI 时，先确认集群尚未运行不兼容的主 CNI，并按所选版本的官方安装文档配置。现有 Cilium v1.20.2 兼容矩阵没有列出 Kubernetes v1.37，不要将其描述为已支持。若要使用 [Cilium BGP 与 IPv6](../extension/network/cilium-bgp-ipv6.md)，先验证 Pod／节点 IPv6 路由、地址分配和对端路由策略，再启用 BGP 对外发布。控制平面可达不等于路由已安全收敛；不要向邻居发布未经审核的前缀。
- [nftables kube-proxy 模式](../network/nftables.md)是 kube-proxy 的一种选择，不是 Kubernetes v1.37 的默认模式。确认 Linux 内核至少为 5.13，并核对发行版及 CNI 的兼容要求后再切换。若 Cilium 以 eBPF 取代 kube-proxy，不要同时按本手册安装 nftables kube-proxy 路径；只能按所选 Cilium 版本的代理模式文档配置。

### 存储与虚拟化

- [Longhorn](../extension/volume/longhorn.md) v1.13.0 依赖节点磁盘、网络和 CSI。先审查磁盘分区、容量、节点标签、StorageClass、复制策略、备份目标与恢复演练，再安装控制器并创建卷。本书隔离实验使用 Longhorn V1，并在 StorageClass 明确设置 `dataEngine: "v1"`。Longhorn V1 与 V2 数据引擎的内核和硬件前提不同，不能只切换 StorageClass 参数就改用 V2；按该章和对应版本文档分别核对前置条件。
- [KubeVirt](../apps/kubevirt.md) 先检查节点是否提供所需 KVM 硬件虚拟化、虚拟机磁盘所需的持久化存储和网络。随后安装 Operator，等待相关 CRD 显示 `Established=True`，创建 `KubeVirt` 自定义资源并等待其状态为 `Available=True`，再创建 VirtualMachine。先准备 PVC 和可启动的虚拟机磁盘，并在隔离测试 Namespace 验证镜像、网络和启动权限。

### 工作流程与平台控制器

- [Argo Workflows](../apps/devops/argo.md) 与 [Argo CD](../apps/devops/argo-cd.md) 是不同产品，应分别决定是否需要。为 Workflow 配置专用 ServiceAccount 和完成任务所需的最小 Role／RoleBinding。Workflow executor 的文档化规则至少需要对 `argoproj.io` API group 中的 `workflowtaskresults` 资源授予 `create`、`patch`；按实际工作流再增加权限，不要沿用默认高权限身份。Argo CD v3.5.3 的测试表列出 Kubernetes 1.33 至 1.36，未列 v1.37。先决定受信任的 Git 来源、仓库凭证和同步权限，再配置 Argo CD 的目标 Namespace 与资源范围。
- [Kubeflow](../apps/kubeflow.md) 是由多个独立版本化项目组成的发行版。安装前核对发行版所选组件、资源需求、用户身份与隔离方式，以及该发行版附带的 Istio sidecar 依赖。26.03.1 的发行说明提到 Kubernetes 1.36 CI，但没有声明支持 v1.37。Kubeflow 使用的 sidecar 版本不等同于可独立升级的 Ambient 安装；不可将 [Istio Ambient](../apps/istio/ambient.md) 视为可直接替代的方案。依所选发行版的文档验证用户认证、流量策略、Notebook／训练工作负载及资源配额；不要把示例 overlay 当成无条件支持的安装指令。
- [Istio Ambient](../apps/istio/ambient.md) 先按版本化文档安装所需 Gateway API CRD 与 Istio base、`istiod`、CNI 集成和 `ztunnel`。只有需要 L7 处理时才部署使用 `istio-waypoint` GatewayClass 的 Gateway，并为 Namespace 配置 `istio.io/use-waypoint` 标签。Istio 1.31.1 官方支持表未列 Kubernetes v1.37。Waypoint 会改变请求的身份判定；按所选数据平面配置相应的 L4 或 waypoint L7 AuthorizationPolicy，不要混用两种模式的主体规则。不要同时用 sidecar 注入和 Ambient 标签接入同一工作负载。

## 本机文档工具也按需安装

- 仅构建本书时，只需仓库 `.nvmrc` 指定的 Node.js 24.21.0、npm 11.19.0 和锁定依赖。可按[网站构建指南](site-build.md)使用 `mise install node@24.21.0`，再运行 `mise exec node@24.21.0 -- npm ci`。阅读章节不需要 Kubernetes 集群或容器运行环境。
- 只有执行对应的内嵌检查时才需要 uv；`check-current-content.py` 还要求 Go 1.26.0 或更高版本位于 `PATH` 中。详情见[清单验证指南](verification.md)。只编辑文档时不要预装这些工具。
- `kubectl`、Helm、CNI／CSI 专用 CLI 和集群管理工具只在实际操作目标环境时安装。先确认工具版本、目标 kubeconfig 和权限；不要把本机开发依赖当成集群组件。

## 不使用的组件与磁盘空间

先盘点再决定。可使用只读命令查看可用磁盘、容器引擎空间、构建缓存和本机集群清单：

```sh
df -h "$HOME"
docker system df -v
docker buildx du
kind get clusters
du -sh "${HOME}/Library/Caches" "${HOME}/.cache" 2>/dev/null
```

这些命令只用于查看，不会确认数据可删除。区分可重建的构建缓存、可重新拉取的镜像，以及可能含唯一数据的容器卷、PVC、PV、数据库和集群状态。不要停止运行中的服务或容器，也不要移除当前使用的磁盘区、语言运行时、mise 工具链、环境或依赖。

清理前由有权限的人确认每个对象的负责人、用途、恢复来源和备份。先为配置制作带时间戳的副本；为卷创建 tar 备份；为 Kubernetes 状态导出 YAML；为数据库制作数据库级备份，并确认能恢复。只允许人工选择明确的可重建缓存，再依该工具的文档单独清理该缓存。不要运行 Docker system／volume prune，不要把 `helm uninstall` 或删除 PVC／PV／Namespace 当作通用清理步骤。本书维护者不会代替操作者执行清理操作，本书没有删除数据或释放磁盘空间。
