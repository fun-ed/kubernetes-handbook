# kubectl

kubectl 是 Kubernetes 的命令列工具（CLI），是 Kubernetes 使用者和管理員必備的管理工具。

kubectl 提供了大量的子命令，方便管理 Kubernetes 叢集中的各種功能。這裡不再羅列各種子命令的格式，而是介紹下如何查詢命令的幫助

* `kubectl -h` 檢視子命令列表
* `kubectl options` 檢視全域性選項
* `kubectl <command> --help` 檢視子命令的幫助
* `kubectl [command] [PARAMS] -o=<format>` 設定輸出格式（如 json、yaml、jsonpath 等）
* `kubectl explain [RESOURCE]` 檢視資源的定義

## 設定

通常由叢集部署工具或平台提供 kubeconfig。檢視當前 Context 和已有設定：

```bash
kubectl config current-context
kubectl config get-contexts
kubectl config view --minify
kubectl config use-context <context-name>
kubectl config set-context --current --namespace=<namespace>
```

## 常用命令格式

* 建立一個獨立 Pod：`kubectl run <name> --image=<image>`
* 建立由 Deployment 管理的應用：`kubectl create deployment <name> --image=<image>`
* 建立 Job：`kubectl create job <name> --image=<image> -- <command>`
* 建立 CronJob：`kubectl create cronjob <name> --image=<image> --schedule='<cron>' -- <command>`
* 從清單建立或更新資源：`kubectl apply -f manifest.yaml`
* 查詢：`kubectl get <resource>`
* 更新：`kubectl set` 或 `kubectl patch`
* 刪除：`kubectl delete <resource> <name>` 或 `kubectl delete -f manifest.yaml`
* 查詢 Pod IP：`kubectl get pod <pod-name> -o jsonpath='{.status.podIP}'`
* 在容器內執行命令：`kubectl exec -it <pod-name> -- sh`
* 檢視容器日誌：`kubectl logs [-f] <pod-name>`
* 為 Deployment 建立 Service：`kubectl expose deployment <name> --port=80`

在 Kubernetes v1.37 中，`kubectl run` 建立 Pod。它不再像早期版本那樣生成 Deployment、ReplicationController、Job 或 CronJob。
## 命令列自動補全

Linux 系統 Bash：

```bash
source /usr/share/bash-completion/bash_completion
source <(kubectl completion bash)
```

MacOS zsh

```bash
source <(kubectl completion zsh)
```

## 自定義輸出列

比如，查詢所有 Pod 的資源請求和限制：

```bash
kubectl get pods --all-namespaces -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name,"CPU(requests)":.spec.containers[*].resources.requests.cpu,"CPU(limits)":.spec.containers[*].resources.limits.cpu,"MEMORY(requests)":.spec.containers[*].resources.requests.memory,"MEMORY(limits)":.spec.containers[*].resources.limits.memory
```

## 日誌檢視

`kubectl logs` 用於顯示 pod 執行中，容器內程式輸出到標準輸出的內容。跟 docker 的 logs 命令類似。

```bash
# Return snapshot logs from pod nginx with only one container
kubectl logs nginx

# Return snapshot of previous terminated ruby container logs from pod web-1
kubectl logs -p -c ruby web-1

# Begin streaming the logs of the ruby container in pod web-1
kubectl logs -f -c ruby web-1
```

