# PV 排错

先确定 PVC 所在 Namespace、Pod、PV 与 StorageClass，再从 Events 和 CSI 资源状态定位故障。旧版指南中检查特定 external-provisioner 镜像版本以及移除 PV finalizer 的命令已移至[历史归档](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/troubleshooting/pv/README.md)；不要将强制移除 finalizer 当作常规清理步骤。

```bash
NAMESPACE='<namespace>'
PVC='<pvc-name>'
kubectl get pvc "$PVC" -n "$NAMESPACE" -o wide
kubectl describe pvc "$PVC" -n "$NAMESPACE"
kubectl get pv -o wide
kubectl get storageclass
kubectl get csidrivers
kubectl get events -n "$NAMESPACE" --sort-by=.metadata.creationTimestamp
```

若 PVC 未绑定，依 Events 检查 StorageClass、CSI provisioner、容量、拓扑、配额与后端权限。若卷挂载或解除挂载失败，检查相关 Pod／Node Events、PV、`VolumeAttachment`、`CSINode` 及驱动日志：

```bash
kubectl describe pv '<pv-name>'
kubectl get volumeattachments
kubectl get csinodes
kubectl -n kube-system get pods -o wide
```

CSI controller/node Pod 名称、容器和 Namespace 由驱动及集群发行版决定；先发现实际对象，再读取对应日志。PV 停留在 `Terminating` 时，检查被引用的 PVC/Pod、reclaim policy、驱动健康状态及 finalizer 对应的清理责任者。CSI deletion finalizer 可用于等待外部后端清理；不要手动清除 finalizer、删除 `VolumeAttachment`，或在未核实数据保留策略时删除云端卷。若后端不可用，遵循驱动／云服务商的恢复流程并保留事件、对象 YAML 和日志供支持人员诊断。

Azure 专项流程见 [Azure Disk CSI](azuredisk.md) 与 [Azure Files CSI](azurefile.md)。Kubernetes CSI 卷概念见[官方文档](https://kubernetes.io/docs/concepts/storage/volumes/#csi)；最终处置应遵循所用驱动与发行版的受支持流程。
