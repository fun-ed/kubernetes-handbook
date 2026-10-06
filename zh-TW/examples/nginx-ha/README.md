# 零停機服務更新

本範例資訊清單用於搭配[文章中的滾動更新與節點排空說明](https://blog.gruntwork.io/zero-downtime-server-updates-for-your-kubernetes-cluster-902009df5b33)。請僅從儲存庫根目錄套用此範例目錄。

這些資訊清單示範由 Service 前端連接的一組副本，以及 Pod 中斷預算。這不是可直接用於正式環境的高可用性完整方案：請先檢視應用程式就緒狀態、正常關閉、拓撲、負載平衡器健康檢查、儲存空間及叢集逐出限制。Pod 中斷預算不會避免所有服務中斷，也不保證節點排空一定能完成。

## 部署範例

請在儲存庫根目錄執行：

```sh
kubectl apply -f examples/nginx-ha/
```

## 節點排空期間觀察服務

請將節點名稱與位址替換成測試叢集中的實際值。排空節點會逐出符合條件的 Pod，可能影響工作負載；請使用隔離的叢集，並確認 Pod 中斷預算允許此操作。

```sh
kubectl get pods -l app=nginx -o wide
echo "GET http://${LOAD_BALANCER_IP}" | vegeta attack -rate=100 -timeout=10s -duration=1m | vegeta report
kubectl drain "${NODE}" --ignore-daemonsets --delete-emptydir-data
```

請依照 [Vegeta 官方安裝說明](https://github.com/tsenart/vegeta#install)安裝工具，並使用用戶端可連線的位址。負載測試的速率與時間僅為範例，不代表容量建議。節點排空仍可能中斷現有連線；請依實際負載平衡器健康檢查行為進行驗證。

## 清除

```sh
kubectl uncordon "${NODE}"
kubectl delete -f examples/nginx-ha/
```
