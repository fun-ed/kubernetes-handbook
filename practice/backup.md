# Kubernetes 备份与恢复

[Velero](https://velero.io/) 可备份、恢复和迁移 Kubernetes API 对象，并按所选 provider/plugin 及存储能力保护持久卷数据。它不是 etcd 灾备的替代品，也不能保证应用一致性。

> **当前版本（2026-10-05）**：Velero v1.18.4 是本手册资料截点前最新稳定版：[官方发布页](https://github.com/velero-io/velero/releases/tag/v1.18.4)。本次没有找到覆盖 Kubernetes v1.37.1 的明确兼容声明；部署前核对 Velero 支持矩阵与所选 object-store、CSI/snapshot 插件的兼容版本。

## 部署前设计

- 为 Velero server、CLI 和每个 provider/plugin 固定受支持版本，并验证 release checksum/signature。
- 使用受支持的对象存储后端和最小权限身份。provider 插件、storage location 参数、snapshot API 与凭据方式各不相同；按[官方安装文档](https://velero.io/docs/v1.18/)和插件文档确定命令，不能把旧 Azure recipe 当通用配置。
- 按恢复目标设计 API 对象、PV 数据和 etcd 的独立备份。数据库等有状态应用需要应用一致性钩子、原生复制或经验证的 volume snapshot 流程。
- 加密并限制备份库及凭据的访问，监控备份失效与保留策略，并定期在隔离环境演练恢复。

旧 Azure 示例会创建 Contributor 权限的 service principal、在本地写入明文凭据，并使用过时的 provider/配置参数；它不是安全的 Velero v1.18 部署指南，**不要照抄或运行**。请从当前 Azure 插件文档重新设计身份与存储配置。

## 创建并检查备份

先根据所选 provider 配置并验证 BackupStorageLocation 和必要的 VolumeSnapshotLocation，再查看 CLI 与集群状态：

```bash
velero version
velero backup-location get
velero plugin get
```

创建一次性备份，范围应按恢复需求选择：

```bash
velero backup create pre-upgrade-2026-10-05 \
  --include-namespaces production
velero backup describe pre-upgrade-2026-10-05 --details
velero backup logs pre-upgrade-2026-10-05
```

备份对象成功只表示所配置的操作完成，不证明应用数据一致或恢复可用。检查失败项、快照状态、对象存储内容及应用写入行为。

## 定期备份

```bash
velero schedule create production-daily \
  --schedule="0 7 * * *" \
  --include-namespaces production \
  --ttl 720h
velero schedule get
```

按业务 RPO、保留要求和 storage cost 调整排程与 TTL。仅对必要 namespace 建立备份，避免把临时凭据或无关测试资源无限期保留。

## 恢复与迁移

在恢复目标集群先部署兼容的 Velero server 与插件，再核对 BackupStorageLocation 只读状态、目标 namespace、StorageClass、CRD 和外部依赖。恢复前确认不会覆盖新集群中正在写入的对象：

```bash
velero backup get
velero backup describe <BACKUP_NAME> --details
velero restore create --from-backup <BACKUP_NAME>
velero restore get
velero restore describe <RESTORE_NAME>
```

迁移场景需确保两个集群访问同一受保护备份存储，并检查 PV 数据复制/恢复方式。Velero 不会自动迁移外部数据库、云负载均衡器、DNS、KMS 或其他集群外依赖。

## 参考资料

- [Velero v1.18 文档](https://velero.io/docs/v1.18/)
- [Velero v1.18.4 发布页](https://github.com/velero-io/velero/releases/tag/v1.18.4)
- [Kubeadm etcd 备份与恢复](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)
