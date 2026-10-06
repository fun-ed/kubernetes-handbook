# 叢集排錯

本章介紹叢集狀態異常的排錯方法，包括控制平面、Node 與叢集 DNS 等元件；網路問題另見[網路異常排錯方法](network.md)。

## 概述

排查叢集狀態異常問題通常從 Node 和 Kubernetes 服務 的狀態出發，定位出具體的異常服務，再進而尋找解決方法。叢集狀態異常可能的原因比較多，常見的有

* 虛擬機器或物理機宕機
* 網路分割槽
* Kubernetes 服務未正常啟動
* 資料丟失或持久化儲存不可用（一般在公有云或私有云平台中）
* 操作失誤（如設定錯誤）

按照不同的元件來說，具體的原因可能包括

* kube-apiserver 無法啟動會導致
  * 叢集不可存取
  * 已有的 Pod 和服務正常執行（依賴於 Kubernetes API 的除外）
* etcd 叢集異常會導致
  * kube-apiserver 無法正常讀寫叢集狀態，進而導致 Kubernetes API 存取出錯
  * kubelet 無法週期性更新狀態
* kube-controller-manager/kube-scheduler 異常會導致
  * 複製控制器、節點控制器、雲服務控制器等無法工作，從而導致 Deployment、Service 等無法工作，也無法註冊新的 Node 到叢集中來
  * 新建立的 Pod 無法排程（總是 Pending 狀態）
* Node 本身宕機或者 Kubelet 無法啟動會導致
  * Node 上面的 Pod 無法正常執行
  * 已在執行的 Pod 無法正常終止
* 網路分割槽會導致 Kubelet 等與控制平面通訊異常以及 Pod 之間通訊異常

為了維持叢集的健康狀態，推薦在部署叢集時就考慮以下

* 在雲平台上開啟 VM 的自動重啟功能
* 為 Etcd 設定多節點高可用叢集，使用持久化儲存（如 AWS EBS 等），定期備份資料
* 為控制平面設定高可用，例如多 kube-apiserver 與多節點執行 kube-controller-manager、kube-scheduler；叢集 DNS 通常由 CoreDNS 提供
* 儘量使用複製控制器和 Service，而不是直接管理 Pod
* 跨地域的多 Kubernetes 叢集

## 檢視 Node 狀態

一般來說，可以首先檢視 Node 的狀態，確認 Node 本身是不是 Ready 狀態

```bash
kubectl get nodes
kubectl describe node <node-name>
```

如果是 NotReady 狀態，可以執行 `kubectl describe node <node-name>` 指令，檢視目前 Node 的事件。這些事件通常有助於排查 Node 發生的問題。

## 安全存取 Node

需要檢查 Node 作業系統、kubelet 或 CRI 執行環境時，請使用雲端平台控制台或組織核准的 SSH/bastion 通道，並將管理連接埠限制為僅接受可信來源。不要透過公網 `LoadBalancer` 暴露 SSH 服務。

在可信的測試叢集中，如只需執行網路診斷，可參考 [`examples/ssh.yaml`](../examples/ssh.yaml) 部署受限的互動式 `node-debug-shell` Pod。先在清單中將 `nodeName` 替換為已授權的目標 Node：

```bash
kubectl apply -f examples/ssh.yaml
kubectl wait --for=condition=Ready pod/node-debug-shell --timeout=60s
kubectl exec -it node-debug-shell -- /bin/sh
kubectl delete -f examples/ssh.yaml
```

此清單不會執行 sshd，也不建立 SSH Service；`kubectl exec` 只提供容器內 shell，不會自動授予存取 Node 檔案系統、程序命名空間或 systemd 的權限。只有在可信叢集並經過授權時才使用 `hostNetwork` 除錯 Pod；作業系統級診斷仍應透過受控 Node 管理通道完成。

## 檢視日誌

一般來說，Kubernetes 的主要元件有兩種部署方法

