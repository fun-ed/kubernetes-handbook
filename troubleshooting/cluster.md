# 集群排错

本章介绍集群状态异常的排错方法，包括控制平面、Node 与集群 DNS 等组件；网络问题另见[网络异常排错方法](network.md)。

## 概述

排查集群状态异常问题通常从 Node 和 Kubernetes 服务 的状态出发，定位出具体的异常服务，再进而寻找解决方法。集群状态异常可能的原因比较多，常见的有

* 虚拟机或物理机宕机
* 网络分区
* Kubernetes 服务未正常启动
* 数据丢失或持久化存储不可用（一般在公有云或私有云平台中）
* 操作失误（如配置错误）

按照不同的组件来说，具体的原因可能包括

* kube-apiserver 无法启动会导致
  * 集群不可访问
  * 已有的 Pod 和服务正常运行（依赖于 Kubernetes API 的除外）
* etcd 集群异常会导致
  * kube-apiserver 无法正常读写集群状态，进而导致 Kubernetes API 访问出错
  * kubelet 无法周期性更新状态
* kube-controller-manager/kube-scheduler 异常会导致
  * 复制控制器、节点控制器、云服务控制器等无法工作，从而导致 Deployment、Service 等无法工作，也无法注册新的 Node 到集群中来
  * 新创建的 Pod 无法调度（总是 Pending 状态）
* Node 本身宕机或者 Kubelet 无法启动会导致
  * Node 上面的 Pod 无法正常运行
  * 已在运行的 Pod 无法正常终止
* 网络分区会导致 Kubelet 等与控制平面通信异常以及 Pod 之间通信异常

为了维持集群的健康状态，推荐在部署集群时就考虑以下

* 在云平台上开启 VM 的自动重启功能
* 为 Etcd 配置多节点高可用集群，使用持久化存储（如 AWS EBS 等），定期备份数据
* 为控制平面配置高可用，例如多 kube-apiserver 与多节点运行 kube-controller-manager、kube-scheduler；集群 DNS 通常由 CoreDNS 提供
* 尽量使用复制控制器和 Service，而不是直接管理 Pod
* 跨地域的多 Kubernetes 集群

## 查看 Node 状态

一般来说，可以首先查看 Node 的状态，确认 Node 本身是不是 Ready 状态

```bash
kubectl get nodes
kubectl describe node <node-name>
```

如果是 NotReady 状态，则可以执行 `kubectl describe node <node-name>` 命令来查看当前 Node 的事件。这些事件通常都会有助于排查 Node 发生的问题。

## 安全访问 Node

需要检查 Node 操作系统、kubelet 或 CRI 运行时时，请使用云平台控制台或组织批准的 SSH/bastion 通道，并将管理端口限制在可信来源。不要通过公网 `LoadBalancer` 暴露 SSH 服务。

在可信的测试集群中，如只需执行网络诊断，可参考 [`examples/ssh.yaml`](../examples/ssh.yaml) 部署受限的交互式 `node-debug-shell` Pod。先在清单中将 `nodeName` 替换为已授权的目标 Node：

```bash
kubectl apply -f examples/ssh.yaml
kubectl wait --for=condition=Ready pod/node-debug-shell --timeout=60s
kubectl exec -it node-debug-shell -- /bin/sh
kubectl delete -f examples/ssh.yaml
```

此清单不会运行 sshd，也不创建 SSH Service；`kubectl exec` 只提供容器内 shell，不会自动授予访问 Node 文件系统、进程命名空间或 systemd 的权限。只有在可信集群并经过授权时才使用 `hostNetwork` 调试 Pod；操作系统级诊断仍应通过受控 Node 管理通道完成。

## 查看日志

一般来说，Kubernetes 的主要组件有两种部署方法

* 直接使用 systemd 等启动控制节点的各个服务
* 使用 Static Pod 来管理和启动控制节点的各个服务

使用 systemd 等管理控制节点服务时，查看日志必须要首先 SSH 登录到机器上，然后查看具体的日志文件。如

```bash
journalctl -l -u kube-apiserver
journalctl -l -u kube-controller-manager
journalctl -l -u kube-scheduler
journalctl -l -u kubelet
journalctl -l -u kube-proxy
```

或者直接查看日志文件

* /var/log/kube-apiserver.log
* /var/log/kube-scheduler.log
* /var/log/kube-controller-manager.log
* /var/log/kubelet.log
* /var/log/kube-proxy.log

而对于使用 Static Pod 部署集群控制平面服务的场景，可以参考下面这些查看日志的方法。

### kube-apiserver 日志

```bash
PODNAME=$(kubectl -n kube-system get pod -l component=kube-apiserver -o jsonpath='{.items[0].metadata.name}')
kubectl -n kube-system logs $PODNAME --tail 100
```

### kube-controller-manager 日志

```bash
PODNAME=$(kubectl -n kube-system get pod -l component=kube-controller-manager -o jsonpath='{.items[0].metadata.name}')
kubectl -n kube-system logs $PODNAME --tail 100
```

### kube-scheduler 日志

