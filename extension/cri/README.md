# 运行时插件 CRI

容器运行时插件（Container Runtime Interface，简称 CRI）是 Kubernetes v1.5 引入的容器运行时接口，它将 Kubelet 与容器运行时解耦，将原来完全面向 Pod 级别的内部接口拆分成面向 Sandbox 和 Container 的 gRPC 接口，并将镜像管理和容器管理分离到不同的服务。

## Kubernetes v1.37.1 当前运行时

Kubernetes v1.37.1 只接受 CRI v1。Kubernetes 1.26 起不再连接只实现 `v1alpha2` 的运行时；容器运行时若不支持 CRI v1，kubelet 无法注册为 Node。选择运行时之前，还要查看该运行时自己的发布和发行版支持矩阵。

| 运行时 | 2026-10-05 稳定版本 | Kubernetes v1.37.1 的证据 |
| :--- | :--- | :--- |
| [containerd](https://github.com/containerd/containerd/releases/tag/v2.4.1) | v2.4.1（2026-09-24） | Kubernetes 要求 CRI v1；本书未找到 containerd v2.4.1 对 Kubernetes v1.37 的官方兼容矩阵。 |
| [CRI-O](https://github.com/cri-o/cri-o/releases/tag/v1.37.2) | v1.37.2（2026-10-02） | CRI-O 官方安装仓库按 Kubernetes 次版本发布流配套，使用 v1.37 Kubernetes 时选择 CRI-O v1.37 流。 |

Kubernetes 不再内置 dockershim。Docker Engine 需要独立的 CRI 适配器，例如 `cri-dockerd`；它与 Docker Engine 分开发布和支持。

### containerd 2.4.1

containerd 包含 CRI 插件。生成对应版本默认配置后，确认 CRI 插件没有禁用，并让 containerd 与 kubelet 使用相同 cgroup 驱动。systemd 主机推荐 `systemd`。下面是 containerd v2 的配置版本 3 语法：

```toml
version = 3

[plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.runc.options]
  SystemdCgroup = true

[plugins.'io.containerd.cri.v1.images'.pinned_images]
  sandbox = 'registry.k8s.io/pause:3.10.2'
```

CRI socket 为 `unix:///run/containerd/containerd.sock`。配置变更后重启 containerd。二进制包安装、CNI 插件安装和其他配置项见 [containerd v2.4.1 安装说明](https://github.com/containerd/containerd/blob/v2.4.1/docs/getting-started.md) 与 [CRI 插件配置说明](https://github.com/containerd/containerd/blob/v2.4.1/docs/cri/config.md)。

### CRI-O 1.37.2

CRI-O 的稳定软件包发布流与 Kubernetes 次版本对应。用于 Kubernetes v1.37 时使用 CRI-O v1.37 软件包流。CRI-O 默认使用 systemd cgroup manager；以下显式配置示例可放入 `/etc/crio/crio.conf.d/02-runtime.conf`：

```toml
[crio.runtime]
cgroup_manager = "systemd"

[crio.image]
pause_image = "registry.k8s.io/pause:3.10.2"
```

CRI-O 的 CRI socket 为 `unix:///var/run/crio/crio.sock`。配置变更后重启 CRI-O。按发行版安装仓库和软件包的步骤见 [CRI-O 官方打包说明](https://github.com/cri-o/packaging#usage)。

CRI socket 必须与 kubelet 的 `--container-runtime-endpoint` 一致。使用 kubeadm 时，在 `InitConfiguration.nodeRegistration.criSocket` 指定节点运行时 socket。用 `crictl info` 检查 CRI 服务，再按 [crictl 指南](cri-tools.md)诊断节点。

> 以下 CRI v1alpha2 代码、dockershim、Frakti、rktlet 和 cri-containerd 历史版本表只用于理解接口沿革，不是 Kubernetes v1.37.1 的运行时选择或配置指南。


![](../../.gitbook/assets/cri%20%287%29.png)

CRI 最早从从 1.4 版就开始设计讨论和开发，在 v1.5 中发布第一个测试版。在 v1.6 时已经有了很多外部容器运行时，如 frakti 和 cri-o 等。v1.7 中又新增了 cri-containerd 支持用 Containerd 来管理容器。

采用 CRI 后，Kubelet 的架构如下图所示：

![image-20190316183052101](../../.gitbook/assets/image-20190316183052101.png)

> 旧 CRI v1alpha2 代码、dockershim、旧 kubelet flags 与已停止维护的 runtime 示例已封存；当前部署请使用本页上方 CRI v1 配置。见[封存材料](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/extension/cri/README.md)。

## RuntimeClass

RuntimeClass 是内置的集群级 API 对象，用来选择一个已在容器运行时配置的 handler。它不需要 CRD，也不需要启用特性门控。Kubernetes v1.37 使用 `node.k8s.io/v1`，`handler` 是 RuntimeClass 的顶层字段，必须与运行时配置名称一致。

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: kata
handler: kata
```

在 Pod 中通过 `runtimeClassName` 选择该 handler：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: isolated-workload
spec:
  runtimeClassName: kata
  containers:
  - name: app
    image: registry.k8s.io/pause:3.10.2
```

有关替代 runtime handler 的容器运行时配置，请参阅 [containerd CRI 配置文档](https://github.com/containerd/containerd/blob/v2.4.1/docs/cri/config.md)和所选运行时项目的 Kubernetes 支持说明。

## 参考文档

* [Runtime Class Documentation](https://kubernetes.io/docs/concepts/containers/runtime-class/#runtime-class)
* [Sandbox Isolation Level Decision](https://docs.google.com/document/d/1fe7lQUjYKR0cijRmSbH_y0_l3CYPkwtQa5ViywuNo8Q/preview)

