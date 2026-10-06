# Deployment 滾動升級

Deployment 透過滾動替換 ReplicaSet 中的 Pod 釋出新版本。準備相容的應用版本、健康檢查、資源請求與回復路徑後，再更新 Deployment 的 Pod template。

## Kubernetes v1.37 範例

`apps/v1` Deployment 必須包含與 Pod template labels 匹配的 `spec.selector`。將映像檔名稱改為組織實際 registry 中固定版本的應用，並確保 tag/digest 已推送：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello
  namespace: default
spec:
  replicas: 3
  revisionHistoryLimit: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: hello
  template:
    metadata:
      labels:
        app: hello
    spec:
      containers:
        - name: hello
          image: registry.example.com/team/hello:v2
          ports:
            - name: http
              containerPort: 8080
          readinessProbe:
            httpGet:
              path: /
              port: http
            periodSeconds: 5
```

對外流量透過 selector 指向相同標籤的 Service；滾動升級不能替代應用級相容性檢查。特別是資料庫 schema 變更，應採用新舊版本並存的遷移策略。

```bash
kubectl apply -f deployment.yaml
kubectl rollout status deployment/hello
kubectl rollout history deployment/hello
```

更新映像檔時使用已釋出、受信任的版本：

```bash
kubectl set image deployment/hello \
  hello=registry.example.com/team/hello:v3
kubectl rollout status deployment/hello
```

發現問題時回復到上一個 revision，並檢查事件、日誌和新舊 ReplicaSet：

```bash
kubectl rollout undo deployment/hello
kubectl rollout history deployment/hello
kubectl get replicasets,pods -l app=hello
```

透過 `maxUnavailable` 與 `maxSurge` 控制升級期間的容量。Readiness probe 應只在例項可提供服務時成功；還應設定合理的 `terminationGracePeriodSeconds` 與 `preStop` 行為，保護正在處理的請求。

## 舊範例說明

原章節中的 `extensions/v1beta1` Deployment、未選擇器驗證的模板、Traefik 舊 `serviceName/servicePort` Ingress、Alpine 3.5 映像檔和固定私有測試 registry 均為歷史內容，不可直接用於 Kubernetes v1.37。ReplicationController 的舊 `kubectl rollingupdate` 操作也不應作為當前釋出方法；新部署優先使用 Deployment。
