# Longhorn 分布式块存储

本文以 Kubernetes v1.37.1 为背景。截至 2026-10-05，Longhorn 最新稳定版为 **v1.13.0**，官方 [v1.13.0 release](https://github.com/longhorn/longhorn/releases/tag/v1.13.0) 发布于 2026-09-29；同一 tag 的 Helm chart 版本和 appVersion 均为 `1.13.0`，chart 要求 Kubernetes `>=1.34.0-0`。Longhorn release notes 也指出 v1.13.0 的 CSI external-provisioner v6.3.0 要求 Kubernetes v1.34 或更新版本。v1.37.1 满足此下限，但这不等同于 Longhorn 对每种作业系统、核心、CNI 或硬件的认证。请以 [安装需求](https://longhorn.io/docs/1.13.0/deploy/install/)、[最佳实务](https://longhorn.io/docs/1.13.0/best-practices/)及发行说明为准。

Longhorn 通过 CSI 为 Pod 提供可复制的区块磁盘区。它不是 Kubernetes 内置储存，也不会替代集群 CNI。部署前需已有可运作的 CNI、DNS、StorageClass 管理方案，以及符合需求的 Linux 节点与数据磁盘。以下命令仅供隔离实验室参考，本章未执行这些命令，也不应直接套用到使用者集群。

## 架构与数据引擎

`longhorn-manager` 管理 Longhorn 资源、节点磁盘及卷生命周期；v1.13 引入 `longhorn-global-manager` Deployment，分担集群范围的 PersistentVolume 与 Pod 控制器工作。Longhorn CSI controller sidecars 通过 Kubernetes API 观察 PVC，并呼叫 CSI controller；节点上的 CSI plugin 以 `driver.longhorn.io` 名称向 kubelet 注册，负责 stage/publish 磁盘区。CSI provisioner 名称是 `driver.longhorn.io`，`StorageClass.provisioner` 必须使用此值。Longhorn 自定义资源由其 CRD 定义，例如 `longhorn.io/v1beta2` 的 `Volume`、`Node`、`Engine` 与 `Replica`。安装 CRD 不代表内置 Kubernetes schema 能验证这些自定义字段。

V1 data engine 使用 Longhorn engine 管理网络块 I/O；文件系统类型磁盘是常见数据存储配置，节点需安装并启用 `open-iscsi`/`iscsid`，以便节点挂载 iSCSI target。V2 data engine 基于 SPDK，使用 `block-type` 磁盘；需要 VFIO/UIO/NVMe-TCP 内核模块、IOMMU 组隔离、大页内存与额外 CPU/内存，并非只切换设置即可。官方 V2 最低建议仍为三节点及通用基础硬件配置，另每节点预留 1 CPU 核心与 2 GiB 大页内存，并使用 `vfio_pci`、`uio_pci_generic`、`nvme-tcp` 模块；NVMe/TCP 最低内核为 5.19，官方建议 6.7 或更新版本以改善稳定性。V2 的 SPDK NVMe 磁盘需有可隔离 IOMMU 组，或使用文档允许的替代 AIO 模式。V2 不应套用 V1 专属的 iSCSI 主机依赖。v1.13 release 将 V2 标为 GA，但其中 UBLK frontend 仍是实验性功能，勿将该状态套用至整个 V2 引擎。v1.13 建议每个集群只启用其中一种引擎以免增加资源消耗。本文实验只使用默认 V1；不设置 V2 主机需求或功能。

Longhorn 一般安装需求包括可执行 root/privileged 工作负载、启用 mount propagation、基本主机命令（`bash`、`curl`、`findmnt`、`grep`、`awk`、`blkid`、`lsblk`）及容器执行环境。V1 每个节点要安装 iSCSI initiator；Debian/Ubuntu 使用 `open-iscsi`，RHEL 系统通常使用 `iscsi-initiator-utils`，请依发行版文档确认服务名称与启用方式。官方建议 V1 最低参考为三节点、每节点 4 vCPU、4 GiB RAM 及本机磁盘；这是建议硬件，不是 Helm 强制检查值。根磁盘保留率默认 25%；专用数据磁盘可按官方指引评估 10%。生产环境使用独立磁盘并确保重启后挂载路径不变。v1.13 发行测试列出的作业系统包括 Ubuntu 26.04、SLES 16.0、SLE Micro 6.1、RHEL/Oracle/Rocky Linux 10.2、Talos 1.13.4 及 GKE Container-Optimized OS 125；这是该版本测试清单，不代表其他 Linux 系统必然不支持。

## 隔离实验室安装

先确认集群版本及三个或更多可排程的 Linux 节点。此范例的 `numberOfReplicas: "3"` 要求至少三个符合磁盘与节点排程条件的 Longhorn 节点；未达条件时 PVC 会无法创建完整副本，不可借由隐藏 degraded 状态当作成功。确认现有 CNI 已支持一般 Pod 通讯；Longhorn 不安装 CNI。先依官方文件安装主机需求并核对磁盘，勿把安装套件命令交给集群工作负载执行。

以下 Helm 命令将安装固定 chart 版本至新命名空间。`--wait` 等候资源就绪，但不会验证真实磁盘 I/O、备份或灾难复原。

```bash
helm repo add longhorn https://charts.longhorn.io
helm repo update
helm show chart longhorn/longhorn --version 1.13.0
helm install longhorn longhorn/longhorn \
  --namespace longhorn-system --create-namespace \
  --version 1.13.0 --wait --timeout 10m
```

创建非默认 StorageClass，明确设定三副本和 `Retain`。这避免删除 PVC 时由 reclaim policy 自动删除底层 PV/Longhorn volume，但保留数据仍需管理员按照程序回收。

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: longhorn-lab-retain
provisioner: driver.longhorn.io
allowVolumeExpansion: true
reclaimPolicy: Retain
volumeBindingMode: Immediate
parameters:
  dataEngine: "v1"
  numberOfReplicas: "3"
  dataLocality: disabled
  fsType: ext4
```

```bash
kubectl apply -f longhorn-storageclass.yaml
kubectl get storageclass longhorn-lab-retain
```

使用小型官方 BusyBox 1.37.0 映像档创建 PVC 与写入档案的消费端。PVC 指定实验 StorageClass，Pod 将 volume 挂载至 `/data`。完成后在同一 Pod 中读回内容，才算测过基本挂载及写入路径。

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: longhorn-lab-data
  namespace: default
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: longhorn-lab-retain
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: longhorn-lab-writer
  namespace: default
spec:
  restartPolicy: Never
  containers:
    - name: writer
      image: busybox:1.37.0
      command: ["sh", "-c", "echo longhorn-ok > /data/health.txt && cat /data/health.txt && sleep 3600"]
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: longhorn-lab-data
```

```bash
kubectl apply -f longhorn-lab.yaml
kubectl -n default wait --for=jsonpath='{.status.phase}'=Bound pvc/longhorn-lab-data --timeout=5m
kubectl -n default wait --for=condition=Ready pod/longhorn-lab-writer --timeout=5m
kubectl -n default exec longhorn-lab-writer -- cat /data/health.txt
```

预期 PVC 为 `Bound`，Pod 为 `Running`，读回 `longhorn-ok`。这只证明单一实验 Pod 的基本写入/读取，不验证节点失效复原、磁盘耐久性、性能或备份还原。不要用默认自动创建的 StorageClass 代替此明确指定的实验类别。

## UI 与唯读检查

UI 默认不应公开到公网。隔离实验室可用本机 port-forward，仅监听 loopback；Service 名称请先由唯读查询确认。

```bash
kubectl -n longhorn-system get svc
kubectl -n longhorn-system port-forward --address 127.0.0.1 svc/longhorn-frontend 8080:80
```

只在本机浏览 `http://127.0.0.1:8080`。不要创建无认证的 LoadBalancer/Ingress，也不要把 UI 管理权限交给一般使用者。

```bash
kubectl -n longhorn-system get pods -o wide
kubectl -n longhorn-system get pods -o wide | grep -E 'csi|manager|engine-image|instance-manager'
kubectl -n longhorn-system get volumes.longhorn.io
kubectl -n longhorn-system get replicas.longhorn.io
kubectl -n longhorn-system get nodes.longhorn.io
kubectl get csidrivers.storage.k8s.io driver.longhorn.io
kubectl get csinodes
kubectl -n default describe pvc longhorn-lab-data
kubectl -n default describe pod longhorn-lab-writer
kubectl get volumeattachments.storage.k8s.io
```

`longhorn-manager`、CSI controller 与节点 plugin Pod 应就绪；Volume 应显示健康状态及预期副本数，PVC 绑定，`CSIDriver` 和包含 `driver.longhorn.io` 的 `CSINode` 资讯可供确认注册。`describe` 的 Events 用来区分 provisioner、排程、attach、mount 问题。这些查询唯读，成功不代表数据已有备份。若 Pod 卡在 Pending，检查 StorageClass/provisioner、至少三个可用节点、磁盘可排程空间及事件；若 attach/mount 失败，检查 iSCSI 服务、节点 CSI plugin、mount propagation、核心日志及 Longhorn volume/replica CR 状态。勿直接删除 Volume 或 Replica CR 排错。

## 备份、扩容与维护

副本是同一个线上磁盘区的即时副本，不是备份。操作错误、勒索软体、集群或多节点同时故障可能影响所有副本。设定外部 backup target（例如受保护的物件储存或独立 NFSv4 备份端），限制凭证权限，创建排程备份并监控完成状态。在隔离环境将备份还原成新 volume，启动测试消费端并验证应用数据，才有可用的还原证据；CSI snapshot 或同一磁盘上的副本不能取代外部备份。

StorageClass 开启 `allowVolumeExpansion` 仅表示 Kubernetes 可请求扩容，仍须确认 Longhorn 及档案系统支持。修改 PVC 的储存请求会扩大卷，不能缩小。离线扩容可先停止使用 Pod 再变更 PVC；线上扩容是否完成 filesystem resize，取决于 CSI、档案系统及 kubelet，检查 PVC conditions/events 与容器内 `df -h`。先备份并在测试卷验证，勿假定所有工作负载都支持线上扩容。

维护节点前确认所有卷有足够健康副本及其他节点的磁盘容量；依 Longhorn 节点维护程序先禁用磁盘排程或迁移副本，配合 Kubernetes drain 时逐一确认使用中的卷及应用可用性。磁盘故障时先保留故障磁盘与日志，不要格式化、清除 `/var/lib/longhorn` 或删除 Replica 资源；依健康副本重建或使用备份还原，并核对数据完整性。升级前备份应用数据和 Longhorn 系统状态，阅读逐版升级路径及 V2 引擎特殊条件；v1.13 V2 live upgrade 只支持特定前版与前置条件。控制器降版不会自动回复数据格式或卷状态，不可把 Helm rollback 当成安全数据回复方案。按官方 [升级指南](https://longhorn.io/docs/1.13.0/deploy/upgrade/)规划及先在隔离环境演练。

## 来源

- [Longhorn v1.13.0 release notes](https://github.com/longhorn/longhorn/releases/tag/v1.13.0)
- [v1.13.0 Helm chart metadata](https://github.com/longhorn/longhorn/blob/v1.13.0/chart/Chart.yaml)
- [安装与主机需求](https://longhorn.io/docs/1.13.0/deploy/install/)
- [最佳实务与硬件、作业系统、磁盘建议](https://longhorn.io/docs/1.13.0/best-practices/)
- [v1.13.0 StorageClass 参数](https://longhorn.io/docs/1.13.0/references/storage-class-parameters/)
- [Longhorn CSI](https://longhorn.io/docs/1.13.0/deploy/install/#installation-requirements)