```bash
PODNAME=$(kubectl -n kube-system get pod -l component=kube-scheduler -o jsonpath='{.items[0].metadata.name}')
kubectl -n kube-system logs $PODNAME --tail 100
```

### CoreDNS 日志

CoreDNS Pod 的名称和标签会因发行版不同而变化。先查看 `kube-system` 中的 DNS Pod，再读取实际 Pod 的日志：

```bash
kubectl -n kube-system get pods
kubectl -n kube-system logs <coredns-pod> --all-containers=true --tail=100
```

### Kubelet 日志

查看 Kubelet 日志需要首先 SSH 登录到 Node 上。

```bash
journalctl -l -u kubelet
```

### Kube-proxy 日志

Kube-proxy 通常以 DaemonSet 的方式部署

```bash
$ kubectl -n kube-system get pod -l component=kube-proxy
NAME               READY     STATUS    RESTARTS   AGE
kube-proxy-42zpn   1/1       Running   0          1d
kube-proxy-7gd4p   1/1       Running   0          3d
kube-proxy-87dbs   1/1       Running   0          4d
$ kubectl -n kube-system logs kube-proxy-42zpn
```

## API Server 健康与内存排查

`/healthz` 已弃用；检查 API Server 时使用 `/livez` 和 `/readyz`。`livez` 检查进程是否存活，`readyz` 检查是否已准备好接收请求：

```bash
kubectl get --raw='/livez'
kubectl get --raw='/readyz?verbose'
```

执行大量 List 请求时出现延迟或 API Server 内存压力，应先检查组件日志、Pod 资源使用情况和请求规模。资源指标查询要求集群提供可用的 Metrics API：

```bash
kubectl -n kube-system get pods
kubectl -n kube-system describe pod <apiserver-pod>
kubectl -n kube-system logs <apiserver-pod> --tail=100
kubectl top pod -n kube-system
```

Kubernetes v1.33 为 JSON/Protobuf List 响应增加逐项编码，可在特定请求场景降低内存使用；收益因请求和集群而异，不应承诺固定倍率。相关 feature gates 在 v1.37 已移除，不要继续配置。若问题持续，应基于监控和目标发行版文档评估 API Server 资源分配及访问模式，不要直接套用过时的静态 Pod 参数或 `etcd-servers-overrides` 示例。

## CoreDNS 故障排查

集群 DNS 常由 CoreDNS 提供。先查看集群 DNS Pod 与 Service 的实际名称，再检查对应 CoreDNS Pod 的日志：

```bash
kubectl -n kube-system get pods
kubectl -n kube-system get service
kubectl -n kube-system logs <coredns-pod> --all-containers=true --tail=100
DNS_SERVICE='<dns-service-name-shown-above>'
kubectl -n kube-system get endpointslices -l "kubernetes.io/service-name=$DNS_SERVICE"
```


CoreDNS 无法响应时，检查 Corefile、上游 DNS 可达性、Pod 网络和节点防火墙，并查看 CNI 与 kubelet 日志。不要通过 `iptables -P FORWARD ACCEPT` 放开主机转发策略；这会改变整台 Node 的安全边界。网络问题的进一步检查见[网络排错指南](network.md)。

## Node NotReady

先执行 `kubectl describe node <node-name>` 查看 Node Conditions 和 Events，再根据发行版检查 kubelet 与实际 CRI 运行时服务的状态和日志。常见原因包括：

* kubelet 或 CRI 运行时未运行，或 socket 配置不匹配
* CNI 插件未就绪、IP 地址耗尽或网络配置异常
* CPU、内存、磁盘空间或 inode 压力
* 控制平面或 Node 之间的网络中断

Kubernetes 默认使用 CRI 兼容运行时（例如 containerd 或 CRI-O）；Docker Engine 若通过外部适配器提供 CRI，应按该适配器文档排查。可结合 Node Problem Detector 报告的 Conditions 与 Events 定位主机问题。
## Node Allocatable 事件

