> HISTORICAL: This chapter contains a Kubernetes v1.3-era command transcript with obsolete resource names, container runtime details, and node/network output. It is preserved only as a dated historical example; do not rerun its commands.

# Kubernetes 101

用 `kubectl create deployment` 建立由 Deployment 管理的應用。`kubectl run` 在當前版本建立單個 Pod，不會建立 Deployment。

```bash
kubectl create deployment nginx-app --image=nginx:1.30.5 --port=80
kubectl get deployment,pods
```

等到容器變成 Running 後，就可以用 `kubectl` 命令來操作它了，比如

* `kubectl get` - 類似於 `docker ps`，查詢資源列表
* `kubectl describe` - 類似於 `docker inspect`，獲取資源的詳細資訊
* `kubectl logs` - 類似於 `docker logs`，獲取容器的日誌
* `kubectl exec` - 類似於 `docker exec`，在容器內執行一個命令

下面的終端輸出記錄於 2016 年的 Kubernetes 叢集。容器 ID、輸出欄位和時間戳是歷史範例，不代表 v1.37 的執行時或命令輸出。
```bash
$ kubectl get pods
NAME                         READY     STATUS    RESTARTS   AGE
nginx-app-4028413181-cnt1i   1/1       Running   0          6m

kubectl exec nginx-app-4028413181-cnt1i -- ps aux
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.5  31736  5108 ?        Ss   00:19   0:00 nginx: master process nginx -g daemon off;
nginx        5  0.0  0.2  32124  2844 ?        S    00:19   0:00 nginx: worker process
root        18  0.0  0.2  17500  2112 ?        Rs   00:25   0:00 ps aux

$ kubectl describe pod nginx-app-4028413181-cnt1i
Name:          nginx-app-4028413181-cnt1i
Namespace:         default
Node:          boot2docker/192.168.64.12
Start Time:        Tue, 06 Sep 2016 08:18:41 +0800
Labels:        pod-template-hash=4028413181
               run=nginx-app
Status:        Running
IP:            172.17.0.3
Controllers:       ReplicaSet/nginx-app-4028413181
Containers:
  nginx-app:
    Container ID:              docker://4ef989b57d0a7638ad9c5bbc22e16d5ea5b459281c77074fc982eba50973107f
    Image:                 nginx
    Image ID:              docker://sha256:4efb2fcdb1ab05fb03c9435234343c1cc65289eeb016be86193e88d3a5d84f6b
    Port:                  80/TCP
    State:                 Running
      Started:             Tue, 06 Sep 2016 08:19:30 +0800
    Ready:                 True
    Restart Count:             0
    Environment Variables:         <none>
Conditions:
  Type         Status
  Initialized      True
  Ready            True
  PodScheduled     True
Volumes:
  default-token-9o8ks:
    Type:          Secret (a volume populated by a Secret)
    SecretName:    default-token-9o8ks
QoS Tier:          BestEffort
Events:
  FirstSeen        LastSeen           Count      From               SubobjectPath              Type           Reason         Message
  ---------        --------           -----      ----               -------------              --------           ------         -------
  8m           8m             1          {default-scheduler}                       Normal         Scheduled          Successfully assigned nginx-app-4028413181-cnt1i to boot2docker
  8m           8m             1          {kubelet boot2docker}      spec.containers{nginx-app}         Normal         Pulling        pulling image "nginx"
  7m           7m             1          {kubelet boot2docker}      spec.containers{nginx-app}         Normal         Pulled         Successfully pulled image "nginx"
  7m           7m             1          {kubelet boot2docker}      spec.containers{nginx-app}         Normal         Created        Created container with docker id 4ef989b57d0a
  7m           7m             1          {kubelet boot2docker}      spec.containers{nginx-app}         Normal         Started        Started container with docker id 4ef989b57d0a

$ curl http://172.17.0.3
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>Welcome to nginx!</h1>
<p>If you see this page, the nginx web server is successfully installed and
working. Further configuration is required.</p>
<p>For online documentation and support please refer to
<a href="http://nginx.org/">nginx.org</a>.<br/>
Commercial support is available at
<a href="http://nginx.com/">nginx.com</a>.</p>
<p><em>Thank you for using nginx.</em></p>
</body>
</html>

$ kubectl logs nginx-app-4028413181-cnt1i
127.0.0.1 - - [06/Sep/2016:00:27:13 +0000] "GET / HTTP/1.0" 200 612 "-" "-" "-"
```

上面用 `kubectl run` 建立了一個獨立 Pod。生產部署通常使用宣告式 YAML，透過 `kubectl apply -f file.yaml` 建立或更新資源。一個簡單的 nginx Pod 如下：
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.30.5
    ports:
    - containerPort: 80
```

Deployment 的清單使用 `apps/v1`，並且必須明確設定 selector，使其與 Pod 模板標籤匹配：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    run: nginx-app
  name: nginx-app
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      run: nginx-app
  strategy:
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
    type: RollingUpdate
  template:
    metadata:
      labels:
        run: nginx-app
    spec:
      containers:
      - image: nginx:1.30.5
        name: nginx-app
        ports:
        - containerPort: 80
          protocol: TCP
      dnsPolicy: ClusterFirst
      restartPolicy: Always
```

## 使用 Volume

Pod 的生命週期通常比較短，只要出現了異常，就會建立一個新的 Pod 來代替它。那容器產生的資料呢？容器內的資料會隨著 Pod 消亡而自動消失。Volume 就是為了持久化容器資料而生，比如可以為 redis 容器指定一個 hostPath 來儲存 redis 資料：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: redis
spec:
  containers:
  - name: redis
    image: redis
    volumeMounts:
    - name: redis-persistent-storage
      mountPath: /data/redis
  volumes:
  - name: redis-persistent-storage
    hostPath:
      path: /data/
```

Kubernetes 提供多種捲來源，常見的有：

* `emptyDir`
* `configMap`
* `secret`
* `projected`
* `downwardAPI`
* `persistentVolumeClaim`，通常由 CSI 驅動提供持久儲存
* `hostPath`，只適用於明確需要存取節點檔案系統的場景
## 使用 Service

前面雖然建立了 Pod，但是在 kubernetes 中，Pod 的 IP 位址會隨著 Pod 的重啟而變化，並不建議直接拿 Pod 的 IP 來互動。那如何來存取這些 Pod 提供的服務呢？使用 Service。Service 為一組 Pod（透過 labels 來選擇）提供一個統一的入口，併為它們提供負載平衡和自動服務發現。比如，可以為前面的 `nginx-app` 建立一個 service：

```bash
kubectl expose deployment nginx-app --port=80 --target-port=80
kubectl get service nginx-app
kubectl get endpointslice -l kubernetes.io/service-name=nginx-app
```

Service 為匹配 selector 的 Pod 提供穩定的叢集內入口。需要從叢集外存取時，請按叢集網路和暴露策略設定 Service 或 Gateway API。不要依賴範例中的 Pod IP 或固定位址。
