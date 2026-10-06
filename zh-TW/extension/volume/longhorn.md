# Longhorn 分散式區塊儲存

本文以 Kubernetes v1.37.1 為背景。截至 2026-10-05，Longhorn 最新穩定版為 **v1.13.0**，官方 [v1.13.0 release](https://github.com/longhorn/longhorn/releases/tag/v1.13.0) 發布於 2026-09-29；同一 tag 的 Helm chart 版本和 appVersion 均為 `1.13.0`，chart 要求 Kubernetes `>=1.34.0-0`。Longhorn release notes 也指出 v1.13.0 的 CSI external-provisioner v6.3.0 要求 Kubernetes v1.34 或更新版本。v1.37.1 符合此下限，但這不等於 Longhorn 對每種作業系統、核心、CNI 或硬體的認證。請以[安裝需求](https://longhorn.io/docs/1.13.0/deploy/install/)、[最佳實務](https://longhorn.io/docs/1.13.0/best-practices/)及發行說明為準。

Longhorn 透過 CSI 為 Pod 提供可複製的區塊磁碟區。它不是 Kubernetes 內建儲存，也不會取代叢集 CNI。部署前需已有可運作的 CNI、DNS、StorageClass 管理方案，以及符合需求的 Linux 節點與資料磁碟。以下命令僅供隔離實驗室參考，本章未執行這些命令，也不應直接套用到使用者叢集。

## 架構與資料引擎

`longhorn-manager` 管理 Longhorn 資源、節點磁碟及卷生命週期；v1.13 引入 `longhorn-global-manager` Deployment，分擔叢集範圍的 PersistentVolume 與 Pod 控制器工作。Longhorn CSI controller sidecars 透過 Kubernetes API 觀察 PVC，並呼叫 CSI controller；節點上的 CSI plugin 以 `driver.longhorn.io` 名稱向 kubelet 註冊，負責 stage/publish 磁碟區。CSI provisioner 名稱是 `driver.longhorn.io`，`StorageClass.provisioner` 必須使用此值。Longhorn 自訂資源由其 CRD 定義，例如 `longhorn.io/v1beta2` 的 `Volume`、`Node`、`Engine` 與 `Replica`。安裝 CRD 不代表內建 Kubernetes schema 能驗證這些自訂欄位。

V1 data engine 使用 Longhorn engine 管理網路區塊 I/O；檔案系統類型磁碟是常見資料儲存配置，節點需安裝並啟用 `open-iscsi`/`iscsid`，以便節點掛載 iSCSI target。V2 data engine 基於 SPDK，使用 `block-type` 磁碟；需要 VFIO/UIO/NVMe-TCP 核心模組、IOMMU 群組隔離、巨頁與額外 CPU/記憶體，並非只切換設定即可。官方 V2 最低建議仍為三節點及 V1 的基礎配置，另每節點預留 1 CPU 核心與 2 GiB 巨頁記憶體，並使用 `vfio_pci`、`uio_pci_generic`、`nvme-tcp` 模組；NVMe/TCP 最低核心為 5.19，官方建議 6.7 或更新版本以改善穩定性。V2 的 SPDK NVMe 磁碟需有可隔離 IOMMU 群組，或使用文件允許的替代 AIO 模式。這些是獨立的主機條件，不能與 V1 的 iSCSI 安裝需求混為一談。v1.13 release 將 V2 標為 GA，但其中 UBLK frontend 仍是實驗性功能，勿將該狀態套用至整個 V2 引擎。v1.13 建議每個叢集只啟用其中一種引擎以免增加資源耗用。本文實驗只使用預設 V1；不設定 V2 主機需求或功能。

Longhorn 一般安裝需求包括可執行 root/privileged 工作負載、啟用 mount propagation、基本主機命令（`bash`、`curl`、`findmnt`、`grep`、`awk`、`blkid`、`lsblk`）及容器執行環境。V1 每個節點要安裝 iSCSI initiator；Debian/Ubuntu 使用 `open-iscsi`，RHEL 系統通常使用 `iscsi-initiator-utils`，請依發行版文件確認服務名稱與啟用方式。官方建議 V1 最低參考為三節點、每節點 4 vCPU、4 GiB RAM 及本機磁碟；這是建議硬體，不是 Helm 強制檢查值。根磁碟保留率預設 25%；專用資料磁碟可按官方指引評估 10%。正式環境使用獨立磁碟並確保重新開機後掛載路徑不變。v1.13 發行測試列出的作業系統包括 Ubuntu 26.04、SLES 16.0、SLE Micro 6.1、RHEL/Oracle/Rocky Linux 10.2、Talos 1.13.4 及 GKE Container-Optimized OS 125；這是該版本測試清單，不代表其他 Linux 系統必然不支援。

## 隔離實驗室安裝

先確認叢集版本及三個或更多可排程的 Linux 節點。此範例的 `numberOfReplicas: "3"` 要求至少三個符合磁碟與節點排程條件的 Longhorn 節點；未達條件時 PVC 會無法建立完整副本，不可藉由隱藏 degraded 狀態當作成功。確認現有 CNI 已支援一般 Pod 通訊；Longhorn 不安裝 CNI。先依官方文件安裝主機需求並核對磁碟，勿把安裝套件命令交給叢集工作負載執行。

以下 Helm 命令將安裝固定 chart 版本至新命名空間。`--wait` 等候資源就緒，但不會驗證實際磁碟 I/O、備份或災難復原。

```bash
helm repo add longhorn https://charts.longhorn.io
helm repo update
helm show chart longhorn/longhorn --version 1.13.0
helm install longhorn longhorn/longhorn \
  --namespace longhorn-system --create-namespace \
  --version 1.13.0 --wait --timeout 10m
```

建立非預設 StorageClass，明確設定三副本和 `Retain`。這避免刪除 PVC 時由 reclaim policy 自動刪除底層 PV/Longhorn volume，但保留資料仍需管理員按照程序回收。

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

使用小型官方 BusyBox 1.37.0 映像檔建立 PVC 與寫入檔案的消費端。PVC 指定實驗 StorageClass，Pod 將 volume 掛載至 `/data`。完成後在同一 Pod 中讀回內容，才算測過基本掛載及寫入路徑。

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

預期 PVC 為 `Bound`，Pod 為 `Running`，讀回 `longhorn-ok`。這只證明單一實驗 Pod 的基本寫入/讀取，不驗證節點失效復原、磁碟耐久性、效能或備份還原。不要用預設自動建立的 StorageClass 代替此明確指定的實驗類別。

## UI 與唯讀檢查

UI 預設不應公開到公網。隔離實驗室可用本機 port-forward，僅監聽 loopback；Service 名稱請先由唯讀查詢確認。

```bash
kubectl -n longhorn-system get svc
kubectl -n longhorn-system port-forward --address 127.0.0.1 svc/longhorn-frontend 8080:80
```

只在本機瀏覽 `http://127.0.0.1:8080`。不要建立無認證的 LoadBalancer/Ingress，也不要把 UI 管理權限交給一般使用者。

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

`longhorn-manager`、CSI controller 與節點 plugin Pod 應就緒；Volume 應顯示健康狀態及預期副本數，PVC 綁定，`CSIDriver` 和包含 `driver.longhorn.io` 的 `CSINode` 資訊可供確認註冊。`describe` 的 Events 用來區分 provisioner、排程、attach、mount 問題。這些查詢唯讀，成功不代表資料已有備份。若 Pod 卡在 Pending，檢查 StorageClass/provisioner、至少三個可用節點、磁碟可排程空間及事件；若 attach/mount 失敗，檢查 iSCSI 服務、節點 CSI plugin、mount propagation、核心日誌及 Longhorn volume/replica CR 狀態。勿直接刪除 Volume 或 Replica CR 排錯。

## 備份、擴容與維護

副本是同一個線上磁碟區的即時副本，不是備份。操作錯誤、勒索軟體、叢集或多節點同時故障可能影響所有副本。設定外部 backup target（例如受保護的物件儲存或獨立 NFSv4 備份端），限制憑證權限，建立排程備份並監控完成狀態。在隔離環境將備份還原成新 volume，啟動測試消費端並驗證應用資料，才有可用的還原證據；CSI snapshot 或同一磁碟上的副本不能取代外部備份。

StorageClass 開啟 `allowVolumeExpansion` 僅表示 Kubernetes 可請求擴容，仍須確認 Longhorn 及檔案系統支援。修改 PVC 的儲存請求會擴大卷，不能縮小。離線擴容可先停止使用 Pod 再變更 PVC；線上擴容是否完成 filesystem resize，取決於 CSI、檔案系統及 kubelet，檢查 PVC conditions/events 與容器內 `df -h`。先備份並在測試卷驗證，勿假定所有工作負載都支援線上擴容。

維護節點前確認所有卷有足夠健康副本及其他節點的磁碟容量；依 Longhorn 節點維護程序先禁用磁碟排程或遷移副本，配合 Kubernetes drain 時逐一確認使用中的卷及應用可用性。磁碟故障時先保留故障磁碟與日誌，不要格式化、清除 `/var/lib/longhorn` 或刪除 Replica 資源；依健康副本重建或使用備份還原，並核對資料完整性。升級前備份應用資料和 Longhorn 系統狀態，閱讀逐版升級路徑及 V2 引擎特殊條件；v1.13 V2 live upgrade 只支援特定前版與前置條件。控制器降版不會自動回復資料格式或卷狀態，不可把 Helm rollback 當成安全資料回復方案。按官方[升級指南](https://longhorn.io/docs/1.13.0/deploy/upgrade/)規劃並先在隔離環境演練。

## 來源

- [Longhorn v1.13.0 release notes](https://github.com/longhorn/longhorn/releases/tag/v1.13.0)
- [v1.13.0 Helm chart metadata](https://github.com/longhorn/longhorn/blob/v1.13.0/chart/Chart.yaml)
- [安裝與主機需求](https://longhorn.io/docs/1.13.0/deploy/install/)
- [最佳實務與硬體、作業系統、磁碟建議](https://longhorn.io/docs/1.13.0/best-practices/)
- [v1.13.0 StorageClass 參數](https://longhorn.io/docs/1.13.0/references/storage-class-parameters/)
- [Longhorn CSI](https://longhorn.io/docs/1.13.0/deploy/install/#installation-requirements)
