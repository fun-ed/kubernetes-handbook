# Windows 排錯

本章介紹 Windows 容器異常的排錯方法。

## 安全存取 Windows Node

Node 管理優先使用雲平台控制檯、受控 Bastion 或組織批准的遠端管理通道。不要把 RDP 3389 連接埠直接暴露到公網。

除非平台文件明確提供負載平衡器的私有設定與來源限制，否則不要使用 `type: LoadBalancer` 轉發 RDP；通用 Service 範例可能建立公網端點。需要遠端管理時，使用雲服務商控制檯、受控 Bastion 或組織批准的管理通道。若經授權確需透過網路轉發，僅採用相應雲服務商支援的私有負載平衡器設定和網路存取控制，並先確認不會產生公網入口。

## Windows 容器映像檔與主機版本

Windows 容器映像檔必須與 Node 的 Windows 版本和隔離模式相容。部署前查閱 Microsoft 當前的[容器版本相容性文件](https://learn.microsoft.com/en-us/virtualization/windowscontainers/deploy-containers/version-compatibility)，並在 `kubectl describe pod` 的 Events 與 kubelet 日誌中確認實際錯誤。

本頁舊版 Windows Server 1709/1803 映像檔標籤是歷史記錄，不是當前可用映像檔建議；不要將這些舊標籤用於新叢集。

## Windows Pod DNS 或網路異常

先檢查 Pod Events、CoreDNS 狀態、EndpointSlices、Windows Node 狀態以及所用 CNI/kube-proxy 實現的日誌：

```bash
kubectl describe pod <pod-name>
kubectl -n kube-system get pods
kubectl -n kube-system get service
kubectl -n kube-system get endpointslices -l kubernetes.io/service-name=kube-dns
kubectl get nodes -o wide
```

Windows 網路依賴主機版本、HNS、網路外掛及 Kubernetes 發行版。針對特定版本查閱平台供應商當前的 Windows 網路排錯文件；不要直接執行會刪除 HNS 網路或策略、重啟所有 Node 服務、或將 DNS 伺服器改成固定叢集 IP 的舊指令碼。

## HNS 或 kube-proxy 舊版錯誤

本節原有的 `KB4089848` 和 Windows 10 1803 安裝步驟是 2018 年的歷史故障記錄，不適用於當前 Windows Server Node。遇到 HNS 或 kube-proxy 錯誤時，記錄 Windows build、Kubernetes/kube-proxy 版本和網路外掛版本，並按這些版本對應的 Microsoft 與發行版文件排查；不要下載或安裝本頁中的舊更新包。

## Windows Pod 無法存取 ServiceAccount Secret

本節所關聯的 Moby issue 是舊版 Windows 容器的歷史問題。遇到當前故障時，先檢查目標 Pod 的投射 token volume、服務帳戶設定、Windows build 與執行時版本，並參考當前 Kubernetes 與執行時文件，不要僅憑舊版 issue 升級主機。

## Windows Node 的 Service 可達性

從 Windows Pod 與 Node 主機分別測試 Service 的可達性，並檢查後端 EndpointSlices、kube-proxy 或替代實現以及 CNI/HNS 日誌。Node 主機、Pod 和遠端客戶端的流量路徑可能不同；不要將舊版協議棧限制外推到所有當前網路實現。

## Docker 18.03 / kubelet v1.12 API 版本錯誤（歷史記錄）

本節記錄的是 Kubernetes v1.12 與 Docker 18.03 的舊版客戶端 API 不相容問題。Docker Engine 已不是 Kubernetes 的內建 CRI 執行時；不要將 `DOCKER_API_VERSION` 環境變數 workaround 用於當前 containerd、CRI-O 或其他 CRI 執行時。

## 參考文件

* [Kubernetes On Windows - Troubleshooting Kubernetes](https://docs.microsoft.com/en-us/virtualization/windowscontainers/kubernetes/common-problems)
* [Debug Networking issues on Windows](https://github.com/microsoft/SDN/tree/master/Kubernetes/windows/debug)
