# PersistentVolume

PersistentVolume \(PV\) 和 PersistentVolumeClaim \(PVC\) 提供了方便的持久化卷：PV 提供網路儲存資源，而 PVC 請求儲存資源。這樣，設定持久化的工作流包括設定底層檔案系統或者雲資料卷、建立永續性資料卷、最後建立 PVC 來將 Pod 跟資料卷關聯起來。PV 和 PVC 可以將 pod 和資料卷解耦，pod 不需要知道確切的檔案系統或者支援它的持久化引擎。

## Volume 生命週期

PV 可靜態建立，也可由 StorageClass 動態供應；PVC 請求並綁定 PV，Pod 透過 PVC 使用該卷。卷狀態包括 `Available`、`Bound`、`Released` 和 `Failed`。PVC/PV 的保護 finalizer 可延遲刪除，回收策略決定釋放後的儲存資產如何處理。

## API 版本

| 資源 | Kubernetes v1.37 API |
| :--- | :--- |
| PersistentVolume、PersistentVolumeClaim | `v1` |
| StorageClass | `storage.k8s.io/v1` |

## PV

PersistentVolume（PV）是叢集級儲存資源，生命週期獨立於單個 Pod。靜態 NFS PV 可使用以下結構；`server` 和 `path` 必須對應已設定、可由節點存取的 NFS 匯出，不能直接應用佔位值：

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

PV 的存取模式（accessModes）有三種：

* `ReadWriteOnce`（RWO）：以讀寫方式掛載到單個 Node；具體能否多 Pod 共用還取決於儲存實現
* `ReadOnlyMany`（ROX）：以只讀方式掛載到多個 Node（需儲存支援）
* `ReadWriteMany`（RWX）：以讀寫方式掛載到多個 Node（需儲存支援）
* `ReadWriteOncePod`（RWOP）：限制卷只掛載到一個 Pod，需支援的 CSI driver

存取模式是掛載/綁定能力約束，不是所有儲存都支援每種模式。

PV 的回收策略決定 PVC 釋放後如何處理儲存：

* `Retain` 保留底層儲存及資料，由管理員按流程回收；
* `Delete` 刪除 PV 及底層儲存，僅在相應 provisioner/driver 支援時生效；
* `Recycle` 已棄用，不要用於新設定。

## StorageClass

StorageClass 描述動態供應卷的 provisioner、引數、回收策略和拓撲綁定行為。Kubernetes v1.37 的雲盤和外部儲存通常由 CSI driver 提供；in-tree 外掛、FlexVolume、GlusterFS 等舊版範例已不適用於當前版本。請使用所選 CSI driver 維護者提供的 `storage.k8s.io/v1` 設定與相容矩陣。

