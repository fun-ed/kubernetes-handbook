# Kubernetes v1.37.1 元件與映像檔現況稽核

**稽核截點：2026-10-05。** 本報告以同日凍結的[元件版本快照](component-versions.md)為歷史基準，不覆寫該快照。本次透過 GitHub Releases API（以 `gh api` 唯讀查詢）重新檢查追蹤清單中的 26 項，以及快照中其他有 GitHub Release 的元件；僅納入非 draft、非 prerelease 的穩定版，並依各專案的版本序比較。除下文記錄的 Spinnaker 穩定版更新與 CSI sidecar 發布日期差異外，快照中有 GitHub Release 的元件版本均與本次結果相同。Kubernetes 支援判斷仍沿用快照，不能由「上游最新」推導為相容 v1.37。沒有 GitHub Release 的元件則依官方 tag、版本記錄或政策來源個別核對；alpha、beta、RC、draft 及明確標示為 unstable 的版本不列入穩定版。上游版本、Kubernetes／kubeadm 固定值與發行版隨附值分開列出。

## 稽核範圍與結論

- 已透過 GitHub Releases API 查核 `component-watchlist.json` 中的 26 個追蹤項目，以及 `component-versions.md` 中其他有 GitHub Release 的元件；僅將 `draft=false`、`prerelease=false` 的穩定版納入比較。多產品／多維護分支專案依版本序或專案發布序比較。快照中有 GitHub Release 的元件版本均與本次結果相同，Spinnaker 除外；發布日期差異另列。官方來源與人工相容性結論見[元件版本清單](component-versions.md)。上游新版本不代表支援 v1.37。
- 掃描 `examples/`、`manifests/` 後，共找到 **58 個 image 宣告，分布於 32 個檔案**。本次使用 Docker Hub v2 `GET https://hub.docker.com/v2/repositories/{namespace}/{repository}/tags/{tag}` 直接查詢 12 個範例 tag：nginx 1.30.5／1.31.6、nginx-unprivileged 1.30.5-alpine3.24、Alpine 3.24.2、BusyBox 1.37.0／1.38.0、Python 3.14.8-slim-trixie、Redis 8.10.2、PostgreSQL 18.6-alpine3.24、TensorFlow 2.21.0、Fluent Bit 5.1.3、Ubuntu 26.04。並非所有映像 tag 或非 Hub registry 都重新查詢，不能據此宣稱所有範例映像都是最新。未更動 `examples/`／`manifests/` 中的 image pin。另外在活躍 Markdown 教學中找到 **16** 處使用 BusyBox 1.36／1.36.1 的舊版參照，已更新為穩定標籤 `1.37.0`；繁體中文副本的 **16** 處也已同步。
- 所有 Docker Hub 映像標籤都只是固定 tag，不是不可變的映像 digest。官方 Hub 在 **2026-10-05** 顯示 `nginxinc/nginx-unprivileged:1.30.5-alpine3.24` 同一標籤於當日更新；標籤未變但內容可能已變更，不可把 tag 當成 digest 鎖定。
- k0s 與 RKE2 是獨立的發行版基準：k0s 最新穩定版使用 Kubernetes 1.36.4，並非 v1.37；RKE2 最新穩定版已使用 Kubernetes v1.37.1。其內含 etcd、runtime 與附加元件不是 kubeadm 固定版本，詳見下節。
- 未更動歷史封存內容中的版本固定值、`en/` 或相依套件；另將 Azure 排障文件中的過期 GPU 清單抽出至封存區。未執行安裝程式或操作叢集。

## 現行元件版本逐項稽核

表內列出本次核實的截點最新穩定版，可透過官方發布連結查閱發布資訊；「待確認」或「不相容」等 Kubernetes 支援判斷維持[原矩陣](component-versions.md)中的人工結論，不因上游版本較新而改寫。Spinnaker 的 stable release 標籤 `spinnaker-release-2026.3.0`（2026-09-07）依數值版本序高於 2026.1.3；凍結矩陣版本仍保留為歷史紀錄。CSI sidecar 版本相同，但 GitHub API `published_at` 顯示 external-provisioner v6.3.0 為 2026-06-04，external-attacher v4.13.0、node-driver-registrar v2.18.0、livenessprobe v2.20.0 均為 2026-09-04；凍結矩陣所列日期不同，因此此處以 API 日期為準，不改寫歷史快照。

