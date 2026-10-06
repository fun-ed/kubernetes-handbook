# Node

Node 是 Pod 實際執行的主機，可以是實體機或虛擬機器。每個 Node 都需要 kubelet 和符合 CRI 的容器執行時。kube-proxy 通常負責實作 Service 網路，但部分網路實作會取代它。

![node](../../.gitbook/assets/node%20%284%29.png)

## Node 管理

不像其他的资源（如 Pod 和 Namespace），Node 本质上不是 Kubernetes 来创建的，Kubernetes 只是管理 Node 上的资源。虽然可以通过 Manifest 创建一个 Node 对象（如下 yaml 所示），但 Kubernetes 也只是去检查是否真的是有这么一个 Node，如果检查失败，也不会往上调度 Pod。

```yaml
kind: Node
apiVersion: v1
metadata:
  name: 10-240-79-157
  labels:
    name: my-first-k8s-node
```

这个检查是由 Node Controller 来完成的。Node Controller 负责

* 维护 Node 状态
* 与 Cloud Provider 同步 Node
* 给 Node 分配容器 CIDR
* 删除带有 `NoExecute` taint 的 Node 上的 Pods

默认情况下，kubelet 在启动时会向 master 注册自己，并创建 Node 资源。

## Node 的状态

每个 Node 都包括以下状态信息：

* 位址：包含 hostname、外部 IP 和內部 IP
* 條件（Condition）：包含 Ready、MemoryPressure、DiskPressure、PIDPressure 等狀態；OutOfDisk 已移除
* 容量（Capacity）：Node 上的總資源，包括 CPU、記憶體和 Pod 數量
* 可分配（Allocatable）：扣除系統保留後，可分配給 Pod 的資源量；部分資源限制取決於叢集設定
* 基本資訊（Info）：包含核心、容器執行時與作業系統版本等資訊

## Taints 和 tolerations

Taints 和 tolerations 用于保证 Pod 不被调度到不合适的 Node 上，Taint 应用于 Node 上，而 toleration 则应用于 Pod 上（Toleration 是可选的）。

比如，可以使用 taint 命令给 node1 添加 taints：

```bash
kubectl taint nodes node1 key1=value1:NoSchedule
kubectl taint nodes node1 key1=value2:NoExecute
```

Taints 和 tolerations 的具体使用方法请参考 [调度器章节](../components/scheduler.md#taints-和-tolerations)。

## Node 维护模式

标志 Node 不可调度但不影响其上正在运行的 Pod，这在维护 Node 时是非常有用的：

```bash
kubectl cordon $NODENAME
```

## Node 优雅关闭

当配置 `ShutdownGracePeriod` 和 `ShutdownGracePeriodCriticalPods` 后，Kubelet 会根据 systemd 事件检测 Node 的关闭状态，并自动终止其上运行的 Pod（ShutdownGracePeriodCriticalPods 需要小于 ShutdownGracePeriod）。注意，这两个参数默认配置为 0，即优雅关闭特性默认是未开启的。

比如，如果 ShutdownGracePeriod 设置为 30s，而 ShutdownGracePeriodCriticalPods 设置为 10s，那么 Kubelet 将使节点关闭延迟 30 秒。 在关闭期间，将保留前20（30-10）秒以终止普通 Pod，而保留最后 10 秒以终止关键 Pod。

## Node 非优雅关闭

在 Node 发生异常的情况下，Kubelet 可能没有机会检测并执行优雅关闭。在这种情况下，StatefulSet 无法创建同名的新 Pod，如果 Pod 使用了卷，则 VolumeAttachments 不会从原来的已关闭节点上删除，因此这些 Pod 所使用的卷也无法挂接到新的运行节点上。

Node 非优雅关闭正是为了解决这些问题。用户可以手动将具有 `NoExecute` 或 `NoSchedule` 效果的 `node.kubernetes.io/out-of-service` 污点添加到节点上，标记其无法提供服务。如果在 kube-controller-manager 上启用了 `NodeOutOfServiceVolumeDetach` 特性，并且 Pod 上没有设置对应的容忍度，那么这些 Pod 将被强制删除，并且该在节点上被终止的 Pod 将立即进行卷卸载操作。这样就允许那些在无法提供服务节点上的 Pod 能在其他节点上快速恢复。

## 动态节点资源分配

`MutableCSINodeAllocatableCount` 在 v1.33 以 Alpha 引入，v1.34 升為 Beta，並自 v1.35 起預設啟用；v1.37 中仍為 Beta。它允許 CSI 驅動更新節點可分配的卷附件數量，讓調度器使用較新的限制資訊。CSI 驅動與 kubelet 必須支援此功能；行為與設定細節請依目標 CSI 驅動文件確認。

此功能受 `MutableCSINodeAllocatableCount` feature gate 控制。v1.37 預設已啟用，除非有明確需要，勿為此額外設定 feature gate。參閱 [CSI 章節](../../extension/volume/csi.md#csidriver-对象和节点可分配卷数)與[v1.37.1 feature gate 原始碼](https://github.com/kubernetes/kubernetes/blob/v1.37.1/pkg/features/kube_features.go)。

## 参考文档

* [Kubernetes Node](https://kubernetes.io/docs/concepts/architecture/nodes/)
* [Taints 和 tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)
