# 雲端排錯

公有雲託管 Kubernetes 與在雲端虛擬機器上自行部署的叢集，在控制平面日誌、雲端身分、網路、負載平衡和 CSI 儲存的管理方式上並不相同。先確認發行版、Kubernetes 版本、網路模式、雲端控制器／CSI 驅動及其管理者，再依相應雲服務商文件排查；不要假設每個雲平台都由 kube-controller-manager 自動為所有 Node 設定 Pod 路由。

## 先收集 Kubernetes 端證據

```bash
kubectl get nodes -o wide
kubectl get events -A --sort-by=.metadata.creationTimestamp
kubectl get services -A
kubectl get endpointslices -A
kubectl get pods -A -o wide
```

依故障類型進一步檢查 Node Conditions、Service/PVC 事件、EndpointSlices、NetworkPolicy、CSI 物件與相關工作負載日誌。請避免輸出雲端憑證、ServiceAccount token 或 Secret 內容。

## Node 尚未註冊或雲端初始化未完成

```bash
kubectl describe node '<node-name>'
kubectl get events -A --sort-by=.metadata.creationTimestamp
```

檢查 Node Conditions、taint、事件和註冊／初始化錯誤。託管服務通常不允許檢視控制平面 Pod 日誌；請透過雲服務商的叢集診斷、活動記錄及節點管理通道取得相應證據。外部 cloud-controller-manager 叢集才依其發行版文件檢查 CCM 部署、啟動參數、身分權限和日誌。`node.cloudprovider.kubernetes.io/uninitialized` taint 表示雲端初始化尚未完成，不應以手動移除 taint 代替修復。

## 網路、Service 與負載平衡

比對 Pod/Node 位址、Service 連接埠、EndpointSlices、NetworkPolicy 與實際 CNI/Service 資料平面，確認故障發生於叢集內、節點間或雲端網路邊界。雲服務商管理的路由、NSG／防火牆、負載平衡探測、IP 配額和私有端點，須使用該平台當前診斷工具及權限流程；不要套用通用假設或直接改寫雲端資源。

## 持久化儲存

檢查 PVC、PV、StorageClass、VolumeAttachment、CSI driver/controller/node 狀態和 Events。核對所選 CSI 驅動的身分權限、區域／拓撲、配額、網路與後端狀態；不要將歷史 in-tree 外掛參數或 Secret 授權範例用於目前 CSI 驅動。

## 雲端專頁

- [Azure／AKS 排錯](azure.md)
- [Kubernetes 網路排錯](../network.md)
- [持久卷排錯](../pv/)

不同雲端的控制平面可見度、網路實現和診斷介面各有差異；本章沒有列出未經驗證的通用雲端修復命令。
