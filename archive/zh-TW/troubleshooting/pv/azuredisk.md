# AzureDisk

[AzureDisk](https://docs.microsoft.com/zh-cn/azure/virtual-machines/windows/about-disks-and-vhds) 為 Azure 上面執行的虛擬機器提供了彈性塊儲存服務，它以 VHD 的形式掛載到虛擬機器中，並可以在 Kubernetes 容器中使用。AzureDisk 優點是效能高，特別是 Premium Storage 提供了非常好的[效能](https://docs.microsoft.com/en-us/azure/virtual-machines/windows/premium-storage)；其缺點是不支援共享，只可以用在單個 Pod 內。

根據設定的不同，Kubernetes 支援的 AzureDisk 可以分為以下幾類

* Managed Disks: 由 Azure 自動管理磁碟和儲存帳戶
* Blob Disks:
  * Dedicated \(預設\)：為每個 AzureDisk 建立單獨的儲存帳戶，當刪除 PVC 的時候刪除該儲存帳戶
  * Shared：AzureDisk 共享 ResourceGroup 內的同一個儲存帳戶，這時刪除 PVC 不會刪除該儲存帳戶

> 注意：
>
> * AzureDisk 的型別必須跟 VM OS Disk 型別一致，即要麼都是 Manged Disks，要麼都是 Blob Disks。當兩者不一致時，AzureDisk PV 會報無法掛載的錯誤。
> * 由於 Managed Disks 需要建立和管理儲存帳戶，其建立過程會比 Blob Disks 慢（3 分鐘 vs 1-2 分鐘）。
> * 但節點最大支援同時掛載 16 個 AzureDisk。

使用 AzureDisk 推薦的版本：

| Kubernetes version | Recommended version |
| :--- | :---: |
| 1.12 | 1.12.9 或更高版本 |
| 1.13 | 1.13.6 或更高版本 |
| 1.14 | 1.14.2 或更高版本 |
| &gt;=1.15 | &gt;=1.15 |

使用 [aks-engine](https://github.com/Azure/aks-engine) 部署的 Kubernetes 叢集，會自動建立兩個 StorageClass，預設為managed-standard（即HDD）：

```bash
kubectl get storageclass
NAME                PROVISIONER                AGE
default (default)   kubernetes.io/azure-disk   45d
managed-premium     kubernetes.io/azure-disk   53d
managed-standard    kubernetes.io/azure-disk   53d
```

## AzureDisk 掛載失敗

在 AzureDisk 從一個 Pod 遷移到另一 Node 上面的 Pod 時或者同一臺 Node 上面使用了多塊 AzureDisk 時有可能會碰到這個問題。這是由於 kube-controller-manager 未對 AttachDisk 和 DetachDisk 操作加鎖從而引發了競爭問題（[kubernetes\#60101](https://github.com/kubernetes/kubernetes/issues/60101) [acs-engine\#2002](https://github.com/Azure/acs-engine/issues/2002) [ACS\#12](https://github.com/Azure/ACS/issues/12)）。

透過 kube-controller-manager 的日誌，可以檢視具體的錯誤原因。常見的錯誤日誌為

```bash
Cannot attach data disk 'cdb-dynamic-pvc-92972088-11b9-11e8-888f-000d3a018174' to VM 'kn-edge-0' because the disk is currently being detached or the last detach operation failed. Please wait until the disk is completely detached and then try again or delete/detach the disk explicitly again.
```

臨時性解決方法為

（1）更新所有受影響的虛擬機器狀態

使用powershell：

```text
$vm = Get-AzureRMVM -ResourceGroupName $rg -Name $vmname
Update-AzureRmVM -ResourceGroupName $rg -VM $vm -verbose -debug
```

使用 Azure CLI：

```bash
# For VM:
az vm update -n <VM_NAME> -g <RESOURCE_GROUP_NAME>

# For VMSS:
az vmss update-instances -g <RESOURCE_GROUP_NAME> --name <VMSS_NAME> --instance-id <ID>
```

（2）重啟虛擬機器

* `kubectl cordon NODE`
* 如果 Node 上執行有 StatefulSet，需要手動刪除相應的 Pod
* `kubectl drain NODE`
* `Get-AzureRMVM -ResourceGroupName $rg -Name $vmname | Restart-AzureVM`
* `kubectl uncordon NODE`

該問題的修復 [\#60183](https://github.com/kubernetes/kubernetes/pull/60183) 已包含在 v1.10 中。

## 掛載新的 AzureDisk 後，該 Node 中其他 Pod 已掛載的 AzureDisk 不可用

在 Kubernetes v1.7 中，AzureDisk 預設的快取策略修改為 `ReadWrite`，這會導致在同一個 Node 中掛載超過 5 塊 AzureDisk 時，已有 AzureDisk 的磁碟機代號會隨機改變（[kubernetes\#60344](https://github.com/kubernetes/kubernetes/issues/60344) [kubernetes\#57444](https://github.com/kubernetes/kubernetes/issues/57444) [AKS\#201](https://github.com/Azure/AKS/issues/201) [acs-engine\#1918](https://github.com/Azure/acs-engine/issues/1918)）。比如，當掛載第六塊 AzureDisk 後，原來 lun0 磁碟的掛載磁碟機代號有可能從 `sdc` 變成 `sdk`：

```bash
$ tree /dev/disk/azure
...
â””â”€â”€ scsi1
    â”œâ”€â”€ lun0 -> ../../../sdk
    â”œâ”€â”€ lun1 -> ../../../sdj
    â”œâ”€â”€ lun2 -> ../../../sde
    â”œâ”€â”€ lun3 -> ../../../sdf
    â”œâ”€â”€ lun4 -> ../../../sdg
    â”œâ”€â”€ lun5 -> ../../../sdh
    â””â”€â”€ lun6 -> ../../../sdi
```

這樣，原來使用 lun0 磁碟的 Pod 就無法存取 AzureDisk 了

```bash
[root@admin-0 /]# ls /datadisk
ls: reading directory .: Input/output error
```

臨時性解決方法是設定 AzureDisk StorageClass 的 `cachingmode: None`，如

```yaml
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: managed-standard
provisioner: kubernetes.io/azure-disk
parameters:
  skuname: Standard_LRS
  kind: Managed
  cachingmode: None
```

該問題的修復 [\#60346](https://github.com/kubernetes/kubernetes/pull/60346) 將包含在 v1.10 中。

## AzureDisk 掛載慢

AzureDisk PVC 的掛載過程一般需要 1 分鐘的時間，這些時間主要消耗在 Azure ARM API 的呼叫上（查詢 VM 以及掛載 Disk）。[\#57432](https://github.com/kubernetes/kubernetes/pull/57432) 為 Azure VM 增加了一個快取，消除了 VM 的查詢時間，將整個掛載過程縮短到大約 30 秒。該修復包含在v1.9.2+ 和 v1.10 中。

另外，如果 Node 使用了 `Standard_B1s` 型別的虛擬機器，那麼 AzureDisk 的第一次掛載一般會超時，等再次重複時才會掛載成功。這是因為在 `Standard_B1s` 虛擬機器中格式化 AzureDisk 就需要很長時間（如超過 70 秒）。

```bash
$ kubectl describe pod <pod-name>
...
Events:
  FirstSeen     LastSeen        Count   From                                    SubObjectPath                           Type            Reason                  Message
  ---------     --------        -----   ----                                    -------------                           --------        ------                  -------
  8m            8m              1       default-scheduler                                                               Normal          Scheduled               Successfully assigned nginx-azuredisk to aks-nodepool1-15012548-0
  7m            7m              1       kubelet, aks-nodepool1-15012548-0                                               Normal          SuccessfulMountVolume   MountVolume.SetUp succeeded for volume "default-token-mrw8h"
  5m            5m              1       kubelet, aks-nodepool1-15012548-0                                               Warning         FailedMount             Unable to mount volumes for pod "nginx-azuredisk_default(4eb22bb2-0bb5-11e8-8
d9e-0a58ac1f0a2e)": timeout expired waiting for volumes to attach/mount for pod "default"/"nginx-azuredisk". list of unattached/unmounted volumes=[disk01]
  5m            5m              1       kubelet, aks-nodepool1-15012548-0                                               Warning         FailedSync              Error syncing pod
  4m            4m              1       kubelet, aks-nodepool1-15012548-0                                               Normal          SuccessfulMountVolume   MountVolume.SetUp succeeded for volume "pvc-20240841-0bb5-11e8-8d9e-0a58ac1f0
a2e"
  4m            4m              1       kubelet, aks-nodepool1-15012548-0       spec.containers{nginx-azuredisk}        Normal          Pulling                 pulling image "nginx"
  3m            3m              1       kubelet, aks-nodepool1-15012548-0       spec.containers{nginx-azuredisk}        Normal          Pulled                  Successfully pulled image "nginx"
  3m            3m              1       kubelet, aks-nodepool1-15012548-0       spec.containers{nginx-azuredisk}        Normal          Created                 Created container
  2m            2m              1       kubelet, aks-nodepool1-15012548-0       spec.containers{nginx-azuredisk}        Normal          Started                 Started container
```

## Azure German Cloud 無法使用 AzureDisk

Azure German Cloud 僅在 v1.7.9+、v1.8.3+ 以及更新版本中支援（[\#50673](https://github.com/kubernetes/kubernetes/pull/50673)），升級 Kubernetes 版本即可解決。

## MountVolume.WaitForAttach failed

```bash
MountVolume.WaitForAttach failed for volume "pvc-f1562ecb-3e5f-11e8-ab6b-000d3af9f967" : azureDisk - Wait for attach expect device path as a lun number, instead got: /dev/disk/azure/scsi1/lun1 (strconv.Atoi: parsing "/dev/disk/azure/scsi1/lun1": invalid syntax)
```

[該問題](https://github.com/kubernetes/kubernetes/issues/62540) 僅在 Kubernetes v1.10.0 和 v1.10.1 中存在，將在 v1.10.2 中修復。

## 在 mountOptions 中設定 uid 和 gid 時失敗

預設情況下，Azure 磁碟使用 ext4、xfs filesystem 和 mountOptions，如 uid = x，gid = x 無法在裝入時設定。 例如，如果你嘗試設定 mountOptions uid = 999，gid = 999，將看到類似於以下內容的錯誤:

```text
Warning  FailedMount             63s                  kubelet, aks-nodepool1-29460110-0  MountVolume.MountDevice failed for volume "pvc-d783d0e4-85a1-11e9-8a90-369885447933" : azureDisk - mountDevice:FormatAndMount failed with mount failed: exit status 32
Mounting command: systemd-run
Mounting arguments: --description=Kubernetes transient mount for /var/lib/kubelet/plugins/kubernetes.io/azure-disk/mounts/m436970985 --scope -- mount -t xfs -o dir_mode=0777,file_mode=0777,uid=1000,gid=1000,defaults /dev/disk/azure/scsi1/lun2 /var/lib/kubelet/plugins/kubernetes.io/azure-disk/mounts/m436970985
Output: Running scope as unit run-rb21966413ab449b3a242ae9b0fbc9398.scope.
mount: wrong fs type, bad option, bad superblock on /dev/sde,
       missing codepage or helper program, or other error
```

可以透過執行以下操作之一來緩解此問題

* 透過在 fsGroup 中的 runAsUser 和 gid 中設定 uid 來[設定 pod 的安全上下文](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)。例如，以下設定會將 pod 設定為 root，使其可供任何檔案存取：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: security-context-demo
spec:
  securityContext:
    runAsUser: 0
    fsGroup: 0
```

> 備註: 因為 gid 和 uid 預設裝載為 root 或0。如果 gid 或 uid 設定為非根（例如1000），則 Kubernetes 將使用 `chown` 更改該磁碟下的所有目錄和檔案。此操作可能非常耗時，並且可能會導致裝載磁碟的速度非常慢。

* 使用 initContainers 中的 `chown` 設定 gid 和 uid。例如：

```yaml
initContainers:
- name: volume-mount
  image: busybox
  command: ["sh", "-c", "chown -R 100:100 /data"]
  volumeMounts:
  - name: <your data volume>
    mountPath: /data
```

## 刪除 pod 使用的 Azure 磁碟 PersistentVolumeClaim 時出錯

如果嘗試刪除 pod 使用的 Azure 磁碟 PersistentVolumeClaim，可能會看到錯誤。例如：

```text
$ kubectl describe pv pvc-d8eebc1d-74d3-11e8-902b-e22b71bb1c06
...
Message:         disk.DisksClient#Delete: Failure responding to request: StatusCode=409 -- Original Error: autorest/azure: Service returned an error. Status=409 Code="OperationNotAllowed" Message="Disk kubernetes-dynamic-pvc-d8eebc1d-74d3-11e8-902b-e22b71bb1c06 is attached to VM /subscriptions/{subs-id}/resourceGroups/MC_markito-aks-pvc_markito-aks-pvc_westus/providers/Microsoft.Compute/virtualMachines/aks-agentpool-25259074-0."
```

在 Kubernetes 版本1.10 及更高版本中，預設情況下已啟用 PersistentVolumeClaim protection 功能以防止此錯誤。如果你使用的 Kubernetes 版本不能解決此問題，則可以透過在刪除 PersistentVolumeClaim 前使用 PersistentVolumeClaim 刪除 pod 來緩解此問題。

## 參考文件

* [Known kubernetes issues on Azure](https://github.com/andyzhangx/demo/tree/master/issues)
* [Introduction of AzureDisk](https://docs.microsoft.com/zh-cn/azure/virtual-machines/windows/about-disks-and-vhds)
* [AzureDisk volume examples](https://github.com/kubernetes/examples/tree/master/staging/volumes/azure_disk)
* [High-performance Premium Storage and managed disks for VMs](https://docs.microsoft.com/en-us/azure/virtual-machines/windows/premium-storage)
