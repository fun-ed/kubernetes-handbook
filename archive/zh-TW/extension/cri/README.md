# 歷史 CRI legacy sections（封存）

> 不適用於 Kubernetes v1.37.1 的歷史範例；勿當作目前安裝或診斷指令。

## 歷史 CRI 介面和舊實現
> 本節保留早期 CRI API 和執行時資訊。`v1alpha2`、CRI-O incubator 專案位址及 dockershim 整合不適用於 Kubernetes v1.37.1。當前執行時僅需要關注 CRI v1 及上方版本化設定。


CRI 基於 gRPC 定義了 RuntimeService 和 ImageService 等兩個 gRPC 服務，分別用於容器執行時和映像檔的管理。其定義在

* 當前 CRI 文件：[Kubernetes Container Runtime Interface](https://kubernetes.io/docs/concepts/containers/cri/)
* v1.10-v1.13: [pkg/kubelet/apis/cri/runtime/v1alpha2](https://github.com/kubernetes/kubernetes/tree/release-1.13/pkg/kubelet/apis/cri/runtime/v1alpha2)
* v1.7-v1.9: [pkg/kubelet/apis/cri/v1alpha1/runtime](https://github.com/kubernetes/kubernetes/tree/release-1.9/pkg/kubelet/apis/cri/v1alpha1/runtime)
* v1.6: [pkg/kubelet/api/v1alpha1/runtime](https://github.com/kubernetes/kubernetes/tree/release-1.6/pkg/kubelet/api/v1alpha1/runtime)

Kubelet 作為 CRI 的客戶端，而容器執行時則需要實現 CRI 的服務端（即 gRPC server，通常稱為 CRI shim）。容器執行時在啟動 gRPC server 時需要監聽在本地的 Unix Socket （Windows 使用 tcp 格式）。

### 開發 CRI 容器執行時

開發新的容器執行時只需要實現 CRI 的 gRPC Server，包括 RuntimeService 和 ImageService。該 gRPC Server 需要監聽在本地的 unix socket（Linux 支援 unix socket 格式，Windows 支援 tcp 格式）。

一個簡單的範例為

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

對於 Streaming API（Exec、PortForward 和 Attach），CRI 要求容器執行時返回一個 streaming server 的 URL 以便 Kubelet 重定向 API Server 傳送過來的請求。在 v1.10 及更早版本中，容器執行時必需返回一個 API Server 可直接存取的 URL（通常跟 Kubelet 使用相同的監聽位址）；而從 v1.11 開始，Kubelet 新增了 `--redirect-container-streaming`（預設為 false），預設不再轉發而是代理 Streaming 請求，這樣執行時可以返回一個 localhost 的 URL（當然也不再需要設定 TLS）。

![image-20190316183005314](../../../.gitbook/assets/image-20190316183005314%20%281%29.png)

詳細的實現方法可參考 [Kubernetes v1.23.17 dockershim 歸檔程式碼](https://github.com/kubernetes/kubernetes/tree/v1.23.17/pkg/kubelet/dockershim)和 [CRI-O 專案](https://github.com/cri-o/cri-o)。dockershim 已從 Kubernetes v1.24 移除。

### 舊版 kubelet runtime flags（歷史範例）

早期 Kubernetes 版本使用過 `--container-runtime=remote`、`--container-runtime-endpoint` 和 `--image-service-endpoint` 這些啟動引數。不要把歷史 flags 當作 v1.37.1 的完整節點設定；當前執行時 socket 與 kubeadm 的設定方式見本頁上方。

## 歷史容器執行時列表

> 以下實現及版本說明來自早期 Kubernetes 版本，不是 Kubernetes v1.37.1 的執行時建議。


| **CRI** **容器執行時** | **維護者** | **主要特性** | **容器引擎** |
| :--- | :--- | :--- | :--- |
| **Dockershim** | Kubernetes | 內建實現、特性最新 | docker |
| **cri-o** | Kubernetes | OCI標準不需要Docker | OCI（runc、kata、gVisor…） |
| **cri-containerd** | Containerd | 基於 containerd 不需要Docker | OCI（runc、kata、gVisor…） |
| **Frakti** | Kubernetes | 虛擬化容器 | hyperd、docker |
| **rktlet** | Kubernetes | 支援rkt | rkt |
| **PouchContainer** | Alibaba | 富容器 | OCI（runc、kata…） |
| **Virtlet** | Mirantis | 虛擬機器和QCOW2映像檔 | Libvirt（KVM） |

目前基於 CRI 容器引擎已經比較豐富了，包括

* Docker Engine：dockershim 已於 Kubernetes v1.24 移除；需要獨立的 CRI 介面卡，詳見上方當前執行時說明。
* OCI 容器執行時：
  * 社群有兩個實現
    * [containerd](https://github.com/containerd/containerd)：歷史列表中曾透過 cri-containerd 對接 CRI
    * [CRI-O](https://github.com/cri-o/cri-o)：OCI 容器執行時
  * 支援的 OCI 容器引擎包括
    * [runc](https://github.com/opencontainers/runc)：OCI 標準容器引擎
    * [gVisor](https://github.com/google/gvisor)：谷歌開源的基於使用者空間核心的沙箱容器引擎
    * [Clear Containers](https://github.com/clearcontainers/runtime)：Intel 開源的基於虛擬化的容器引擎
    * [Kata Containers](https://github.com/kata-containers/runtime)：基於虛擬化的容器引擎，由 Clear Containers 和 runV 合併而來
* [PouchContainer](https://github.com/alibaba/pouch)：阿里巴巴開源的胖容器引擎
* [Frakti](https://github.com/kubernetes/frakti)：支援 Kubernetes v1.6+，提供基於 hypervisor 和 docker 的混合執行時，適用於執行非可信應用，如多租戶和 NFV 等場景
* Rktlet：歷史 Kubernetes/rkt 整合，已不適用於當前叢集
* [Virtlet](https://github.com/Mirantis/virtlet)：Mirantis 開源的虛擬機器容器引擎，直接管理 libvirt 虛擬機器，映像檔須是 qcow2 格式
* [Infranetes](https://github.com/apporbit/infranetes)：直接管理 IaaS 平臺虛擬機器，如 GCE、AWS 等

### Containerd

以 Containerd 為例，在 1.0 及以前版本將 dockershim 和 docker daemon 替換為 cri-containerd + containerd，而在 1.1 版本直接將 cri-containerd 內建在 Containerd 中，簡化為一個 CRI 外掛。

![](../../../.gitbook/assets/cri-containerd%20%282%29.png)

Containerd 內建的 CRI 外掛實現了 Kubelet CRI 介面中的 Image Service 和 Runtime Service，透過內部介面管理容器和映像檔，並透過 CNI 外掛給 Pod 設定網路。

![](../../../.gitbook/assets/containerd%20%281%29.png)
