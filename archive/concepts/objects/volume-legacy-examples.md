# 歷史卷範例（不適用於 Kubernetes v1.37）

本頁保留自 `concepts/objects/volume.md` 移出的舊版範例，僅供辨識舊清單及遷移使用。這些範例不是目前部署指引。原始內容由本手冊 `concepts/objects/volume.md` 移轉，原範例歸屬 Kubernetes 官方文件或各對應儲存專案；Kubernetes 文件授權與歸屬說明見[官方儲存庫](https://github.com/kubernetes/website)。

## GCE Persistent Disk

此 in-tree 驅動已移除。新部署應依 GCE PD CSI 驅動文件遷移。

```yaml
volumes:
  - name: test-volume
    gcePersistentDisk:
      pdName: my-data-disk
      fsType: ext4
```

## AWS Elastic Block Store

此 in-tree 驅動已移除。新部署應依 Amazon EBS CSI 驅動文件遷移。

```yaml
volumes:
  - name: test-volume
    awsElasticBlockStore:
      volumeID: <volume-id>
      fsType: ext4
```

## gitRepo

`gitRepo` volume 已移除。需提供程式碼或資料時，請使用映像檔建置流程或維護中的 init container 設計。

```yaml
volumes:
- name: git-volume
  gitRepo:
    repository: "git@somewhere:me/my-git-repository.git"
    revision: "22f1d8406d464b0c0874075539c1f2e96c253775"
```

## FlexVolume

FlexVolume 已移除，不可用來實作新的儲存外掛。新驅動使用 CSI。

```yaml
volumes:
- name: test
  flexVolume:
    driver: "kubernetes.io/lvm"
    fsType: "ext4"
    options:
      volumeID: "vol1"
      size: "1000m"
      volumegroup: "kube_vg"
```

## 舊版掛載傳播設定

掛載傳播功能已不需要 feature gate。下列資料只記錄舊版文件曾要求的設定，不可用來設定目前節點：

- v1.9/v1.10 預設值為 `None`，v1.11 預設值為 `HostToContainer`。
- 舊版 Docker systemd 設定曾要求 `MountFlags=shared`。

目前配置請參閱 [Kubernetes 掛載傳播文件](https://kubernetes.io/docs/concepts/storage/volumes/#mount-propagation)。

## 舊版 in-tree 卷類型清單

舊文件列出 `flocker`、`glusterfs`、`rbd`、`cephfs`、`azureFile`、`azureDisk`、`vsphereVolume`、`quobyte`、`portworx`、`scaleIO`、`storageos` 等卷欄位。不要假定其仍是 Kubernetes v1.37 的 in-tree 驅動；請依儲存廠商與 CSI 專案文件確認替代方案及遷移方式。
