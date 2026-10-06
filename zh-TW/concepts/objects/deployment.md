# Deployment

`Deployment` 管理無狀態應用程式的 ReplicaSet 與 Pod，並協調宣告式更新。控制器會逐步使實際狀態符合 `.spec`；發布完成與否應以 rollout 狀態確認，而不是只看 API 寫入成功。

此範例使用官方 NGINX 映像檔標籤 `1.30.5`。正式環境請依組織的映像檔來源、弱點掃描、版本固定及發布政策選擇映像檔。

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  labels:
    app: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: nginx
          image: nginx:1.30.5
          ports:
            - name: http
              containerPort: 80
```

將清單儲存為 `deployment.yaml`，在目標叢集與命名空間確認無誤後套用：

```bash
kubectl apply -f deployment.yaml
kubectl rollout status deployment/web
kubectl get deployment,replicaset,pods -l app=web
```
更新映像檔時，將清單中的 `spec.template.spec.containers[].image` 改為已審核的目標標籤，然後重新套用並監看 rollout：

```bash
kubectl apply -f deployment.yaml
kubectl rollout status deployment/web
kubectl rollout history deployment/web
```


若更新失敗，先檢查 Pod 事件、容器狀態與映像檔可用性。確認前一個版本仍符合需求後，才回復至上一版：

```bash
kubectl rollout undo deployment/web
kubectl rollout status deployment/web
```

`kubectl rollout undo` 只回復 Deployment 的 Pod template revision，不會回復外部資料或其他資源。重大發布前應規劃相容性、健康檢查、資料遷移及回復程序。

## 滾動更新策略

Deployment 預設採用 RollingUpdate。`maxUnavailable` 與 `maxSurge` 控制更新期間可不可用的副本數及額外 Pod 數；對於單副本工作負載，預設值可能導致短暫容量變動。`minReadySeconds` 可要求 Pod 維持 Ready 一段時間後才計為可用。這些欄位需配合容量、就緒探測及應用程式特性設定。

`Recreate` 策略會先刪除舊 Pod 再建立新 Pod，可能造成服務中斷。Deployment 的 rollout 不提供跨資料庫或其他 API 物件的交易保證。

## 參考文件

- [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [kubectl rollout](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_rollout/)
- [NGINX 官方容器映像檔](https://hub.docker.com/_/nginx)

舊版 Deployment 教學、輸出及不再建議使用的映像檔範例已移至[歷史歸檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/concepts/objects/deployment-legacy-zh-TW.md)。
