# 核心组件

![components](../../.gitbook/assets/components%20%2811%29.png)

Kubernetes 集群通常包含以下控制平面和节点组件：

* etcd 保存集群状态。
* API Server 提供资源 API，并执行认证、授权和准入控制。
* Controller Manager 运行控制器，维护资源的期望状态。
* Scheduler 为尚未调度的 Pod 选择节点。
* Kubelet 在节点上管理 Pod 生命周期，并通过 CRI 与容器运行时通信。
* CNI 插件提供 Pod 网络，CSI 驱动提供持久卷。
* kube-proxy 为 Service 配置网络转发；部分网络实现会替代 kube-proxy。

## 组件通信

Kubernetes 多组件之间的通信原理为

* API Server 负责 etcd 存储的所有操作，且只有 API Server 才直接操作 etcd 集群
* API Server 对内（集群中的其他组件）和对外（用户）提供统一的 REST API，其他组件均通过 API Server 进行通信
  * Controller Manager、Scheduler、Kube-proxy 和 Kubelet 等均通过 API Server watch API 监测资源变化情况，并对资源作相应的操作
  * 所有需要更新资源状态的操作均通过 API Server 的 REST API 进行
* API Server 在日志、exec、attach 等操作中会通过 HTTPS 连接 Kubelet。应保护 kubelet API 网络访问，并按集群安全文档配置客户端凭证与服务端证书信任；若未配置 `--kubelet-certificate-authority`，API Server 不会验证 Kubelet serving certificate。不要依赖旧版 SSH 隧道部署的说明。

比如典型的创建 Pod 的流程为

![](../../.gitbook/assets/workflow%20%281%29.png)

1. 用户通过 REST API 创建一个 Pod
2. API Server 将其写入 etcd
3. Scheduluer 检测到未绑定 Node 的 Pod，开始调度并更新 Pod 的 Node 绑定
4. Kubelet 检测到有新的 Pod 调度过来，通过 Container Runtime 运行该 Pod
5. Kubelet 通过 Container Runtime 取到 Pod 状态，并更新到 API Server 中

## 端口号

![ports](../../.gitbook/assets/ports.png)

### Control plane node(s)

| Protocol | Direction | Port Range | Purpose |
| :--- | :--- | :--- | :--- |
| TCP | Inbound | 6443 | Kubernetes API server |
| TCP | Inbound | 2379-2380 | etcd client API，仅允许 API Server 与 etcd 成员访问 |
| TCP | Inbound | 10250 | Kubelet HTTPS API，限制为所需控制平面和节点通信 |
| TCP | Inbound | 10257 | kube-controller-manager secure port |
| TCP | Inbound | 10259 | kube-scheduler secure port |

### Worker node(s)

| Protocol | Direction | Port Range | Purpose |
| :--- | :--- | :--- | :--- |
| TCP | Inbound | 10250 | Kubelet HTTPS API，限制为所需控制平面和节点通信 |
| TCP/UDP | Inbound | 30000-32767 | NodePort Services 的默认端口范围 |

端口清单以 Kubernetes [Ports and Protocols](https://kubernetes.io/docs/reference/networking/ports-and-protocols/) 为准。不要开放旧版的不安全 API、kubelet 只读端口 10255 或 cAdvisor 端口 4194。实际监听地址和端口可由组件配置或集群发行版更改。默认只允许集群拓扑实际需要的流量。

## 版本兼容策略

Kubernetes v1.37 的组件版本必须遵守[官方版本偏差策略](https://kubernetes.io/releases/version-skew-policy/)：

* 高可用集群中的 kube-apiserver 实例最多相差一个次要版本。
* kubelet 和 kube-proxy 不得比其通信的 kube-apiserver 新，最多可比 API Server 旧三个次要版本。kube-proxy 与同一节点上的 kubelet 允许相差三个次要版本。
* kube-controller-manager、kube-scheduler 和 cloud-controller-manager 不得比其通信的 API Server 新，通常与其版本相同；升级期间最多旧一个次要版本。
* kubectl 可以比 API Server 新或旧一个次要版本。高可用 API Server 存在版本差异时，按所有实例计算兼容范围。

从 v1.36 升级到 v1.37 时，先升级 API Server，再升级 controller manager、scheduler 和 cloud controller manager。确认 API Server 到达目标版本后，再逐节点升级 kubelet 和 kube-proxy。节点小版本升级前按发行版的操作流程安全迁移工作负载。

## 参考文档

* [Control plane 与 Node 通信](https://kubernetes.io/docs/concepts/architecture/control-plane-node-communication/)
* [Kubernetes 架构](https://kubernetes.io/docs/concepts/architecture/)
* [Kubernetes 网络端口](https://kubernetes.io/docs/reference/networking/ports-and-protocols/)
* [Kubelet TLS 启动引导与证书轮换](https://kubernetes.io/docs/tasks/tls/certificate-rotation/)
