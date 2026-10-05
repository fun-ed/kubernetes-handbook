# 本地单机学习集群

本页用于开发和学习，不是生产集群部署指南。截至 2026-10-05，Minikube v1.39.0 明确支持 Kubernetes v1.36/v1.37，默认使用 Kubernetes v1.37.0。上游未确认 v1.37.1 的 Minikube image；如果测试必须使用 v1.37.1，先确认所用 image 在当前 Minikube 版本中可用，再指定该 patch。

从 [Minikube v1.39.0 release](https://github.com/kubernetes/minikube/releases/tag/v1.39.0) 和 [Minikube 官方快速入门](https://minikube.sigs.k8s.io/docs/start/)安装当前 CLI 与适合操作系统的 driver。启动同 minor 的本地集群：

```bash
minikube start --kubernetes-version=v1.37.0
kubectl get nodes
```

此集群运行 Kubernetes v1.37.0，不是本手册自建集群的 v1.37.1 patch。Minikube driver（Docker、Podman、虚拟机等）按平台选择；遇到镜像网络问题时配置本机/driver 支持的代理，不要把代理凭据硬编码进集群配置。通过 `minikube profile list` 查看环境，通过 `minikube delete` 删除本地练习集群。

## kind

截至截稿日，kind v0.33.0 有 Kubernetes v1.37.0 node image。kind 版本与 node image 都应固定；该 image 不是 Kubernetes v1.37.1。按 [kind Quick Start](https://kind.sigs.k8s.io/docs/user/quick-start/) 安装 kind v0.33.0 及 Docker/Podman，再使用官方 node image：

```bash
kind create cluster --name dev --image kindest/node:v1.37.0
kubectl cluster-info --context kind-dev
kubectl get nodes
```

kind 默认会安装网络组件；除非你有明确测试目的，不要使用 `disableDefaultCNI`。如需要逐字节可复现的 node image，按该 tag 的 [kind node images](https://github.com/kubernetes-sigs/kind/releases/tag/v0.33.0) release 记录固定 digest。

## 与 kubeadm 部署的区别

本地集群由 Minikube/kind 管理其生命周期，不能作为学习自建生产 control plane 的替代品。需要安装真正的 Linux 节点集群时，转到[使用 kubeadm 部署 Kubernetes v1.37.1](cluster/kubeadm.md)。