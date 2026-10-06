# Kubernetes 集群

![](../.gitbook/assets/architecture%20%287%29.png)

一个 Kubernetes 集群由控制平面和工作节点组成。控制平面维护集群状态并安排工作负载，工作节点运行已调度的 Pod。etcd 保存集群状态；kubelet 通过 CRI 与容器运行时通信。

详细介绍请参考 [Kubernetes 架构](../concepts/architecture.md)。

## 多集群管理

Kubernetes 核心 API 管理单个集群，不包含 Federation 控制平面。旧版 Kubernetes Federation（KubeFed）已退役。其 API 和旧教程仅作历史参考，见[归档索引](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/index.md)。当前多集群方案由集群发行版或独立的多集群管理工具提供。

## 创建 Kubernetes 集群

可以参考 [Kubernetes 部署指南](../setup/index.md) 来部署一套 Kubernetes 集群。而对于初学者或者简单验证测试的用户，则可以使用以下几种更简单的方法。

### minikube

[minikube](https://minikube.sigs.k8s.io/docs/start/) 可以在本地启动 Kubernetes 集群。具体启动参数取决于所选驱动和操作系统。启动后，使用 `kubectl get nodes` 检查节点，并参考 minikube 文档访问其 Service。

