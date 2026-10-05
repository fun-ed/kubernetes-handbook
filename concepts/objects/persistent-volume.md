# PersistentVolume

PersistentVolume \(PV\) 和 PersistentVolumeClaim \(PVC\) 提供了方便的持久化卷：PV 提供网络存储资源，而 PVC 请求存储资源。这样，设置持久化的工作流包括配置底层文件系统或者云数据卷、创建持久性数据卷、最后创建 PVC 来将 Pod 跟数据卷关联起来。PV 和 PVC 可以将 pod 和数据卷解耦，pod 不需要知道确切的文件系统或者支持它的持久化引擎。

## Volume 生命周期

PV 可静态创建，也可由 StorageClass 动态供应；PVC 请求并绑定 PV，Pod 通过 PVC 使用该卷。卷状态包括 `Available`、`Bound`、`Released` 和 `Failed`。PVC/PV 的保护 finalizer 可延迟删除，回收策略决定释放后的存储资产如何处理。

## API 版本

| 资源 | Kubernetes v1.37 API |
| :--- | :--- |
| PersistentVolume、PersistentVolumeClaim | `v1` |
| StorageClass | `storage.k8s.io/v1` |

## PV

PersistentVolume（PV）是集群级存储资源，生命周期独立于单个 Pod。静态 NFS PV 可使用以下结构；`server` 和 `path` 必须对应已配置、可由节点访问的 NFS 导出，不能直接应用占位值：

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv0003
spec:
  capacity:
    storage: 5Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  nfs:
    path: /srv/nfs/k8s/example
    server: 203.0.113.10
```

PV 的访问模式（accessModes）有三种：

* `ReadWriteOnce`（RWO）：以读写方式挂载到单个 Node；具体能否多 Pod 共用还取决于存储实现
* `ReadOnlyMany`（ROX）：以只读方式挂载到多个 Node（需存储支持）
* `ReadWriteMany`（RWX）：以读写方式挂载到多个 Node（需存储支持）
* `ReadWriteOncePod`（RWOP）：限制卷只挂载到一个 Pod，需支持的 CSI driver

访问模式是挂载/绑定能力约束，不是所有存储都支持每种模式。

PV 的回收策略决定 PVC 释放后如何处理存储：

* `Retain` 保留底层存储及数据，由管理员按流程回收；
* `Delete` 删除 PV 及底层存储，仅在相应 provisioner/driver 支持时生效；
* `Recycle` 已弃用，不要用于新配置。

## StorageClass

StorageClass 描述动态供应卷的 provisioner、参数、回收策略和拓扑绑定行为。Kubernetes v1.37 的云盘和外部存储通常由 CSI driver 提供；in-tree 插件、FlexVolume、GlusterFS 等旧版示例已不适用于当前版本。请使用所选 CSI driver 维护者提供的 `storage.k8s.io/v1` 配置与兼容矩阵。

以下清单仅展示 API 形状；`csi.example.com` 是占位 provisioner，未安装对应 CSI driver 前不能创建可用卷。`allowVolumeExpansion` 也只有在 driver 明确支持扩容时才应启用：

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: example-csi
provisioner: csi.example.com
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer
```

未显式指定 StorageClass 的 PVC 只有在集群配置了默认 StorageClass 时才会被动态供应。默认 StorageClass 使用 annotation `storageclass.kubernetes.io/is-default-class: "true"`；修改集群默认类会影响之后创建的 PVC，应先核对集群中所有 StorageClass 与工作负载要求。

本页旧版 GCE PD、GlusterFS、Cinder、Ceph RBD 和其他 in-tree provisioner 示例仅作历史资料，不应复制到 Kubernetes v1.37。
## PVC

PV 是存储资源，而 PersistentVolumeClaim \(PVC\) 是对 PV 的请求。PVC 跟 Pod 类似：Pod 消费 Node 资源，而 PVC 消费 PV 资源；Pod 能够请求 CPU 和内存资源，而 PVC 请求特定大小和访问模式的数据卷。

```yaml
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: myclaim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 8Gi
  storageClassName: slow
  selector:
    matchLabels:
      release: "stable"
    matchExpressions:
      - {key: environment, operator: In, values: [dev]}
```

PVC 可以直接挂载到 Pod 中：

```yaml
kind: Pod
apiVersion: v1
metadata:
  name: mypod
spec:
  containers:
    - name: myfrontend
      image: nginx:1.30.5
      volumeMounts:
      - mountPath: "/var/www/html"
        name: mypd
  volumes:
    - name: mypd
      persistentVolumeClaim:
        claimName: myclaim
```

## 扩展 PV 空间

PersistentVolumeClaim 扩容已在 Kubernetes v1.24 达到 Stable，v1.37 不需要开启 `ExpandPersistentVolumes` feature gate。扩容前确认 StorageClass 设置了 `allowVolumeExpansion: true`，且所用 CSI driver、底层存储和文件系统支持在线或离线扩容。具体步骤请遵循该 CSI driver 的文档；旧版仅支持特定 in-tree 插件的清单不适用于当前版本。

