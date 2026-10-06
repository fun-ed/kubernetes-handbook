# 網路政策範例

## 事前需求

網路政策由網路外掛程式實作，因此您必須使用支援 NetworkPolicy 的網路解決方案——如果只建立資源，卻沒有控制器來實作它，將不會有任何效果。

## 範例工作流程

請從儲存庫根目錄僅套用此目錄：

```sh
kubectl apply -f examples/network-policy/
```

允許存取的測試應會成功；不允許存取的測試會重試連線，最多約三分鐘後失敗。請僅在會強制執行 NetworkPolicy 的 CNI 上觀察此結果：

```sh
kubectl get pods -l app=access-pod
kubectl get pods -l app=no-access-pod
```