Node Allocatable 用于为系统守护进程和驱逐阈值预留节点资源，具体配置由 kubelet 与集群发行版管理。旧示例中的 AKS/Docker overlay 路径和直接运行 kubelet 命令属于历史环境，不要照搬。若出现 `FailedNodeAllocatableEnforcement`，先查看 Node Conditions、kubelet 日志、操作系统 cgroup 模式与发行版配置，再按对应版本的 [Node Allocatable 文档](https://kubernetes.io/docs/tasks/administer-cluster/reserve-compute-resources/)排查。
## kube-proxy 与 conntrack 错误

kube-proxy 的日志、所需内核功能及网络规则取决于代理模式和发行版。遇到 conntrack 错误时，先确认所用 kube-proxy 模式、节点内核/conntrack 支持与 kube-proxy 当前文档；旧版日志中的 `conntrack` 二进制缺失不能证明所有集群都应安装同一个软件包。若集群使用替代 Service 实现，应改查该实现的日志与规则。
## Dashboard 中没有资源指标

Heapster 已退出维护，不要重新部署 Heapster。排查 Dashboard 缺少指标时，检查 `v1beta1.metrics.k8s.io` APIService 是否注册且后端可用；截至本书基线的 Metrics Server v0.9.0 提供的是 v1beta1。Kubernetes 的 `metrics.k8s.io/v1` API 稳定，不代表此版本的 Metrics Server 已提供 v1；`kubectl top` 可查询 v1 并回退至 v1beta1，因此 `kubectl top` 成功也不能证明 Dashboard 所用 API 可用。另须确认所用 Dashboard 版本支援的指标 API。不要依赖旧版 Heapster 标签、安装命令或资源图表截图。
## HPA 不自动扩展 Pod

查看 HPA 的事件，发现

```bash
$ kubectl describe hpa php-apache
Name:                                                  php-apache
Namespace:                                             default
Labels:                                                <none>
Annotations:                                           <none>
CreationTimestamp:                                     Wed, 27 Dec 2017 14:36:38 +0800
Reference:                                             Deployment/php-apache
Metrics:                                               ( current / target )
  resource cpu on pods  (as a percentage of request):  <unknown> / 50%
Min replicas:                                          1
Max replicas:                                          10
Conditions:
  Type           Status  Reason                   Message
  ----           ------  ------                   -------
  AbleToScale    True    SucceededGetScale        the HPA controller was able to get the target's current scale
  ScalingActive  False   FailedGetResourceMetric  the HPA was unable to compute the replica count: unable to get metrics for resource cpu: unable to fetch metrics from API: the server could not find the requested resource (get pods.metrics.k8s.io)
Events:
  Type     Reason                   Age                  From                       Message
  ----     ------                   ----                 ----                       -------
  Warning  FailedGetResourceMetric  3m (x2231 over 18h)  horizontal-pod-autoscaler  unable to get metrics for resource cpu: unable to fetch metrics from API: the server could not find the requested resource (get pods.metrics.k8s.io)
```

这说明 Metrics API 未正常提供指标。检查 Metrics Server 及 `v1beta1.metrics.k8s.io` APIService 状态；Kubernetes v1.37.1 的 HPA resource-metrics client 仍使用 v1beta1，不能只确认 `metrics.k8s.io/v1` 可用。`kubectl top` 可先查询 v1 再回退至 v1beta1；还需核对 aggregation、节点／Pod 指标采集链路和 Metrics Server 的日志。不要假设旧版 API 或独立安装命令仍适用。

## Node 存储空间不足

Kubelet 会按节点可用空间阈值回收未使用的镜像与容器。先确认实际占满的文件系统和容器运行时，再按发行版及 CRI 运行时文档检查：

```bash
df -h
sudo crictl info
sudo crictl images
sudo crictl ps -a
```

`crictl` 必须连接到节点实际使用的 CRI endpoint。不要对 Docker socket 运行 `docker-gc`，也不要在未确认镜像、容器是否仍被工作负载使用前手动删除运行时数据。

## `/sys/fs/cgroup` 空间或资源控制异常

cgroup 故障通常与节点操作系统、systemd、内核、容器运行时及 kubelet 配置相关。先读取 Node conditions、Events 和受控的节点 kubelet/runtime 日志，再按当前发行版和内核版本排查。不要部署旧 Gist、定时脚本或 DaemonSet 来清理 systemd cgroup；手工删除 cgroup 可能破坏仍在运行的 Pod。

## ConfigMap/Secret watch 的历史问题

Kubernetes issue [#74412](https://github.com/kubernetes/kubernetes/issues/74412) 记录的是 v1.12/v1.13 时期的特定负载和实现问题。该历史案例不是 v1.37 的通用故障说明；不要据此调整 API Server HTTP/2 限制或套用旧 kubelet workaround。当前排查应从 API Server、kubelet 和节点指标及 Events 入手，并核对目标版本文档。

## Kubelet 内存和指标排错

本页原先的 pprof 输出来自旧版 hyperkube，并使用了未认证的 kubelet read-only 端口 `10255`；该示例已过时，不要启用或暴露此端口，也不要照旧建议关闭 Reflector metrics。当前诊断应通过发行版支持的监控与安全 kubelet 指标接口收集数据。pprof 或节点日志可能包含敏感信息，只能在授权、受控且审计的环境中访问。

## kube-controller-manager 更新冲突

对象更新冲突可能是正常的 optimistic concurrency 行为：客户端应基于最新 `resourceVersion` 重读对象后重试。原案例使用的 `autoscaling/v2beta2` 是历史 API；不要把控制平面组件缓存不一致当作唯一原因，也不要在没有灾难恢复 runbook 指引时重启全部控制平面组件。etcd 恢复应遵循集群发行版的受测恢复流程。

## 其他已知问题

早期 Kubernetes 版本的缺陷报告可能不适用于当前版本；先核对 issue 的受影响版本与修复版本，再按当前集群支持流程处置。

## 参考文档

* [Troubleshoot Clusters](https://kubernetes.io/docs/tasks/debug-application-cluster/debug-cluster/)
* [Azure Kubernetes Service 节点访问说明](https://learn.microsoft.com/azure/aks/node-access)
