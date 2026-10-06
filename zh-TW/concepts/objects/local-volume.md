# 本機持久性磁碟區

本機持久性磁碟區會公開連接到特定節點的儲存裝置，例如本機磁碟或分割區。`local` 類型的 PersistentVolume（PV）已是穩定功能，並非 Kubernetes alpha 或 beta 功能。本機 PV 必須指定節點親和性，讓排程器將 Pod 安排到具備該儲存裝置的節點。

Kubernetes 不會動態佈建本機 PV。管理員或獨立的佈建器必須先準備儲存裝置並建立 PV。以下範例採用靜態佈建：建立 StorageClass、為節點上已準備好的路徑建立 PV，再建立 PVC 與 Pod。請將範例中的節點名稱和路徑換成實際使用的節點及儲存位置。PV 宣告的容量供排程使用，並非檔案系統配額；請確保容量符合實際提供的儲存空間。

## StorageClass

`WaitForFirstConsumer` 會延後綁定，直到使用該 PVC 的 Pod 開始排程；如此排程器就能考量 PV 的節點親和性。

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
```

## PersistentVolume

建立此 PV 前，請先在 `example-node` 準備好 `/mnt/disks/ssd1`。`Retain` 回收政策會在 PVC 釋放後保留底層資料，供管理員檢查與回收；它不會自動清理或安全抹除儲存裝置。

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: example-local-pv
spec:
  capacity:
    storage: 100Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
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

## PersistentVolumeClaim

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: example-local-claim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: local-storage
```

## 使用 PVC 的 Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: local-volume-demo
spec:
  containers:
    - name: web
      image: nginx:1.30.5
      volumeMounts:
        - name: web-content
          mountPath: /usr/share/nginx/html
  volumes:
    - name: web-content
      persistentVolumeClaim:
        claimName: example-local-claim
```

PV 的節點親和性會限制 Pod 的排程位置；PV 使用期間請勿刪除或取代該節點、搬動儲存裝置，或讓其他節點重複使用相同主機名稱。請為節點或磁碟故障規劃備份與復原程序：Kubernetes 不會複製本機儲存資料。回收 `Retain` PV 前，請確認 PVC 及其資料都不再需要。

上游[本機持久性磁碟區指南](https://kubernetes.io/docs/concepts/storage/volumes/#local)說明此磁碟區類型及排程行為。如需自動探索與管理，請參閱社群維護的 [sig-storage-local-static-provisioner](https://github.com/kubernetes-sigs/sig-storage-local-static-provisioner)；採用前請自行確認其維護狀態及與環境的相容性。本指南不宣稱任何特定叢集發行版或佈建器版本受支援。

舊版 v1.7–1.10 教學保留於[歷史封存](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/concepts/objects/local-volume-legacy-zh-TW.md)。
