# 容器儲存介面 CSI

Container Storage Interface（CSI）是 Kubernetes 與儲存外掛之間的標準介面。Kubernetes 自 v1.13 起穩定支援 CSI；v1.37.1 使用 `storage.k8s.io/v1` API。CSI 規範與 sidecar 有各自獨立的版本，選擇驅動時必須同時核對驅動廠商提供的 Kubernetes、CSI、sidecar 和儲存後端支援範圍。

截至 2026-10-05，CSI Spec 最新穩定版本為 [v1.13.0](https://github.com/container-storage-interface/spec/releases/tag/v1.13.0)。上游 Kubernetes CSI sidecar 最新穩定 tag 和相容性證據見[元件版本表](../../setup/component-versions.md#可安裝外掛與附加元件)；「最新 tag」不代表該版本已由特定 CSI 驅動驗證或提供 Kubernetes v1.37 相容保證。

## 部署架構

CSI driver 實現 CSI gRPC 的 Identity、Node，以及可選的 Controller 服務。Kubelet 在每個使用該驅動的節點上透過 Unix socket 呼叫 Node 服務，因此節點服務通常以 DaemonSet 執行，並使用驅動文件要求的 kubelet plugin registration/socket hostPath 和權限。Controller 服務及 sidecar 常以 Deployment 執行；實際副本、leader election 和權限應依驅動文件部署，不要求所有驅動都使用同一種工作負載佈局。

Kubernetes control plane 元件透過 Kubernetes API 工作，不會直接連線驅動的 Unix socket；需要編排卷生命週期的 CSI sidecar 觀察 API 物件並呼叫 CSI Controller 服務。常見的可選 sidecar 包括：

| Sidecar | 用途 | 上游專案 |
| :--- | :--- | :--- |
| external-provisioner | 觀察 PVC 並觸發動態卷建立 | [external-provisioner](https://github.com/kubernetes-csi/external-provisioner) |
| external-attacher | 協調 VolumeAttachment 與 attach/detach 操作 | [external-attacher](https://github.com/kubernetes-csi/external-attacher) |
| external-resizer | 協調 PVC 擴容 | [external-resizer](https://github.com/kubernetes-csi/external-resizer) |
| external-snapshotter | 協調快照生命週期 | [external-snapshotter](https://github.com/kubernetes-csi/external-snapshotter) |
| node-driver-registrar | 向 kubelet 註冊節點外掛 | [node-driver-registrar](https://github.com/kubernetes-csi/node-driver-registrar) |
| livenessprobe | 為 driver 提供存活檢查端點 | [livenessprobe](https://github.com/kubernetes-csi/livenessprobe) |

部署前應按[sidecar 專案策略](https://kubernetes-csi.github.io/docs/project-policies.html)、具體 tag 的釋出說明以及驅動廠商矩陣協調版本。`cluster-driver-registrar` 已棄用，不要用於新驅動；驅動應直接部署 `storage.k8s.io/v1` `CSIDriver` 物件。

## CSIDriver 物件和節點可分配卷數

`CSIDriver.metadata.name` 必須與驅動返回的 CSI plugin name 完全一致。以下是 `nodeAllocatableUpdatePeriodSeconds` 用法範例；該欄位從 Kubernetes v1.33 引入，`MutableCSINodeAllocatableCount` 自 v1.36 起穩定，v1.37 預設啟用。欄位最小值為 10 秒；僅在驅動支援更新 CSINode 可分配卷數、且需要週期重新整理時設定。

```yaml
apiVersion: storage.k8s.io/v1
kind: CSIDriver
metadata:
  name: example.csi.k8s.io
spec:
  attachRequired: true
  nodeAllocatableUpdatePeriodSeconds: 60
```

Kubernetes v1.37 不需要為普通 CSI 驅動啟用舊的 `CSIPersistentVolume`、`MountPropagation` 或 `CustomResourceValidation` feature gates，也不需要開啟 `storage.k8s.io/v1alpha1` API。它們是歷史設定；不要照抄舊文件中的 kube-apiserver、controller-manager 或 kubelet flags。欄位預設值、功能 gate 歷史和元件設定應以 [v1.37 CSIDriver API](https://kubernetes.io/docs/reference/kubernetes-api/storage/csi-driver-v1/) 和 [feature gate 參考](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/) 為準。

## 快照與 PVC 資料來源

CSI 快照使用 `snapshot.storage.k8s.io/v1` 的 `VolumeSnapshot` / `VolumeSnapshotContent` 等獨立 CRD。使用 upstream `external-snapshotter` v8.6.0 時，叢集需安裝匹配版本的 snapshot CRD 和 snapshot-controller；CRD schema 使用 CEL 驗證，不需要單獨部署舊的 validating webhook。該 webhook 在 v8.0.0 起棄用，並在後續版本移除，詳見 [v8.0.0 變更記錄](https://github.com/kubernetes-csi/external-snapshotter/blob/v8.6.0/CHANGELOG/CHANGELOG-8.0.md) 和 [v8.6.0 VolumeSnapshot CRD](https://github.com/kubernetes-csi/external-snapshotter/blob/v8.6.0/client/config/crd/snapshot.storage.k8s.io_volumesnapshots.yaml)。CSI 驅動還需支援對應的 snapshot RPC，並部署匹配版本的 `external-snapshotter` sidecar。VolumeGroupSnapshot v1beta1/v1beta2 API 轉換所需的 conversion webhook 是另一項可選元件，參見 [v8.6.0 安裝說明](https://github.com/kubernetes-csi/external-snapshotter/blob/v8.6.0/README.md)。不要假定安裝驅動會自動安裝叢集級 snapshot CRD/controller。

`PersistentVolumeClaim.spec.dataSourceRef` 可引用自定義資料來源，但 volume populator 是配套的資料來源 CRD 與控制器機制，不是 CSI 驅動在 `CSIDriver.spec` 中宣告的 `populatorPolicy`。部署自定義資料來源前必須安裝相應 populator/controller 並遵循該專案文件；本文舊範例中的 `CSIDriver.spec.populatorPolicy` 不是 Kubernetes v1.37.1 有效欄位。

## 舊範例說明

本頁早期版本中的 NFS driver `git clone`、master 分支 manifest、`csi.volume.kubernetes.io/volume-attributes` PV annotation 和 CSI sidecar v1.0.x 表格均為歷史材料，版本過舊且不應部署。v1.37.1 環境應按具體驅動官方文件選擇版本化映像檔、權限、RBAC、StorageClass、Secret 和拓撲設定；不要使用 mutable `master` 安裝連結。

## 參考文件

* [Kubernetes CSI Developer Documentation](https://kubernetes-csi.github.io/docs/)
* [CSI Sidecar Containers](https://kubernetes-csi.github.io/docs/sidecar-containers.html)
* [CSI 專案策略](https://kubernetes-csi.github.io/docs/project-policies.html)
* [Kubernetes CSI volumes](https://kubernetes.io/docs/concepts/storage/volumes/#csi)
* [Storage API reference](https://kubernetes.io/docs/reference/kubernetes-api/config-and-storage-resources/)
