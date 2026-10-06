# Kubernetes v1.37.1 组件与镜像现状盘点

**盘点截点：2026-10-05。** 本报告以同日冻结的[组件版本快照](component-versions.md)为历史基线，不覆写该快照。本次通过 GitHub Releases API（经 `gh api` 只读查询）重新检查追踪清单中的 26 项，以及快照中其余有 GitHub Release 的组件；只纳入非 draft、非 prerelease 的稳定发布，并按各项目的版本序比较。除下文记录的 Spinnaker 稳定版更新及 CSI sidecar 发布日期差异外，快照中有 GitHub Release 的组件版本与本次结果一致。Kubernetes 支持判断仍沿用快照，不能由「上游最新」推导为 v1.37 相容。没有 GitHub Release 的组件以官方 tag、版本记录或政策来源分别核对；alpha、beta、RC、draft 及明确标示为 unstable 的版本不算稳定版。上游版本、Kubernetes／kubeadm 固定值与发行版随附值分别列出。

## 盘点范围与结论

- 已通过 GitHub Releases API 查核 `component-watchlist.json` 中的 26 个追踪项，以及 `component-versions.md` 中其余有 GitHub Release 的组件；只将 `draft=false`、`prerelease=false` 的稳定发布纳入比较。多产品／多维护分支项目使用版本序或项目发布序比较。快照中有 GitHub Release 的组件版本均与本次结果相同，Spinnaker 除外；发布日期差异另列。官方来源和人工兼容性结论见[组件版本清单](component-versions.md)。上游新版本不代表支持 v1.37。
- 扫描 `examples/`、`manifests/` 后，共找到 **58 个 image 声明，分布于 32 个文件**。本次使用 Docker Hub v2 `GET https://hub.docker.com/v2/repositories/{namespace}/{repository}/tags/{tag}` 直接查询 12 个样例 tag：nginx 1.30.5／1.31.6、nginx-unprivileged 1.30.5-alpine3.24、Alpine 3.24.2、BusyBox 1.37.0／1.38.0、Python 3.14.8-slim-trixie、Redis 8.10.2、PostgreSQL 18.6-alpine3.24、TensorFlow 2.21.0、Fluent Bit 5.1.3、Ubuntu 26.04。并非所有镜像 tag 或非 Hub registry 都重新查询，不能据此声称所有样例镜像都是最新。未更动 `examples/` / `manifests/` 中的 image pin。另在活跃 Markdown 教学中找到 **16** 处使用 BusyBox 1.36 / 1.36.1 的旧版参照，已更新为稳定 tag `1.37.0`；繁体中文副本的 **16** 处也已同步。
- 所有 Docker Hub 标签只固定 tag，非不可变镜像 digest。官方 Hub 在 **2026-10-05** 对 `nginxinc/nginx-unprivileged:1.30.5-alpine3.24` 显示同一标签于当日更新；标签未变但内容可能变更，不能将 tag 当成 digest 锁定。
- K0s 与 RKE2 是独立发行版基线：k0s 最新稳定版使用 Kubernetes 1.36.4，并非 v1.37；RKE2 最新稳定版已使用 Kubernetes v1.37.1。它们的内含 etcd、runtime 及附加组件不是 kubeadm 固定值，详见下节。
- 未改动历史归档中的版本固定值、`en/` 或依赖项目；另外将 Azure 排障文档中的过期 GPU 清单抽出至归档。没有安装工具或操作集群。

## 目前组件版本逐项盘点

表内列出本次核实的截点最新稳定版，官方发布链接可查其发布信息；「待确认」或「不兼容」等 Kubernetes 支持判断维持[原矩阵](component-versions.md)中的人工结论，不因上游版本较新而改写。Spinnaker 的 stable release 标签 `spinnaker-release-2026.3.0`（2026-09-07）按数值版本序高于 2026.1.3；冻结矩阵的版本仍作为历史记录保留。CSI sidecar 的版本相同，但 GitHub API `published_at` 分别显示 external-provisioner v6.3.0 为 2026-06-04，以及 external-attacher v4.13.0、node-driver-registrar v2.18.0、livenessprobe v2.20.0 均为 2026-09-04；冻结矩阵中这些日期不同，故此处以 API 日期为准，不改写历史快照。