### 核心元件、執行階段與建置前提

| 元件 | 截點最新穩定版（本次核實） | 官方來源 |
| --- | --- | --- |
| Kubernetes | v1.37.1 | [發行版](https://github.com/kubernetes/kubernetes/releases/tag/v1.37.1) |
| etcd | v3.7.2 | [發行版](https://github.com/etcd-io/etcd/releases/tag/v3.7.2) |
| CoreDNS | v1.14.7 | [發行版](https://github.com/coredns/coredns/releases/tag/v1.14.7) |
| containerd | v2.4.1 | [發行版](https://github.com/containerd/containerd/releases/tag/v2.4.1) |
| runc | v1.5.2 | [發行版](https://github.com/opencontainers/runc/releases/tag/v1.5.2) |
| CRI-O | v1.37.2 | [發行版](https://github.com/cri-o/cri-o/releases/tag/v1.37.2) |
| cri-dockerd | v0.4.7 | [發行版](https://github.com/Mirantis/cri-dockerd/releases/tag/v0.4.7) |
| cri-tools／crictl | v1.37.0 | [發行版](https://github.com/kubernetes-sigs/cri-tools/releases/tag/v1.37.0) |
| CNI plugins | v1.9.1 | [發行版](https://github.com/containernetworking/plugins/releases/tag/v1.9.1) |
| pause sandbox image | 無獨立穩定版日期；kubeadm 固定 3.10.2 | [Kubernetes v1.37.1 dependencies](https://github.com/kubernetes/kubernetes/blob/v1.37.1/build/dependencies.yaml) |
| Go | go1.27.1 | [官方版本記錄](https://go.dev/doc/devel/release) |

### 可安裝外掛與附加元件

| 元件 | 截點最新穩定版（本次核實） | 官方來源 |
| --- | --- | --- |
| Metrics Server | v0.9.0（chart 3.14.0） | [應用發行版](https://github.com/kubernetes-sigs/metrics-server/releases/tag/v0.9.0) · [chart](https://github.com/kubernetes-sigs/metrics-server/releases/tag/metrics-server-helm-chart-3.14.0) |
| node-problem-detector | v1.36.0 | [發行版](https://github.com/kubernetes/node-problem-detector/releases/tag/v1.36.0) |
| CSI external-provisioner | v6.3.0 | [發行版](https://github.com/kubernetes-csi/external-provisioner/releases/tag/v6.3.0) |
| CSI external-attacher | v4.13.0 | [發行版](https://github.com/kubernetes-csi/external-attacher/releases/tag/v4.13.0) |
| CSI external-snapshotter | v8.6.0 | [發行版](https://github.com/kubernetes-csi/external-snapshotter/releases/tag/v8.6.0) |
| CSI external-resizer | v2.3.0 | [發行版](https://github.com/kubernetes-csi/external-resizer/releases/tag/v2.3.0) |
| CSI node-driver-registrar | v2.18.0 | [發行版](https://github.com/kubernetes-csi/node-driver-registrar/releases/tag/v2.18.0) |
| CSI livenessprobe | v2.20.0 | [發行版](https://github.com/kubernetes-csi/livenessprobe/releases/tag/v2.20.0) |
| Gateway API | v1.6.2 | [發行版](https://github.com/kubernetes-sigs/gateway-api/releases/tag/v1.6.2) |
| Cilium | v1.20.2 | [發行版](https://github.com/cilium/cilium/releases/tag/v1.20.2) |
| Calico | v3.33.0 | [發行版](https://github.com/projectcalico/calico/releases/tag/v3.33.0) |
| Flannel | v0.28.9 | [發行版](https://github.com/flannel-io/flannel/releases/tag/v0.28.9) |
| Traefik | v3.7.13（chart 41.6.1） | [發行版](https://github.com/traefik/traefik/releases/tag/v3.7.13) · [chart index](https://traefik.github.io/charts/index.yaml) |
| Envoy Gateway | v1.9.2 | [發行版](https://github.com/envoyproxy/gateway/releases/tag/v1.9.2) |
| Istio | 1.31.1 | [發行版](https://github.com/istio/istio/releases/tag/1.31.1) |
| Prometheus | v3.15.0 | [發行版](https://github.com/prometheus/prometheus/releases/tag/v3.15.0) |
| Grafana | v13.2.3 | [發行版](https://github.com/grafana/grafana/releases/tag/v13.2.3) |
| cert-manager | v1.21.2 | [發行版](https://github.com/cert-manager/cert-manager/releases/tag/v1.21.2) |
| kube-state-metrics | v2.20.0 | [發行版](https://github.com/kubernetes/kube-state-metrics/releases/tag/v2.20.0) |
| Cluster Autoscaler | v1.36.1 | [發行版](https://github.com/kubernetes/autoscaler/releases/tag/cluster-autoscaler-1.36.1) |
| ip-masq-agent | v2.12.6（tag，非 GitHub Release） | [Tag](https://github.com/kubernetes-sigs/ip-masq-agent/tree/v2.12.6) |
| Kured | v1.23.0 | [發行版](https://github.com/kubereboot/kured/releases/tag/1.23.0) |
| NVIDIA GPU Operator | v26.7.1 | [發行版](https://github.com/NVIDIA/gpu-operator/releases/tag/v26.7.1) |
| NVIDIA Kubernetes Device Plugin | v0.20.1 | [發行版](https://github.com/NVIDIA/k8s-device-plugin/releases/tag/v0.20.1) |
| Fluentd | v1.19.4 | [發行版](https://github.com/fluent/fluentd/releases/tag/v1.19.4) |
| Elasticsearch | v9.5.4 | [發行版](https://github.com/elastic/elasticsearch/releases/tag/v9.5.4) |
| Kibana | v9.5.4 | [發行版](https://github.com/elastic/kibana/releases/tag/v9.5.4) |
| Argo Workflows | v4.1.4 | [發行版](https://github.com/argoproj/argo-workflows/releases/tag/v4.1.4) |
| Argo CD | v3.5.3 | [發行版](https://github.com/argoproj/argo-cd/releases/tag/v3.5.3) |
| Apache Spark | 4.2.0 | [發行公告](https://spark.apache.org/news/spark-4-2-0-released.html) |
| Flux | v2.9.6 | [發行版](https://github.com/fluxcd/flux2/releases/tag/v2.9.6) |
| Velero | v1.18.4 | [發行版](https://github.com/velero-io/velero/releases/tag/v1.18.4) |
| Linkerd OSS | edge-26.9.3（無 OSS stable artifact） | [發行政策](https://linkerd.io/releases/) · [edge](https://github.com/linkerd/linkerd2/releases/tag/edge-26.9.3) |

### 用戶端與本機叢集工具

| 元件 | 截點最新穩定版（本次核實） | 官方來源 |
| --- | --- | --- |
| Helm | v4.3.0 | [發行版](https://github.com/helm/helm/releases/tag/v4.3.0) |
| kind | v0.33.0 | [發行版](https://github.com/kubernetes-sigs/kind/releases/tag/v0.33.0) |
| minikube | v1.39.0 | [發行版](https://github.com/kubernetes/minikube/releases/tag/v1.39.0) |
| client-go | v0.37.1（tag，無 GitHub Release） | [Tag](https://github.com/kubernetes/client-go/tree/v0.37.1) |
| Skaffold | v2.25.0 | [發行版](https://github.com/GoogleContainerTools/skaffold/releases/tag/v2.25.0) |
| Kompose | v1.38.0 | [發行版](https://github.com/kubernetes/kompose/releases/tag/v1.38.0) |
| Draft | v0.17.15 | [發行版](https://github.com/Azure/draft/releases/tag/v0.17.15) |
| Jenkins X CLI | v3.17.111 | [發行版](https://github.com/jenkins-x/jx/releases/tag/v3.17.111) |
| Spinnaker | 2026.3.0（2026-09-07） | [穩定版釋出](https://github.com/spinnaker/spinnaker/releases/tag/spinnaker-release-2026.3.0) |
| kOps | v1.36.2 | [發行版](https://github.com/kubernetes/kops/releases/tag/v1.36.2) |
| Kubespray | v2.32.0 | [發行版](https://github.com/kubernetes-sigs/kubespray/releases/tag/v2.32.0) |
| OVN-Kubernetes | v1.4.0 | [發行版](https://github.com/ovn-kubernetes/ovn-kubernetes/releases/tag/v1.4.0) |
| SR-IOV Network Operator | v1.6.0 | [發行版](https://github.com/k8snetworkplumbingwg/sriov-network-operator/releases/tag/v1.6.0) |
| k0s | v1.36.4+k0s.1 | [官方發行版](https://github.com/k0sproject/k0s/releases/tag/v1.36.4%2Bk0s.1) |
| RKE2 | v1.37.1+rke2r1 | [官方發行版](https://github.com/rancher/rke2/releases/tag/v1.37.1%2Brke2r1) |

### 發行版固定版本：不可由上游最新版取代

| 發行版 | 截點前最新穩定版與隨附 Kubernetes | 其他核對的隨附版本 | 結果 |
| --- | --- | --- | --- |
| k0s | `v1.36.4+k0s.1`，Kubernetes `v1.36.4`；2026-09-19T21:23:36Z 發布 | containerd `2.3.5`；release note 另列 Traefik `v3.7.13-k0s.0`、Helm `v3.21.4`、Kine `v0.16.5` | 本次查詢 `GET https://api.github.com/repos/k0sproject/k0s/releases/latest`，回傳穩定 tag，`draft=false`、`prerelease=false`。不可宣稱支援手冊基準 v1.37；保留該發行版自身的 bundled pins。[Release](https://github.com/k0sproject/k0s/releases/tag/v1.36.4%2Bk0s.1) · [版本文件](https://docs.k0sproject.io/v1.36.4+k0s.1/) |
| RKE2 | `v1.37.1+rke2r1`，Kubernetes `v1.37.1`；2026-09-30T16:49:06Z 發布 | etcd `v3.7.1-k3s3`、containerd `v2.3.4-k3s1`、runc `v1.4.3`、CoreDNS `1.14.7`、metrics-server `0.9.0`、Traefik `3.7.13`；預設 Canal 使用 Flannel `0.28.9`／Calico `3.32.2` | 本次檢查 `GET https://api.github.com/repos/rancher/rke2/releases?per_page=100` 的分頁穩定 tags，`draft=false`、`prerelease=false`；SUSE 支援矩陣包含 v1.37。這些發行版 pins 與 kubeadm pins 各自獨立。[Release](https://github.com/rancher/rke2/releases/tag/v1.37.1%2Brke2r1) · [支援矩陣](https://www.suse.com/suse-rke2/support-matrix/all-supported-versions/rke2-v1-37/) |

GitHub Release tag 中的 `+k0s.N`、`+rke2rN` 是穩定的發行版重建修訂後綴，不是預發布後綴。追蹤程式會逐頁讀取這兩個發行版的 Releases API，並依 Kubernetes 三段版本及數值修訂序比較（例如 r10 大於 r9）；若發行版後綴未知或格式錯誤，會回報錯誤，而不會把一般 SemVer build metadata 排序規則改為全域比較。

## 範例與映像檔 pins

稽核 `examples/` 與 `manifests/` 中的 **58 個 image 宣告／32 個檔案**，結果如下。可變標籤、佔位映像與第三方重新包裝映像另列為例外；「查得到 tag」不代表適合替換，也不代表已驗證可在 v1.37 執行。

| 映像系列 | 目前 pin | 截點稽核結果與來源 |
| --- | --- | --- |
| NGINX stable | `1.30.5` | 保留 stable 1.30 系列；Hub 較新的 `1.31.6` 是 mainline，不是 stable 更新。[Hub](https://hub.docker.com/_/nginx) · [1.30 變更記錄](https://nginx.org/en/CHANGES-1.30) |
| 非特權 NGINX | `1.30.5-alpine3.24` | tag 存在；2026-10-05 Hub 記錄此 tag 當日更新。tag 可能移動，若要求不可變引用，應另行固定 digest。[Hub](https://hub.docker.com/r/nginxinc/nginx-unprivileged) |
| Alpine | `3.24.2` | 穩定 3.24 系列版本。[Hub](https://hub.docker.com/_/alpine) · [官方發行公告](https://www.alpinelinux.org/posts/Alpine-3.21.8-3.22.6-3.23.6-3.24.2-released.html) |
| BusyBox | `1.37.0` | 保留。上游明確將 1.38.0 標示為 **unstable**，因此不替換成較高但非穩定的版本。[公告](https://busybox.net/news.html) · [Hub tags](https://hub.docker.com/_/busybox) |
| Python | `3.14.8-slim-trixie` | tag 存在；Python 3.14.8 是截點前的穩定版。[Hub](https://hub.docker.com/_/python) · [Python 發行版](https://www.python.org/downloads/release/python-3148/) |
| Redis | `8.10.2` | 本次查詢確認 tag 存在；未重新檢視 Redis 穩定版發行序列。[Hub](https://hub.docker.com/_/redis) |
| PostgreSQL | `18.6-alpine3.24` | 本次查詢確認 tag 存在；19 beta 不作為穩定版替代，穩定版基準沿用凍結快照。[Hub](https://hub.docker.com/_/postgres) |
| TensorFlow | `2.21.0` | tag 存在；2.22.0 是 RC，已排除。[Hub](https://hub.docker.com/r/tensorflow/tensorflow) |
| Fluent Bit | `5.1.3` | 與截點前最新穩定 release 相同。[release](https://github.com/fluent/fluent-bit/releases/tag/v5.1.3) · [映像文件](https://docs.fluentbit.io/manual/installation/downloads/docker) |
| NodeLocal DNS cache | `1.26.8` | Kubernetes DNS 儲存庫有 `1.26.8` tag，但沒有對應的 GitHub Release；最新 stable Release 仍為 `v1.26.0`（2025-05-13）。2026-10-05 的唯讀 registry GET 確認映像標籤可解析，OCI index digest 為 `sha256:bc6e64e2c85956af2fcc0aa720086410d41b4f31f378c9a92646fecc85cd4739`，平台包含 linux/amd64、arm64、arm/v7、ppc64le、s390x。此處僅驗證映像標籤與平台存在，不代表仍受維護或相容 v1.37。[tag](https://github.com/kubernetes/dns/tree/1.26.8) · [Releases](https://github.com/kubernetes/dns/releases) · [registry index](https://registry.k8s.io/v2/dns/k8s-dns-node-cache/manifests/1.26.8) |
| Ubuntu | `26.04` | 保留穩定 LTS pin；26.10／development 標籤不是穩定版替代。[Hub](https://hub.docker.com/_/ubuntu) |
| Kubernetes echoserver | `registry.k8s.io/echoserver:1.10` | 2026-10-05 的唯讀 registry GET 確認標籤可解析，manifest digest 為 `sha256:cb5c1bddd1b5665e1867a7fa1b5fa843a47ee433bbb75d4293888b71def53229`，映像平台為 linux/amd64。此處只確認標籤存在，不代表仍受維護或支援 v1.37 工作負載。[manifest](https://registry.k8s.io/v2/echoserver/manifests/1.10) · [原始碼](https://github.com/kubernetes/kubernetes/tree/master/test/images/echoserver) |
| Metrics Server | `v0.9.0` | manifest tag 與凍結快照記錄的穩定版相同；本次未重新查詢 release API。v1.37 支援狀態與 API 限制見矩陣。[manifest image](https://github.com/kubernetes-sigs/metrics-server/releases/tag/v0.9.0) |
| node-problem-detector | `v1.36.0` | manifest tag 與凍結快照記錄的穩定版相同；本次未重新查詢 release API。Kubernetes `dependencies.yaml` 中的測試映像 `v1.35.2` 是獨立固定值，不是 kubeadm addon。[release](https://github.com/kubernetes/node-problem-detector/releases/tag/v1.36.0) · [Kubernetes dependencies](https://github.com/kubernetes/kubernetes/blob/v1.37.1/build/dependencies.yaml) |
| Traefik | `v3.7.13` | manifest tag 與凍結快照記錄的穩定版相同；本次未重新查詢 release API，也不代表 Traefik 宣告相容 v1.37。[release](https://github.com/traefik/traefik/releases/tag/v3.7.13) |
| CoreDNS | `v1.14.6` | 刻意保留 kubeadm v1.37.1 預設值；上游已有 `v1.14.7` 不會覆寫 kubeadm pin。[kubeadm dependencies](https://github.com/kubernetes/kubernetes/blob/v1.37.1/build/dependencies.yaml) · [上游 release](https://github.com/coredns/coredns/releases/tag/v1.14.7) |
| pause | `3.10.2` | 僅在其他 active Markdown 範例中明確出現；刻意保留 kubeadm 固定值。 |

另外，`myapp:*`、`legacy-app:*`、`registry.example.com/*`、`postgresql-proxy:*`、`metrics/prometheus-adapter:*`、`atuvenie/mounttest:1.0` 與內部範例儲存庫等，都是佔位或情境專用映像，不是本手冊維護的上游元件版本；除非範例改為實際部署教學，否則不可用上游版本號替換。舊 Azure GPU Device Plugin 範例已移至[封存檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/troubleshooting/cloud/azure-gpu-device-plugin.md)，不屬於本次現行內容稽核。其他未標籤 `nginx`、`busybox` 及教學用 `:latest` 也不是可重現的版本 pin，並未假裝是固定版本。測試用第三方 `sz-pg-oam-docker-hub-001.tendcloud.com/library/hello:v1` 與 `atuvenie/mounttest:1.0` 也不是本手冊維護的上游元件。

## 明確限制與使用方式

- 「最新穩定上游版本」只說明發布排序，不代表與 Kubernetes v1.37 相容、不會移動的映像 digest、最佳維護系列或本手冊建議部署。NGINX stable 1.30 與 mainline 1.31.6 是刻意區分的維護線；BusyBox 1.38.0、TensorFlow 2.22.0 RC、PostgreSQL 19 beta、Ubuntu 26.10 development 均排除。
- 不將 etcd 3.7.2、CoreDNS 1.14.7 等上游新版替換 kubeadm v1.37.1 固定值 etcd 3.7.0、CoreDNS 1.14.6、pause 3.10.2。RKE2／k0s 同樣依各自發行文件保留版本組合。
- 本報告未覆寫 [component-versions.md](component-versions.md) 歷史快照，也未將找不到官方 v1.37 支援矩陣的項目描述為已支援。相容性判讀仍依該矩陣逐項列示。
- 本次僅進行唯讀來源檢視與本機文件修改；沒有安裝器、叢集、registry push 或其他外部寫入操作。

## 新主題追蹤補充（2026-10-06）

本報告的 2026-10-05 稽核範圍與結果仍是歷史記錄；以下補充不表示重新執行全部 Release API、映像檔查詢或既有相容性審查。新主題整合時發現，凍結矩陣已有 Argo Workflows v4.1.4（2026-09-18）記錄，但機器追蹤清單未列出該儲存庫；現已補入清單。該版本未找到肯定的 Kubernetes v1.37 相容矩陣。

- Longhorn v1.13.0（2026-09-29）及 chart 1.13.0 已加入機器追蹤清單。上游發行說明要求 Kubernetes 至少為 v1.34；這只是最低版本要求，不代表通過所有平台、核心、CNI 或硬體組合的認證。未確認該版本對本手冊 v1.37.1 部署的供應商認證。[發行說明](https://github.com/longhorn/longhorn/releases/tag/v1.13.0) · [chart](https://github.com/longhorn/longhorn/blob/v1.13.0/chart/Chart.yaml)
- KubeVirt v1.9.0（2026-07-30）是截點時核實到的最高穩定版，已加入機器追蹤清單。上游已發布的 v1.10.0-alpha.0 屬預發布版，不列為穩定基準；已查閱的正式資料沒有聲明支援 Kubernetes v1.37。[發行版](https://github.com/kubevirt/kubevirt/releases/tag/v1.9.0)
- Kubeflow Community Distribution 26.03.1（2026-06-15）包含多個各自獨立版本化的專案，例如 Pipelines 2.16.1、Trainer 2.2.0、Istio 1.30.1、cert-manager 1.20.2、Dex 2.45.1 與 Notebooks v1.11.0。發行說明提到 Kubernetes 1.36 CI，但未說明支援 v1.37。由於此發行版採 CalVer，且包含不同版本序列的產品，本次未將單一 Kubeflow 版本冒充為 SemVer 元件加入自動追蹤清單。[發行說明](https://github.com/kubeflow/community-distribution/releases/tag/26.03.1)
- Argo CD v3.5.3 的版本化測試表列出 Kubernetes 1.33–1.36，未列 v1.37；不更動其版本基準。[測試版本表](https://github.com/argoproj/argo-cd/blob/v3.5.3/docs/operator-manual/tested-kubernetes-versions.md)。Cilium、Istio 未因新增章節而自動更換版本。

新增 Argo Workflows、Longhorn 與 KubeVirt 後，機器清單目前有 29 個儲存庫。此補充所列支援狀態只記錄各來源明確說明的範圍；未聲明的組合仍未確認。凍結的 [component-versions.md](component-versions.md) 與原稽核結論均未改寫。