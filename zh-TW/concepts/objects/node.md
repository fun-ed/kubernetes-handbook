# Node

Node 是 Pod 實際執行的主機，可以是實體機或虛擬機器。每個 Node 都需要 kubelet 和符合 CRI 的容器執行時。kube-proxy 通常負責實作 Service 網路，但部分網路實作會取代它。

![node](../../.gitbook/assets/node%20%284%29.png)

## Node 管理

不像其他的資源（如 Pod 和 Namespace），Node 本質上不是 Kubernetes 來建立的，Kubernetes 只是管理 Node 上的資源。雖然可以透過 Manifest 建立一個 Node 物件（如下 yaml 所示），但 Kubernetes 也只是去檢查是否真的是有這麼一個 Node，如果檢查失敗，也不會往上排程 Pod。

```yaml
kind: Node
apiVersion: v1
metadata:
  name: 10-240-79-157
  labels:
    name: my-first-k8s-node
```

這個檢查是由 Node Controller 來完成的。Node Controller 負責

* 維護 Node 狀態
* 與 Cloud Provider 同步 Node
* 給 Node 分配容器 CIDR
* 刪除帶有 `NoExecute` taint 的 Node 上的 Pods

預設情況下，kubelet 在啟動時會向 master 註冊自己，並建立 Node 資源。

## Node 的狀態

每個 Node 都包括以下狀態資訊：

* 位址：包含 hostname、外部 IP 和內部 IP
* 條件（Condition）：包含 Ready、MemoryPressure、DiskPressure、PIDPressure 等狀態；OutOfDisk 已移除
* 容量（Capacity）：Node 上的總資源，包括 CPU、記憶體和 Pod 數量
* 可分配（Allocatable）：扣除系統保留後，可分配給 Pod 的資源量；部分資源限制取決於叢集設定
* 基本資訊（Info）：包含核心、容器執行時與作業系統版本等資訊

## Taints 和 tolerations

Taints 和 tolerations 用於保證 Pod 不被排程到不合適的 Node 上，Taint 應用於 Node 上，而 toleration 則應用於 Pod 上（Toleration 是可選的）。

比如，可以使用 taint 命令給 node1 新增 taints：

```bash
kubectl taint nodes node1 key1=value1:NoSchedule
kubectl taint nodes node1 key1=value2:NoExecute
```

Taints 和 tolerations 的具體使用方法請參考 [排程器章節](../components/scheduler.md#taints-和-tolerations)。

## Node 維護模式

標誌 Node 不可排程但不影響其上正在執行的 Pod，這在維護 Node 時是非常有用的：

```bash
kubectl cordon $NODENAME
```

## Node 優雅關閉

當設定 `ShutdownGracePeriod` 和 `ShutdownGracePeriodCriticalPods` 後，Kubelet 會根據 systemd 事件檢測 Node 的關閉狀態，並自動終止其上執行的 Pod（ShutdownGracePeriodCriticalPods 需要小於 ShutdownGracePeriod）。注意，這兩個引數預設設定為 0，即優雅關閉特性預設是未開啟的。

比如，如果 ShutdownGracePeriod 設定為 30s，而 ShutdownGracePeriodCriticalPods 設定為 10s，那麼 Kubelet 將使節點關閉延遲 30 秒。 在關閉期間，將保留前20（30-10）秒以終止普通 Pod，而保留最後 10 秒以終止關鍵 Pod。

## Node 非優雅關閉

在 Node 發生異常的情況下，Kubelet 可能沒有機會檢測並執行優雅關閉。在這種情況下，StatefulSet 無法建立同名的新 Pod，如果 Pod 使用了卷，則 VolumeAttachments 不會從原來的已關閉節點上刪除，因此這些 Pod 所使用的卷也無法掛接到新的執行節點上。

Node 非優雅關閉正是為了解決這些問題。使用者可以手動將具有 `NoExecute` 或 `NoSchedule` 效果的 `node.kubernetes.io/out-of-service` 汙點新增到節點上，標記其無法提供服務。如果在 kube-controller-manager 上啟用了 `NodeOutOfServiceVolumeDetach` 特性，並且 Pod 上沒有設定對應的容忍度，那麼這些 Pod 將被強制刪除，並且該在節點上被終止的 Pod 將立即進行卷解除安裝操作。這樣就允許那些在無法提供服務節點上的 Pod 能在其他節點上快速恢復。

## 動態節點資源分配

`MutableCSINodeAllocatableCount` 在 v1.33 以 Alpha 引入，v1.34 升為 Beta，並自 v1.35 起預設啟用；v1.37 中仍為 Beta。它允許 CSI 驅動更新節點可分配的卷附件數量，讓排程器使用較新的限制資訊。CSI 驅動與 kubelet 必須支援此功能；行為與設定細節請依目標 CSI 驅動文件確認。

此功能受 `MutableCSINodeAllocatableCount` feature gate 控制。v1.37 預設已啟用，除非有明確需要，勿為此額外設定 feature gate。參閱 [CSI 章節](../../extension/volume/csi.md#csidriver-物件和節點可分配卷數)與[v1.37.1 feature gate 原始碼](https://github.com/kubernetes/kubernetes/blob/v1.37.1/pkg/features/kube_features.go)。

## 參考文件

* [Kubernetes Node](https://kubernetes.io/docs/concepts/architecture/nodes/)
* [Taints 和 tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)
