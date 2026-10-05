# kubelet

kubelet 运行在每个工作节点上，负责管理调度到该节点的 Pod，并向 API Server 报告节点和 Pod 状态。其 HTTPS API 默认监听 TCP 10250。请限制访问范围，只允许控制平面和获准的运维人员访问。

## 节点管理

节点管理主要是节点自注册和节点状态更新：

* Kubelet 可以通过设置启动参数 --register-node 来确定是否向 API Server 注册自己；
* 如果 Kubelet 没有选择自注册模式，则需要用户自己配置 Node 资源信息，同时需要告知 Kubelet 集群上的 API Server 的位置；
* Kubelet 在启动时通过 API Server 注册节点信息，并定时向 API Server 发送节点新消息，API Server 在接收到新消息后，将信息写入 etcd

## Pod 管理

### 获取 Pod 清单

kubelet 从 API Server 接收调度到本节点的 Pod，并负责让 Pod 达到期望状态。它不直接监视 etcd。静态 Pod 可由 kubelet 配置中的 `staticPodPath` 指定本地清单目录；静态 Pod 的状态会通过对应的 Mirror Pod 报告给 API Server。

创建 Pod 时，kubelet 通过 CRI 请求容器运行时创建 Pod sandbox 和容器。运行时使用的 sandbox 镜像由集群配置决定。Pod 网络由节点上的 CNI 实现配置，卷由相应的卷插件（包括 CSI 驱动）处理。kubelet 再把运行状态报告给 API Server。

### Static Pod

所有以非 API Server 方式创建的 Pod 都叫 Static Pod。Kubelet 将 Static Pod 的状态汇报给 API Server，API Server 为该 Static Pod 创建一个 Mirror Pod 和其相匹配。Mirror Pod 的状态将真实反映 Static Pod 的状态。当 Static Pod 被删除时，与之相对应的 Mirror Pod 也会被删除。

## 容器健康检查

Pod 支持三类探针，用于检查容器和应用的状态：

* `startupProbe` 判断应用是否完成启动。配置后，在启动探针成功之前，kubelet 不会运行 liveness 和 readiness 探针。
* `livenessProbe` 检查容器是否仍能正常工作。连续失败会导致 kubelet 按 Pod 重启策略重启容器。
* `readinessProbe` 检查应用是否准备好接收流量。探针失败时，EndpointSlice 控制器会更新该 Pod 对应端点的就绪状态。

探针支持 exec、TCP socket 和 HTTP 检查。探针定义位于 Pod 中相应容器的配置下。

## 节点和容器度量

cAdvisor 集成在 kubelet 中，不再单独监听旧版 4194 端口。授权后，可通过 kubelet HTTPS API（默认 10250）或 API Server 节点代理读取 `/metrics`、`/metrics/cadvisor` 和 `/stats/summary`。

```bash
kubectl get --raw "/api/v1/nodes/<node-name>/proxy/stats/summary"
```

Kubernetes v1.37 的 kubelet 不再在 `/stats/summary` 中返回 `userDefinedMetrics`，也不再导出 cAdvisor 应用自定义度量。容器度量的具体字段和可用系列以当前 kubelet 文档及发行说明为准。
## Memory Manager 的历史说明

以下内容记录 Kubernetes v1.21 时期的 Alpha 功能状态，不代表 v1.37 的功能门控状态。当前配置请查阅 [KubeletConfiguration API](https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/)。

## Kubelet Eviction（驱逐）

Kubelet 会监控资源的使用情况，并使用驱逐机制防止计算和存储资源耗尽。在驱逐时，Kubelet 将 Pod 的所有容器停止，并将 PodPhase 设置为 Failed。

Kubelet 定期（`housekeeping-interval`）检查系统的资源是否达到了预先配置的驱逐阈值，包括

