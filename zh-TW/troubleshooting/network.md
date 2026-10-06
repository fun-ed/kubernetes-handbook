# 網路排錯

本章主要介紹各種常見的網路問題以及排錯方法，包括 Pod 存取異常、Service 存取異常以及網路安全策略異常等。

說到 Kubernetes 的網路，其實無非就是以下三種情況之一

* Pod 存取容器外部網路
* 從容器外部存取 Pod 網路
* Pod 之間相互存取

當然，以上每種情況還都分別包括本地存取和跨主機存取兩種場景，並且一般情況下都是透過 Service 間接存取 Pod。

排查網路問題基本上也是從這幾種情況出發，定位出具體的網路異常點，再進而尋找解決方法。網路異常可能的原因比較多，常見的有

* CNI 網路外掛設定錯誤，導致多主機網路不通，比如
  * IP 網段與現有網路衝突
  * 外掛使用了底層網路不支援的協議
  * 忘記開啟 IP 轉發等
    * `sysctl net.ipv4.ip_forward`
    * `sysctl net.bridge.bridge-nf-call-iptables`
* Pod 網路路由丟失，比如
  * kubenet 要求網路中有 podCIDR 到主機 IP 位址的路由，這些路由如果沒有正確設定會導致 Pod 網路通訊等問題
  * 在公有云平台上，kube-controller-manager 會自動為所有 Node 設定路由，但如果設定不當（如認證授權失敗、超出配額等），也有可能導致無法設定路由
