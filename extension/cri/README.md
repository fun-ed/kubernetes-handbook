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

## 历史 CRI 接口和旧实现
> 本节保留早期 CRI API 和运行时信息。`v1alpha2`、CRI-O incubator 项目地址及 dockershim 集成不适用于 Kubernetes v1.37.1。当前运行时仅需要关注 CRI v1 及上方版本化配置。


CRI 基于 gRPC 定义了 RuntimeService 和 ImageService 等两个 gRPC 服务，分别用于容器运行时和镜像的管理。其定义在

* 当前 CRI 文档：[Kubernetes Container Runtime Interface](https://kubernetes.io/docs/concepts/containers/cri/)
* v1.10-v1.13: [pkg/kubelet/apis/cri/runtime/v1alpha2](https://github.com/kubernetes/kubernetes/tree/release-1.13/pkg/kubelet/apis/cri/runtime/v1alpha2)
* v1.7-v1.9: [pkg/kubelet/apis/cri/v1alpha1/runtime](https://github.com/kubernetes/kubernetes/tree/release-1.9/pkg/kubelet/apis/cri/v1alpha1/runtime)
* v1.6: [pkg/kubelet/api/v1alpha1/runtime](https://github.com/kubernetes/kubernetes/tree/release-1.6/pkg/kubelet/api/v1alpha1/runtime)

Kubelet 作为 CRI 的客户端，而容器运行时则需要实现 CRI 的服务端（即 gRPC server，通常称为 CRI shim）。容器运行时在启动 gRPC server 时需要监听在本地的 Unix Socket （Windows 使用 tcp 格式）。

### 开发 CRI 容器运行时

开发新的容器运行时只需要实现 CRI 的 gRPC Server，包括 RuntimeService 和 ImageService。该 gRPC Server 需要监听在本地的 unix socket（Linux 支持 unix socket 格式，Windows 支持 tcp 格式）。

一个简单的示例为

```go
import (
    // Import essential packages
    "google.golang.org/grpc"
    runtime "k8s.io/kubernetes/pkg/kubelet/apis/cri/runtime/v1alpha2"
)

// Serivice implements runtime.ImageService and runtime.RuntimeService.
type Service struct {
    ...
}

func main() {
    service := &Service{}
    s := grpc.NewServer(grpc.MaxRecvMsgSize(maxMsgSize),
        grpc.MaxSendMsgSize(maxMsgSize))
    runtime.RegisterRuntimeServiceServer(s, service)
    runtime.RegisterImageServiceServer(s, service)
    lis, err := net.Listen("unix", "/var/run/runtime.sock")
    if err != nil {
        logrus.Fatalf("Failed to create listener: %v", err)
    }
    go s.Serve(lis)

    // Other codes
}
```

对于 Streaming API（Exec、PortForward 和 Attach），CRI 要求容器运行时返回一个 streaming server 的 URL 以便 Kubelet 重定向 API Server 发送过来的请求。在 v1.10 及更早版本中，容器运行时必需返回一个 API Server 可直接访问的 URL（通常跟 Kubelet 使用相同的监听地址）；而从 v1.11 开始，Kubelet 新增了 `--redirect-container-streaming`（默认为 false），默认不再转发而是代理 Streaming 请求，这样运行时可以返回一个 localhost 的 URL（当然也不再需要配置 TLS）。

![image-20190316183005314](../../.gitbook/assets/image-20190316183005314%20%281%29.png)

详细的实现方法可参考 [Kubernetes v1.23.17 dockershim 归档代码](https://github.com/kubernetes/kubernetes/tree/v1.23.17/pkg/kubelet/dockershim)和 [CRI-O 项目](https://github.com/cri-o/cri-o)。dockershim 已从 Kubernetes v1.24 移除。

### 旧版 kubelet runtime flags（历史示例）

早期 Kubernetes 版本使用过 `--container-runtime=remote`、`--container-runtime-endpoint` 和 `--image-service-endpoint` 这些启动参数。不要把历史 flags 当作 v1.37.1 的完整节点配置；当前运行时 socket 与 kubeadm 的配置方式见本页上方。

## 历史容器运行时列表

> 以下实现及版本说明来自早期 Kubernetes 版本，不是 Kubernetes v1.37.1 的运行时建议。


| **CRI** **容器运行时** | **维护者** | **主要特性** | **容器引擎** |
| :--- | :--- | :--- | :--- |
| **Dockershim** | Kubernetes | 内置实现、特性最新 | docker |
| **cri-o** | Kubernetes | OCI标准不需要Docker | OCI（runc、kata、gVisor…） |
| **cri-containerd** | Containerd | 基于 containerd 不需要Docker | OCI（runc、kata、gVisor…） |
| **Frakti** | Kubernetes | 虚拟化容器 | hyperd、docker |
| **rktlet** | Kubernetes | 支持rkt | rkt |
| **PouchContainer** | Alibaba | 富容器 | OCI（runc、kata…） |
| **Virtlet** | Mirantis | 虚拟机和QCOW2镜像 | Libvirt（KVM） |

目前基于 CRI 容器引擎已经比较丰富了，包括

* Docker Engine：dockershim 已于 Kubernetes v1.24 移除；需要独立的 CRI 适配器，详见上方当前运行时说明。
* OCI 容器运行时：
  * 社区有两个实现
    * [containerd](https://github.com/containerd/containerd)：历史列表中曾通过 cri-containerd 对接 CRI
    * [CRI-O](https://github.com/cri-o/cri-o)：OCI 容器运行时
  * 支持的 OCI 容器引擎包括
    * [runc](https://github.com/opencontainers/runc)：OCI 标准容器引擎
    * [gVisor](https://github.com/google/gvisor)：谷歌开源的基于用户空间内核的沙箱容器引擎
    * [Clear Containers](https://github.com/clearcontainers/runtime)：Intel 开源的基于虚拟化的容器引擎
    * [Kata Containers](https://github.com/kata-containers/runtime)：基于虚拟化的容器引擎，由 Clear Containers 和 runV 合并而来
* [PouchContainer](https://github.com/alibaba/pouch)：阿里巴巴开源的胖容器引擎
* [Frakti](https://github.com/kubernetes/frakti)：支持 Kubernetes v1.6+，提供基于 hypervisor 和 docker 的混合运行时，适用于运行非可信应用，如多租户和 NFV 等场景
* Rktlet：历史 Kubernetes/rkt 集成，已不适用于当前集群
* [Virtlet](https://github.com/Mirantis/virtlet)：Mirantis 开源的虚拟机容器引擎，直接管理 libvirt 虚拟机，镜像须是 qcow2 格式
* [Infranetes](https://github.com/apporbit/infranetes)：直接管理 IaaS 平台虚拟机，如 GCE、AWS 等

### Containerd

以 Containerd 为例，在 1.0 及以前版本将 dockershim 和 docker daemon 替换为 cri-containerd + containerd，而在 1.1 版本直接将 cri-containerd 内置在 Containerd 中，简化为一个 CRI 插件。

![](../../.gitbook/assets/cri-containerd%20%282%29.png)

Containerd 内置的 CRI 插件实现了 Kubelet CRI 接口中的 Image Service 和 Runtime Service，通过内部接口管理容器和镜像，并通过 CNI 插件给 Pod 配置网络。

![](../../.gitbook/assets/containerd%20%281%29.png)

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

