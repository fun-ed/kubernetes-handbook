# 容器存储接口 CSI

Container Storage Interface（CSI）是 Kubernetes 与存储插件之间的标准接口。Kubernetes 自 v1.13 起稳定支持 CSI；v1.37.1 使用 `storage.k8s.io/v1` API。CSI 规范与 sidecar 有各自独立的版本，选择驱动时必须同时核对驱动厂商提供的 Kubernetes、CSI、sidecar 和存储后端支持范围。

截至 2026-10-05，CSI Spec 最新稳定版本为 [v1.13.0](https://github.com/container-storage-interface/spec/releases/tag/v1.13.0)。上游 Kubernetes CSI sidecar 最新稳定 tag 和兼容性证据见[组件版本表](../../setup/component-versions.md#可安装插件与附加组件)；“最新 tag”不代表该版本已由特定 CSI 驱动验证或提供 Kubernetes v1.37 兼容保证。

## 部署架构

CSI driver 实现 CSI gRPC 的 Identity、Node，以及可选的 Controller 服务。Kubelet 在每个使用该驱动的节点上通过 Unix socket 调用 Node 服务，因此节点服务通常以 DaemonSet 运行，并使用驱动文档要求的 kubelet plugin registration/socket hostPath 和权限。Controller 服务及 sidecar 常以 Deployment 运行；实际副本、leader election 和权限应依驱动文档部署，不要求所有驱动都使用同一种工作负载布局。

Kubernetes control plane 组件通过 Kubernetes API 工作，不会直接连接驱动的 Unix socket；需要编排卷生命周期的 CSI sidecar 观察 API 对象并调用 CSI Controller 服务。常见的可选 sidecar 包括：

| Sidecar | 用途 | 上游项目 |
| :--- | :--- | :--- |
| external-provisioner | 观察 PVC 并触发动态卷创建 | [external-provisioner](https://github.com/kubernetes-csi/external-provisioner) |
| external-attacher | 协调 VolumeAttachment 与 attach/detach 操作 | [external-attacher](https://github.com/kubernetes-csi/external-attacher) |
| external-resizer | 协调 PVC 扩容 | [external-resizer](https://github.com/kubernetes-csi/external-resizer) |
| external-snapshotter | 协调快照生命周期 | [external-snapshotter](https://github.com/kubernetes-csi/external-snapshotter) |
| node-driver-registrar | 向 kubelet 注册节点插件 | [node-driver-registrar](https://github.com/kubernetes-csi/node-driver-registrar) |
| livenessprobe | 为 driver 提供存活检查端点 | [livenessprobe](https://github.com/kubernetes-csi/livenessprobe) |

部署前应按[sidecar 项目策略](https://kubernetes-csi.github.io/docs/project-policies.html)、具体 tag 的发布说明以及驱动厂商矩阵协调版本。`cluster-driver-registrar` 已弃用，不要用于新驱动；驱动应直接部署 `storage.k8s.io/v1` `CSIDriver` 对象。

## CSIDriver 对象和节点可分配卷数

`CSIDriver.metadata.name` 必须与驱动返回的 CSI plugin name 完全一致。以下是 `nodeAllocatableUpdatePeriodSeconds` 用法示例；该字段从 Kubernetes v1.33 引入，`MutableCSINodeAllocatableCount` 自 v1.36 起稳定，v1.37 默认启用。字段最小值为 10 秒；仅在驱动支持更新 CSINode 可分配卷数、且需要周期刷新时设置。

```yaml
apiVersion: storage.k8s.io/v1
kind: CSIDriver
metadata:
  name: example.csi.k8s.io
spec:
  attachRequired: true
  nodeAllocatableUpdatePeriodSeconds: 60
```

Kubernetes v1.37 不需要为普通 CSI 驱动启用旧的 `CSIPersistentVolume`、`MountPropagation` 或 `CustomResourceValidation` feature gates，也不需要打开 `storage.k8s.io/v1alpha1` API。它们是历史配置；不要照抄旧文档中的 kube-apiserver、controller-manager 或 kubelet flags。字段默认值、功能 gate 历史和组件配置应以 [v1.37 CSIDriver API](https://kubernetes.io/docs/reference/kubernetes-api/storage/csi-driver-v1/) 和 [feature gate 参考](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/) 为准。

## 快照与 PVC 数据源

CSI 快照使用 `snapshot.storage.k8s.io/v1` 的 `VolumeSnapshot` / `VolumeSnapshotContent` 等独立 CRD。使用 upstream `external-snapshotter` v8.6.0 时，集群需安装匹配版本的 snapshot CRD 和 snapshot-controller；CRD schema 使用 CEL 校验，不需要单独部署旧的 validating webhook。该 webhook 在 v8.0.0 起弃用，并在后续版本移除，详见 [v8.0.0 变更记录](https://github.com/kubernetes-csi/external-snapshotter/blob/v8.6.0/CHANGELOG/CHANGELOG-8.0.md) 和 [v8.6.0 VolumeSnapshot CRD](https://github.com/kubernetes-csi/external-snapshotter/blob/v8.6.0/client/config/crd/snapshot.storage.k8s.io_volumesnapshots.yaml)。CSI 驱动还需支持对应的 snapshot RPC，并部署匹配版本的 `external-snapshotter` sidecar。VolumeGroupSnapshot v1beta1/v1beta2 API 转换所需的 conversion webhook 是另一项可选组件，参见 [v8.6.0 安装说明](https://github.com/kubernetes-csi/external-snapshotter/blob/v8.6.0/README.md)。不要假定安装驱动会自动安装集群级 snapshot CRD/controller。

`PersistentVolumeClaim.spec.dataSourceRef` 可引用自定义数据源，但 volume populator 是配套的数据源 CRD 与控制器机制，不是 CSI 驱动在 `CSIDriver.spec` 中声明的 `populatorPolicy`。部署自定义数据源前必须安装相应 populator/controller 并遵循该项目文档；本文旧示例中的 `CSIDriver.spec.populatorPolicy` 不是 Kubernetes v1.37.1 有效字段。

## 旧示例说明

本页早期版本中的 NFS driver `git clone`、master 分支 manifest、`csi.volume.kubernetes.io/volume-attributes` PV annotation 和 CSI sidecar v1.0.x 表格均为历史材料，版本过旧且不应部署。v1.37.1 环境应按具体驱动官方文档选择版本化镜像、权限、RBAC、StorageClass、Secret 和拓扑配置；不要使用 mutable `master` 安装链接。

## 参考文档

* [Kubernetes CSI Developer Documentation](https://kubernetes-csi.github.io/docs/)
* [CSI Sidecar Containers](https://kubernetes-csi.github.io/docs/sidecar-containers.html)
* [CSI 项目策略](https://kubernetes-csi.github.io/docs/project-policies.html)
* [Kubernetes CSI volumes](https://kubernetes.io/docs/concepts/storage/volumes/#csi)
* [Storage API reference](https://kubernetes.io/docs/reference/kubernetes-api/config-and-storage-resources/)
