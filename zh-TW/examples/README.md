# Kubernetes 範例

這些資訊清單以 Kubernetes v1.37.1 為目標。它們是教學範例，不是可一次安裝的完整堆疊：請勿套用整個目錄。檢查各範例的註解與必要條件後，再從中挑選個別檔案，套用至可拋棄式叢集。

核心 Kubernetes 元件的版本固定資訊與來源佐證，請參閱
[`../setup/component-versions.md`](../setup/component-versions.md)。

## 套用前先驗證

對內建資源，請使用 v1.37.1 測試叢集及伺服器端 dry-run：

```sh
kubectl --context "$KUBE_CONTEXT" apply --dry-run=server -f examples/deployment.yaml
```

此操作會根據該叢集的 API 進行驗證，但不會持久化物件。它仍需要存取 API，也可能呼叫准入 Webhook。也可以使用
`kubeconform -strict -kubernetes-version 1.37.1 <manifest>` 進行離線結構描述驗證。自訂資源需要 CRD 結構描述（或已安裝的 CRD，才能進行伺服器端驗證），而需要功能閘門的範例則必須啟用相關功能。這兩種檢查都無法證明工作負載所需的外部映像檔、憑證、儲存空間或服務確實存在。

## 有額外需求的範例

- `hpa.yaml` 和 `hpa-memory.yaml` 的目標是 `deployment.yaml` 中的 `nginx` Deployment，並需要可正常運作的 metrics API，通常是 metrics-server。此 Deployment 包含 CPU 與記憶體 requests。
- `network-policy/` 需要會強制執行 NetworkPolicy 的 CNI；其中允許存取與不允許存取的 Pod，是一次性的連線能力檢查。
- `service.yaml` 會選取標籤為 `app: nginx` 的 Pod；其第二個連接埠也需要有應用程式在容器連接埠 8080 上接聽。
- `indexed-job-with-backoff.yaml` 和 `job-success-policy-v1.33.yaml` 使用的 Job 功能，在 v1.37.1 中已穩定並預設啟用。
- `lifecycle-v1.33.yaml` 混用穩定的生命週期 sleep 範例與仍處於 alpha 階段的 `stopSignal`；後者需要 `ContainerStopSignals` 功能閘門。除非叢集中負責處理 Pod 的元件已啟用此閘門，否則請略過這些資源。
- `user-namespace.yaml` 使用穩定版的 Pod 使用者命名空間（`hostUsers: false`，自 v1.36 起穩定）；它需要支援使用者命名空間的 Linux 叢集。其中的 ConfigMap、Secret、PVC 和自訂映像檔範例包含佔位值或外部必要條件。PostgreSQL 18 範例會將資料儲存在 `/var/lib/postgresql`。
- `seccomp.yaml` 需要在每個符合條件的節點上，於 `/var/lib/kubelet/seccomp/prevent-chmod` 提供隨附的 `prevent-chmod` 設定檔。
- `calico/calico-packet-logs.yaml` 是 Calico 專用的自訂資源與 DaemonSet：請使用已設定 CRD 與記錄功能的 Calico 3.33.0。其選擇性啟用政策只會選取帶有 `packet-log-demo` 標籤的端點。套用前請審慎新增此標籤；符合條件的 TCP/UDP 輸入與輸出流量會被記錄並允許通過。
- `service-without-selector.yaml` 示範手動管理 EndpointSlice。請將僅供文件範例使用的 `192.0.2.10` 位址，替換為用戶端可連線的位址。
- 舊版通用 RDP LoadBalancer 範例已封存，因為連接埠 3389 可能會公開至網際網路；請只使用供應商專用的私人存取控制。[歷史資訊清單](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/examples/rdp.yaml)不是目前的部署指引。
- `multi-container-patterns.yaml` 是五種多容器模式的教學範本；自訂應用程式／代理程式映像檔及參照的 ConfigMap、Secret、Service 為佔位項目；其中固定版本的 NGINX、Fluent Bit、Alpine、BusyBox 標籤則是實際映像檔。使用 sidecar-init 範例前，請替換僅供文件使用的 Git 儲存庫網址。原指標配接器區塊已移除，因其映像檔標籤無法取得，且 Kubernetes SIGS 的指標配接器並不會將 JSON 檔轉成 Prometheus 指標；請參閱[已封存的原始版本](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/examples/multi-container-patterns.yaml)。
- 舊版 Windows projected volume 資訊清單已封存；其自訂 `atuvenie/mounttest:1.0` 映像檔最後更新於 2018 年，Windows 基礎映像檔版本未能證實可搭配目前的 Windows 節點。請參閱官方 [projected volume 概念](https://kubernetes.io/docs/concepts/storage/projected-volumes)與 [Windows 容器／節點相容性說明](https://kubernetes.io/docs/concepts/windows/intro/)。
- `ssh.yaml` 是使用主機網路的偵錯 Shell，不是 SSH 伺服器。請替換節點名稱，並在可信任的叢集上使用 `kubectl exec -it node-debug-shell -- /bin/sh`。
- `host-volume.yaml` 要求所選節點上已存在 `/data`。`netns-volume.yaml` 使用主機網路、主機命名空間及具特權的容器；僅可在可拋棄式且可信任的節點上使用。
- `admin-service-account.yaml` 會授予實際上的 cluster-admin 權限。請避免在共用或正式環境叢集中建立此帳戶。
- `evaluate-pod-creation.sh` 會建立並刪除 Pod 和 Service。請先檢查此指令碼，並且僅在隔離的測試叢集中使用。

## 歷史範例

標記為 `HISTORICAL:` 的範例已移出目前的驗證根目錄。其中包括 Kubernetes v1.13 kube-bench 工作，以及供應商專用的 NodeLocal DNS 設定。原始路徑、檔案與原因請參閱[封存索引](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/index.md)；請勿將它們作為 Kubernetes v1.36/v1.37 的預設設定套用。

## 映像檔版本固定

NGINX stable 版本固定為 `1.30.5`，於 2026-09-15 發布，並包含官方
[1.30 變更記錄](https://nginx.org/en/CHANGES-1.30)中記載的安全性修正 CVE-2026-90439。下列公開映像檔標籤已於 2026-10-05 檢查。NGINX 1.31.6 是較新的 mainline 標籤，不能取代 stable 1.30 系列；BusyBox 上游明確將 1.38.0 標示為 unstable，因此最新穩定版仍固定為 1.37.0。相較於 `latest`，標籤能提供更高的可重現性，但並非摘要雜湊鎖定；若部署要求不可變的成品，也請固定映像檔摘要。

| 映像檔系列 | 使用的標籤 | 上游來源 |
| --- | --- | --- |
| NGINX | `1.30.5` | [NGINX 官方映像檔](https://hub.docker.com/_/nginx)；[1.30 stable 變更記錄](https://nginx.org/en/CHANGES-1.30) |
| 非特權 NGINX | `1.30.5-alpine3.24` | [NGINX 非特權映像檔](https://hub.docker.com/r/nginxinc/nginx-unprivileged)；[1.30 stable 變更記錄](https://nginx.org/en/CHANGES-1.30) |
| Alpine | `3.24.2` | [Alpine 官方映像檔](https://hub.docker.com/_/alpine)；[3.24.2 stable 發行版本（2026-09-17）](https://www.alpinelinux.org/posts/Alpine-3.21.8-3.22.6-3.23.6-3.24.2-released.html) |
| BusyBox | `1.37.0` | [BusyBox 穩定版發行記錄](https://busybox.net/news.html)（1.38.0 標示為 unstable） |
| Python | `3.14.8-slim-trixie` | [Python 官方映像檔](https://hub.docker.com/_/python)；[3.14.8 發行版本（2026-09-30）](https://www.python.org/downloads/release/python-3148/) |
| Redis | `8.10.2` | [Redis 官方映像檔](https://hub.docker.com/_/redis) |
| PostgreSQL | `18.6-alpine3.24` | [PostgreSQL 官方映像檔](https://hub.docker.com/_/postgres) |
| TensorFlow | `2.21.0` | [TensorFlow Docker 映像檔](https://hub.docker.com/r/tensorflow/tensorflow) |
| Fluent Bit | `5.1.3` | [容器映像檔文件](https://docs.fluentbit.io/manual/installation/downloads/docker)；[上游 5.1.3 發行版本（2026-10-01）](https://github.com/fluent/fluent-bit/releases/tag/v5.1.3) |
| NodeLocal DNS 快取 | `1.26.8`（已封存的供應商專用資訊清單） | Registry 標籤可解析；OCI index 列出 linux/amd64、arm64、arm/v7、ppc64le 與 s390x。[Manifest index](https://registry.k8s.io/v2/dns/k8s-dns-node-cache/manifests/1.26.8) |
| Ubuntu | `26.04` | [Ubuntu 官方映像檔](https://hub.docker.com/_/ubuntu) |
| Kubernetes echoserver | `registry.k8s.io/echoserver:1.10` | Registry manifest 可解析為 linux/amd64；此處僅確認標籤可用，不代表仍受維護或具工作負載支援。[Manifest](https://registry.k8s.io/v2/echoserver/manifests/1.10)；[原始碼](https://github.com/kubernetes/kubernetes/tree/master/test/images/echoserver) |