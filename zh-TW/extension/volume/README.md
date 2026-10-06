# 儲存外掛

Kubernetes 已經提供豐富的 [Volume](../../concepts/objects/volume.md) 和 [Persistent Volume](../../concepts/objects/persistent-volume.md) 外掛，可以根據需要使用這些外掛給容器提供持久化儲存。

Kubernetes v1.33 中還引入了新的 image volume 功能（Beta），允許將容器映像檔作為 volume 掛載，詳見 [Volume 文件](../../concepts/objects/volume.md#image-卷)。

如果內建 Volume 不能滿足要求，應選擇由供應商維護、明確支援目標 Kubernetes 版本的 CSI 驅動。舊版 FlexVolume 已棄用，其歷史介面不再是新驅動的推薦方式。
