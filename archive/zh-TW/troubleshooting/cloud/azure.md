# Azure

## Azure 負載平衡

使用 Azure Cloud Provider 後，Kubernetes 會為 LoadBalancer 類型的 Service 建立 Azure 負載平衡器，以及相關的公用 IP、BackendPool 和 Network Security Group \(NSG\)。請注意，目前 Azure Cloud Provider 僅支援 `Basic` SKU 的負載平衡器，並將於 v1.11 支援 Standard SKU。與 `Basic` 和 `Standard` SKU 的負載平衡器相比，存在一些[限制](https://docs.microsoft.com/en-us/azure/load-balancer/load-balancer-standard-overview)：

| 負載平衡器 | Basic | Standard |
| :--- | :--- | :--- |
| 後端集區大小 | 最多 100 個 | 最多 1,000 個 |
| 後端集區範圍 | 可用性設定組 | 虛擬網路、區域 |
| 後端集區設計 | 可用性設定組中的 VM、可用性設定組中的虛擬機器擴展集 | 虛擬網路中的任何 VM 執行個體 |
| HA 連接埠 | 不支援 | 可用 |
| 診斷 | 有限，僅限公用 | 可用 |
| VIP 可用性 | 不支援 | 可用 |
| 快速 IP 移動性 | 不支援 | 可用 |
| 可用性區域情境 | 僅限區域性 | 區域性、區域備援、跨區域負載平衡 |
| 輸出 SNAT 演算法 | 隨需 | 預先設定 |
| 輸出 SNAT 前端選取 | 無法設定，有多個候選項目 | 可選擇設定以減少候選項目 |
| Network Security Group | NIC／子網路上可選 | 必要 |

同樣地，對應的 Public IP 也是 Basic SKU，與 Standard SKU 相比也有一些[限制](https://docs.microsoft.com/en-us/azure/load-balancer/load-balancer-standard-overview#sku-service-limits-and-abilities)：

| Public IP | Basic | Standard |
| :--- | :--- | :--- |
| 可用性區域情境 | 僅限區域性 | 區域備援 \(預設\)、區域性 \(選用\) |
| 快速 IP 移動性 | 不支援 | 可用 |
| VIP 可用性 | 不支援 | 可用 |
| 計數器 | 不支援 | 可用 |
| Network Security Group | NIC 上可選 | 必要 |

建立 Service 時，可以透過 `metadata.annotation` 自訂 Azure 負載平衡器的行為。可用的 Annotation 清單請參閱 [Cloud Provider Azure 文件](https://github.com/kubernetes-sigs/cloud-provider-azure/tree/master/docs/services)。

在 Kubernetes 中，負載平衡器的建立邏輯都位於 kube-controller-manager，因此排查負載平衡相關問題時，除了查看 Service 本身的狀態，例如：

```bash
kubectl describe service <service-name>
```

也需要查看 kube-controller-manager 是否發生異常：

```bash
PODNAME=$(kubectl -n kube-system get pod -l component=kube-controller-manager -o jsonpath='{.items[0].metadata.name}')
kubectl -n kube-system logs $PODNAME --tail 100
```

## LoadBalancer Service 一直處於 pending 狀態

查看 Service `kubectl describe service <service-name>` 時沒有錯誤訊息，但 EXTERNAL-IP 一直是 `<pending>`，表示 Azure Cloud Provider 在建立 LB／NSG／PublicIP 時發生錯誤。一般依照前述步驟查看 kube-controller-manager，就能找到具體的失敗原因。可能的因素包括：

* clientId、clientSecret、tenandId 或 subscriptionId 設定錯誤，導致 Azure API 驗證失敗：更新所有節點的 `/etc/kubernetes/azure.json`，即可修正錯誤設定並恢復服務
* 設定的用戶端沒有管理 LB／NSG／PublicIP／VM 的權限：可以為使用的 clientId 增加授權，或建立新的 `az ad sp create-for-rbac --role="Contributor" --scopes="/subscriptions/<subscriptionID>/resourceGroups/<resourceGroupName>"`
* Kuberentes v1.8.X 中也可能出現 `Security rule must specify SourceAddressPrefixes, SourceAddressPrefix, or SourceApplicationSecurityGroups` 錯誤，這是 Azure Go SDK 的問題所致。可以將叢集升級至 v1.9.X／v1.10.X，或將 SourceAddressPrefixes 替換為多條 SourceAddressPrefix 規則來解決

## 負載平衡器公用 IP 無法存取

Azure Cloud Provider 會為負載平衡器建立探測器，只有探測正常的服務才能回應使用者的要求。負載平衡器公用 IP 無法存取，通常是探測失敗所致。可能原因如下：

* 後端 VM 本身異常（可以重新啟動 VM 以恢復）
* 後端容器未在設定的連接埠上接聽（可透過設定正確的連接埠解決）
* 防火牆或網路安全性群組封鎖了要存取的連接埠（可透過新增安全性規則解決）
* 使用內部網路負載平衡器時，從同一個 ILB 的後端 VM 存取 ILB VIP 也會失敗；這是 Azure 的[預期行為](https://docs.microsoft.com/en-us/azure/load-balancer/load-balancer-troubleshoot#cause-4-accessing-the-internal-load-balancer-vip-from-the-participating-load-balancer-backend-pool-vm)（此時可以存取 service 的 clusterIP）
* 後端容器無法回應部分或全部外部要求時，也會導致負載平衡器 IP 無法存取。請注意，這也包含**部分容器無法回應的情境**，這是 Azure 探測器與 Kubernetes 服務探索機制共同造成的結果：
  * （1）Azure 探測器會定期存取 service 的連接埠（即 NodeIP:NodePort）
  * （2）Kubernetes 會將其負載平衡至後端容器
  * （3）負載平衡至異常容器時，存取失敗會導致探測失敗，進而使 Azure 可能將 VM 從負載平衡器中移除
  * 解決方法是使用[健康探查](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-probes/)，確保異常容器會自動從服務的後端（endpoints）中移除。

## 內部網路負載平衡器的 BackendPool 為空

Kubernetes 1.9.0-1.9.3 中會發生這個問題（[kubernetes\#59746](https://github.com/kubernetes/kubernetes/issues/59746) [kubernetes\#60060](https://github.com/kubernetes/kubernetes/issues/60060) [acs-engine\#2151](https://github.com/Azure/acs-engine/issues/2151)），原因是查找負載平衡器所屬 AvaibilitySet 時存在缺陷。

此問題的修正（[kubernetes\#59747](https://github.com/kubernetes/kubernetes/pull/59747) [kubernetes\#59083](https://github.com/kubernetes/kubernetes/pull/59083)）將納入 v1.9.4 和 v1.10。

## 外部網路負載平衡器的 BackendPool 為空

在使用不支援 Cloud Provider 的工具（例如 kubeadm）部署的叢集中，如果未為 Kubelet 設定 `--cloud-provider=azure --cloud-config=/etc/kubernetes/cloud-config`，Kubelet 就會以 hostname 將其註冊至叢集。此時查看該 Node 的資訊（kubectl get node -o yaml），會發現其 externalID 與 hostname 相同。此時，kube-controller-manager 也無法將其加入負載平衡器的後端。

簡單的確認方式是檢查 Node 的 externalID 和 name 是否不同：

```bash
$ kubectl get node -o jsonpath='{.items[*].metadata.name}'
k8s-agentpool1-27347916-0
$ kubectl get node -o jsonpath='{.items[*].spec.externalID}'
/subscriptions/<subscription-id>/resourceGroups/<rg-name>/providers/Microsoft.Compute/virtualMachines/k8s-agentpool1-27347916-0
```

解決方法是先刪除 Node `kubectl delete node <node-name>`，為 Kubelet 設定 `--cloud-provider=azure --cloud-config=/etc/kubernetes/cloud-config`，最後重新啟動 Kubelet。

## 刪除 Service 後 Azure 公用 IP 未自動刪除

Kubernetes 1.9.0-1.9.3 中會發生這個問題（[kubernetes\#59255](https://github.com/kubernetes/kubernetes/issues/59255)）：建立超過 10 個 LoadBalancer Service 後，可能會因為超過 FrontendIPConfiguations Quota（預設為 10）而無法建立負載平衡器。此時雖然負載平衡器無法建立，但公用 IP 已成功建立；由於 Cloud Provider 的缺陷，刪除 Service 後公用 IP 卻不會刪除。

此問題的修正（[kubernetes\#59340](https://github.com/kubernetes/kubernetes/pull/59340)）將納入 v1.9.4 和 v1.10。

此外，若要解決超過 FrontendIPConfiguations Quota 的問題，可以參閱 [Azure 訂用帳戶和服務限制、配額與條件約束](https://docs.microsoft.com/en-us/azure/azure-subscription-service-limits)來增加 Quota。

## MSI 無法使用

設定 `"useManagedIdentityExtension": true` 後，可以使用[受控服務識別 \(MSI\)](https://docs.microsoft.com/en-us/azure/active-directory/msi-overview) 管理 Azure API 的驗證授權。但由於 Cloud Provider 的缺陷（[kubernetes \#60691](https://github.com/kubernetes/kubernetes/issues/60691)），未定義 `useManagedIdentityExtension` yaml 標籤，導致無法剖析此選項。

此問題的修正（[kubernetes\#60775](https://github.com/kubernetes/kubernetes/pull/60775)）將納入 v1.10。

## Azure ARM API 呼叫要求過多

有時 kube-controller-manager 或 kubelet 會因呼叫要求過多而導致 Azure ARM API 失敗，例如：

```bash
"OperationNotAllowed",\r\n    "message": "The server rejected the request because too many requests have been received for this subscription.
```

尤其是在建立 Kubernetes 叢集或大量新增 Nodes 時。從 [v1.9.2 和 v1.10](https://github.com/kubernetes/kubernetes/issues/58770) 開始，Azure cloud provider 為一系列 Azure 資源（例如 VM、VMSS、安全性群組和路由表等）加入快取，大幅緩解了此問題。

一般而言，如果此問題重複發生，可以考慮：

* 使用 Azure 執行個體中繼資料，也就是為所有 Node 的 `/etc/kubernetes/azure.json` 設定 `"useInstanceMetadata": true`，並重新啟動 kubelet
* 增加 kube-controller-manager 的 `--route-reconciliation-period`（預設為 10s）。例如，在 `/etc/kubernetes/manifests/kube-controller-manager.yaml` 中設定 `--route-reconciliation-period=1m` 後，kubelet 會自動重新建立 kube-controller-manager Pod。

## AKS kubectl logs 連線逾時

`kubectl logs` 命令回報 `getsockopt: connection timed out` 錯誤（[AKS\#232](https://github.com/Azure/AKS/issues/232)）：

```bash
$ kubectl --v=8 logs x
I0308 10:32:21.539580   26486 round_trippers.go:417] curl -k -v -XGET  -H "Accept: application/json, */*" -H "User-Agent: kubectl/v1.8.1 (linux/amd64) kubernetes/f38e43b" -H "Authorization: Bearer x" https://x:443/api/v1/namespaces/default/pods/x/log?container=x
I0308 10:34:32.790295   26486 round_trippers.go:436] GET https://X:443/api/v1/namespaces/default/pods/x/log?container=x 500 Internal Server Error in 131250 milliseconds
I0308 10:34:32.790356   26486 round_trippers.go:442] Response Headers:
I0308 10:34:32.790376   26486 round_trippers.go:445]     Content-Type: application/json
I0308 10:34:32.790390   26486 round_trippers.go:445]     Content-Length: 275
I0308 10:34:32.790414   26486 round_trippers.go:445]     Date: Thu, 08 Mar 2018 09:34:32 GMT
I0308 10:34:32.790504   26486 request.go:836] Response Body: {"kind":"Status","apiVersion":"v1","metadata":{},"status":"Failure","message":"Get https://aks-nodepool1-53392281-1:10250/containerLogs/default/x: dial tcp 10.240.0.6:10250: getsockopt: connection timed out","code":500}
I0308 10:34:32.790999   26486 helpers.go:207] server response object: [{
  "metadata": {},
  "status": "Failure",
  "message": "Get https://aks-nodepool1-53392281-1:10250/containerLogs/default/x/x: dial tcp 10.240.0.6:10250: getsockopt: connection timed out",
  "code": 500
}]
F0308 10:34:32.791043   26486 helpers.go:120] Error from server: Get https://aks-nodepool1-53392281-1:10250/containerLogs/default/x/x: dial tcp 10.240.0.6:10250: getsockopt: connection timed out
```

在 AKS 中，kubectl logs、exec 和 attach 等命令需要在 Master 與 Nodes 節點之間建立通道連線。在 `kube-system` namespace 中可以看到 `tunnelfront` 和 `kube-svc-redirect` Pod：

```text
$ kubectl -n kube-system get po -l component=tunnel
NAME                           READY     STATUS    RESTARTS   AGE
tunnelfront-7644cd56b7-l5jmc   1/1       Running   0          2d

$ kubectl -n kube-system get po -l component=kube-svc-redirect
NAME                      READY     STATUS    RESTARTS   AGE
kube-svc-redirect-pq6kf   1/1       Running   0          2d
kube-svc-redirect-x6sq5   1/1       Running   0          2d
kube-svc-redirect-zjl7x   1/1       Running   1          2d
```

如果它們不處於 `Running` 狀態，或 Exec／Logs／PortForward 等命令回報 `net/http: TLS handshake timeout` 錯誤，請刪除 `tunnelfront` Pod，稍等片刻就會自動建立新的 Pod，例如：

```bash
$ kubectl -n kube-system delete po -l component=tunnel
pod "tunnelfront-7644cd56b7-l5jmc" deleted
```

## 使用 Virtual Kubelet 後 LoadBalancer Service 無法取得公用 IP

使用 Virtual Kubelet 後，LoadBalancer Service 可能會一直處於 pending 狀態，無法取得 IP 位址。查看該服務的事件（例如 `kubectl describe svc）`）會發現錯誤 `CreatingLoadBalancerFailed 4m (x15 over 45m) service-controller Error creating load balancer (will retry): failed to ensure load balancer for service default/nginx: ensure(default/nginx): lb(kubernetes) - failed to ensure host in pool: "instance not found"`。這是因為 Virtual Kubelet 建立的虛擬 Node 不存在於 Azure 雲端平台中，因此無法將其加入 Azure Load Balancer 的後端。

解決方法是啟用 ServiceNodeExclusion 功能，也就是設定 `kube-controller-manager --feature-gates=ServiceNodeExclusion=true`。啟用後，所有帶有 `alpha.service-controller.kubernetes.io/exclude-balancer` 標籤的 Node 都不會加入雲端平台負載平衡器的後端。

請注意，此功能僅適用於 Kubernetes 1.9 及以上版本。

## Node 的 GPU 數量總是 0

如果 AKS GPU 工作負載無法排程，且 Node 的 `nvidia.com/gpu` 容量為 0，請先依目前 AKS 的 GPU 管理方式進行診斷，不要部署舊版裝置外掛清單。

1. 確認叢集有支援的 GPU 節點集區，並核對 VM SKU、節點作業系統及所選的 GPU 管理方式。
2. 使用 `kubectl describe node <GPU_NODE>` 檢查該節點的 `Capacity` 和 `Allocatable` 是否包含 `nvidia.com/gpu`。
3. 查看 `kubectl get pods -A -o wide` 及相關 Pod 事件／記錄，確認目前由 AKS 管理的元件或所選裝置外掛是否正常執行；後續檢查與修復步驟請依照 AKS 官方指南。

節點集區、驅動程式及裝置外掛的設定會依 AKS 管理模式而異。請先參閱本手冊的 [Kubernetes GPU 工作負載指南](../../setup/addon-list/gpu.md)，並遵循 [Microsoft Learn 的 AKS GPU 官方說明](https://learn.microsoft.com/en-us/azure/aks/use-nvidia-gpu)。不要只替換舊清單中的映像標籤後繼續使用。

舊版 `extensions/v1beta1` DaemonSet 和完整上下文已保存在[歷史歸檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/troubleshooting/cloud/azure-gpu-device-plugin.md)，僅供追溯，不可套用至目前的叢集。

## Azure ServicePrincipal 過期

預設情況下，Service Principal 的到期時間為 1 年。可以使用下列命令延長到期時間：

```bash
az ad sp credential reset --name <clientId> --password <clientSecret> --years <newYears>
```

## Node 自動重新啟動

為了保護 AKS 叢集，安全性更新會自動套用至所有 Linux 節點。這些更新包括 OS 安全性修補程式或核心更新，其中部分更新需要重新啟動節點才能完成。AKS 不會自動重新啟動這些 Linux 節點，但你可以參閱[此處](https://docs.microsoft.com/zh-cn/azure/aks/node-updates-kured)設定 [kured](https://github.com/weaveworks/kured)，以自動重新啟動節點。

此外，如果你也想收到節點需要重新啟動的通知，可以參閱 [AKS 上必要工作節點重新啟動的儀表板與通知](https://medium.com/@denniszielke/dashboard-and-notifications-on-aks-for-required-worker-nodes-reboots-c883d08e9404)進行設定。

## AKS Periscope

[AKS Periscope](https://github.com/Azure/aks-periscope) 是用於排查 AKS 叢集問題的偵錯工具，開放原始碼專案位於 &lt;github.com/Azure/aks-periscope&gt;。

使用方式：

```bash
az extension add --name aks-preview
az aks kollect -g MyResourceGroup -n MyManagedCluster --storage-account MyStorageAccount --sas-token "MySasToken"
```

## 已知問題及修正版本

1. 手動將 VMSS VM 更新至最新版本時，Azure LoadBalancer 後端遺失問題
   * 問題連結：[https://github.com/kubernetes/kubernetes/issues/80365](https://github.com/kubernetes/kubernetes/issues/80365) 和 [https://github.com/kubernetes/kubernetes/issues/89336](https://github.com/kubernetes/kubernetes/issues/89336)
   * Basic LoadBalancer 修正版本：v1.14.7、v1.15.4、v1.16.0 及更新版本
   * Standard LoadBalancer 修正版本：v1.15.12、v1.16.9、v1.17.5、v1.18.1 及更新版本
2. Service 未設定 DNS 標籤，導致公用 IP 上的 DNS 標籤遺失
   * 問題連結：[https://github.com/kubernetes/kubernetes/issues/87127](https://github.com/kubernetes/kubernetes/issues/87127)
   * 受影響版本：v1.17.0-v1.17.2、v1.16.0-v1.16.6、v1.15.7-v1.15.9、v1.14.10
   * 修正版本：v1.15.10、v1.16.7、v1.17.3、v1.18.0 及更新版本
3. 路由表並行更新衝突問題
   * 問題連結：[https://github.com/kubernetes/kubernetes/issues/88151](https://github.com/kubernetes/kubernetes/issues/88151)
   * 修正版本：v1.15.11、v1.16.8、v1.17.4、v1.18.0 及更新版本
4. VMSS VM 並行更新衝突問題
   * 問題連結：[https://github.com/kubernetes/kubernetes/pull/88094](https://github.com/kubernetes/kubernetes/pull/88094)
   * 修正版本：v1.15.11、v1.16.8、v1.17.4、v1.18.0 及更新版本
   * 僅包含於 v1.18.0 或更新版本的效能最佳化：[https://github.com/kubernetes/kubernetes/pull/88699](https://github.com/kubernetes/kubernetes/pull/88699)
5. VMSS 快取不一致問題
   * 問題連結：[https://github.com/kubernetes/kubernetes/issues/89025](https://github.com/kubernetes/kubernetes/issues/89025)
   * 受影響版本：v1.15.8-v1.15.11、v1.16.5-v1.16.8、v1.17.1-v1.17.4
   * 修正版本：v1.15.12、v1.16.9、v1.17.5、v1.18.0 及更新版本

## 參考文件

更多 AKS 疑難排解資訊，請參閱 [AKS 常見問題](https://docs.microsoft.com/zh-cn/azure/aks/troubleshooting)。

* [AKS 疑難排解](https://docs.microsoft.com/en-us/azure/aks/troubleshooting)
* [Azure 訂用帳戶和服務限制、配額與條件約束](https://docs.microsoft.com/en-us/azure/azure-subscription-service-limits)
* [Virtual Kubelet－服務缺少 Load Balancer IP 位址](https://github.com/virtual-kubelet/virtual-kubelet#missing-load-balancer-ip-addresses-for-services)
* [疑難排解 Azure Load Balancer](https://docs.microsoft.com/en-us/azure/load-balancer/load-balancer-troubleshoot#cause-4-accessing-the-internal-load-balancer-vip-from-the-participating-load-balancer-backend-pool-vm)
* [疑難排解 CustomScriptExtension \(CSE\) 和 acs-engine](https://github.com/Azure/acs-engine/blob/master/docs/kubernetes/troubleshooting.md)
* [設定 Azure 防火牆以分析 AKS 中的輸出流量](https://medium.com/@denniszielke/setting-up-azure-firewall-for-analysing-outgoing-traffic-in-aks-55759d188039)
* [AKS 上必要工作節點重新啟動的儀表板與通知](https://medium.com/@denniszielke/dashboard-and-notifications-on-aks-for-required-worker-nodes-reboots-c883d08e9404)