* Service NodePort 和 health probe 連接埠衝突
  * 在 1.10.4 版本之前的叢集中，多個不同的 Service 之間的 NodePort 和 health probe 連接埠有可能會有重合 （已經在 [kubernetes\#64468](https://github.com/kubernetes/kubernetes/pull/64468) 修復）
* 主機內或者雲平台的安全組、防火牆或者安全策略等阻止了 Pod 網路，比如
  * 非 Kubernetes 管理的 iptables 規則禁止了 Pod 網路
  * 公有云平台的安全組禁止了 Pod 網路（注意 Pod 網路有可能與 Node 網路不在同一個網段）
  * 交換機或者路由器的 ACL 禁止了 Pod 網路

## CNI 外掛無法啟動

網路外掛的 DaemonSet、映像檔和設定由叢集發行版或網路供應商維護。不要直接應用分支上的未固定版本清單；先檢查相關 Pod Events 和容器日誌：

```bash
kubectl -n kube-system get pods -o wide
CNI_POD='<cni-pod>'
kubectl -n kube-system describe pod "$CNI_POD"
kubectl -n kube-system logs "$CNI_POD" --all-containers=true --tail=100
```

如果日誌提示 SELinux 拒絕存取，應檢視節點審計日誌並按所選網路外掛的當前文件修正策略。不要透過禁用 SELinux 或改成 permissive 來繞過問題。
## Pod 無法分配 IP

先檢視 Pod Events、Node Pod CIDR 與節點資源，確認問題屬於 IP 位址耗盡、CNI 初始化失敗還是執行時 sandbox 建立失敗：

```bash
NODE='<node-name>'
kubectl describe pod '<pod-name>' -n '<namespace>'
kubectl describe node "$NODE"
kubectl get pods --all-namespaces -o wide --field-selector="spec.nodeName=$NODE"
```

在 Node 上可用 `crictl` 對照當前 runtime 的容器與 Pod sandbox；確保 `crictl` 使用該 Node 實際 CRI socket。IPAM 狀態檔案的位置和恢復方式由具體 CNI/IPAM 外掛決定：

```bash
sudo crictl info
sudo crictl pods
sudo crictl ps -a
```

IPAM 位址池顯示耗盡或狀態不一致時，先檢查外掛日誌、位址池容量和已分配 Pod，再按 CNI 供應商文件處理。不要停止 kubelet、直接刪除 IPAM 分配檔案、虛擬網絡卡或網路命名空間；這些操作可能破壞仍在使用的位址並造成更大範圍網路中斷。

## Pod 無法解析 DNS

先檢視 CoreDNS Pod、Service 與 EndpointSlices，再從 Pod 內測試叢集域名：

```bash
kubectl -n kube-system get pods
kubectl -n kube-system get services
# Replace with the DNS Service name shown above
DNS_SERVICE='<dns-service-name>'
kubectl -n kube-system get endpointslices -l "kubernetes.io/service-name=$DNS_SERVICE"
kubectl run dns-check --image=busybox:1.37.0 --restart=Never --rm -it -- \
  nslookup kubernetes.default.svc.cluster.local
```

若叢集 DNS 的 Service 或 EndpointSlices 異常，檢視 DNS Pod 日誌、Corefile、NetworkPolicy 及 Pod 到 DNS Service 的網路路徑。DNS Service 名稱可能因發行版而異；不要直接建立或替換一個硬編碼 ClusterIP 的 kube-dns Service。

CoreDNS 設定語法與外掛支援依賴實際 CoreDNS 版本。遇到 `proxy`、`forward` 等外掛問題時，先核對當前 Corefile 和所用 CoreDNS 版本文件；本頁舊版 proxy 遷移設定不應直接用於生產環境。檢查 Service 網路時請同時確認 kube-proxy 或替代實現是否正常。

## DNS 解析緩慢

DNS 延遲可能來自上游 DNS、CoreDNS 資源限制、節點網路或 conntrack 壓力。先比較叢集 Service 域名和外部域名的查詢結果，檢查 CoreDNS 與 CNI 日誌，再按核心、容器執行時和叢集網路實現的版本文件定位。

舊版 `single-request-reopen` 與特定核心 conntrack 問題的 workaround 並非通用修復；不要透過容器啟動指令碼修改 `/etc/resolv.conf` 或盲目增加 DNS 引數。對於需要本地快取的叢集，可評估受維護且與目標版本相容的 NodeLocal DNSCache 部署文件。

更多 DNS 設定方法見 [Customizing DNS Service](https://kubernetes.io/docs/tasks/administer-cluster/dns-custom-nameservers/)。

## Service 無法存取

先確認 Service selector 匹配到預期 Pod，並使用 EndpointSlices 檢查後端位址與連接埠：

```bash
SERVICE='<service-name>'
kubectl get service "$SERVICE" -o yaml
kubectl get pods -l '<key1=value1,key2=value2>' -o wide
kubectl get endpointslices -l "kubernetes.io/service-name=$SERVICE" -o yaml
```

如果沒有後端，檢查 selector、Pod readiness 與連接埠設定。若 EndpointSlices 正常，再分別從客戶端 Pod 測試 Service DNS、ClusterIP 和後端 Pod IP，並檢查 NetworkPolicy、CNI 路由、防火牆與 kube-proxy（或其替代實現）的日誌。資料平面規則因 iptables、nftables、IPVS 或 eBPF 等實現而異，不要照搬另一種模式的靜態規則。

## Pod 無法透過 Service 存取自己

Pod 存取指向自身的 Service 時，行為取決於 Service 流量策略、CNI 與 kube-proxy 或替代實現。先確認 Service 後端 EndpointSlices 與 Pod readiness，再檢視所用網路外掛的 hairpin/loopback 文件；不要依賴舊版 `cbr0`、`--hairpin-mode` 或固定網橋的命令。

## Pod 無法存取 Kubernetes API

先確認控制平面與 `kubernetes` Service 狀態，再分別檢查網路連通性和 RBAC 授權：

```bash
kubectl get service kubernetes
kubectl get endpointslices -l kubernetes.io/service-name=kubernetes
NAMESPACE='<namespace>'
SERVICE_ACCOUNT='<service-account>'
kubectl auth can-i list pods --as="system:serviceaccount:${NAMESPACE}:${SERVICE_ACCOUNT}" -n "$NAMESPACE"
```

EndpointSlice 檢查控制平面後端發現，`kubectl auth can-i` 檢查授權；兩者都不能代替從故障 Pod 到 API Server 的實際網路測試。不要在互動式 shell 或日誌中列印 ServiceAccount token。如需應用級驗證，應使用可信診斷工具並避免暴露憑證。

## 核心或 Service 資料平面問題

連線超時可能與核心、conntrack、CNI 或 Service 代理設定有關。舊文章中的 iptables/SNAT workaround 針對特定核心和資料平面實現，不應當作通用修復。先確認叢集的 kube-proxy 模式或替代實現，再按其當前文件和節點發行版定位。

## 參考文件

* [Troubleshoot Applications](https://kubernetes.io/docs/tasks/debug-application-cluster/debug-application/)
* [Debug Services](https://kubernetes.io/docs/tasks/debug-application-cluster/debug-service/)