扩容只支持增大请求，不支持缩小 PVC；扩容期间查看 PVC 状态、Events 及 CSI controller/node plugin 日志。参阅 [扩容 PersistentVolumeClaim](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#expanding-persistent-volumes-claims)。
## 块存储（Raw Block Volume）

`volumeMode: Block` 将支持的 PersistentVolume 以原始块设备提供给容器；它自 Kubernetes v1.18 起为 Stable，不需要开启 `BlockVolume` feature gate。是否可用取决于存储后端和 CSI driver 对块设备的支持。

原始块设备内容不会自动格式化。应用必须能安全操作设备，并通过 Pod 的 `volumeDevices` 选择目标设备路径。部署前按 CSI driver 文档确认设备映射、备份与权限要求；不要照搬旧版示例中的 Fiber Channel WWN、AppArmor Beta annotation、未固定 Fedora 镜像或 `SYS_ADMIN` 特权容器。
## StorageObjectInUseProtection

`StorageObjectInUseProtection` 会延迟删除仍被 Pod 使用的 PVC，以及仍绑定 PVC 的 PV，以避免丢失正在使用的存储对象。该准入功能已于 v1.11 达到 GA；标准集群通常会启用，不需要照搬旧版 `--admission-control` 参数。受保护的资源可能在使用结束前保持 `Terminating` 状态。
## PersistentVolume 删除保护 finalizer（v1.33 GA）

PV 删除保护 finalizer 确保采用 `Delete` 回收策略的 PV 在底层存储删除完成前不会从 API 中最终移除。相关机制自 v1.31 引入、在 v1.33 达到 Stable；v1.37 不需要配置已移除的 feature gate。

CSI 卷由 external-provisioner 管理时，可在静态或动态创建的 PV 上看到 `external-provisioner.volume.kubernetes.io/finalizer`。动态创建的 in-tree 卷使用 `kubernetes.io/pv-controller` finalizer。具体 finalizer 取决于供应方式、CSI external-provisioner 与 Kubernetes 版本。

finalizer 保留期间，PV 保持 `Terminating` 是异步清理的一部分。排错时检查 PVC、PV 的 `reclaimPolicy`、相关 CSI provisioner/controller 日志与底层存储状态；不要为消除 `Terminating` 手工移除 finalizer，否则可能遗留未清理的存储资产或造成数据丢失。
## 拓扑感知动态卷供应

卷的拓扑支持由 CSI driver、StorageClass 与集群调度配置共同决定。使用 `volumeBindingMode: WaitForFirstConsumer` 可让动态供应等待 Pod 调度信息，以便存储系统按其可用拓扑创建卷；请遵循实际 CSI driver 的拓扑文档。

## 存储容量评分（v1.37 Beta）

`StorageCapacityScoring` 自 v1.33 起为 Alpha，并在 v1.37 成为默认启用的 Beta。它通过 kube-scheduler 的 VolumeBinding 插件，在适用的延迟绑定动态卷场景中按存储容量评估节点；无需在 v1.37 手工开启该 feature gate。

该功能并不替代 CSI driver、StorageClass 或拓扑配置。启用前确认 CSI driver 会正确发布容量信息，并按集群调度配置文档检查 `WaitForFirstConsumer` 等卷供应要求。不要复用本页旧版的 GCE in-tree StorageClass、`failure-domain.beta.kubernetes.io/zone` 标签或无效的历史清单。

## 卷数据填充器（Volume Populators，GA）

卷数据填充器允许兼容的外部控制器在创建 PVC 时将自定义资源作为数据源。此机制在 v1.33 达到 GA；`AnyVolumeDataSource` feature gate 在 v1.37 已移除。Kubernetes API 负责表达数据源引用，实际数据复制由识别对应资源类型的 populator/controller 完成。

### 配置数据源

自定义 `dataSourceRef` 只有在相应 GVK 已注册、目标命名空间可见、且有能够处理该资源的 volume populator/controller 时才可用。以下资源名和 StorageClass 是占位符，不应在未部署对应 CRD、控制器与存储实现前直接应用：

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: populated-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: example-storageclass
  dataSourceRef:
    apiGroup: provider.example.com
    kind: Provider
    name: provider1
```

### 优势

1. **灵活性** - 支持从任意自定义资源初始化存储卷
2. **可扩展性** - 开发者可以创建特定的数据填充逻辑
3. **高效性** - 新的插件接口减少了资源开销
4. **自动化** - 支持自动清理和错误处理

### 常见用例

* **数据库初始化** - 从备份或模板初始化数据库存储卷
* **应用数据预填充** - 为应用预装配置文件或静态资源
* **多环境数据同步** - 在不同环境间同步数据状态
* **备份恢复** - 从备份系统恢复数据到新的存储卷

### 注意事项

* 需要相应的卷填充器控制器支持特定的自定义资源类型
* 数据填充过程可能需要一定时间，Pod 调度会等待填充完成
* 确保自定义资源和 PVC 在同一命名空间中

## 存储快照

VolumeSnapshot API 已由 CSI snapshot 机制提供，不再是本页所述的 v1.12 Alpha 功能。使用时需要兼容的 CSI driver、`snapshot.storage.k8s.io/v1` API/CRD 与 external-snapshotter 组件；并非所有存储后端都支持快照。

本页旧 `VolumeSnapshotDataSource` feature gate 和 `snapshot.storage.k8s.io/v1alpha1` manifests 已过时，不能在 Kubernetes v1.37 应用。应按 CSI driver 文档配置 `VolumeSnapshotClass`、创建 `VolumeSnapshot`，并遵循后端的保留、删除和恢复语义。参阅 [Volume Snapshots](https://kubernetes.io/docs/concepts/storage/volume-snapshots/)。
## 参考文档

* [Kubernetes Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
* [Kubernetes Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/)
* [Dynamic Volume Provisioning](https://kubernetes.io/docs/concepts/storage/dynamic-provisioning/)
* [Kubernetes CSI Documentation](https://kubernetes-csi.github.io/docs/)
* [Volume Snapshots Documentation](https://kubernetes.io/docs/concepts/storage/volume-snapshots/)
