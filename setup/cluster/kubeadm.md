# 使用 kubeadm 部署 Kubernetes v1.37.1

本页示例部署一套 Linux、单控制平面的 Kubernetes v1.37.1 集群，并使用 containerd 2.4.1 与 Calico 3.33.0。kubeadm 是集群生命周期工具，不会替你安装 CRI runtime 或 Pod 网络。生产集群还需按环境配置高可用 API endpoint、证书、访问控制、备份、存储、监控与防火墙。

> 版本和兼容性资料截至 2026-10-05。组件来源及兼容矩阵见[组件版本清单](../component-versions.md)。云托管集群请优先使用云厂商当前支持的部署方式。

## 1. 检查主机

每个 Linux 节点应满足 kubeadm 的主机、端口、主机名和网络要求：控制平面至少 2 CPU、每台至少 2 GiB RAM，节点之间网络可达，节点具有唯一 hostname/MAC/product UUID。检查官方[所需端口列表](https://kubernetes.io/docs/reference/networking/ports-and-protocols/)。若主机有多个网络接口，先确认默认路由选择的是集群可达的接口。

本示例使用 systemd 主机。默认情况下 kubelet 检测到 swap 会拒绝启动；要么按官方[swap 管理说明](https://kubernetes.io/docs/concepts/cluster-administration/swap-memory-management/)关闭并持久化关闭，要么明确配置受支持的 swap 行为。按[容器运行时网络前置条件](https://kubernetes.io/docs/setup/production-environment/container-runtimes/#install-and-configure-prerequisites)配置 IPv4 forwarding 及所选 CNI 要求的内核设置。

## 2. 安装 containerd

安装 **containerd 2.4.1**、配套的 runc 和 CNI binaries。可从 [containerd 官方安装文档](https://containerd.io/docs/2.4/getting-started/)选择适合发行版的官方/发行版安装方式；检查安装包中是否包含 CRI plugin 与 CNI binaries。containerd v2 的 CRI plugin 必须启用，CRI API 必须实现 v1。

若因已有基础设施必须使用 Docker Engine，仍需在节点安装并维护 `cri-dockerd`；Docker 本身不是 CRI runtime。另有上游报告称 cri-dockerd 0.4.7 在 Kubernetes 1.36+、`ExtendWebSocketsToKubelet` 默认开启时存在 exec/attach 问题（[issue 569](https://github.com/Mirantis/cri-dockerd/issues/569)、[issue 560](https://github.com/Mirantis/cri-dockerd/issues/560)）。不要据此假定 Docker adapter 与 v1.37 无条件兼容或自行关闭 gate；先确认当前 adapter release、上游 workaround 和 provider 支持。新集群优先采用已验证的 containerd/CRI-O 路径。


在 `/etc/containerd/config.toml` 中让 runc 使用 systemd cgroup driver。containerd 2.x 的 TOML 配置如下；若默认配置已包含该 table，只修改现有值，不要重复追加同名 table：

```toml
version = 3
[plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.runc.options]
  SystemdCgroup = true
```

containerd 2.4 默认配置的 sandbox image 应为 `registry.k8s.io/pause:3.10.2`；若发行版配置不同，在 `[plugins.'io.containerd.cri.v1.images'.pinned_images]` 中将 `sandbox` 对齐到该版本。检查 `disabled_plugins` 中没有 `cri`，保存后重启并启用服务：

```bash
sudo systemctl enable --now containerd
sudo systemctl restart containerd
```

> Kubernetes v1.37 可对支持 CRI `RuntimeConfig` RPC 的 runtime 自动检测 cgroup driver，但兼容回退到 kubelet 显式配置要到 v1.38 才会移除。新节点仍建议一致配置 systemd；不要把旧 runtime 的回退行为当作配置方案。

## 3. 安装 kubeadm、kubelet 和 kubectl

每个节点都要安装 Kubernetes 工具。以 Debian/Ubuntu 为例，以下使用 v1.37 专属软件源；**它不是跨 minor 自动升级通道**。完整安装步骤及 RPM 配置见官方[安装 kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)页面。

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.37/deb/Release.key \
  | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.37/deb/ /' \
  | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y 'kubelet=1.37.1-*' 'kubeadm=1.37.1-*' 'kubectl=1.37.1-*'
sudo apt-mark hold kubelet kubeadm kubectl
sudo systemctl enable --now kubelet
```

包版本末尾的发行版修订号由仓库提供；安装前用 `apt-cache policy kubelet kubeadm kubectl` 确认仓库当前确实提供 v1.37.1。若该 patch 不在所用镜像源，勿静默安装别的 minor。需要新 patch 时，先按发行说明审阅后更新软件包，再解除相应 hold。

## 4. 初始化集群

选定 Pod CIDR 前，确认它不与任一主机、VPC/VNet、VPN 或 Service CIDR 重叠。下面的 `192.168.0.0/16` 与 Calico 3.33.0 默认 IPv4 pool 相同；若需改变，必须同时改 kubeadm 和 Calico 的安装配置。

创建 `kubeadm.yaml`：

```yaml
apiVersion: kubeadm.k8s.io/v1beta4
kind: InitConfiguration
nodeRegistration:
  criSocket: unix:///run/containerd/containerd.sock
---
apiVersion: kubeadm.k8s.io/v1beta4
kind: ClusterConfiguration
kubernetesVersion: v1.37.1
networking:
  podSubnet: 192.168.0.0/16
---
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
cgroupDriver: systemd
---
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
mode: iptables
```

本示例显式选择 `iptables`。在满足内核与 CNI 要求的新 Linux 集群中可评估 `nftables`；不要把它当作 v1.37 的默认模式，也不要继续以已弃用的 IPVS 作为新部署基线。`KubeProxyConfiguration` 的配置 API 仍为 `v1alpha1`，不是已移除的工作负载 API。

如果以后要扩成高可用集群，初始化时就应配置稳定的 `controlPlaneEndpoint`（负载均衡器 DNS/IP），并按官方 [HA kubeadm 指南](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)准备额外节点。

在控制平面节点执行：

```bash
sudo kubeadm init --config kubeadm.yaml
```

按命令输出配置管理员 kubeconfig。使用普通用户时：

```bash
mkdir -p "$HOME/.kube"
sudo cp -i /etc/kubernetes/admin.conf "$HOME/.kube/config"
sudo chown "$(id -u):$(id -g)" "$HOME/.kube/config"
```

`admin.conf` 具有集群管理员权限，不要复制到不受信任的机器或提交到版本库。保存 `kubeadm init` 输出的 join 命令和 CA hash，但将 bootstrap token 作为秘密管理。

## 5. 安装 Pod 网络

没有 CNI 时节点会保持 `NotReady`，CoreDNS 也无法启动。kubeadm 不会安装 CNI；不要把旧教程的 CNI URL 直接用在 v1.37 集群。

本示例选择明确列出 Kubernetes 1.35–1.37 兼容范围的 **Calico 3.33.0**。在控制平面执行官方安装步骤：

```bash
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/v3_projectcalico_org.yaml
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/tigera-operator.yaml
kubectl create namespace calico-system --dry-run=client -o yaml | kubectl apply -f -
kubectl label --overwrite namespace calico-system pod-security.kubernetes.io/enforce=privileged
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/custom-resources.yaml
```

Calico 的默认 custom resources 使用 `192.168.0.0/16`，与上方 kubeadm 配置匹配。专用的 `calico-system` namespace 设为 Pod Security `privileged`，因为 CNI node agent 需要相应主机网络权限；不要把整个集群或应用 namespace 放宽为 privileged。监控 `kubectl get tigerastatus` 及 `kubectl get nodes`，等待 Calico 与节点就绪。Calico 安装文件、CRD 与支持信息详见[上游 v3.33.0 文档](https://docs.tigera.io/calico/latest/getting-started/kubernetes/quickstart)及[需求说明](https://docs.tigera.io/calico/latest/getting-started/kubernetes/requirements)。

若更换其他 CNI，重新核对 Kubernetes v1.37 支持、Pod CIDR、节点防火墙/隧道端口、网络策略和 PSA 要求；不要同时部署两套 Pod network。

## 6. 加入 worker 节点并检查

在每台 worker 上完成相同的 runtime 和 Kubernetes 工具安装，然后执行 `kubeadm init` 输出的 `kubeadm join ...` 命令。该 token 有效期有限；如过期，使用 `kubeadm token create --print-join-command` 生成新命令。

检查节点和系统 Pod：

```bash
kubectl get nodes -o wide
kubectl get pods -A
```

DNS Pod 在 CNI 就绪前不会正常工作。kubeadm 默认会创建 CoreDNS；不要再套用旧 kube-dns Deployment。升级 CoreDNS 镜像时，先核对 kubeadm 版本默认值和 CoreDNS 上游兼容资料。

## 参考来源

- [Kubernetes v1.37.1 release](https://kubernetes.io/releases/)
- [Kubernetes v1.37.1 kubeadm image defaults](https://raw.githubusercontent.com/kubernetes/kubernetes/v1.37.1/cmd/kubeadm/app/constants/constants.go)
- [Installing kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)
- [Creating a cluster with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)
- [Container runtimes](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)
- [Calico v3.33.0 requirements](https://docs.tigera.io/calico/latest/getting-started/kubernetes/requirements)
