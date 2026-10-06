# AzureFile

[AzureFile](https://docs.microsoft.com/zh-cn/azure/storage/files/storage-files-introduction) 提供了基於 SMB 協議（也稱 CIFS）託管檔案共享服務。它支援 Windows 和 Linux 容器，並支援跨主機的共享，可用於多個 Pod 之間的共享儲存。AzureFile 的缺點是效能[較差](https://docs.microsoft.com/en-us/azure/storage/files/storage-files-scale-targets)（[AKS\#223](https://github.com/Azure/AKS/issues/223)），並且不提供 Premium 儲存。

推薦基於 StorageClass 來使用 AzureFile，即

```yaml
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: azurefile
provisioner: kubernetes.io/azure-file
mountOptions:
  - dir_mode=0777
  - file_mode=0777
  - uid=1000
  - gid=1000
parameters:
  skuName: Standard_LRS
```

使用 AzureFile 推薦的版本：

| Kubernetes version | Recommended version |
| :--- | :---: |
| 1.12 | 1.12.6 或更高版本 |
| 1.13 | 1.13.4 或更高版本 |
| 1.14 | 1.14.0 或更高版本 |
| &gt;=1.15 | &gt;=1.15 |

## 存取權限

AzureFile 使用 [mount.cifs](https://linux.die.net/man/8/mount.cifs) 將其遠端儲存掛載到 Node 上，而`fileMode` 和 `dirMode` 控制了掛載後檔案和目錄的存取權限。不同的 Kubernetes 版本，`fileMode` 和 `dirMode` 的預設選項是不同的

| Kubernetes 版本 | fileMode和dirMode |
| :--- | :--- |
| v1.6.x, v1.7.x | 0777 |
| v1.8.0-v1.8.5 | 0700 |
| v1.8.6 or above | 0755 |
| v1.9.0 | 0700 |
| v1.9.1-v1.12.1 | 0755 |
| &gt;=v1.12.2 | 0777 |

按照預設的權限會導致非跟使用者無法在目錄中建立新的檔案，解決方法為

* v1.8.0-v1.8.5：設定容器以 root 使用者執行，如設定 `spec.securityContext.runAsUser: 0`
* v1.8.6 以及更新版本：在 AzureFile StorageClass 透過 mountOptions 設定預設權限，比如設定為 `0777` 的方法為

```yaml
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: azurefile
provisioner: kubernetes.io/azure-file
mountOptions:
  - dir_mode=0777
  - file_mode=0777
  - uid=1000
  - gid=1000
  - mfsymlinks
  - nobrl
  - cache=none
parameters:
  skuName: Standard_LRS
```

## Windows Node 重啟後無法存取 AzureFile

Windows Node 重啟後，掛載 AzureFile 的 Pod 可以看到如下錯誤（[\#60624](https://github.com/kubernetes/kubernetes/issues/60624)）：

```bash
Warning  Failed                 1m (x7 over 1m)  kubelet, 77890k8s9010  Error: Error response from daemon: invalid bind mount spec "c:\\var\\lib\\kubelet\\pods\\07251c5c-1cfc-11e8-8f70-000d3afd4b43\\volumes\\kubernetes.io~azure-file\\pvc-fb6159f6-1cfb-11e8-8f70-000d3afd4b43:c:/mnt/azure": invalid volume specification: 'c:\var\lib\kubelet\pods\07251c5c-1cfc-11e8-8f70-000d3afd4b43\volumes\kubernetes.io~azure-file\pvc-fb6159f6-1cfb-11e8-8f70-000d3afd4b43:c:/mnt/azure': invalid mount config for type "bind": bind source path does not exist
  Normal   SandboxChanged         1m (x8 over 1m)  kubelet, 77890k8s9010  Pod sandbox changed, it will be killed and re-created.
```

臨時性解決方法為刪除並重新建立使用了 AzureFile 的 Pod。當 Pod 使用控制器（如 Deployment、StatefulSet等）時，刪除 Pod 後控制器會自動建立一個新的 Pod。

該問題的修復 [\#60625](https://github.com/kubernetes/kubernetes/pull/60625) 包含在 v1.10 中。

## AzureFile ProvisioningFailed

Azure 檔案共享的名字最大隻允許 63 個位元組，因而在叢集名字較長的叢集（Kubernetes v1.7.10 或者更老的叢集）裡面有可能會碰到 AzureFile 名字長度超限的情況，導致 AzureFile ProvisioningFailed：

```bash
persistentvolume-controller    Warning    ProvisioningFailed Failed to provision volume with StorageClass "azurefile": failed to find a matching storage account
```

碰到該問題時可以透過升級叢集解決，其修復 [\#48326](https://github.com/kubernetes/kubernetes/pull/48326) 已經包含在 v1.7.11、v1.8 以及更新版本中。

在開啟 RBAC 的叢集中，由於 AzureFile 需要存取 Secret，而 kube-controller-manager 中並未為 AzureFile 自動授權，從而也會導致 ProvisioningFailed：

```bash
Events:
  Type     Reason              Age   From                         Message
  ----     ------              ----  ----                         -------
  Warning  ProvisioningFailed  8s    persistentvolume-controller  Failed to provision volume with StorageClass "azurefile": Couldn't create secret secrets is forbidden: User "system:serviceaccount:kube-syste
m:persistent-volume-binder" cannot create secrets in the namespace "default"
  Warning  ProvisioningFailed  8s    persistentvolume-controller  Failed to provision volume with StorageClass "azurefile": failed to find a matching storage account
```

解決方法是為 ServiceAccount `persistent-volume-binder` 授予 Secret 的存取權限：

```yaml
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: system:azure-cloud-provider
rules:
- apiGroups: ['']
  resources: ['secrets']
  verbs:     ['get','create']
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: system:azure-cloud-provider
roleRef:
  kind: ClusterRole
  apiGroup: rbac.authorization.k8s.io
  name: system:azure-cloud-provider
subjects:
- kind: ServiceAccount
  name: persistent-volume-binder
  namespace: kube-system
```

## Azure German Cloud 無法使用 AzureFile

Azure German Cloud 僅在 v1.7.11+、v1.8+ 以及更新版本中支援（[\#48460](https://github.com/kubernetes/kubernetes/pull/48460)），升級 Kubernetes 版本即可解決。

## "could not change permissions" 錯誤

在 Azure Files 外掛上執行 PostgreSQL 時，可能會看到類似於以下內容的錯誤：

```text
initdb: could not change permissions of directory "/var/lib/postgresql/data": Operation not permitted
fixing permissions on existing directory /var/lib/postgresql/data
```

此錯誤是由使用 cifs/SMB 協議的 Azure 檔案外掛導致的。 使用 cifs/SMB 協議時，無法在裝載後更改檔案和目錄權限。 若要解決此問題，請將子路徑與 Azure 磁碟外掛結合使用。

## 參考文件

* [Known kubernetes issues on Azure](https://github.com/andyzhangx/demo/tree/master/issues)
* [Introduction of Azure File Storage](https://docs.microsoft.com/zh-cn/azure/storage/files/storage-files-introduction)
* [AzureFile volume examples](https://github.com/kubernetes/examples/tree/master/staging/volumes/azure_file)
* [Persistent volumes with Azure files](https://docs.microsoft.com/en-us/azure/aks/azure-files-dynamic-pv)
* [Azure Files scalability and performance targets](https://docs.microsoft.com/en-us/azure/storage/files/storage-files-scale-targets)