### 核心组件、运行时与构建前提

| 组件 | 截点最新稳定版（本次核实） | 官方来源 |
| --- | --- | --- |
| Kubernetes | v1.37.1 | [发布](https://github.com/kubernetes/kubernetes/releases/tag/v1.37.1) |
| etcd | v3.7.2 | [发布](https://github.com/etcd-io/etcd/releases/tag/v3.7.2) |
| CoreDNS | v1.14.7 | [发布](https://github.com/coredns/coredns/releases/tag/v1.14.7) |
| containerd | v2.4.1 | [发布](https://github.com/containerd/containerd/releases/tag/v2.4.1) |
| runc | v1.5.2 | [发布](https://github.com/opencontainers/runc/releases/tag/v1.5.2) |
| CRI-O | v1.37.2 | [发布](https://github.com/cri-o/cri-o/releases/tag/v1.37.2) |
| cri-dockerd | v0.4.7 | [发布](https://github.com/Mirantis/cri-dockerd/releases/tag/v0.4.7) |
| cri-tools / crictl | v1.37.0 | [发布](https://github.com/kubernetes-sigs/cri-tools/releases/tag/v1.37.0) |
| CNI plugins | v1.9.1 | [发布](https://github.com/containernetworking/plugins/releases/tag/v1.9.1) |
| pause sandbox image | 没有独立稳定版日期；kubeadm 固定 3.10.2 | [Kubernetes v1.37.1 dependencies](https://github.com/kubernetes/kubernetes/blob/v1.37.1/build/dependencies.yaml) |
| Go | go1.27.1 | [官方版本记录](https://go.dev/doc/devel/release) |

### 可安装插件与附加组件

| 组件 | 截点最新稳定版（本次核实） | 官方来源 |
| --- | --- | --- |
| Metrics Server | v0.9.0（chart 3.14.0） | [应用发布](https://github.com/kubernetes-sigs/metrics-server/releases/tag/v0.9.0) · [chart](https://github.com/kubernetes-sigs/metrics-server/releases/tag/metrics-server-helm-chart-3.14.0) |
| node-problem-detector | v1.36.0 | [发布](https://github.com/kubernetes/node-problem-detector/releases/tag/v1.36.0) |
| CSI external-provisioner | v6.3.0 | [发布](https://github.com/kubernetes-csi/external-provisioner/releases/tag/v6.3.0) |
| CSI external-attacher | v4.13.0 | [发布](https://github.com/kubernetes-csi/external-attacher/releases/tag/v4.13.0) |
| CSI external-snapshotter | v8.6.0 | [发布](https://github.com/kubernetes-csi/external-snapshotter/releases/tag/v8.6.0) |
| CSI external-resizer | v2.3.0 | [发布](https://github.com/kubernetes-csi/external-resizer/releases/tag/v2.3.0) |
| CSI node-driver-registrar | v2.18.0 | [发布](https://github.com/kubernetes-csi/node-driver-registrar/releases/tag/v2.18.0) |
| CSI livenessprobe | v2.20.0 | [发布](https://github.com/kubernetes-csi/livenessprobe/releases/tag/v2.20.0) |
| Gateway API | v1.6.2 | [发布](https://github.com/kubernetes-sigs/gateway-api/releases/tag/v1.6.2) |
| Cilium | v1.20.2 | [发布](https://github.com/cilium/cilium/releases/tag/v1.20.2) |
| Calico | v3.33.0 | [发布](https://github.com/projectcalico/calico/releases/tag/v3.33.0) |
| Flannel | v0.28.9 | [发布](https://github.com/flannel-io/flannel/releases/tag/v0.28.9) |
| Traefik | v3.7.13（chart 41.6.1） | [发布](https://github.com/traefik/traefik/releases/tag/v3.7.13) · [chart index](https://traefik.github.io/charts/index.yaml) |
| Envoy Gateway | v1.9.2 | [发布](https://github.com/envoyproxy/gateway/releases/tag/v1.9.2) |
| Istio | 1.31.1 | [发布](https://github.com/istio/istio/releases/tag/1.31.1) |
| Prometheus | v3.15.0 | [发布](https://github.com/prometheus/prometheus/releases/tag/v3.15.0) |
| Grafana | v13.2.3 | [发布](https://github.com/grafana/grafana/releases/tag/v13.2.3) |
| cert-manager | v1.21.2 | [发布](https://github.com/cert-manager/cert-manager/releases/tag/v1.21.2) |
| kube-state-metrics | v2.20.0 | [发布](https://github.com/kubernetes/kube-state-metrics/releases/tag/v2.20.0) |
| Cluster Autoscaler | v1.36.1 | [发布](https://github.com/kubernetes/autoscaler/releases/tag/cluster-autoscaler-1.36.1) |
| ip-masq-agent | v2.12.6（tag，非 GitHub Release） | [Tag](https://github.com/kubernetes-sigs/ip-masq-agent/tree/v2.12.6) |
| Kured | v1.23.0 | [发布](https://github.com/kubereboot/kured/releases/tag/1.23.0) |
| NVIDIA GPU Operator | v26.7.1 | [发布](https://github.com/NVIDIA/gpu-operator/releases/tag/v26.7.1) |
| NVIDIA Kubernetes Device Plugin | v0.20.1 | [发布](https://github.com/NVIDIA/k8s-device-plugin/releases/tag/v0.20.1) |
| Fluentd | v1.19.4 | [发布](https://github.com/fluent/fluentd/releases/tag/v1.19.4) |
| Elasticsearch | v9.5.4 | [发布](https://github.com/elastic/elasticsearch/releases/tag/v9.5.4) |
| Kibana | v9.5.4 | [发布](https://github.com/elastic/kibana/releases/tag/v9.5.4) |
| Argo Workflows | v4.1.4 | [发布](https://github.com/argoproj/argo-workflows/releases/tag/v4.1.4) |
| Argo CD | v3.5.3 | [发布](https://github.com/argoproj/argo-cd/releases/tag/v3.5.3) |
| Apache Spark | 4.2.0 | [发布公告](https://spark.apache.org/news/spark-4-2-0-released.html) |
| Flux | v2.9.6 | [发布](https://github.com/fluxcd/flux2/releases/tag/v2.9.6) |
| Velero | v1.18.4 | [发布](https://github.com/velero-io/velero/releases/tag/v1.18.4) |
| Linkerd OSS | edge-26.9.3（无 OSS stable artifact） | [Release policy](https://linkerd.io/releases/) · [edge](https://github.com/linkerd/linkerd2/releases/tag/edge-26.9.3) |

### 用户端与本机集群工具

| 组件 | 截点最新稳定版（本次核实） | 官方来源 |
| --- | --- | --- |
| Helm | v4.3.0 | [发布](https://github.com/helm/helm/releases/tag/v4.3.0) |
| kind | v0.33.0 | [发布](https://github.com/kubernetes-sigs/kind/releases/tag/v0.33.0) |
| minikube | v1.39.0 | [发布](https://github.com/kubernetes/minikube/releases/tag/v1.39.0) |
| client-go | v0.37.1（tag，无 GitHub Release） | [Tag](https://github.com/kubernetes/client-go/tree/v0.37.1) |
| Skaffold | v2.25.0 | [发布](https://github.com/GoogleContainerTools/skaffold/releases/tag/v2.25.0) |
| Kompose | v1.38.0 | [发布](https://github.com/kubernetes/kompose/releases/tag/v1.38.0) |
| Draft | v0.17.15 | [发布](https://github.com/Azure/draft/releases/tag/v0.17.15) |
| Jenkins X CLI | v3.17.111 | [发布](https://github.com/jenkins-x/jx/releases/tag/v3.17.111) |
| Spinnaker | 2026.3.0（2026-09-07） | [稳定版发布](https://github.com/spinnaker/spinnaker/releases/tag/spinnaker-release-2026.3.0) |
| kOps | v1.36.2 | [发布](https://github.com/kubernetes/kops/releases/tag/v1.36.2) |
| Kubespray | v2.32.0 | [发布](https://github.com/kubernetes-sigs/kubespray/releases/tag/v2.32.0) |
| OVN-Kubernetes | v1.4.0 | [发布](https://github.com/ovn-kubernetes/ovn-kubernetes/releases/tag/v1.4.0) |
| SR-IOV Network Operator | v1.6.0 | [发布](https://github.com/k8snetworkplumbingwg/sriov-network-operator/releases/tag/v1.6.0) |
| k0s | v1.36.4+k0s.1 | [官方发布](https://github.com/k0sproject/k0s/releases/tag/v1.36.4%2Bk0s.1) |
| RKE2 | v1.37.1+rke2r1 | [官方发布](https://github.com/rancher/rke2/releases/tag/v1.37.1%2Brke2r1) |

### 发行版固定值：不可由上游最新版替换

| 发行版 | 截点前最新稳定版与内含 Kubernetes | 其他核对的内含版本 | 结果 |
| --- | --- | --- | --- |
| k0s | `v1.36.4+k0s.1`，Kubernetes `v1.36.4`；2026-09-19T21:23:36Z 发布 | containerd `2.3.5`；release note 另列 Traefik `v3.7.13-k0s.0`、Helm `v3.21.4`、Kine `v0.16.5` | 上游 latest Release API 的 stable tag，`draft=false`、`prerelease=false`。不支持手册宣称 v1.37；保留其自身 bundled pins。[Release](https://github.com/k0sproject/k0s/releases/tag/v1.36.4%2Bk0s.1) · [版本文档](https://docs.k0sproject.io/v1.36.4+k0s.1/) |
| RKE2 | `v1.37.1+rke2r1`，Kubernetes `v1.37.1`；2026-09-30T16:49:06Z 发布 | etcd `v3.7.1-k3s3`、containerd `v2.3.4-k3s1`、runc `v1.4.3`、CoreDNS `1.14.7`、metrics-server `0.9.0`、Traefik `3.7.13`；预设 Canal 带 Flannel `0.28.9` / Calico `3.32.2` | Releases API 的 stable tag，`draft=false`、`prerelease=false`；SUSE 支持矩阵含 v1.37。这些发行版 pins 与 kubeadm pins 各自独立。[Release](https://github.com/rancher/rke2/releases/tag/v1.37.1%2Brke2r1) · [支持矩阵](https://www.suse.com/suse-rke2/support-matrix/all-supported-versions/rke2-v1-37/) |

GitHub Release 标签中的 `+k0s.N`、`+rke2rN` 是稳定的发行版重建修订后缀，不是预发布后缀。追踪程序逐页读取这两个发行版的 Releases API，依照 Kubernetes 三段版本及数值修订序比较（例如 r10 大于 r9）；未知或格式错误的发行版后缀会报告错误，不会改变一般 SemVer build metadata 的排序规则。

## 样例与镜像 pins

`examples/` 与 `manifests/` 的 **58 个 image 声明／32 个文件**盘点结果如下。可变标签、占位镜像与第三方重新包装镜像另列为例外；「tag 可查到」不等于适合更换或已验证可在 v1.37 执行。

| 镜像系列 | 目前 pin | 截点盘点结果与来源 |
| --- | --- | --- |
| NGINX stable | `1.30.5` | 保留 stable 1.30 线；Hub 较新 `1.31.6` 是 mainline，不是 stable 更新。 [Hub](https://hub.docker.com/_/nginx) · [1.30 changelog](https://nginx.org/en/CHANGES-1.30) |
| 非特权 NGINX | `1.30.5-alpine3.24` | tag 存在；2026-10-05 Hub 记录此 tag 当日更新，tag 可能移动，若需不可变引用应另外固定 digest。[Hub](https://hub.docker.com/r/nginxinc/nginx-unprivileged) |
| Alpine | `3.24.2` | 稳定 3.24 系列版本。[Hub](https://hub.docker.com/_/alpine) · [官方发行公告](https://www.alpinelinux.org/posts/Alpine-3.21.8-3.22.6-3.23.6-3.24.2-released.html) |
| BusyBox | `1.37.0` | 保留。上游将 1.38.0 明确标为 **unstable**，故不替换为较高但非稳定的版本。[公告](https://busybox.net/news.html) · [Hub tags](https://hub.docker.com/_/busybox) |
| Python | `3.14.8-slim-trixie` | tag 存在；Python 3.14.8 为截点前稳定版。[Hub](https://hub.docker.com/_/python) · [Python 发布](https://www.python.org/downloads/release/python-3148/) |
| Redis | `8.10.2` | 本次查询确认 tag 存在；未重新审查 Redis 稳定版发行序列。[Hub](https://hub.docker.com/_/redis) |
| PostgreSQL | `18.6-alpine3.24` | 本次查询确认 tag 存在；19 beta 不作为稳定版替代，稳定版基线沿用冻结快照。[Hub](https://hub.docker.com/_/postgres) |
| TensorFlow | `2.21.0` | tag 存在；2.22.0 为 RC，排除。[Hub](https://hub.docker.com/r/tensorflow/tensorflow) |
| Fluent Bit | `5.1.3` | 与截点前最新稳定 release 相同。[release](https://github.com/fluent/fluent-bit/releases/tag/v5.1.3) · [镜像文档](https://docs.fluentbit.io/manual/installation/downloads/docker) |
| NodeLocal DNS cache | `1.26.8` | Kubernetes DNS 仓库有 `1.26.8` tag，但没有对应 GitHub Release；最新 stable Release 仍为 `v1.26.0`（2025-05-13）。只读 registry GET 于 2026-10-05 确认镜像 tag 可解析，OCI index digest 为 `sha256:bc6e64e2c85956af2fcc0aa720086410d41b4f31f378c9a92646fecc85cd4739`，平台含 linux/amd64、arm64、arm/v7、ppc64le、s390x。这只验证镜像 tag/平台存在，不证明仍受维护或兼容 v1.37。[tag](https://github.com/kubernetes/dns/tree/1.26.8) · [Releases](https://github.com/kubernetes/dns/releases) · [registry index](https://registry.k8s.io/v2/dns/k8s-dns-node-cache/manifests/1.26.8) |
| Ubuntu | `26.04` | 保留稳定 LTS pin；26.10/development 标签不算稳定版替代。[Hub](https://hub.docker.com/_/ubuntu) |
| Kubernetes echoserver | `registry.k8s.io/echoserver:1.10` | 只读 registry GET 于 2026-10-05 确认 tag 可解析，manifest digest 为 `sha256:cb5c1bddd1b5665e1867a7fa1b5fa843a47ee433bbb75d4293888b71def53229`，映像平台为 linux/amd64。此处只确认 tag 存在，不代表仍受维护或具 v1.37 工作負載支援。[manifest](https://registry.k8s.io/v2/echoserver/manifests/1.10) · [原始碼](https://github.com/kubernetes/kubernetes/tree/master/test/images/echoserver) |
| Metrics Server | `v0.9.0` | manifest tag 与冻结快照记录的稳定版相同；本次未重新查询 release API。v1.37 支持与 API 边界见矩阵。[manifest image](https://github.com/kubernetes-sigs/metrics-server/releases/tag/v0.9.0) |
| node-problem-detector | `v1.36.0` | manifest tag 与冻结快照记录的稳定版相同；本次未重新查询 release API。Kubernetes `dependencies.yaml` 中的测试镜像 `v1.35.2` 是独立固定值，非 kubeadm addon。[release](https://github.com/kubernetes/node-problem-detector/releases/tag/v1.36.0) · [Kubernetes dependencies](https://github.com/kubernetes/kubernetes/blob/v1.37.1/build/dependencies.yaml) |
| Traefik | `v3.7.13` | manifest tag 与冻结快照记录的稳定版相同；本次未重新查询 release API，也不代表 Traefik 声明兼容 v1.37。[release](https://github.com/traefik/traefik/releases/tag/v3.7.13) |
| CoreDNS | `v1.14.6` | 刻意保留 kubeadm v1.37.1 预设值；上游已有 `v1.14.7` 不会覆盖 kubeadm pin。[kubeadm dependencies](https://github.com/kubernetes/kubernetes/blob/v1.37.1/build/dependencies.yaml) · [上游 release](https://github.com/coredns/coredns/releases/tag/v1.14.7) |
| pause | `3.10.2` | 仅在其他 active Markdown 范例中明确出现；刻意保留 kubeadm 固定值。 |

此外，`myapp:*`、`legacy-app:*`、`registry.example.com/*`、`postgresql-proxy:*`、`metrics/prometheus-adapter:*`、`atuvenie/mounttest:1.0` 与内部示例仓库等是占位或情境专用镜像，并非本手册维护的上游组件版本；除非其范例改成实际部署教学，否则不可用上游版本号代替。旧 Azure GPU Device Plugin 示例已移至[归档文件](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/troubleshooting/cloud/azure-gpu-device-plugin.md)，不属于本次当前内容盘点。其他未标签 `nginx`、`busybox` 及教学用 `:latest` 也不是可重现版本 pins，并未伪装成固定版本。测试用第三方 `sz-pg-oam-docker-hub-001.tendcloud.com/library/hello:v1` 及 `atuvenie/mounttest:1.0` 也不属于本手册维护的上游组件。

## 明确限制与使用方式

- 「最新稳定上游版本」只回答发布排序；不代表 Kubernetes v1.37 兼容、不会移动的镜像 digest、最佳维护分支或此手册推荐部署。NGINX stable 1.30 与 mainline 1.31.6 是刻意分开的维护线；BusyBox 1.38.0、TensorFlow 2.22.0 RC、PostgreSQL 19 beta、Ubuntu 26.10 development 均排除。
- 不将 etcd 3.7.2、CoreDNS 1.14.7 等上游新版替换 kubeadm v1.37.1 固定值 etcd 3.7.0、CoreDNS 1.14.6、pause 3.10.2。RKE2/k0s 也使用各自发布文档的版本组合。
- 本报告未覆写 [component-versions.md](component-versions.md) 历史快照，也没有把未找到官方 v1.37 支持矩阵的项目描述为已支持。支持判读依该矩阵逐项列示。
- 本次仅进行唯读来源检视与本机文档变更；没有安装器、集群、registry push 或其他外部写入操作。

## 新主题追踪补充（2026-10-06）

本报告的 2026-10-05 盘点范围与结果仍是历史记录；以下补充不表示重跑全部 Release API、镜像查询或既有兼容性审查。新主题整合时发现，冻结矩阵已有 Argo Workflows v4.1.4（2026-09-18）记录，但机器追踪清单未列该仓库；现已补入清单。该版本未找到肯定的 Kubernetes v1.37 兼容矩阵。

- Longhorn v1.13.0（2026-09-29）及 chart 1.13.0 已加入机器追踪清单。上游发布说明要求 Kubernetes 至少为 v1.34；这只是最低版本要求，不是对所有平台、内核、CNI 或硬件组合的认证。没有核实该版本对本手册 v1.37.1 部署的供应商认证。[发布说明](https://github.com/longhorn/longhorn/releases/tag/v1.13.0) · [chart](https://github.com/longhorn/longhorn/blob/v1.13.0/chart/Chart.yaml)
- KubeVirt v1.9.0（2026-07-30）是截点时核实到的最高稳定版，已加入机器追踪清单。上游已发布的 v1.10.0-alpha.0 属预发布版，不作为稳定基线；所查正式资料没有声明 Kubernetes v1.37 支持。[发布](https://github.com/kubevirt/kubevirt/releases/tag/v1.9.0)
- Kubeflow Community Distribution 26.03.1（2026-06-15）包含多个分别版本化的项目，例如 Pipelines 2.16.1、Trainer 2.2.0、Istio 1.30.1、cert-manager 1.20.2、Dex 2.45.1 与 Notebooks v1.11.0。发行说明提到 Kubernetes 1.36 CI，但没有说明支持 v1.37。由于此发行版采用 CalVer 且包含不同版本序列的产品，本次没有将单一 Kubeflow 版本伪装成 SemVer 组件加入自动追踪清单。[发行说明](https://github.com/kubeflow/community-distribution/releases/tag/26.03.1)
- Argo CD v3.5.3 的版本化测试表列出 Kubernetes 1.33–1.36，未列 v1.37；不更动其版本基线。[测试版本表](https://github.com/argoproj/argo-cd/blob/v3.5.3/docs/operator-manual/tested-kubernetes-versions.md)。Cilium、Istio 未因新增章节而自动更换版本。

新增 Argo Workflows、Longhorn 与 KubeVirt 后，机器清单现有 29 个仓库。补充所列支持状态只记录各自来源明确说明的范围；没有声明的组合仍属未确认。冻结的 [component-versions.md](component-versions.md) 与原盘点结论均未改写。