# Volume

我们知道默认情况下容器的数据都是非持久化的，在容器消亡以后数据也跟着丢失，所以 Docker 提供了 Volume 机制以便将数据持久化存储。类似的，Kubernetes 提供了更强大的 Volume 机制和丰富的插件，解决了容器数据持久化和容器间共享数据的问题。

与 Docker 不同，Kubernetes Volume 的生命周期与 Pod 绑定

* 容器挂掉后 Kubelet 再次重启容器时，Volume 的数据依然还在
* 而 Pod 删除时，Volume 才会清理。数据是否丢失取决于具体的 Volume 类型，比如 emptyDir 的数据会丢失，而 PV 的数据则不会丢

## Volume 类型

目前，Kubernetes 支持以下 Volume 类型：

* emptyDir
* hostPath
* gcePersistentDisk
* awsElasticBlockStore
* nfs
* iscsi
* flocker
* glusterfs
* rbd
* cephfs
* gitRepo
* secret
* persistentVolumeClaim
* downwardAPI
* azureFileVolume
* azureDisk
* vsphereVolume
* Quobyte
* PortworxVolume
* ScaleIO
* FlexVolume
* StorageOS
* local
* image

注意，这些 volume 并非全部都是持久化的，比如 emptyDir、secret、gitRepo 等，这些 volume 会随着 Pod 的消亡而消失。

## API 版本对照表

| Kubernetes 版本 | Core API 版本 |
| :--- | :--- |
| v1.5+ | core/v1 |

## emptyDir

如果 Pod 设置了 emptyDir 类型 Volume， Pod 被分配到 Node 上时候，会创建 emptyDir，只要 Pod 运行在 Node 上，emptyDir 都会存在（容器挂掉不会导致 emptyDir 丢失数据），但是如果 Pod 从 Node 上被删除（Pod 被删除，或者 Pod 发生迁移），emptyDir 也会被删除，并且永久丢失。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-pd
spec:
  containers:
  - image: gcr.io/google_containers/test-webserver
    name: test-container
    volumeMounts:
    - mountPath: /cache
      name: cache-volume
  volumes:
  - name: cache-volume
    emptyDir: {}
```

## hostPath

hostPath 允许挂载 Node 上的文件系统到 Pod 里面去。如果 Pod 需要使用 Node 上的文件，可以使用 hostPath。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-pd
spec:
  containers:
  - image: gcr.io/google_containers/test-webserver
    name: test-container
    volumeMounts:
    - mountPath: /test-pd
      name: test-volume
  volumes:
  - name: test-volume
    hostPath:
      path: /data
```

## NFS

NFS 是 Network File System 的缩写，即网络文件系统。Kubernetes 中通过简单地配置就可以挂载 NFS 到 Pod 中，而 NFS 中的数据是可以永久保存的，同时 NFS 支持同时写操作。

```yaml
volumes:
- name: nfs
  nfs:
    # FIXME: use the right hostname
    server: 10.254.234.223
    path: "/"
```

## gcePersistentDisk

gcePersistentDisk 可以挂载 GCE 上的永久磁盘到容器，需要 Kubernetes 运行在 GCE 的 VM 中。

```yaml
volumes:
  - name: test-volume
    # This GCE PD must already exist.
    gcePersistentDisk:
      pdName: my-data-disk
      fsType: ext4
```

## awsElasticBlockStore

awsElasticBlockStore 可以挂载 AWS 上的 EBS 盘到容器，需要 Kubernetes 运行在 AWS 的 EC2 上。

```yaml
volumes:
  - name: test-volume
    # This AWS EBS volume must already exist.
    awsElasticBlockStore:
      volumeID: <volume-id>
      fsType: ext4
```

## gitRepo

gitRepo volume 将 git 代码下拉到指定的容器路径中

```yaml
  volumes:
  - name: git-volume
    gitRepo:
      repository: "git@somewhere:me/my-git-repository.git"
      revision: "22f1d8406d464b0c0874075539c1f2e96c253775"
```

## image

image volume 在 Kubernetes v1.33 成为 Beta，并自 v1.35 起默认启用；在 v1.37 仍为 Beta。它允许将容器镜像内容挂载为只读数据卷，具体支持情况取决于节点 CRI 运行时。

