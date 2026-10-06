# 存储插件

Kubernetes 已经提供丰富的 [Volume](../../concepts/objects/volume.md) 和 [Persistent Volume](../../concepts/objects/persistent-volume.md) 插件，可以根据需要使用这些插件给容器提供持久化存储。

Kubernetes v1.33 中还引入了新的 image volume 功能（Beta），允许将容器镜像作为 volume 挂载，详见 [Volume 文档](../../concepts/objects/volume.md#image-卷)。

如果内置 Volume 不能满足要求，应选择由供应商维护、明确支持目标 Kubernetes 版本的 CSI 驱动。旧版 FlexVolume 已弃用，其历史接口不再是新驱动的推荐方式。

[Longhorn](longhorn.md) 是 Kubernetes 的分散式区块储存系统；使用前请依该章的相容性与儲存需求檢查，避免將 CSI 驅動支援誤當成整體叢集或資料路徑的保證。