| Eviction Signal | Condition | Description |
| :--- | :--- | :--- |
| `memory.available` | MemoryPressure | `memory.available` := `node.status.capacity[memory]` - `node.stats.memory.workingSet` （计算方法参考[这里](https://kubernetes.io/docs/tasks/administer-cluster/memory-available.sh)） |
| `nodefs.available` | DiskPressure | `nodefs.available` := `node.stats.fs.available`（Kubelet Volume以及日志等） |
| `nodefs.inodesFree` | DiskPressure | `nodefs.inodesFree` := `node.stats.fs.inodesFree` |
| `imagefs.available` | DiskPressure | `imagefs.available` := `node.stats.runtime.imagefs.available`（镜像以及容器可写层等） |
| `imagefs.inodesFree` | DiskPressure | `imagefs.inodesFree` := `node.stats.runtime.imagefs.inodesFree` |

这些驱逐阈值可以使用百分比，也可以使用绝对值，如

```bash
--eviction-hard=memory.available<500Mi,nodefs.available<1Gi,imagefs.available<100Gi
--eviction-minimum-reclaim="memory.available=0Mi,nodefs.available=500Mi,imagefs.available=2Gi"`
--system-reserved=memory=1.5Gi
```

这些驱逐信号可以分为软驱逐和硬驱逐

* 软驱逐（Soft Eviction）：配合驱逐宽限期（eviction-soft-grace-period和eviction-max-pod-grace-period）一起使用。系统资源达到软驱逐阈值并在超过宽限期之后才会执行驱逐动作。
* 硬驱逐（Hard Eviction ）：系统资源达到硬驱逐阈值时立即执行驱逐动作。

驱逐动作包括回收节点资源和驱逐用户 Pod 两种：

* 回收节点资源
  * 配置了 imagefs 阈值时
    * 达到 nodefs 阈值：删除已停止的 Pod
    * 达到 imagefs 阈值：删除未使用的镜像
  * 未配置 imagefs 阈值时
    * 达到 nodefs阈值时，按照删除已停止的 Pod 和删除未使用镜像的顺序清理资源
* 驱逐用户 Pod
  * 驱逐顺序为：BestEffort、Burstable、Guaranteed
  * 配置了 imagefs 阈值时
    * 达到 nodefs 阈值，基于 nodefs 用量驱逐（local volume + logs）
    * 达到 imagefs 阈值，基于 imagefs 用量驱逐（容器可写层）
  * 未配置 imagefs 阈值时
    * 达到 nodefs阈值时，按照总磁盘使用驱逐（local volume + logs + 容器可写层）

## 容器垃圾回收参数（历史说明）

本节早期的参数对照表描述旧版本的垃圾回收计划，不是当前配置建议。kubelet 在较新版本中移除了部分容器统计和垃圾回收选项。请根据目标版本的 kubelet 命令行参考和 KubeletConfiguration API 检查参数，不要从此处复制旧 flag。
## 容器运行时

kubelet 通过 CRI v1 与容器运行时交互，并调用 RuntimeService 和 ImageService 管理 Pod sandbox、容器和镜像。常见实现包括 containerd 和 CRI-O；其他运行时也必须提供兼容的 CRI。

Kubernetes v1.24 移除了内置 dockershim。Docker Engine 不能直接作为 kubelet 的 CRI 运行时；需要继续使用 Docker Engine 的集群必须自行部署并维护外部适配器，例如 cri-dockerd。容器镜像由 CRI 运行时管理，不能假定节点上的 Docker CLI 与 kubelet 使用同一套镜像存储。

Pod sandbox 镜像（常称 pause 镜像）由运行时配置管理。请使用集群发行版为目标 Kubernetes 版本提供的配置，避免单独覆盖该镜像。
## Kubelet 配置

kubelet 的生产配置应使用 `KubeletConfiguration` 和集群发行版规定的配置管理方式。较早章节中的 `--network-plugin`、`--cni-bin-dir`、`--cluster-dns` 和 `--cadvisor-port` 命令行参数不是 Kubernetes v1.37 的通用配置示例。字段和移除的参数请查阅 [KubeletConfiguration](https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/) 与 [kubelet 命令行参考](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/)。

## kubelet 工作原理

如下 kubelet 内部组件结构图所示，Kubelet 由许多内部组件构成

Kubelet 当前以 CRI 管理容器运行时，以 CNI 配置 Pod 网络，并由节点上的卷插件处理存储。旧版架构图中的 dockershim、rkt、HTTP manifest server 和独立 cAdvisor 端口不代表 v1.37 的节点组件。

![](../../.gitbook/assets/kubelet%20%283%29.png)

### Pod 启动流程

![Pod Start](../../.gitbook/assets/pod-start%20%281%29.png)

### 通过 API Server 查询节点汇总指标

旧版文档曾展示通过 kubelet 的匿名只读 10255 端口访问汇总指标。该端口不应启用或开放。通过 API Server 节点代理查询时，请使用经授权的 kubeconfig：

```bash
kubectl get --raw "/api/v1/nodes/<node-name>/proxy/stats/summary"
```

## Kubelet API

kubelet HTTPS API 默认监听 TCP 10250，访问需要通过 kubelet 的认证和授权配置。API Server 也可以根据 RBAC 权限代理到该节点。常见的度量路径包括 `/metrics`、`/metrics/cadvisor`、`/metrics/resource`、`/metrics/probes` 和 `/stats/summary`。不要启用或暴露旧版只读端口 10255，也不要将 kubelet API 暴露给不受信任的网络。
