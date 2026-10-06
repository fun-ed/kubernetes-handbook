# Azure Disk CSI 排错

Kubernetes v1.36／v1.37 的 Azure Disk 应通过 Azure Disk CSI driver 使用；旧版 `kubernetes.io/azure-disk` in-tree StorageClass、aks-engine 固定值、AzureRM 命令和旧内核事件案例已移至[历史归档](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/troubleshooting/pv/azuredisk.md)，不可作为当前配置或恢复指令。

AKS 管理的驱动和自管 CSI 安装方式不同。先依据集群发行版和 [AKS Azure Disk CSI 文件](https://learn.microsoft.com/azure/aks/create-volume-azure-disk)确认驱动状态、StorageClass 和支持的磁盘功能；不要将另一版本 StorageClass 的参数直接套用到当前集群。

## PVC 无法绑定或动态配置失败

```bash
NAMESPACE='<namespace>'
PVC='<pvc-name>'
kubectl get pvc "$PVC" -n "$NAMESPACE" -o wide
kubectl describe pvc "$PVC" -n "$NAMESPACE"
kubectl get storageclass
kubectl get csidrivers
kubectl get events -n "$NAMESPACE" --sort-by=.metadata.creationTimestamp
```

根据 Events 检查 StorageClass 的 CSI provisioner、参数、区域／可用区、请求容量、访问模式、订阅配额及驱动身份权限。先确认 PVC 与 Pod 处于预期命名空间，并依供应商文件核实当前 AKS 集群支持的磁盘类型和拓扑约束。

## Pod 挂载失败或多次重试

```bash
kubectl describe pod '<pod-name>' -n "$NAMESPACE"
kubectl describe pvc "$PVC" -n "$NAMESPACE"
kubectl get pv
kubectl get volumeattachment
kubectl get csinodes
kubectl -n kube-system get pods -o wide
```

查看 Pod／PVC Events、PV `nodeAffinity`、`VolumeAttachment` 状态及目标 Node 的 CSI Node Pod 状态。若需日志，先依发行版找出 Azure Disk CSI controller 与 node Pod，再读取具体容器日志；AKS 管理的附加组件名称和日志访问方式可能不同。核对磁盘当前附加节点、拓扑、节点可附加磁盘限制、磁盘状态与 Azure API 错误；不要因为一次 `FailedMount` 就重启 VM、手动卸载磁盘、删除 `VolumeAttachment` 或直接修改云端资源。

## PVC／PV 删除或 Azure 磁盘仍处于附加状态

在删除声明前确认没有 Pod 使用该 PVC，并依据 PV 的 reclaim policy 与组织备份／保留流程确认数据处置。若 CSI 仍报告挂载或分离中，收集 PVC/PV、Pod、VolumeAttachment、CSI 日志与 Azure 错误码，交由平台管理员按相应 AKS／驱动版本流程处理。不要强制删除 finalizer、PV 或磁盘资源；此操作可能导致数据丢失或孤儿磁盘。

## 参考文件

- [AKS Azure Disk CSI 驱动与动态配置](https://learn.microsoft.com/azure/aks/create-volume-azure-disk)
- [Kubernetes CSI 卷](https://kubernetes.io/docs/concepts/storage/volumes/#csi)
- [CSI VolumeAttachment API](https://kubernetes.io/docs/reference/kubernetes-api/config-and-storage-resources/volume-attachment-v1/)