* 直接使用 systemd 等啟動控制節點的各個服務
* 使用 Static Pod 來管理和啟動控制節點的各個服務

使用 systemd 等管理控制節點服務時，檢視日誌必須要首先 SSH 登入到機器上，然後檢視具體的日誌檔案。如

```bash
journalctl -l -u kube-apiserver
journalctl -l -u kube-controller-manager
journalctl -l -u kube-scheduler
journalctl -l -u kubelet
journalctl -l -u kube-proxy
```

或者直接檢視日誌檔案

* /var/log/kube-apiserver.log
* /var/log/kube-scheduler.log
* /var/log/kube-controller-manager.log
* /var/log/kubelet.log
* /var/log/kube-proxy.log

而對於使用 Static Pod 部署叢集控制平面服務的場景，可以參考下面這些檢視日誌的方法。

### kube-apiserver 日誌

```bash
PODNAME=$(kubectl -n kube-system get pod -l component=kube-apiserver -o jsonpath='{.items[0].metadata.name}')
kubectl -n kube-system logs $PODNAME --tail 100
```

### kube-controller-manager 日誌

```bash
PODNAME=$(kubectl -n kube-system get pod -l component=kube-controller-manager -o jsonpath='{.items[0].metadata.name}')
kubectl -n kube-system logs $PODNAME --tail 100
```

### kube-scheduler 日誌

```bash
PODNAME=$(kubectl -n kube-system get pod -l component=kube-scheduler -o jsonpath='{.items[0].metadata.name}')
kubectl -n kube-system logs $PODNAME --tail 100
```

### CoreDNS 日誌

CoreDNS Pod 的名稱和標籤會因發行版不同而變化。先檢視 `kube-system` 中的 DNS Pod，再讀取實際 Pod 的日誌：

```bash
kubectl -n kube-system get pods
kubectl -n kube-system logs <coredns-pod> --all-containers=true --tail=100
```

### Kubelet 日誌

檢視 Kubelet 日誌需要首先 SSH 登入到 Node 上。

```bash
journalctl -l -u kubelet
```

### Kube-proxy 日誌

Kube-proxy 通常以 DaemonSet 的方式部署

```bash
$ kubectl -n kube-system get pod -l component=kube-proxy
NAME               READY     STATUS    RESTARTS   AGE
kube-proxy-42zpn   1/1       Running   0          1d
kube-proxy-7gd4p   1/1       Running   0          3d
kube-proxy-87dbs   1/1       Running   0          4d
$ kubectl -n kube-system logs kube-proxy-42zpn
```

## API Server 健康與記憶體排查

`/healthz` 已棄用；檢查 API Server 時使用 `/livez` 和 `/readyz`。`livez` 檢查程序是否存活，`readyz` 檢查是否已準備好接收請求：

```bash
kubectl get --raw='/livez'
kubectl get --raw='/readyz?verbose'
```

執行大量 List 請求時出現延遲或 API Server 記憶體壓力，應先檢查元件日誌、Pod 資源使用情況和請求規模。資源指標查詢要求叢集提供可用的 Metrics API：

```bash
kubectl -n kube-system get pods
kubectl -n kube-system describe pod <apiserver-pod>
kubectl -n kube-system logs <apiserver-pod> --tail=100
kubectl top pod -n kube-system
```

Kubernetes v1.33 為 JSON/Protobuf List 回應新增逐項編碼，可在特定請求情境降低記憶體使用量；實際效益因請求和叢集而異，不應承諾固定倍率。相關 feature gates 在 v1.37 已移除，不要繼續設定。若問題持續，應根據監控和目標發行版文件評估 API Server 資源分配及存取方式，不要直接套用過時的靜態 Pod 引數或 `etcd-servers-overrides` 範例。

## CoreDNS 故障排查

叢集 DNS 常由 CoreDNS 提供。先檢視叢集 DNS Pod 與 Service 的實際名稱，再檢查對應 CoreDNS Pod 的日誌：