> 注：kubectl 只可以檢視單個容器的日誌，如果想要同時檢視多個 Pod 的日誌，可以使用 [stern](https://github.com/wercker/stern)。比如： `stern --all-namespaces -l run=nginx`。

## 連線到一個正在執行的容器

`kubectl attach` 用於連線到一個正在執行的容器。跟 docker 的 attach 命令類似。

```bash
  # Get output from running pod 123456-7890, using the first container by default
  kubectl attach 123456-7890

  # Get output from ruby-container from pod 123456-7890
  kubectl attach 123456-7890 -c ruby-container

  # Switch to raw terminal mode, sends stdin to 'bash' in ruby-container from pod 123456-7890
  # and sends stdout/stderr from 'bash' back to the client
  kubectl attach 123456-7890 -c ruby-container -i -t

Options:
  -c, --container='': Container name. If omitted, the first container in the pod will be chosen
  -i, --stdin=false: Pass stdin to the container
  -t, --tty=false: Stdin is a TTY
```

## 在容器內部執行命令

`kubectl exec` 用於在一個正在執行的容器執行命令。跟 docker 的 exec 命令類似。

> 多容器 Pod 可透過 `kubectl.kubernetes.io/default-container` annotation 設定 kubectl 命令的預設容器。

```bash
  # Get output from running 'date' from pod 123456-7890, using the first container by default
  kubectl exec 123456-7890 -- date

  # Switch to raw terminal mode, sends stdin to 'bash' in ruby-container from pod 123456-7890
  # and sends stdout/stderr from 'bash' back to the client
  kubectl exec 123456-7890 -c ruby-container -i -t -- bash -il

Options:
  -c, --container='': Container name. If omitted, the first container in the pod will be chosen
  -p, --pod='': Pod name
  -i, --stdin=false: Pass stdin to the container
  -t, --tty=false: Stdin is a TT
```

## 連接埠轉送

`kubectl port-forward` 用於將本地連接埠轉送到指定的 Pod。

```bash
# Listen on ports 5000 and 6000 locally, forwarding data to/from ports 5000 and 6000 in the pod
kubectl port-forward mypod 5000 6000

# Listen on port 8888 locally, forwarding to 5000 in the pod
kubectl port-forward mypod 8888:5000

# Listen on a random port locally, forwarding to 5000 in the pod
kubectl port-forward mypod :5000

# Listen on a random port locally, forwarding to 5000 in the pod
kubectl port-forward mypod 0:5000
```

也可以將本地連接埠轉送到服務、複製控制器或者部署的連接埠。

```bash
# Forward to deployment
kubectl port-forward deployment/redis-master 6379:6379

# Forward to replicaSet
kubectl port-forward rs/redis-master 6379:6379

# Forward to service
kubectl port-forward svc/redis-master 6379:6379
```

## API Server 代理

`kubectl proxy` 命令提供了一個 Kubernetes API 服務的 HTTP 代理。

```bash
$ kubectl proxy --port=8080
Starting to serve on 127.0.0.1:8080
```

可以透過代理位址 `http://localhost:8080/api/` 來直接存取 Kubernetes API，比如查詢 Pod 列表

```bash
curl http://localhost:8080/api/v1/namespaces/default/pods
```

`kubectl proxy` 預設只監聽本地迴環位址。不要用 `--address=0.0.0.0` 或寬泛的 `--accept-hosts` 將代理暴露到網路。

```bash
kubectl proxy --port=8001
curl http://127.0.0.1:8001/api/
```

## 檔案複製

`kubectl cp` 支援從容器中複製，或者複製檔案到容器中

```bash
  # Copy /tmp/foo_dir local directory to /tmp/bar_dir in a remote pod in the default namespace
  kubectl cp /tmp/foo_dir <some-pod>:/tmp/bar_dir

  # Copy /tmp/foo local file to /tmp/bar in a remote pod in a specific container
  kubectl cp /tmp/foo <some-pod>:/tmp/bar -c <specific-container>

  # Copy /tmp/foo local file to /tmp/bar in a remote pod in namespace <some-namespace>
  kubectl cp /tmp/foo <some-namespace>/<some-pod>:/tmp/bar

  # Copy /tmp/foo from a remote pod to /tmp/bar locally
  kubectl cp <some-namespace>/<some-pod>:/tmp/foo /tmp/bar

Options:
  -c, --container='': Container name. If omitted, the first container in the pod will be chosen
```

注意：檔案複製依賴於 tar 命令，所以容器中需要能夠執行 tar 命令

## kubectl drain

```bash
kubectl drain NODE [Options]
```

* 它會刪除該 NODE 上由 ReplicationController, ReplicaSet, DaemonSet, StatefulSet or Job 建立的 Pod
* 不刪除 mirror pods（因為不可透過 API 刪除 mirror pods）
* 如果還有其它型別的 Pod（比如不透過 RC 而直接透過 kubectl create 的 Pod）並且沒有 --force 選項，該命令會直接失敗
* 如果命令中增加了 --force 選項，則會強制刪除這些不是透過 ReplicationController, Job 或者 DaemonSet 建立的 Pod

有的時候不需要 evict pod，只需要標記 Node 不可呼叫，可以用 `kubectl cordon` 命令。

恢復的話只需要執行 `kubectl uncordon NODE` 將 NODE 重新改成可排程狀態。

## 權限檢查

`kubectl auth` 提供了兩個子命令用於檢查使用者的鑑權情況：

* `kubectl auth can-i` 檢查使用者是否有權限進行某個操作，比如

```bash
  # Check to see if I can create pods in any namespace
  kubectl auth can-i create pods --all-namespaces

  # Check to see if I can list deployments in my current namespace
  kubectl auth can-i list deployments.apps

  # Check to see if I can do everything in my current namespace ("*" means all)
  kubectl auth can-i '*' '*'

  # Check to see if I can get the job named "bar" in namespace "foo"
  kubectl auth can-i list jobs.batch/bar -n foo
```

* `kubectl auth reconcile` 自動修復有問題的 RBAC 策略，如

```bash
  # Reconcile rbac resources from a file
  kubectl auth reconcile -f my-rbac-rules.yaml
```

## 模擬其他使用者

kubectl 支援模擬其他使用者或者組來進行叢集管理操作，比如

```bash
kubectl drain mynode --as=superman --as-group=system:masters
```

這實際上就是在請求 Kubernetes API 時新增了如下的 HTTP HEADER：

```bash
Impersonate-User: superman
Impersonate-Group: system:masters
```

## 檢視事件（events）

```bash
# 查看所有事件
kubectl get events --all-namespaces

# 查看名为nginx对象的事件
kubectl get events --field-selector involvedObject.name=nginx,involvedObject.namespace=default

# 查看名为nginx的服务事件
kubectl get events --field-selector involvedObject.name=nginx,involvedObject.namespace=default,involvedObject.kind=Service

# 查看Pod的事件
kubectl get events --field-selector involvedObject.name=nginx-85cb5867f-bs7pn,involvedObject.kind=Pod

# 按时间对events排序
kubectl get events --sort-by=.metadata.creationTimestamp

# 自定义events输出格式
kubectl get events --sort-by='.eventTime' -o 'go-template={{range .items}}{{.involvedObject.name}}{{"\t"}}{{.involvedObject.kind}}{{"\t"}}{{.message}}{{"\t"}}{{.reason}}{{"\t"}}{{.type}}{{"\t"}}{{.eventTime}}{{"\n"}}{{end}}'
```

## kubectl 外掛

kubectl 外掛提供了一種擴充套件 kubectl 的機制，比如新增新的子命令。外掛可以以任何語言編寫，只需要滿足以下條件即可

* 外掛放在 `~/.kube/plugins` 或環境變數 `KUBECTL_PLUGINS_PATH` 指定的目錄中
* 外掛的格式為 `子目录 / 可执行文件或脚本` 且子目錄中要包括 `plugin.yaml` 設定檔案

比如

```bash
$ tree
.
└── hello
    └── plugin.yaml

1 directory, 1 file

$ cat hello/plugin.yaml
name: "hello"
shortDesc: "Hello kubectl plugin!"
command: "echo Hello plugins!"

$ kubectl plugin hello
Hello plugins!
```

你也可以使用 [krew](../../setup/kubectl.md) 來管理 kubectl 外掛。

## 原始 URI

kubectl 也可以用來直接存取原始 URI，比如要存取 [Metrics API](https://github.com/kubernetes-sigs/metrics-server) 可以

* `kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes`
* `kubectl get --raw /apis/metrics.k8s.io/v1beta1/pods`
* `kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes/<node-name>`
* `kubectl get --raw /apis/metrics.k8s.io/v1beta1/namespaces/<namespace-name>/pods/<pod-name>`

## 附錄

kubectl 的安裝方法

```bash
# OS X
curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/darwin/amd64/kubectl

# Linux
curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl

# Windows
curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/windows/amd64/kubectl.exe
```
