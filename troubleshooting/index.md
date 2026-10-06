# 排错概览

Kubernetes 集群以及应用排错的一般方法，主要包括

* [集群状态异常排错](cluster.md)
* [Pod运行异常排错](pod.md)
* [网络异常排错](network.md)
* [持久化存储异常排错](pv/)
  * [Azure Disk CSI 排错](pv/azuredisk.md)
  * [Azure Files CSI 排错](pv/azurefile.md)
* [Windows容器排错](windows.md)
* [云平台异常排错](cloud/)
  * [Azure 排错](cloud/azure.md)
* [常用排错工具](tools.md)

第三方 AI 排错工具若具备 Kubernetes API 存取权限，应先审查其维护状态、权限范围、凭证处理及数据留存政策；不得将未审查的工具连接至生产集群。

在排错过程中，`kubectl` 是最重要的工具，通常也是定位错误的起点。这里也列出一些常用的命令，在后续的各种排错过程中都会经常用到。

### 查看 Pod 状态以及运行节点

```bash
kubectl get pods -o wide
kubectl -n kube-system get pods -o wide
```

### 查看 Pod 事件

```bash
kubectl describe pod <pod-name>
```

### 查看 Node 状态

```bash
kubectl get nodes
kubectl describe node <node-name>
```

### kube-apiserver 日志

```bash
PODNAME=$(kubectl -n kube-system get pod -l component=kube-apiserver -o jsonpath='{.items[0].metadata.name}')
kubectl -n kube-system logs $PODNAME --tail 100
```

以上命令操作假设控制平面以 Kubernetes 静态 Pod 的形式来运行。如果 kube-apiserver 是用 systemd 管理的，则需要登录到 master 节点上，然后使用 journalctl -u kube-apiserver 查看其日志。

### kube-controller-manager 日志

```bash
PODNAME=$(kubectl -n kube-system get pod -l component=kube-controller-manager -o jsonpath='{.items[0].metadata.name}')
kubectl -n kube-system logs $PODNAME --tail 100
```

以上命令操作假设控制平面以 Kubernetes 静态 Pod 的形式来运行。如果 kube-controller-manager 是用 systemd 管理的，则需要登录到 master 节点上，然后使用 journalctl -u kube-controller-manager 查看其日志。

### kube-scheduler 日志

```bash
PODNAME=$(kubectl -n kube-system get pod -l component=kube-scheduler -o jsonpath='{.items[0].metadata.name}')
kubectl -n kube-system logs $PODNAME --tail 100
```

以上命令适用于通过 API Server 暴露日志的控制平面 Pod。若组件以 systemd 服务运行，请使用发行版提供的受控主机访问途径读取 `journalctl` 日志。

### CoreDNS 日志

集群 DNS 通常由 CoreDNS 提供；Pod 标签和部署方式依发行版而异。先列出 `kube-system` 中的 Pod，再检查实际 DNS Pod 的日志：

```bash
kubectl -n kube-system get pods
kubectl -n kube-system logs <coredns-pod> --all-containers=true --tail=100
```

### Kubelet 日志

Kubelet 日志通常由节点上的 systemd 收集。先用 Kubernetes Events 和 Node 状态缩小问题范围；若必须读取 kubelet 主机日志，请遵循云服务商或节点发行版提供的受控访问与审计流程。不要下载并运行未经审核的特权 `kubectl-node-shell` 插件，也不要为排错给节点配置公网 IP。

### Kube-proxy 日志

Kube-proxy 通常以 DaemonSet 的方式部署，可以直接用 kubectl 查询其日志

```bash
$ kubectl -n kube-system get pod -l component=kube-proxy
NAME               READY     STATUS    RESTARTS   AGE
kube-proxy-42zpn   1/1       Running   0          1d
kube-proxy-7gd4p   1/1       Running   0          3d
kube-proxy-87dbs   1/1       Running   0          4d
$ kubectl -n kube-system logs kube-proxy-42zpn
```

## 参考文档

* [hjacobs/kubernetes-failure-stories](https://github.com/hjacobs/kubernetes-failure-stories) 整理了一些公开的 Kubernetes 异常案例。
* [AKS 疑难排解](https://learn.microsoft.com/azure/aks/troubleshooting)提供 Azure Kubernetes Service 的官方排错资料。
* [GKE 疑难排解](https://cloud.google.com/kubernetes-engine/docs/troubleshooting)提供 Google Kubernetes Engine 的官方排错资料。
