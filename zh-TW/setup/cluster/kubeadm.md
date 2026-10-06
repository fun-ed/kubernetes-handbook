# 使用 kubeadm 部署 Kubernetes v1.37.1

本頁範例部署一套 Linux、單控制平面的 Kubernetes v1.37.1 叢集，並使用 containerd 2.4.1 與 Calico 3.33.0。kubeadm 是叢集生命週期工具，不會替你安裝 CRI runtime 或 Pod 網路。生產叢集還需按環境設定高可用 API endpoint、證書、存取控制、備份、儲存、監控與防火牆。

> 版本和相容性資料截至 2026-10-05。元件來源及相容矩陣見[元件版本清單](../component-versions.md)。雲託管叢集請優先使用雲廠商當前支援的部署方式。

## 1. 檢查主機

每個 Linux 節點應滿足 kubeadm 的主機、連接埠、主機名和網路要求：控制平面至少 2 CPU、每臺至少 2 GiB RAM，節點之間網路可達，節點具有唯一 hostname/MAC/product UUID。檢查官方[所需連接埠列表](https://kubernetes.io/docs/reference/networking/ports-and-protocols/)。若主機有多個網路介面，先確認預設路由選擇的是叢集可達的介面。

本範例使用 systemd 主機。預設情況下 kubelet 檢測到 swap 會拒絕啟動；要麼按官方[swap 管理說明](https://kubernetes.io/docs/concepts/cluster-administration/swap-memory-management/)關閉並持久化關閉，要麼明確設定受支援的 swap 行為。按[容器執行時網路前置條件](https://kubernetes.io/docs/setup/production-environment/container-runtimes/#install-and-configure-prerequisites)設定 IPv4 forwarding 及所選 CNI 要求的核心設定。

## 2. 安裝 containerd

安裝 **containerd 2.4.1**、配套的 runc 和 CNI binaries。可從 [containerd 官方安裝文件](https://containerd.io/docs/2.4/getting-started/)選擇適合發行版的官方/發行版安裝方式；檢查安裝包中是否包含 CRI plugin 與 CNI binaries。containerd v2 的 CRI plugin 必須啟用，CRI API 必須實現 v1。

若因已有基礎設施必須使用 Docker Engine，仍需在節點安裝並維護 `cri-dockerd`；Docker 本身不是 CRI runtime。另有上游報告稱 cri-dockerd 0.4.7 在 Kubernetes 1.36+、`ExtendWebSocketsToKubelet` 預設開啟時存在 exec/attach 問題（[issue 569](https://github.com/Mirantis/cri-dockerd/issues/569)、[issue 560](https://github.com/Mirantis/cri-dockerd/issues/560)）。不要據此假定 Docker adapter 與 v1.37 無條件相容或自行關閉 gate；先確認當前 adapter release、上游 workaround 和 provider 支援。新叢集優先採用已驗證的 containerd/CRI-O 路徑。


在 `/etc/containerd/config.toml` 中讓 runc 使用 systemd cgroup driver。containerd 2.x 的 TOML 設定如下；若預設設定已包含該 table，只修改現有值，不要重複追加同名 table：

```toml
version = 3
[plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.runc.options]
  SystemdCgroup = true
```

containerd 2.4 預設設定的 sandbox image 應為 `registry.k8s.io/pause:3.10.2`；若發行版設定不同，在 `[plugins.'io.containerd.cri.v1.images'.pinned_images]` 中將 `sandbox` 對齊到該版本。檢查 `disabled_plugins` 中沒有 `cri`，儲存後重啟並啟用服務：

```bash
sudo systemctl enable --now containerd
sudo systemctl restart containerd
```

> Kubernetes v1.37 可對支援 CRI `RuntimeConfig` RPC 的 runtime 自動檢測 cgroup driver，但相容回復到 kubelet 顯式設定要到 v1.38 才會移除。新節點仍建議一致設定 systemd；不要把舊 runtime 的回復行為當作設定方案。

## 3. 安裝 kubeadm、kubelet 和 kubectl

每個節點都要安裝 Kubernetes 工具。以 Debian/Ubuntu 為例，以下使用 v1.37 專屬軟體源；**它不是跨 minor 自動升級通道**。完整安裝步驟及 RPM 設定見官方[安裝 kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)頁面。

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

包版本末尾的發行版修訂號由儲存庫提供；安裝前用 `apt-cache policy kubelet kubeadm kubectl` 確認儲存庫當前確實提供 v1.37.1。若該 patch 不在所用映像檔源，勿靜默安裝別的 minor。需要新 patch 時，先按發行說明審閱後更新套件，再解除相應 hold。

## 4. 初始化叢集

選定 Pod CIDR 前，確認它不與任一主機、VPC/VNet、VPN 或 Service CIDR 重疊。下面的 `192.168.0.0/16` 與 Calico 3.33.0 預設 IPv4 pool 相同；若需改變，必須同時改 kubeadm 和 Calico 的安裝設定。

建立 `kubeadm.yaml`：

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

本範例顯式選擇 `iptables`。在滿足核心與 CNI 要求的新 Linux 叢集中可評估 `nftables`；不要把它當作 v1.37 的預設模式，也不要繼續以已棄用的 IPVS 作為新部署基線。`KubeProxyConfiguration` 的設定 API 仍為 `v1alpha1`，不是已移除的工作負載 API。

如果以後要擴成高可用叢集，初始化時就應設定穩定的 `controlPlaneEndpoint`（負載平衡器 DNS/IP），並按官方 [HA kubeadm 指南](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/)準備額外節點。

在控制平面節點執行：

```bash
sudo kubeadm init --config kubeadm.yaml
```

按命令輸出設定管理員 kubeconfig。使用普通使用者時：

```bash
mkdir -p "$HOME/.kube"
sudo cp -i /etc/kubernetes/admin.conf "$HOME/.kube/config"
sudo chown "$(id -u):$(id -g)" "$HOME/.kube/config"
```

`admin.conf` 具有叢集管理員權限，不要複製到不受信任的機器或提交到版本庫。儲存 `kubeadm init` 輸出的 join 命令和 CA hash，但將 bootstrap token 作為秘密管理。

## 5. 安裝 Pod 網路

沒有 CNI 時節點會保持 `NotReady`，CoreDNS 也無法啟動。kubeadm 不會安裝 CNI；不要把舊教程的 CNI URL 直接用在 v1.37 叢集。

本範例選擇明確列出 Kubernetes 1.35–1.37 相容範圍的 **Calico 3.33.0**。在控制平面執行官方安裝步驟：

```bash
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/v3_projectcalico_org.yaml
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/tigera-operator.yaml
kubectl create namespace calico-system --dry-run=client -o yaml | kubectl apply -f -
kubectl label --overwrite namespace calico-system pod-security.kubernetes.io/enforce=privileged
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/custom-resources.yaml
```

Calico 的預設 custom resources 使用 `192.168.0.0/16`，與上方 kubeadm 設定匹配。專用的 `calico-system` namespace 設為 Pod Security `privileged`，因為 CNI node agent 需要相應主機網路權限；不要把整個叢集或應用 namespace 放寬為 privileged。監控 `kubectl get tigerastatus` 及 `kubectl get nodes`，等待 Calico 與節點就緒。Calico 安裝檔案、CRD 與支援資訊詳見[上游 v3.33.0 文件](https://docs.tigera.io/calico/latest/getting-started/kubernetes/quickstart)及[需求說明](https://docs.tigera.io/calico/latest/getting-started/kubernetes/requirements)。

若更換其他 CNI，重新核對 Kubernetes v1.37 支援、Pod CIDR、節點防火牆/隧道連接埠、網路策略和 PSA 要求；不要同時部署兩套 Pod network。

## 6. 加入 worker 節點並檢查

在每臺 worker 上完成相同的 runtime 和 Kubernetes 工具安裝，然後執行 `kubeadm init` 輸出的 `kubeadm join ...` 命令。該 token 有效期有限；如過期，使用 `kubeadm token create --print-join-command` 生成新命令。

檢查節點和系統 Pod：

```bash
kubectl get nodes -o wide
kubectl get pods -A
```

DNS Pod 在 CNI 就緒前不會正常工作。kubeadm 預設會建立 CoreDNS；不要再套用舊 kube-dns Deployment。升級 CoreDNS 映像檔時，先核對 kubeadm 版本預設值和 CoreDNS 上游相容資料。

## 參考來源

- [Kubernetes v1.37.1 release](https://kubernetes.io/releases/)
- [Kubernetes v1.37.1 kubeadm image defaults](https://raw.githubusercontent.com/kubernetes/kubernetes/v1.37.1/cmd/kubeadm/app/constants/constants.go)
- [Installing kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)
- [Creating a cluster with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)
- [Container runtimes](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)
- [Calico v3.33.0 requirements](https://docs.tigera.io/calico/latest/getting-started/kubernetes/requirements)
