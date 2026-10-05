# Kubernetes v1.37 适配指南

本章的版本快照截止于 **2026-10-05**，目标为 **Kubernetes v1.37.1**。只选择截止日期前发布的稳定版本，不使用 v1.38 alpha 或组件的预发布版本。组件的最新版本、kubeadm 内置版本与 Kubernetes 兼容声明是不同信息，见[组件版本清单](component-versions.md)。

版本依据为 [Kubernetes 发布列表](https://kubernetes.io/releases/)、[v1.37.1 发布记录](https://github.com/kubernetes/kubernetes/releases/tag/v1.37.1)和 [v1.37 源码变更记录](https://github.com/kubernetes/kubernetes/blob/v1.37.1/CHANGELOG/CHANGELOG-1.37.md)。这些页面的发布时间信息可能不同，本书以版本标签及截止日期为筛选依据，不把发布时间差异解释为不同版本。

## 部署基线

- 控制平面、kubelet、kube-proxy、kubeadm、kubectl 使用 v1.37.1；镜像仓库使用 `registry.k8s.io`。
- 节点使用支持 CRI v1 的运行时，优先选择 containerd 2.x 或同次版本的 CRI-O。Docker Engine 本身不是 CRI 实现；cri-dockerd 路径还有 exec/attach 的已知兼容性问题，不作为本章新部署基线。
- Linux 新节点使用 cgroup v2，运行时与 kubelet 的 cgroup 驱动保持一致。在 systemd 系统中使用 `systemd` 驱动。
- kubeadm v1.37.1 源码的组件基线包括 etcd 3.7.0、CoreDNS 1.14.6 和 pause 3.10.2。它们不是所有第三方组件的通用兼容性保证。安装时用 `kubeadm config images list --kubernetes-version v1.37.1` 核对具体镜像标签。
- 使用维护中的 CNI、CSI 和 Gateway API 控制器。只安装 CRD 不会产生网络或存储实现。

基线依赖见 [v1.37.1 dependencies.yaml](https://github.com/kubernetes/kubernetes/blob/v1.37.1/build/dependencies.yaml)。运行时设置见[官方运行时指南](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)。containerd 2.x 的插件路径与 1.x 不同，应从所安装版本生成默认配置再修改，不直接复制旧版 `config.toml`。

如必须沿用 Docker Engine，先核对 [cri-dockerd 的流式请求问题](https://github.com/Mirantis/cri-dockerd/issues/569)。Kubernetes v1.36 起默认启用 `ExtendWebSocketsToKubelet`，旧适配器的相对 streaming URL 可能导致 `kubectl exec`、`attach` 失败。上游部署工具采用过在 kube-apiserver 暂时关闭该开关的规避方式，但这不是本书已经验证的 v1.37 配置；优先迁移到 containerd 或 CRI-O，而不是绕过错误后宣称 Docker 路径相容。

## 升级前检查

不能从本书早期的 v1.6、v1.13 或 v1.33 教程直接跨次版本升级到 v1.37。先升级到当前次版本的最新补丁，再逐次升级；每一步都遵循部署工具和组件的升级说明。

1. 备份 etcd、集群配置与工作负载数据，并在隔离环境验证恢复。etcd 跨次版本迁移按 etcd 官方顺序执行，不能仅替换二进制。
2. 核对 CNI、CSI、运行时、云控制器、准入 webhook、监控和 ingress/Gateway 控制器的支持矩阵。最新 release 不等于已通过 v1.37 验证。
3. 清理已移除的 API、特性开关和组件启动参数。检查实际 API discovery、审计记录以及 `apiserver_requested_deprecated_apis` 指标。
4. 在测试集群验证网络、DNS、持久卷、准入策略、证书与监控告警，然后逐节点 drain、升级并 uncordon。

### v1.37 的特殊升级风险

以下内容来自[官方 v1.37 变更记录](https://github.com/kubernetes/kubernetes/blob/v1.37.1/CHANGELOG/CHANGELOG-1.37.md)。

| 项目 | 迁移要求 |
| --- | --- |
| SELinux 卷标签 | `SELinuxMount` 升级为 GA 并默认启用。启用 SELinux 的集群应在 v1.36 阶段检查共享卷与工作负载的标签冲突，见[官方迁移说明](https://kubernetes.io/blog/2026/04/22/breaking-changes-in-selinux-volume-labeling/)。 |
| 工作负载感知调度 | 升级前清除 `scheduling.k8s.io/v1alpha2` 对象；核心 Workload/PodGroup 使用 `v1beta1`，CompositePodGroup 使用 `v1alpha3`。这些 API 的启用仍取决于相应特性开关，不能批量替换所有 alpha API。 |
| 特性开关 | 移除 `GangScheduling`、`WorkloadAwarePreemption`、`AnyVolumeDataSource` 和 kubeadm 的 `NodeLocalCRISocket` 旧配置；`DeclarativeValidationTakeover` 已锁定，不能继续显式设置。 |
| kubelet 事件限流 | `eventRecordQPS: 0` 表示不限流。需要限流时设置明确的非零值，例如 `50`。 |
| kubelet 日志权限 | kubelet 启动日志会记录有效配置。限制 `nodes/log` 子资源权限，仅授予可信管理者，避免泄露配置。 |
| cAdvisor | 除 `--housekeeping-interval` 外，旧的 cAdvisor 启动参数已移除。自定义应用指标、CPU load 和 tasks-state 等旧指标不再导出，升级后要调整采集和告警。 |
| kube-proxy | 显式配置 `mode`。IPVS 自 v1.35 起弃用；新 Linux 内核可选择 nftables，旧内核可使用 iptables。v1.37 的默认模式仍不是 nftables。 |
| 运行时 cgroup 检测 | 支持 CRI `RuntimeConfig` 的运行时可提供 cgroup 驱动。旧运行时的回退行为在 v1.37 尚未移除，移除延期到 v1.38；新部署仍应选择支持该接口的运行时。 |

## API 与安全迁移

常见旧示例按[官方 API 迁移指南](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)修改字段，不能只修改 `apiVersion`。

| 对象 | v1.37 使用方式 |
| --- | --- |
| Deployment、DaemonSet、ReplicaSet、StatefulSet | `apps/v1`，显式 selector，且与 Pod template 标签一致。 |
| CronJob | `batch/v1`。 |
| Ingress | `networking.k8s.io/v1`，设置 `pathType`，后端为 `service.name` 与 `service.port`。新入口优先评估 Gateway API。 |
| RBAC | `rbac.authorization.k8s.io/v1`，按实际权限使用最小授权。 |
| HPA | `autoscaling/v2` 支持多指标与可配置容差；`autoscaling/v1` 仍可用于简单 CPU 示例。 |
| PDB | `policy/v1`，必须检查 selector。空 selector 会选择命名空间全部 Pod。 |
| CRD | `apiextensions.k8s.io/v1`，使用 `spec.versions` 和结构化 schema。 |
| APIService | `apiregistration.k8s.io/v1`，版本声明必须与后端实际服务一致。 |
| CSR | `certificates.k8s.io/v1`，显式指定 `signerName`、`usages`。 |
| PodSecurityPolicy | 已移除，迁移到 Pod Security Admission 或维护中的准入策略实现。 |
| ServiceAccount 凭据 | 使用投射的短期令牌或 `kubectl create token`，不依赖自动生成永久 token Secret。 |

v1.37 的 `metrics.k8s.io/v1` 已稳定，`kubectl top` 支持该版本并可回退到 v1beta1。但 [Metrics Server v0.9.0 的官方清单](https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.9.0/components.yaml)仍注册 `v1beta1.metrics.k8s.io`，v1.37 的 HPA 资源指标客户端也使用 v1beta1。保留后端的 v1beta1 服务，不要仅把 APIService 名称改为 v1 就假设实现已升级。聚合 API 的实际版本必须与后端匹配。

## v1.37 功能重点

- Pod Certificates、ClusterTrustBundle 与投射功能升级为 GA。PodCertificateRequest 的 v1 API 不再接受旧 `PKIXPublicKey` 和 `ProofOfPossession` 字段。
- DRA 扩展资源、设备污点/容忍和设备状态升级为 GA；驱动仍须匹配 CRI、节点内核与相应 DRA 接口。
- `HPAConfigurableTolerance` 和 `StorageVersionMigration` 升级为 GA。
- `MemoryQoS` 为 Beta；默认不设置 `memory.high`，需要显式配置 `memoryThrottlingFactor`。
- PVC 的 unused-since 状态为 Beta 并默认启用，可辅助识别未使用卷，但不能据此自动删除业务数据。

完整特性与默认值以该版本源码及[特性开关说明](feature-gates.md)为准，不把历史特性表作为当前可设置开关清单。

## 验证与回滚边界

先确认命令指向预期的测试集群。下面命令不创建工作负载，但会访问所选集群。

```bash
kubectl version
kubectl get nodes -o wide
kubectl get --raw='/readyz?verbose'
kubectl api-resources
kubectl get pods -A
kubectl get apiservices
kubectl top nodes
```

对修改过的清单，在兼容的测试集群执行 `kubectl apply --dry-run=server --validate=strict -f <file>`。服务端 dry-run 需要可用的 API、CRD 和 admission webhook，不能代替真实的 DNS、网络、卷与业务验证。CRD 控制器与云资源也需单独验证。

本书保留明确标记的历史教程，供理解旧架构及迁移使用；其中已退役的 Heapster、旧 ingress-nginx、Tiller、Mixer、PodPreset、dockershim、GlusterFS in-tree 卷等不是 v1.37 的部署路径。历史清单不应纳入当前组件的安装命令。

Kubernetes 不支持把升级后的控制平面直接降级作为通用回滚。回滚方案应由部署工具、etcd 快照恢复流程及业务数据恢复共同定义，在升级前完成验证。

## 本次适配验证记录

验证使用隔离的 kind v0.33.0 集群。先用官方 v1.37.0 节点镜像进行排错，再从官方 v1.37.1 服务端发布包构建节点，重新验证 **API server 与 kubelet 均为 v1.37.1**。该测试节点运行 containerd **2.3.4**；这不是组件清单中 containerd 2.4.1 的运行认证。

| 检查 | 实际结果与边界 |
| --- | --- |
| kubeadm 配置 | v1.37.1 `kubeadm config validate` 接受示例的四段配置；镜像列表核实 etcd 3.7.0、CoreDNS 1.14.6、pause 3.10.2。 |
| 独立清单 | 113 个当前资源通过严格 server-side dry-run；其中 96 个内置对象通过 v1.37.1 严格 schema，17 个自定义对象另按 Gateway API 1.6.2、cert-manager 1.21.2、Calico 3.33 CRD 检查。41 个历史文件只检查 YAML，不宣称可部署。 |
| 文档内清单 | 126 个符合测试前提的内置资源在 v1.37.1 实际提交 dry-run，其中 3 个证书占位示例仅在内存中替换为临时测试证书。历史 alpha 注解及 10 个外部控制器、Kata 等前提不满足的示例不计入通过数。 |
| client-go | v0.37.1 示例通过 Go 编译、`go test ./...`、`go vet ./...`；包没有单元测试文件。实际验证首次缓存、Pod 增删改事件、SIGTERM 退出与缺失 kubeconfig 的错误路径。 |
| Gateway | Traefik 3.7.13 与 Gateway API 1.6.2 的 80/443 listener、HTTPRoute 条件及实际 HTTP/HTTPS 请求通过。HTTPS 只信任临时测试证书；没有验证外部 LoadBalancer、ACME 或全部 Gateway 特性。 |
| DNS 与指标 | CoreDNS 1.14.6 的 API/业务 Service DNS 查询通过；Metrics Server 0.9.0 提供 v1beta1 指标，kubectl 1.37.1 `top nodes` 通过。kind 的 kubelet serving 证书不受信任，因此仅临时测试 Deployment 加过 `--kubelet-insecure-tls`，仓库清单没有放宽 TLS。 |
| Node Problem Detector | v1.36.0 发布镜像接受清单启动参数，包括帮助页不列出的 `--logtostderr`。这是 CLI 检查，不是内核、宿主日志或特权 DaemonSet 的运行认证。 |
| 文档与构建 | YAML 围栏、变更引入的相对链接及 diff 空白检查通过；保留 4 个原有失效相对链接，不计为新增问题。完整 GitBook 渲染未通过：本机缺少 CLI，隔离验证又遇到旧 npm 插件安装错误和 github 插件要求 GitBook 4 alpha 的版本冲突。没有把静态检查当成渲染成功，也未把旧 Node/GitBook 工具链作为生产推荐。 |

支持矩阵不包含 v1.37 的 Istio、Cilium、Envoy Gateway、cert-manager，以及尚无同次版本稳定发布的 Cluster Autoscaler，仍按[组件清单](component-versions.md)标注限制。上述结果不是全组件、云环境、持久卷、SELinux/GPU 或生产升级的认证。

本次更新由 AI 辅助调查与修改，并经过分域 review 和实际验证；未宣称已经完成人类逐行审查。调查、排错、维护与发布步骤分别记录于 [.agents/skill-investigate.md](../.agents/skill-investigate.md)、[.agents/skill-debug.md](../.agents/skill-debug.md)、[.agents/skill-maintenance.md](../.agents/skill-maintenance.md)。
