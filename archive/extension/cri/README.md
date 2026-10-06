# 历史 CRI legacy sections（封存）

> 不适用于 Kubernetes v1.37.1 的历史示例；勿当作当前安装或诊断命令。

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

![image-20190316183005314](../../../.gitbook/assets/image-20190316183005314%20%281%29.png)

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

![](../../../.gitbook/assets/cri-containerd%20%282%29.png)

Containerd 内置的 CRI 插件实现了 Kubelet CRI 接口中的 Image Service 和 Runtime Service，通过内部接口管理容器和镜像，并通过 CNI 插件给 Pod 配置网络。

![](../../../.gitbook/assets/containerd%20%281%29.png)
