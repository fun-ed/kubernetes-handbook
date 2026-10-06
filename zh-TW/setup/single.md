# 本地單機學習叢集

本頁用於開發和學習，不是生產叢集部署指南。截至 2026-10-05，Minikube v1.39.0 明確支援 Kubernetes v1.36/v1.37，預設使用 Kubernetes v1.37.0。上游未確認 v1.37.1 的 Minikube image；如果測試必須使用 v1.37.1，先確認所用 image 在當前 Minikube 版本中可用，再指定該 patch。

從 [Minikube v1.39.0 release](https://github.com/kubernetes/minikube/releases/tag/v1.39.0) 和 [Minikube 官方快速入門](https://minikube.sigs.k8s.io/docs/start/)安裝當前 CLI 與適合作業系統的 driver。啟動同 minor 的本地叢集：

```bash
minikube start --kubernetes-version=v1.37.0
kubectl get nodes
```

此叢集執行 Kubernetes v1.37.0，不是本手冊自建叢集的 v1.37.1 patch。Minikube driver（Docker、Podman、虛擬機器等）按平台選擇；遇到映像檔網路問題時設定本機/driver 支援的代理，不要把代理憑證硬編碼進叢集設定。透過 `minikube profile list` 檢視環境，透過 `minikube delete` 刪除本地練習叢集。

## kind

截至截稿日，kind v0.33.0 有 Kubernetes v1.37.0 node image。kind 版本與 node image 都應固定；該 image 不是 Kubernetes v1.37.1。按 [kind Quick Start](https://kind.sigs.k8s.io/docs/user/quick-start/) 安裝 kind v0.33.0 及 Docker/Podman，再使用官方 node image：

```bash
kind create cluster --name dev --image kindest/node:v1.37.0
kubectl cluster-info --context kind-dev
kubectl get nodes
```

kind 預設會安裝網路元件；除非你有明確測試目的，不要使用 `disableDefaultCNI`。如需要逐位元組可復現的 node image，按該 tag 的 [kind node images](https://github.com/kubernetes-sigs/kind/releases/tag/v0.33.0) release 記錄固定 digest。

## 與 kubeadm 部署的區別

本地叢集由 Minikube/kind 管理其生命週期，不能作為學習自建生產 control plane 的替代品。需要安裝真正的 Linux 節點叢集時，轉到[使用 kubeadm 部署 Kubernetes v1.37.1](cluster/kubeadm.md)。