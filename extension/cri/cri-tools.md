# CRI-tools

通常，容器引擎会提供一个命令行工具来帮助用户调试容器应用并简化故障排错。比如使用 Docker 作为容器运行时的时候，可以使用 `docker` 命令来查看容器和镜像的状态，并验证容器的配置是否正确。但在使用其他容器引擎时，推荐使用 `crictl` 来替代 `docker` 工具。

截至 2026-10-05，cri-tools 最新稳定版本为 [v1.37.0](https://github.com/kubernetes-sigs/cri-tools/releases/tag/v1.37.0)。该版本线对应 Kubernetes v1.37，但这不代表任意 CRI 运行时都通过了兼容性测试。Kubernetes v1.37.1 仓库的依赖清单为特定引导脚本固定 crictl v1.36.0；这不是 cri-tools 的最新发布版本。

在节点上设置运行时端点，避免 `crictl` 猜测运行时：

```yaml
# /etc/crictl.yaml
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
timeout: 10
debug: false
```

CRI-O 使用 `unix:///var/run/crio/crio.sock`。更改端点后，可用 `crictl info` 检查运行时是否提供 CRI v1 服务，再用 `crictl pods`、`crictl ps -a`、`crictl images`、`crictl logs <container-id>` 或 `crictl exec -it <container-id> sh` 诊断容器。

官方资料：[cri-tools v1.37.0 发布](https://github.com/kubernetes-sigs/cri-tools/releases/tag/v1.37.0)、[crictl 文档](https://github.com/kubernetes-sigs/cri-tools/blob/v1.37.0/docs/crictl.md)、[Kubernetes 节点 crictl 指南](https://kubernetes.io/docs/tasks/debug/debug-cluster/crictl/)。


`crictl` 是 [cri-tools](https://github.com/kubernetes-sigs/cri-tools) 提供的 CRI 调试客户端。它绕过 kubelet，直接调用容器运行时的 CRI 服务；不能替代 `kubectl`，也不应作为日常工作负载创建工具。节点上手工创建的 Pod 或容器不受 kubelet 管理。
`critest` 是 cri-tools 提供的 CRI 集成测试工具。仅在开发或验证运行时的测试环境运行；不要把它当作生产节点的排障工具。当前文档见 [cri-tools v1.37.0](https://github.com/kubernetes-sigs/cri-tools/tree/v1.37.0)。

`crictl` 提供 `pods`、`ps`、`images`、`inspect`、`logs` 和 `exec` 等诊断命令。只用它查看或排查由 kubelet 管理的运行时对象。不要在 Kubernetes 节点上用 `crictl runp` 或 `crictl create` 管理应用 Pod。

> 下列命令输出来自旧节点和旧镜像。它们只展示 `crictl` 的交互形式，不表示这些镜像、容器或字段适用于当前 Kubernetes。

## crictl 示例

### 查询 Pod

```bash
$ crictl pods --name nginx-65899c769f-wv2gp
POD ID              CREATED             STATE               NAME                     NAMESPACE           ATTEMPT
4dccb216c4adb       2 minutes ago       Ready               nginx-65899c769f-wv2gp   default             0
```

### Pod 列表

```bash
$ crictl pods
POD ID              CREATED              STATE               NAME                         NAMESPACE           ATTEMPT
926f1b5a1d33a       About a minute ago   Ready               sh-84d7dcf559-4r2gq          default             0
4dccb216c4adb       About a minute ago   Ready               nginx-65899c769f-wv2gp       default             0
a86316e96fa89       17 hours ago         Ready               kube-proxy-gblk4             kube-system         0
919630b8f81f1       17 hours ago         Ready               nvidia-device-plugin-zgbbv   kube-system         0
```

### 镜像列表

```bash
$ crictl images
IMAGE                                     TAG                 IMAGE ID            SIZE
busybox                                   latest              8c811b4aec35f       1.15MB
k8s-gcrio.azureedge.net/hyperkube-amd64   v1.10.3             e179bbfe5d238       665MB
k8s-gcrio.azureedge.net/pause-amd64       3.1                 da86e6ba6ca19       742kB
nginx                                     latest              cd5239a0906a6       109MB
```

### 容器列表

```bash
$ crictl ps -a
CONTAINER ID        IMAGE                                                                                                             CREATED             STATE               NAME                       ATTEMPT
1f73f2d81bf98       busybox@sha256:141c253bc4c3fd0a201d32dc1f493bcf3fff003b6df416dea4f41046e0f37d47                                   7 minutes ago       Running             sh                         1
9c5951df22c78       busybox@sha256:141c253bc4c3fd0a201d32dc1f493bcf3fff003b6df416dea4f41046e0f37d47                                   8 minutes ago       Exited              sh                         0
87d3992f84f74       nginx@sha256:d0a8828cccb73397acb0073bf34f4d7d8aa315263f1e7806bf8c55d8ac139d5f                                     8 minutes ago       Running             nginx                      0
1941fb4da154f       k8s-gcrio.azureedge.net/hyperkube-amd64@sha256:00d814b1f7763f4ab5be80c58e98140dfc69df107f253d7fdd714b30a714260a   18 hours ago        Running             kube-proxy                 0
```

### 容器内执行命令

```bash
$ crictl exec -i -t 1f73f2d81bf98 ls
bin   dev   etc   home  proc  root  sys   tmp   usr   var
```

### 容器日志

```bash
crictl logs 87d3992f84f74
10.240.0.96 - - [06/Jun/2018:02:45:49 +0000] "GET / HTTP/1.1" 200 612 "-" "curl/7.47.0" "-"
10.240.0.96 - - [06/Jun/2018:02:45:50 +0000] "GET / HTTP/1.1" 200 612 "-" "curl/7.47.0" "-"
10.240.0.96 - - [06/Jun/2018:02:45:51 +0000] "GET / HTTP/1.1" 200 612 "-" "curl/7.47.0" "-"
```

## 参考文档

* [Debugging Kubernetes nodes with crictl](https://kubernetes.io/docs/tasks/debug/debug-cluster/crictl/)
* [https://github.com/kubernetes-sigs/cri-tools](https://github.com/kubernetes-sigs/cri-tools)

