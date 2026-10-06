# Azure Files CSI 排错

Kubernetes v1.36／v1.37 的 Azure Files 应通过 Azure Files CSI driver 使用；旧版 `kubernetes.io/azure-file` in-tree StorageClass、过时的 RBAC 示例与固定权限／Windows 错误记录已移至[历史归档](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/troubleshooting/pv/azurefile.md)，不可作为当前配置或修复步骤。

AKS 管理的驱动和自管 CSI 安装方式不同。先依 [AKS Azure Files CSI 文档](https://learn.microsoft.com/azure/aks/create-volume-azure-files)确认驱动、StorageClass、SMB/NFS 协议、账户网络和身份验证方式；挂载选项与身份验证应与所用协议和驱动版本一致，不要将旧版 `0777` 或明文存储账户密钥示例复制到新集群。

## PVC 无法绑定或文件共享配置失败

```bash
NAMESPACE='<namespace>'
PVC='<pvc-name>'
kubectl get pvc "$PVC" -n "$NAMESPACE" -o wide
kubectl describe pvc "$PVC" -n "$NAMESPACE"
kubectl get storageclass
kubectl get csidrivers
kubectl get events -n "$NAMESPACE" --sort-by=.metadata.creationTimestamp
```

检查 StorageClass 的 CSI provisioner 与参数、账户／共享配额、订阅区域、网络防火墙与驱动身份权限。不要因为错误信息泛称找不到存储账户，就为所有 ServiceAccount 授予创建 Secret 的权限。

## Pod 挂载失败或挂载后无法读写

```bash
kubectl describe pod '<pod-name>' -n "$NAMESPACE"
kubectl describe pvc "$PVC" -n "$NAMESPACE"
kubectl get pv
kubectl get volumeattachment
kubectl get csinodes
kubectl -n kube-system get pods -o wide
```

根据 Pod/PVC Events、PV、VolumeAttachment 与目标 Node CSI Pod 日志区分身份验证失败、SMB/NFS 网络连接、DNS、协议／挂载选项或 POSIX 权限问题。若需查看 CSI 日志，先依发行版找出实际 Azure Files CSI controller/node Pod 及容器名称；AKS 托管组件名称或日志访问方式可能不同。确认 Node 到存储端点的 DNS、端口、防火墙／私有端点路由与当前身份验证方式。不要在日志、命令行历史或清单中暴露存储账户密钥、SAS token 或其他凭证。

SMB 挂载的 Unix 所有者、模式与 `fsGroup` 行为取决于协议、CSI 驱动参数与存储服务设置；不要只为避开 `Operation not permitted` 就以 root 运行容器、递归 `chown` 大型共享目录，或放宽至 `0777`。先确认共享是否支持应用要求的语义，再依当前驱动文档选择安全配置。

## 删除 PVC 或共享失败

先确认 Pod 已停止使用 PVC，并按 PV reclaim policy、备份和保留规定评估数据影响。若共享仍被挂载或 CSI 报告删除错误，收集 PVC/PV、Pod、VolumeAttachment、CSI 日志及 Azure 错误码，依集群发行版和驱动版本流程处理。不要强制移除 finalizer 或直接删除云端共享来绕过 CSI 状态管理。

## 参考文档

- [AKS Azure Files CSI 驱动与动态配置](https://learn.microsoft.com/azure/aks/create-volume-azure-files)
- [AKS 存储故障排查](https://learn.microsoft.com/azure/aks/troubleshooting)
- [Kubernetes CSI 卷](https://kubernetes.io/docs/concepts/storage/volumes/#csi)
- [Kubernetes VolumeAttachment API](https://kubernetes.io/docs/reference/kubernetes-api/config-and-storage-resources/volume-attachment-v1/)