```bash
kubectl -n kube-system get pods
kubectl -n kube-system get service
kubectl -n kube-system logs <coredns-pod> --all-containers=true --tail=100
DNS_SERVICE='<dns-service-name-shown-above>'
kubectl -n kube-system get endpointslices -l "kubernetes.io/service-name=$DNS_SERVICE"
```


CoreDNS 無法回應時，檢查 Corefile、上游 DNS 可達性、Pod 網路和節點防火牆，並檢視 CNI 與 kubelet 日誌。不要透過 `iptables -P FORWARD ACCEPT` 放寬主機轉送政策；這會改變整台 Node 的安全邊界。網路問題的進一步檢查見[網路排錯指南](network.md)。

## Node NotReady

先執行 `kubectl describe node <node-name>` 檢視 Node Conditions 和 Events，再根據發行版檢查 kubelet 與實際 CRI 執行時服務的狀態和日誌。常見原因包括：

* kubelet 或 CRI 執行時未執行，或 socket 設定不匹配
* CNI 外掛未就緒、IP 位址耗盡或網路設定異常
* CPU、記憶體、磁碟空間或 inode 壓力
* 控制平面或 Node 之間的網路中斷

Kubernetes 預設使用 CRI 相容容器執行環境（例如 containerd 或 CRI-O）；Docker Engine 若透過外部配接器提供 CRI，應按該配接器文件排查。可結合 Node Problem Detector 報告的 Conditions 與 Events 定位主機問題。
## Node Allocatable 事件

