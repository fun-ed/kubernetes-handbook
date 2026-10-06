# Volume

Kubernetes 把卷掛載到 Pod 內的容器。卷的存留時間取決於卷來源：`emptyDir` 隨 Pod 移除而刪除；PVC 通常由外部儲存系統保存資料。容器重新啟動時，Pod 卷仍可供其使用。

## 卷來源與儲存

常用的 Pod 卷來源包括 `emptyDir`、`configMap`、`secret`、`projected`、`downwardAPI`、`persistentVolumeClaim` 和 `hostPath`。持久儲存通常透過 PVC、StorageClass 及 CSI 驅動提供。實際可用的驅動與功能取決於叢集安裝的外掛及儲存後端。

Kubernetes v1.37 的 core/v1 API 仍包含部分舊版雲端與廠商專用卷欄位，但新部署不應選用已移除的 in-tree 卷驅動。請依所選雲端或儲存產品文件使用 CSI。FlexVolume 和 `gitRepo` 卷已移除。

舊版 GCE PD、AWS EBS、`gitRepo`、FlexVolume 及其他 in-tree 卷範例已移至[歷史歸檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/concepts/objects/volume-legacy-examples.md)。不要將其清單套用到 Kubernetes v1.37。

## emptyDir

Pod 排程到節點後，kubelet 會建立 `emptyDir`。容器重新啟動不會清除此卷；Pod 從節點移除時，卷及其資料會刪除。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: emptydir-example
spec:
  containers:
  - name: app
    image: busybox:1.37.0
    command: ["sh", "-c", "sleep 3600"]
    volumeMounts:
    - name: cache
      mountPath: /cache
  volumes:
  - name: cache
    emptyDir: {}
```

## hostPath

`hostPath` 會將節點上的路徑掛載到 Pod。它會讓工作負載接觸節點檔案系統，且 Pod 移至另一節點時不會帶著原節點資料。僅在確有需求時使用，並限制路徑及存取權限。一般應用應使用 PVC，而非 `hostPath`。

## NFS

NFS 卷使用外部 NFS 伺服器。以下僅為 Pod 欄位片段，請將保留的範例位址換成實際伺服器及受限的匯出路徑；儲存的可用性與權限由 NFS 服務設定決定。

```yaml
volumes:
- name: shared-data
  nfs:
    server: nfs.example.invalid
    path: /exports/app
    readOnly: true
```

## image 卷

image 卷在 Kubernetes v1.33 成為 Beta，並自 v1.35 起預設啟用；在 v1.37 仍為 Beta。它會將容器映像檔內容以唯讀資料卷掛載。使用前確認目標節點的 CRI 執行時支援該功能。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: image-volume-example
spec:
  containers:
  - name: shell
    image: debian:trixie-slim
    volumeMounts:
    - name: artifacts
      mountPath: /artifacts
  volumes:
  - name: artifacts
    image:
      reference: quay.io/crio/artifact:v2
      pullPolicy: IfNotPresent
```

## 使用 subPath

`subPath` 可將同一卷中的不同子目錄掛載到容器路徑。PVC 必須事先存在，且需有可用的 StorageClass 或符合的 PV。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: subpath-example
spec:
  containers:
  - name: app
    image: busybox:1.37.0
    command: ["sh", "-c", "sleep 3600"]
    volumeMounts:
    - name: app-data
      mountPath: /data
      subPath: app
  volumes:
  - name: app-data
    persistentVolumeClaim:
      claimName: app-data-pvc
```

## 投射卷

Projected volume 將 Secret、ConfigMap、Downward API 和 service account token 等來源合併掛載到同一個目錄。只有 Pod 所需的來源才應放入投射卷。

## 本地暫存空間

透過容器資源中的 `requests.ephemeral-storage` 和 `limits.ephemeral-storage` 宣告本地暫存空間的請求與限制。實際計量能力取決於節點檔案系統配置；`emptyDir.sizeLimit` 可限制單一 `emptyDir`，但不會取代資源請求。

## 掛載傳播

`mountPropagation` 控制容器與主機間掛載事件的傳遞。`Bidirectional` 可讓容器建立的掛載傳回主機，權限風險高，只應用於經審查的系統工作負載。此功能在目前版本不需 feature gate。設定前請確認節點、CRI 執行時及應用安全需求，並參閱[官方掛載傳播文件](https://kubernetes.io/docs/concepts/storage/volumes/#mount-propagation)。

## VolumeSnapshot

VolumeSnapshot API 由 CSI snapshot 元件提供，並非所有儲存驅動都支援。使用前確認 CSI driver、外部 snapshot-controller 與 CRD 均已安裝，並依該驅動文件設定 `snapshot.storage.k8s.io/v1` 資源。

參閱 [Volume Snapshots](https://kubernetes.io/docs/concepts/storage/volume-snapshots/) 與所選 CSI driver 文件。

## Windows 卷

Windows 節點可用卷來源及掛載路徑受 Windows Server、CRI 執行時、CSI 驅動和 Kubernetes 版本限制。使用符合目標主機版本的 Windows 容器映像檔與驅動文件。Windows 容器不能存取 Linux 節點的主機路徑。

部署前核對[Windows 儲存文件](https://kubernetes.io/docs/concepts/storage/windows-storage/)及所選 CSI 驅動的相容性說明。

## 卷資料填充器（Volume Populators，GA）

卷資料填充器可讓 PVC 的 `dataSourceRef` 指向自訂資源。此功能在 v1.33 達到 GA；`AnyVolumeDataSource` feature gate 在 v1.37 已移除。資料填充需要叢集安裝能識別該 GVK 的外部控制器，Kubernetes API 不會自行複製資料。

以下 `BackupSource`、API 群組及 StorageClass 均為佔位值。只有安裝相應 CRD、populator/controller 和儲存實作後才可使用：

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