以下清單僅展示 API 形狀；`csi.example.com` 是佔位 provisioner，未安裝對應 CSI driver 前不能建立可用卷。`allowVolumeExpansion` 也只有在 driver 明確支援擴容時才應啟用：

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: example-csi
provisioner: csi.example.com
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer
```

未顯式指定 StorageClass 的 PVC 只有在叢集設定了預設 StorageClass 時才會被動態供應。預設 StorageClass 使用 annotation `storageclass.kubernetes.io/is-default-class: "true"`；修改叢集預設類會影響之後建立的 PVC，應先核對叢集中所有 StorageClass 與工作負載要求。

本頁舊版 GCE PD、GlusterFS、Cinder、Ceph RBD 和其他 in-tree provisioner 範例僅作歷史資料，不應複製到 Kubernetes v1.37。
## PVC

PV 是儲存資源，而 PersistentVolumeClaim \(PVC\) 是對 PV 的請求。PVC 跟 Pod 類似：Pod 消費 Node 資源，而 PVC 消費 PV 資源；Pod 能夠請求 CPU 和記憶體資源，而 PVC 請求特定大小和存取模式的資料卷。

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

PVC 可以直接掛載到 Pod 中：

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

## 擴充套件 PV 空間

PersistentVolumeClaim 擴容已在 Kubernetes v1.24 達到 Stable，v1.37 不需要開啟 `ExpandPersistentVolumes` feature gate。擴容前確認 StorageClass 設定了 `allowVolumeExpansion: true`，且所用 CSI driver、底層儲存和檔案系統支援線上或離線擴容。具體步驟請遵循該 CSI driver 的文件；舊版僅支援特定 in-tree 外掛的清單不適用於當前版本。

擴容只支援增大請求，不支援縮小 PVC；擴容期間檢視 PVC 狀態、Events 及 CSI controller/node plugin 日誌。參閱 [擴容 PersistentVolumeClaim](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#expanding-persistent-volumes-claims)。
## 塊儲存（Raw Block Volume）

`volumeMode: Block` 將支援的 PersistentVolume 以原始塊裝置提供給容器；它自 Kubernetes v1.18 起為 Stable，不需要開啟 `BlockVolume` feature gate。是否可用取決於儲存後端和 CSI driver 對塊裝置的支援。

原始塊裝置內容不會自動格式化。應用必須能安全操作裝置，並透過 Pod 的 `volumeDevices` 選擇目標裝置路徑。部署前按 CSI driver 文件確認裝置對映、備份與權限要求；不要照搬舊版範例中的 Fiber Channel WWN、AppArmor Beta annotation、未固定 Fedora 映像檔或 `SYS_ADMIN` 特權容器。
## StorageObjectInUseProtection

`StorageObjectInUseProtection` 會延遲刪除仍被 Pod 使用的 PVC，以及仍綁定 PVC 的 PV，以避免丟失正在使用的儲存物件。該准入功能已於 v1.11 達到 GA；標準叢集通常會啟用，不需要照搬舊版 `--admission-control` 引數。受保護的資源可能在使用結束前保持 `Terminating` 狀態。
## PersistentVolume 刪除保護 finalizer（v1.33 GA）

PV 刪除保護 finalizer 確保採用 `Delete` 回收策略的 PV 在底層儲存刪除完成前不會從 API 中最終移除。相關機制自 v1.31 引入、在 v1.33 達到 Stable；v1.37 不需要設定已移除的 feature gate。

CSI 卷由 external-provisioner 管理時，可在靜態或動態建立的 PV 上看到 `external-provisioner.volume.kubernetes.io/finalizer`。動態建立的 in-tree 卷使用 `kubernetes.io/pv-controller` finalizer。具體 finalizer 取決於供應方式、CSI external-provisioner 與 Kubernetes 版本。

finalizer 保留期間，PV 保持 `Terminating` 是非同步清理的一部分。排錯時檢查 PVC、PV 的 `reclaimPolicy`、相關 CSI provisioner/controller 日誌與底層儲存狀態；不要為消除 `Terminating` 手工移除 finalizer，否則可能遺留未清理的儲存資產或造成資料丟失。
## 拓撲感知動態卷供應

卷的拓撲支援由 CSI driver、StorageClass 與叢集排程設定共同決定。使用 `volumeBindingMode: WaitForFirstConsumer` 可讓動態供應等待 Pod 排程資訊，以便儲存系統按其可用拓撲建立卷；請遵循實際 CSI driver 的拓撲文件。

## 儲存容量評分（v1.37 Beta）

`StorageCapacityScoring` 自 v1.33 起為 Alpha，並在 v1.37 成為預設啟用的 Beta。它透過 kube-scheduler 的 VolumeBinding 外掛，在適用的延遲綁定動態卷場景中按儲存容量評估節點；無需在 v1.37 手工開啟該 feature gate。

該功能並不替代 CSI driver、StorageClass 或拓撲設定。啟用前確認 CSI driver 會正確釋出容量資訊，並按叢集排程設定文件檢查 `WaitForFirstConsumer` 等卷供應要求。不要複用本頁舊版的 GCE in-tree StorageClass、`failure-domain.beta.kubernetes.io/zone` 標籤或無效的歷史清單。

## 卷資料填充器（Volume Populators，GA）

卷資料填充器允許相容的外部控制器在建立 PVC 時將自定義資源作為資料來源。此機制在 v1.33 達到 GA；`AnyVolumeDataSource` feature gate 在 v1.37 已移除。Kubernetes API 負責表達資料來源引用，實際資料複製由識別對應資源型別的 populator/controller 完成。

### 設定資料來源

自定義 `dataSourceRef` 只有在相應 GVK 已註冊、目標命名空間可見、且有能夠處理該資源的 volume populator/controller 時才可用。以下資源名和 StorageClass 是佔位符，不應在未部署對應 CRD、控制器與儲存實現前直接應用：

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

### 優勢

1. **靈活性** - 支援從任意自定義資源初始化儲存卷
2. **可擴充套件性** - 開發者可以建立特定的資料填充邏輯
3. **高效性** - 新的外掛介面減少了資源開銷
4. **自動化** - 支援自動清理和錯誤處理

### 常見用例

* **資料庫初始化** - 從備份或模板初始化資料庫儲存卷
* **應用資料預填充** - 為應用預裝設定檔案或靜態資源
* **多環境資料同步** - 在不同環境間同步資料狀態
* **備份恢復** - 從備份系統恢復資料到新的儲存卷

### 注意事項

* 需要相應的卷填充器控制器支援特定的自定義資源型別
* 資料填充過程可能需要一定時間，Pod 排程會等待填充完成
* 確保自定義資源和 PVC 在同一命名空間中

## 儲存快照

VolumeSnapshot API 已由 CSI snapshot 機制提供，不再是本頁所述的 v1.12 Alpha 功能。使用時需要相容的 CSI driver、`snapshot.storage.k8s.io/v1` API/CRD 與 external-snapshotter 元件；並非所有儲存後端都支援快照。

本頁舊 `VolumeSnapshotDataSource` feature gate 和 `snapshot.storage.k8s.io/v1alpha1` manifests 已過時，不能在 Kubernetes v1.37 應用。應按 CSI driver 文件設定 `VolumeSnapshotClass`、建立 `VolumeSnapshot`，並遵循後端的保留、刪除和恢復語義。參閱 [Volume Snapshots](https://kubernetes.io/docs/concepts/storage/volume-snapshots/)。
## 參考文件

* [Kubernetes Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
* [Kubernetes Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/)
* [Dynamic Volume Provisioning](https://kubernetes.io/docs/concepts/storage/dynamic-provisioning/)
* [Kubernetes CSI Documentation](https://kubernetes-csi.github.io/docs/)
* [Volume Snapshots Documentation](https://kubernetes.io/docs/concepts/storage/volume-snapshots/)