### 使用示例

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: image-volume-example
spec:
  containers:
  - name: shell
    image: debian
    volumeMounts:
    - name: volume
      mountPath: /volume
      subPath: dir
  volumes:
  - name: volume
    image:
      reference: quay.io/crio/artifact:v2
      pullPolicy: IfNotPresent
```

### 容器运行时支持

使用前确认所有目标 Node 上的 CRI 运行时与 Kubernetes 版本支持 image volume，并查阅相应运行时文档。`ImageVolume` feature gate 在 v1.35 起默认开启；不要照搬旧版“需要手动启用”步骤。

## 使用 subPath

Pod 的多个容器使用同一个 Volume 时，subPath 非常有用

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-lamp-site
spec:
    containers:
    - name: mysql
      image: mysql
      volumeMounts:
      - mountPath: /var/lib/mysql
        name: site-data
        subPath: mysql
    - name: php
      image: php
      volumeMounts:
      - mountPath: /var/www/html
        name: site-data
        subPath: html
    volumes:
    - name: site-data
      persistentVolumeClaim:
        claimName: my-lamp-site-data
```

## FlexVolume

如果内置的这些 Volume 不满足要求，则可以使用 FlexVolume 实现自己的 Volume 插件。注意要把 volume plugin 放到 `/usr/libexec/kubernetes/kubelet-plugins/volume/exec/<vendor~driver>/<driver>`，plugin 要实现 `init/attach/detach/mount/umount` 等命令（可参考 lvm 的 [示例](https://github.com/kubernetes/examples/tree/master/staging/volumes/flexvolume)）。

```yaml
  - name: test
    flexVolume:
      driver: "kubernetes.io/lvm"
      fsType: "ext4"
      options:
        volumeID: "vol1"
        size: "1000m"
        volumegroup: "kube_vg"
```

## Projected Volume

Projected volume 将多个 Volume 源映射到同一个目录中，支持 secret、downwardAPI 和 configMap。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: volume-test
spec:
  containers:
  - name: container-test
    image: busybox
    volumeMounts:
    - name: all-in-one
      mountPath: "/projected-volume"
      readOnly: true
  volumes:
  - name: all-in-one
    projected:
      sources:
      - secret:
          name: mysecret
          items:
            - key: username
              path: my-group/my-username
      - downwardAPI:
          items:
            - path: "labels"
              fieldRef:
                fieldPath: metadata.labels
            - path: "cpu_limit"
              resourceFieldRef:
                containerName: container-test
                resource: limits.cpu
      - configMap:
          name: myconfigmap
          items:
            - key: config
              path: my-group/my-config
```

## 本地临时存储

通过容器资源中的 `requests.ephemeral-storage` 和 `limits.ephemeral-storage` 声明本地临时存储请求与限制。它用于 kubelet 可计量的本地写入数据；实际计量能力还取决于节点文件系统布局和 kubelet 配置。`emptyDir.sizeLimit` 可限制单个 emptyDir 卷，但不会替代资源请求。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ephemeral-storage-example
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh", "-c", "sleep 3600"]
    resources:
      requests:
        ephemeral-storage: 64Mi
      limits:
        ephemeral-storage: 128Mi
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    emptyDir:
      sizeLimit: 64Mi
```

## Mount 传播

`mountPropagation` 控制容器与主机之间对挂载事件的可见性。默认 `None` 不传播额外挂载；`HostToContainer` 将主机侧新挂载传播到容器；`Bidirectional` 允许双向传播，权限影响很大，通常只供需要挂载操作的系统级代理使用。只在确认节点、运行时和应用安全要求后配置双向传播。

`MountPropagation` feature gate 已在较早版本中毕业并移除；v1.37 不需要开启该 gate。参阅 [Mount propagation](https://kubernetes.io/docs/concepts/storage/volumes/#mount-propagation)。

## Volume 快照

VolumeSnapshot API 由 CSI snapshot 组件提供，并非所有存储驱动都支持。使用前确认目标 CSI driver、外部 snapshot-controller 与 CRD 均受维护且兼容集群；应用 `snapshot.storage.k8s.io/v1` 清单时应遵循该存储驱动的官方流程。

参阅 [Volume Snapshots](https://kubernetes.io/docs/concepts/storage/volume-snapshots/) 与所选 CSI driver 文档。

## Windows 卷

Windows 节点可用卷类型及挂载路径受 Windows Server、CRI 运行时、CSI 驱动和 Kubernetes Node 版本限制。使用符合目标主机版本的 Windows 容器镜像与驱动说明；不要照搬旧 Windows Server 1709、`microsoft/nanoserver` 或 FlexVolume 示例。

部署前核对 [Windows 存储文档](https://kubernetes.io/docs/concepts/storage/windows-storage/)及所选 CSI 驱动的兼容矩阵。Windows 容器路径使用 Windows 路径格式，且不能访问 Linux Node 的主机路径。

## 卷数据填充器（Volume Populators，GA）

卷数据填充器支持在 PVC 的 `dataSourceRef` 中引用自定义资源。此机制在 v1.33 达到 GA；`AnyVolumeDataSource` feature gate 在 v1.37 已移除。数据填充需要集群安装能识别相应 GVK 的外部控制器，Kubernetes API 本身不会实现数据复制。

示例中 `backup.example.com/BackupSource` 与 StorageClass 是占位符；只有在集群已安装 CRD、populator/controller 和对应存储实现后才可使用：

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: example-storage
  dataSourceRef:
    apiGroup: backup.example.com
    kind: BackupSource
    name: app-backup
```

## 挂载传播

[挂载传播（MountPropagation）](https://www.kernel.org/doc/Documentation/filesystems/sharedsubtree.txt)是 v1.9 引入的新功能，并在 v1.10 中升级为 Beta 版本。挂载传播用来解决同一个 Volume 在不同的容器甚至是 Pod 之间挂载的问题。通过设置 \`Container.volumeMounts.mountPropagation），可以为该存储卷设置不同的传播类型。

支持三种选项：

* None：即私有挂载（private）
* HostToContainer：即 Host 内在该目录中的新挂载都可以在容器中看到，等价于 Linux 内核的 rslave。
* Bidirectional：即 Host 内在该目录中的新挂载都可以在容器中看到，同样容器内在该目录中的任何新挂载也都可以在 Host 中看到，等价于 Linux 内核的 rshared。仅特权容器（privileged）可以使用 Bidirectional 类型。

注意：

* 使用前需要开启 MountPropagation 特性
* 如未设置，则 v1.9 和 v1.10 中默认为私有挂载（`None`），而 v1.11 中默认为 `HostToContainer`
* Docker 服务的 systemd 配置文件中需要设置 `MountFlags=shared`

## 其他的 Volume 参考示例

[https://github.com/kubernetes/examples/tree/master/staging/volumes/iscsi](https://github.com/kubernetes/examples/tree/master/staging/volumes/iscsi)

* [iSCSI Volume 示例](https://github.com/kubernetes/examples/tree/master/staging/volumes/iscsi)
* [cephfs Volume 示例](https://github.com/kubernetes/examples/tree/master/staging/volumes/cephfs)
* [Flocker Volume 示例](https://github.com/kubernetes/examples/tree/master/staging/volumes/flocker)
* [GlusterFS Volume 示例](https://github.com/kubernetes/examples/tree/master/staging/volumes/glusterfs)
* [RBD Volume 示例](https://github.com/kubernetes/examples/tree/master/staging/volumes/rbd)
* [Secret Volume 示例](secret.md)
* [downwardAPI Volume 示例](https://kubernetes.io/docs/tasks/inject-data-application/downward-api-volume-expose-pod-information/)
* [AzureFile Volume 示例](https://github.com/kubernetes/examples/tree/master/staging/volumes/azure_file)
* [AzureDisk Volume 示例](https://github.com/kubernetes/examples/tree/master/staging/volumes/azure_disk)
* [Quobyte Volume 示例](https://github.com/kubernetes/examples/tree/master/staging/volumes/quobyte)
* [Portworx Volume 示例](https://github.com/kubernetes/examples/tree/master/staging/volumes/portworx)
* [ScaleIO Volume 示例](https://github.com/kubernetes/examples/tree/master/staging/volumes/scaleio)
* [StorageOS Volume 示例](https://github.com/kubernetes/examples/tree/master/staging/volumes/storageos)

