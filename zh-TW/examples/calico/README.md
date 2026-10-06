# 查詢 Calico GlobalNetworkPolicy 記錄

由於 Calico NetworkPolicy 是以 iptables 為基礎，calico-node 記錄只會顯示其容器的輸出，不會顯示 GlobalNetworkPolicy 的 Log 動作。此範例說明如何查詢這些記錄。

## 部署

請先確認[`../README.md`](../README.md)所列必要條件，再從儲存庫根目錄僅套用此 Calico 專用範例：

```sh
kubectl apply -f examples/calico/calico-packet-logs.yaml
```

## 讀取收集到的記錄

```sh
kubectl logs -n default -l app=calico-packet-logs --all-containers=true --prefix
```
