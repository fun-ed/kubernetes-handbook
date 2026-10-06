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

> 旧节点的容器、镜像 ID 与输出已移至[封存的诊断输出](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/extension/cri/cri-tools.md)；上方列出的 crictl 命令可用于当前受管理容器的诊断。

## 参考文档

* [Debugging Kubernetes nodes with crictl](https://kubernetes.io/docs/tasks/debug/debug-cluster/crictl/)
* [https://github.com/kubernetes-sigs/cri-tools](https://github.com/kubernetes-sigs/cri-tools)

