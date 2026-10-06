> HISTORICAL: 本頁記錄 Kubernetes v1.7–1.10 的 Local PV 行為與舊範例，僅供參考；請改用目前的本機儲存指南。

# LocalVolume

> 注意：僅在 v1.7 + 中支援，並從 v1.10 開始升級為 beta 版本。

本地資料卷（Local Volume）代表一個本地儲存裝置，比如磁碟、分割槽或者目錄等。主要的應用場景包括分散式儲存和資料庫等需要高效能和高可靠性的環境裡。本地資料卷同時支援塊裝置和檔案系統，透過 `spec.local.path` 指定；但對於檔案系統來說，kubernetes 並不會限制該目錄可以使用的儲存空間大小。

本地資料卷只能以靜態建立的 PV 使用。相對於 [HostPath](https://github.com/fun-ed/kubernetes-handbook/blob/main/concepts/objects/volume.md#hostPath)，本地資料卷可以直接以持久化的方式使用（它總是透過 NodeAffinity 排程在某個指定的節點上）。

另外，社群還提供了一個 [local-volume-provisioner](https://github.com/kubernetes-incubator/external-storage/tree/master/local-volume/provisioner)，用於自動建立和清理本地資料卷。

## 範例

StorageClass

```yaml
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: local-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
```

建立一個排程到 hostname 為 `example-node` 的本地資料卷：

```yaml
# For kubernetes v1.10
apiVersion: v1
kind: PersistentVolume
metadata:
  name: example-local-pv
spec:
  capacity:
    storage: 100Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Delete
  storageClassName: local-storage
  local:
    path: /mnt/disks/ssd1
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - example-node
```

```yaml
# For kubernetes v1.7-1.9
apiVersion: v1
kind: PersistentVolume
metadata:
  name: example-local-pv
  annotations:
    "volume.alpha.kubernetes.io/node-affinity": '{
      "requiredDuringSchedulingIgnoredDuringExecution": {
        "nodeSelectorTerms": [
          { "matchExpressions": [
            { "key": "kubernetes.io/hostname",
              "operator": "In",
              "values": ["example-node"]
            }
          ]}
         ]}
        }',
spec:
  capacity:
    storage: 5Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Delete
  storageClassName: local-storage
  local:
    path: /mnt/disks/ssd1
```

建立 PVC：

```yaml
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: example-local-claim
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: local-storage
```

建立 Pod，引用 PVC：

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
        claimName: example-local-claim
```

## 限制

* 暫不支援一個 Pod 綁定多個本地資料卷的 PVC（計劃 v1.9 支援）
* 有可能導致排程衝突，比如 CPU 或者記憶體資源不足（計劃 v1.9 增強）
* 外部 Provisoner 在啟動後無法正確檢測掛載點的空間大小（需要 Mount Propagation，計劃 v1.9 支援）

## 最佳實踐

* 推薦為每個儲存卷分配獨立的磁碟，以便隔離 IO 請求
* 推薦為每個儲存卷分配獨立的分割槽，以便隔離儲存空間
* 避免重新建立同名的 Node，否則會導致新 Node 無法識別已綁定舊 Node 的 PV
* 推薦使用 UUID 而不是檔案路徑，以避免檔案路徑誤配的問題
* 對於不帶檔案系統的塊儲存，推薦使用唯一 ID（如 `/dev/disk/by-id/`），以避免塊裝置路徑誤配的問題

## 參考文件

* [Local Persistent Storage User Guide](https://github.com/kubernetes-incubator/external-storage/tree/master/local-volume)