Node Allocatable 用於為系統守護程序和驅逐閾值預留節點資源，具體設定由 kubelet 與叢集發行版管理。舊範例中的 AKS/Docker overlay 路徑和直接執行 kubelet 指令屬於歷史環境，不要照搬。若出現 `FailedNodeAllocatableEnforcement`，先檢視 Node Conditions、kubelet 日誌、作業系統 cgroup 模式與發行版設定，再按對應版本的 [Node Allocatable 文件](https://kubernetes.io/docs/tasks/administer-cluster/reserve-compute-resources/)排查。
## kube-proxy 與 conntrack 錯誤

kube-proxy 的日誌、所需核心功能及網路規則取決於代理模式和發行版。遇到 conntrack 錯誤時，先確認所用 kube-proxy 模式、節點核心/conntrack 支援與 kube-proxy 目前文件；舊版日誌中的 `conntrack` 二進位檔缺失不能證明所有叢集都應安裝同一個套件。若叢集使用替代 Service 實作，應改查該實作的日誌與規則。
## Dashboard 中沒有資源指標

Heapster 已停止維護，不要重新部署 Heapster。排查 Dashboard 缺少指標時，檢查 `v1beta1.metrics.k8s.io` APIService 是否已註冊且後端可用；以本書基準版本為準，Metrics Server v0.9.0 僅提供 v1beta1。Kubernetes 的 `metrics.k8s.io/v1` API 已達穩定版，不代表此版本的 Metrics Server 已提供 v1；`kubectl top` 可查詢 v1 並回退至 v1beta1，因此 `kubectl top` 成功也不能證明 Dashboard 使用的 API 可用。另須確認所用 Dashboard 版本支援的指標 API。不要依賴舊版 Heapster 標籤、安裝指令或資源圖表截圖。
## HPA 未自動擴縮 Pod

檢視 HPA 的事件，發現

```bash
$ kubectl describe hpa php-apache
Name:                                                  php-apache
Namespace:                                             default
Labels:                                                <none>
Annotations:                                           <none>
CreationTimestamp:                                     Wed, 27 Dec 2017 14:36:38 +0800
Reference:                                             Deployment/php-apache
Metrics:                                               ( current / target )
  resource cpu on pods  (as a percentage of request):  <unknown> / 50%
Min replicas:                                          1
Max replicas:                                          10
Conditions:
  Type           Status  Reason                   Message
  ----           ------  ------                   -------
  AbleToScale    True    SucceededGetScale        the HPA controller was able to get the target's current scale
  ScalingActive  False   FailedGetResourceMetric  the HPA was unable to compute the replica count: unable to get metrics for resource cpu: unable to fetch metrics from API: the server could not find the requested resource (get pods.metrics.k8s.io)
Events:
  Type     Reason                   Age                  From                       Message
  ----     ------                   ----                 ----                       -------
  Warning  FailedGetResourceMetric  3m (x2231 over 18h)  horizontal-pod-autoscaler  unable to get metrics for resource cpu: unable to fetch metrics from API: the server could not find the requested resource (get pods.metrics.k8s.io)
```

這表示 Metrics API 未正常提供指標。檢查 Metrics Server 及 `v1beta1.metrics.k8s.io` APIService 狀態；Kubernetes v1.37.1 的 HPA 資源指標用戶端仍使用 v1beta1，不能只確認 `metrics.k8s.io/v1` 可用。`kubectl top` 可先查詢 v1，再回退至 v1beta1；另須核對 API 聚合、節點／Pod 指標採集流程和 Metrics Server 日誌。不要假設舊版 API 或獨立安裝指令仍適用。

## Node 儲存空間不足

Kubelet 會按節點可用空間閾值回收未使用的映像檔與容器。先確認實際佔滿的檔案系統和容器執行時，再按發行版及 CRI 執行時文件檢查：

```bash
df -h
sudo crictl info
sudo crictl images
sudo crictl ps -a
```

`crictl` 必須連線到節點實際使用的 CRI endpoint。不要對 Docker socket 執行 `docker-gc`，也不要在未確認映像檔、容器是否仍被工作負載使用前手動刪除執行時資料。

## `/sys/fs/cgroup` 空間或資源控制異常

cgroup 故障通常與節點作業系統、systemd、核心、容器執行環境及 kubelet 設定相關。先讀取 Node conditions、Events 和受控的節點 kubelet/runtime 日誌，再依目前發行版和核心版本排查。不要部署舊 Gist、定時指令碼或 DaemonSet 來清理 systemd cgroup；手動刪除 cgroup 可能破壞仍在執行的 Pod。

## ConfigMap/Secret watch 的歷史問題

Kubernetes issue [#74412](https://github.com/kubernetes/kubernetes/issues/74412) 記錄的是 v1.12/v1.13 時期的特定負載和實作問題。該歷史案例不是 v1.37 的通用故障說明；不要據此調整 API Server HTTP/2 限制或套用舊 kubelet workaround。目前排查應從 API Server、kubelet 和節點指標及 Events 著手，並核對目標版本文件。

## Kubelet 記憶體和指標排錯

本頁原先的 pprof 輸出來自舊版 hyperkube，並使用了未經身分驗證的 kubelet read-only 連接埠 `10255`；該範例已過時，不要啟用或暴露此連接埠，也不要照舊建議關閉 Reflector metrics。目前診斷應透過發行版支援的監控與安全 kubelet 指標介面收集資料。pprof 或節點日誌可能包含敏感資訊，只能在授權、受控且可稽核的環境中存取。

## kube-controller-manager 更新衝突

物件更新衝突可能是正常的 optimistic concurrency 行為：客戶端應基於最新 `resourceVersion` 重讀物件後重試。原案例使用的 `autoscaling/v2beta2` 是歷史 API；不要把控制平面元件快取不一致當作唯一原因，也不要在沒有災難恢復 runbook 指引時重啟全部控制平面元件。etcd 恢復應遵循叢集發行版的受測恢復流程。

## 其他已知問題

早期 Kubernetes 版本的缺陷報告可能不適用於目前版本；先核對 issue 的受影響版本與修復版本，再按目前叢集支援流程處置。

## 參考文件

* [Troubleshoot Clusters](https://kubernetes.io/docs/tasks/debug-application-cluster/debug-cluster/)
* [Azure Kubernetes Service 節點存取說明](https://learn.microsoft.com/azure/aks/node-access)
