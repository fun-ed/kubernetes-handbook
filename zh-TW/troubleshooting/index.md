# 排錯概覽

Kubernetes 叢集以及應用排錯的一般方法，主要包括

* [叢集狀態異常排錯](cluster.md)
* [Pod執行異常排錯](pod.md)
* [網路異常排錯](network.md)
* [持久化儲存異常排錯](pv/)
  * [Azure Disk CSI 排錯](pv/azuredisk.md)
  * [Azure Files CSI 排錯](pv/azurefile.md)
* [Windows容器排錯](windows.md)
* [雲平台異常排錯](cloud/)
  * [Azure 排錯](cloud/azure.md)
* [常用排錯工具](tools.md)

第三方 AI 排錯工具若具備 Kubernetes API 存取權限，應先審查其維護狀態、權限範圍、憑證處理及資料保留政策；不得將未審查的工具連線至正式叢集。

在排錯過程中，`kubectl` 是最重要的工具，通常也是定位錯誤的起點。這裡也列出一些常用的命令，在後續的各種排錯過程中都會經常用到。

### 檢視 Pod 狀態以及執行節點

```bash
kubectl get pods -o wide
kubectl -n kube-system get pods -o wide
```

### 檢視 Pod 事件

```bash
kubectl describe pod <pod-name>
```

### 檢視 Node 狀態

```bash
kubectl get nodes
kubectl describe node <node-name>
```

### kube-apiserver 日誌

```bash
PODNAME=$(kubectl -n kube-system get pod -l component=kube-apiserver -o jsonpath='{.items[0].metadata.name}')
kubectl -n kube-system logs $PODNAME --tail 100
```

以上命令操作假設控制平面以 Kubernetes 靜態 Pod 的形式來執行。如果 kube-apiserver 是用 systemd 管理的，則需要登入到 master 節點上，然後使用 journalctl -u kube-apiserver 檢視其日誌。

### kube-controller-manager 日誌

```bash
PODNAME=$(kubectl -n kube-system get pod -l component=kube-controller-manager -o jsonpath='{.items[0].metadata.name}')
kubectl -n kube-system logs $PODNAME --tail 100
```

以上命令操作假設控制平面以 Kubernetes 靜態 Pod 的形式來執行。如果 kube-controller-manager 是用 systemd 管理的，則需要登入到 master 節點上，然後使用 journalctl -u kube-controller-manager 檢視其日誌。

### kube-scheduler 日誌

```bash
PODNAME=$(kubectl -n kube-system get pod -l component=kube-scheduler -o jsonpath='{.items[0].metadata.name}')
kubectl -n kube-system logs $PODNAME --tail 100
```

以上命令適用於透過 API Server 暴露日誌的控制平面 Pod。若元件以 systemd 服務執行，請使用發行版提供的受控主機存取途徑讀取 `journalctl` 日誌。

### CoreDNS 日誌

叢集 DNS 通常由 CoreDNS 提供；Pod 標籤和部署方式依發行版而異。先列出 `kube-system` 中的 Pod，再檢查實際 DNS Pod 的日誌：

```bash
kubectl -n kube-system get pods
kubectl -n kube-system logs <coredns-pod> --all-containers=true --tail=100
```

### Kubelet 日誌

Kubelet 日誌通常由節點上的 systemd 收集。先用 Kubernetes Events 和 Node 狀態縮小問題範圍；若必須讀取 kubelet 主機日誌，請遵循雲服務商或節點發行版提供的受控存取與審計流程。不要下載並執行未經稽核的特權 `kubectl-node-shell` 外掛，也不要為排錯給節點設定公網 IP。

### Kube-proxy 日誌

Kube-proxy 通常以 DaemonSet 的方式部署，可以直接用 kubectl 查詢其日誌

```bash
$ kubectl -n kube-system get pod -l component=kube-proxy
NAME               READY     STATUS    RESTARTS   AGE
kube-proxy-42zpn   1/1       Running   0          1d
kube-proxy-7gd4p   1/1       Running   0          3d
kube-proxy-87dbs   1/1       Running   0          4d
$ kubectl -n kube-system logs kube-proxy-42zpn
```

## 參考文件

* [hjacobs/kubernetes-failure-stories](https://github.com/hjacobs/kubernetes-failure-stories) 整理了一些公開的 Kubernetes 異常案例。
* [AKS 疑難排解](https://learn.microsoft.com/azure/aks/troubleshooting)提供 Azure Kubernetes Service 官方排錯資料。
* [GKE 疑難排解](https://cloud.google.com/kubernetes-engine/docs/troubleshooting)提供 Google Kubernetes Engine 官方排錯資料。
