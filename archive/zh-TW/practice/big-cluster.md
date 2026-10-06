# 大規模叢集

Kubernetes v1.6+ 單叢集最大支援 5000 個節點，也就是說 Kubernetes 最新穩定版的單個叢集支援

* 不超過 5000 個節點
* 不超過 150000 個 Pod
* 不超過 300000 個容器
* 每臺 Node 上不超過 100 個 Pod

## 公有云配額

對於公有云上的 Kubernetes 叢集，規模大了之後很容易碰到配額問題，需要提前在雲平臺上增大配額。這些需要增大的配額包括

* 虛擬機器個數
* vCPU 個數
* 內網 IP 位址個數
* 公網 IP 位址個數
* 安全組條數
* 路由表條數
* 持久化儲存大小

### Etcd 儲存

除了常規的 [Etcd 高可用叢集](https://coreos.com/etcd/docs/3.2.15/op-guide/clustering.html)設定、使用 SSD 儲存等，還需要為 Events 設定單獨的 Etcd 叢集。即部署兩套獨立的 Etcd 叢集，並設定 kube-apiserver

```bash
--etcd-servers="http://etcd1:2379,http://etcd2:2379,http://etcd3:2379" \
--etcd-servers-overrides="/events#http://etcd4:2379,http://etcd5:2379,http://etcd6:2379"
```

另外，Etcd 預設儲存限制為 2GB，可以透過 `--quota-backend-bytes` 選項增大。

## Master 節點大小

可以參考 AWS 設定 Master 節點的大小：

* 1-5 nodes: m3.medium
* 6-10 nodes: m3.large
* 11-100 nodes: m3.xlarge
* 101-250 nodes: m3.2xlarge
* 251-500 nodes: c4.4xlarge
* more than 500 nodes: c4.8xlarge

## API Server 記憶體最佳化

### 流式列表響應最佳化 (v1.33+)

從 Kubernetes v1.33 開始，API Server 引入流式列表響應機制，專門解決大規模叢集的記憶體消耗問題：

**解決的問題：**
- 傳統 List API 將整個響應載入到記憶體中，大規模叢集下容易導致 API Server OOM
- 併發 List 請求會導致記憶體使用量激增

**最佳化效果：**
- 基準測試顯示記憶體使用降低約 20 倍（從 70-80GB 降至 3GB）
- 顯著減少大規模叢集中 API Server 的記憶體壓力
- 提高叢集在高負載下的穩定性

**建議設定：**
```bash
# 为大规模集群配置更大的内存限制
--max-requests-inflight=3000
--max-mutating-requests-inflight=1000
# 适当增加内存限制以处理流式响应
--memory=16Gi  # 对于 1000+ 节点集群
```

## 為擴充套件分配更多資源

Kubernetes 叢集內的擴充套件也需要分配更多的資源，包括為這些 Pod 分配更大的 CPU 和記憶體以及增大容器副本數量等。當 Node 本身的容量太小時，還需要增大 Node 本身的 CPU 和記憶體（特別是在公有云平臺上）。

以下擴充套件服務需要增大 CPU 和記憶體：

* [DNS \(kube-dns or CoreDNS\)](https://github.com/kubernetes/kubernetes/tree/master/cluster/addons/dns)
* [Kibana](http://releases.k8s.io/master/cluster/addons/fluentd-elasticsearch/kibana-deployment.yaml)
* [FluentD with ElasticSearch Plugin](http://releases.k8s.io/master/cluster/addons/fluentd-elasticsearch/fluentd-es-ds.yaml)
* [FluentD with GCP Plugin](http://releases.k8s.io/master/cluster/addons/fluentd-gcp/fluentd-gcp-ds.yaml)

以下擴充套件服務需要增大副本數：

* [elasticsearch](http://releases.k8s.io/master/cluster/addons/fluentd-elasticsearch/es-statefulset.yaml)
* [DNS \(kube-dns or CoreDNS\)](https://github.com/kubernetes/kubernetes/tree/master/cluster/addons/dns)

另外，為了保證多個副本分散排程到不同的 Node 上，需要為容器設定 [AntiAffinity](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#affinity-and-anti-affinity)。比如，對 kube-dns，可以增加如下的設定：

```yaml
affinity:
 podAntiAffinity:
   requiredDuringSchedulingIgnoredDuringExecution:
   - weight: 100
     labelSelector:
       matchExpressions:
       - key: k8s-app
         operator: In
         values:
         - kube-dns
     topologyKey: kubernetes.io/hostname
```

## Kube-apiserver 設定

* 設定 `--max-requests-inflight=3000`
* 設定 `--max-mutating-requests-inflight=1000`

## Kube-scheduler 設定

* 設定 `--kube-api-qps=100`

## Kube-controller-manager 設定

* 設定 `--kube-api-qps=100`
* 設定 `--kube-api-burst=100`

## Kubelet 設定

* 設定 `--image-pull-progress-deadline=30m`
* 設定 `--serialize-image-pulls=false`（需要 Docker 使用 overlay2 ）
* Kubelet 單節點允許執行的最大 Pod 數：`--max-pods=110`（預設是 110，可以根據實際需要設定）

## Docker 設定

* 設定 `max-concurrent-downloads=10`
* 使用 SSD 儲存 `graph=/ssd-storage-path`
* 預載入 pause 映像檔，比如 `docker image save -o /opt/preloaded_docker_images.tar` 和 `docker image load -i /opt/preloaded_docker_images.tar`

## 節點設定

增大核心選項設定 `/etc/sysctl.conf`：

```bash
fs.file-max=1000000

net.ipv4.ip_forward=1
net.netfilter.nf_conntrack_max=10485760
net.netfilter.nf_conntrack_tcp_timeout_established=300
net.netfilter.nf_conntrack_buckets=655360
net.core.netdev_max_backlog=10000

net.ipv4.neigh.default.gc_thresh1=1024
net.ipv4.neigh.default.gc_thresh2=4096
net.ipv4.neigh.default.gc_thresh3=8192

net.netfilter.nf_conntrack_max=10485760
net.netfilter.nf_conntrack_tcp_timeout_established=300
net.netfilter.nf_conntrack_buckets=655360
net.core.netdev_max_backlog=10000

fs.inotify.max_user_instances=524288
fs.inotify.max_user_watches=524288
```

## 應用設定

在執行 Pod 的時候也需要注意遵循一些最佳實踐，比如

* 為容器設定資源請求和限制
  * `spec.containers[].resources.limits.cpu`
  * `spec.containers[].resources.limits.memory`
  * `spec.containers[].resources.requests.cpu`
  * `spec.containers[].resources.requests.memory`
  * `spec.containers[].resources.limits.ephemeral-storage`
  * `spec.containers[].resources.requests.ephemeral-storage`
* 對關鍵應用使用 PodDisruptionBudget、nodeAffinity、podAffinity 和 podAntiAffinity 等保護。
* 儘量使用控制器來管理容器（如 Deployment、StatefulSet、DaemonSet、Job 等）。
* 開啟 [Watch Bookmarks](https://kubernetes.io/docs/reference/using-api/api-concepts/#watch-bookmarks) 最佳化 Watch 效能（1.17 GA），客戶端凱伊在 Watch 請求中增加 `allowWatchBookmarks=true` 來開啟這個特性。
* 減少映像檔體積，P2P 映像檔分發，預快取熱點映像檔。
* 更多內容參考[這裡](../../setup/kubernetes-configuration-best-practice.md)。

## 必要的擴充套件

監控、告警以及視覺化（如 Prometheus 和 Grafana）至關重要，推薦部署並開啟。

* [如何擴充套件單個Prometheus實現近萬Kubernetes叢集監控](https://mp.weixin.qq.com/s/DBJ0F3g2Y5EhS02D7k2n5w)

## 參考文件

* [Building Large Clusters](https://kubernetes.io/docs/setup/best-practices/cluster-large/)
* [Scaling Kubernetes to 2,500 Nodes](https://blog.openai.com/scaling-kubernetes-to-2500-nodes/)
* [Scaling Kubernetes for 25M users](https://medium.com/@brendanrius/scaling-kubernetes-for-25m-users-a7937e3536a0)
* [How Does Alibaba Ensure the Performance of System Components in a 10,000-node Kubernetes Cluster](https://www.alibabacloud.com/blog/how-does-alibaba-ensure-the-performance-of-system-components-in-a-10000-node-kubernetes-cluster_595469)
* [Architecting Kubernetes clusters — choosing a cluster size](https://itnext.io/architecting-kubernetes-clusters-choosing-a-cluster-size-92f6feaa2908)
* [Bayer Crop Science seeds the future with 15000-node GKE clusters](https://cloud.google.com/blog/products/containers-kubernetes/google-kubernetes-engine-clusters-can-have-up-to-15000-nodes)
