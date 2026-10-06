# kube-proxy 的 nftables 模式

Kubernetes kube-proxy 原生 nftables 模式從 v1.33 起穩定，要求 Linux kernel 5.13 或更高版本。Kubernetes v1.37 的 Linux kube-proxy 預設仍使用 `iptables`；IPVS 模式從 v1.35 起棄用。原生 nftables 模式不同於 `iptables-nft` 相容後端，後者由 iptables 命令在底層操作 nftables。它也不同於 Cilium eBPF Service 實現。應選擇一種 Service 資料平面，除非 CNI 官方整合明確要求，否則不要同時執行相互競爭的 kube-proxy 與 eBPF Service 實現。

原生模式透過 nftables 建立 Service、端點和 NodePort 規則，而非呼叫 iptables 介面。它不會配置主機防火牆、IPv6 路由或 CNI 網路策略。核心版本、nft 使用者空間工具、kube-proxy 配置、防火牆策略和網路介面布局都會影響結果。

## 配置片段

以下是 kube-proxy 配置檔案片段，不是 Kubernetes API 物件。它使用 `kubeproxy.config.k8s.io/v1alpha1` 配置結構，應合併到叢集安裝工具管理的配置中，不能用 `kubectl apply`。

```yaml
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
mode: nftables
clusterCIDR: fd00:10:244::/56
# 雙棧叢集應填寫實際 Pod CIDR，使用逗號分隔。
```

`clusterCIDR` 必須符合實際 Pod 網路，供 kube-proxy 判斷哪些流量需要 masquerade。雙棧叢集填寫兩個真實 CIDR，例如 `10.244.0.0/16,fd00:10:244::/56`。文件示例網段不能用於實際網路。保留髮行版生成的其他欄位；這個片段不是完整配置。

## 在隔離實驗室遷移

先確認 Linux 核心、kube-proxy 版本及叢集管理方式。在一次性測試叢集備份當前配置及其所屬 ConfigMap 或安裝器引數。檢查當前模式、節點地址、Service CIDR、Pod CIDR、NodePort 範圍、防火牆規則及現有 kube-proxy 規則。修改配置源後，按該叢集管理工具文件進行 rollout。kubeadm 管理的叢集通常將 kube-proxy 配置存放在 `kube-proxy` ConfigMap，但仍須確認當前版本與生命週期工具如何管理它。不要清空主機規則集或盲目替換 ConfigMap。

切換前後都從測試工作負載檢查 Service 與 DNS。以下命令只讀取狀態：

```bash
kubectl -n kube-system get daemonset kube-proxy
kubectl -n kube-system get pods -l k8s-app=kube-proxy -o wide
kubectl get services,endpointslices -A
nft list ruleset
iptables --version
```

`nft list ruleset` 會顯示當前主機規則，應由具備節點許可權的管理者檢查。`iptables --version` 可幫助識別 iptables 前端，但無法證明 kube-proxy 使用哪種模式。請同時檢查生效配置與日誌。成功表示 proxy Pod 使用預期配置，且所需網路中的測試 ClusterIP、DNS、NodePort 路徑正常；這不能證明所有防火牆或外部地址路徑都已驗證。

## 地址與故障檢查

根據 v1.37 kube-proxy 配置參考檢查實際配置中的 `nodePortAddresses`、`iptablesLocalhostNodePorts` 與 `detectLocalMode` 等欄位。nftables 模式不支援與 iptables 模式相同的 localhost NodePort 行為。遷移時 NodePort 過濾與來源地址行為可能改變。檢查主機防火牆是否允許目標 NodePort 流量。IPv6 還需確認節點地址、路由及防火牆規則；啟用 nftables 不會建立 IPv6 連通性。

Service 不通時，比對各節點規則與 kube-proxy 日誌，確認 EndpointSlice 有就緒端點，檢查是否有其他 Service proxy 同時處理流量，並分別測試 DNS 與 ClusterIP。僅檢視規則列表不能證明流量正常。

## 正式環境與回退

先在隔離叢集遷移，儲存生效配置、節點規則集與流量測試結果。回退會更改 proxy 配置並重啟節點規則管理，應按叢集安裝器流程驗證，並保留舊配置。不要執行 `nft flush ruleset` 或大範圍 iptables flush 命令回退，它們可能刪除其他主機防火牆與容器規則。

主要來源：[Kubernetes v1.37 nftables proxy mode](https://kubernetes.io/docs/reference/networking/virtual-ips/#nftables-proxy-mode)、[kube-proxy 配置 API](https://kubernetes.io/docs/reference/config-api/kube-proxy-config.v1alpha1/)、[v1.37 kube-proxy 配置原始碼](https://github.com/kubernetes/kubernetes/blob/v1.37.1/pkg/proxy/apis/config/types.go)、[Kubernetes v1.37 變更記錄](https://github.com/kubernetes/kubernetes/blob/v1.37.1/CHANGELOG/CHANGELOG-1.37.md)。
