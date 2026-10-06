# HugePages

Kubernetes 將 Linux HugePages 作為可排程資源向 Pod 暴露。v1.37 不需要舊教程中的 `HugePages=true` feature gate，也不需要在每個 Pod 啟動時手工掛載 `hugetlbfs`。節點核心和發行版必須先設定所需頁大小的 HugePages；節點向 Kubernetes 報告可分配容量後，排程器才能放置請求該資源的 Pod。具體的預分配方法依作業系統和節點引導設定而異。
HugePages 的歷史功能演進始於 Kubernetes v1.9 Alpha、v1.10 Beta；舊發行版的 feature gate 和節點操作說明不應沿用到 v1.37。

檢查節點可分配的頁大小和容量：

```bash
kubectl describe node <node-name>
```

清單中的資源名按節點實際提供的頁大小填寫，如 `hugepages-2Mi`。HugePages 不能超額分配；request 與 limit 必須相等（僅給出 limit 時 Kubernetes 會將其作為 request）。

## 範例：申請 2 MiB HugePages

只有當節點已提供至少 100 MiB 的 `hugepages-2Mi` 容量時，下面的 Pod 才能排程。此清單隻演示資源申請和 HugePages-backed `emptyDir`；應用須自行按 Linux HugePages 介面使用掛載的記憶體。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hugepages-example
spec:
  containers:
  - name: example
    image: busybox:1.37.0
    command: ["sh", "-c", "sleep 3600"]
    volumeMounts:
    - name: hugepages
      mountPath: /hugepages
    resources:
      requests:
        cpu: "100m"
        memory: "100Mi"
        hugepages-2Mi: "100Mi"
      limits:
        cpu: "500m"
        memory: "200Mi"
        hugepages-2Mi: "100Mi"
  volumes:
  - name: hugepages
    emptyDir:
      medium: HugePages-2Mi
```

不同 HugePages 頁大小應使用相應的資源名和卷 medium，例如 `hugepages-1Gi` 與 `HugePages-1Gi`。通用 `medium: HugePages` 僅適用於 Pod 請求一種 HugePages 大小。HugePages-backed `emptyDir` 不得超過 Pod 請求的該類 HugePages；同一 Pod 中各容器的隔離與資源額度按各容器資源宣告執行。

使用 `shmget(SHM_HUGETLB)` 的程式還需要與節點 `/proc/sys/vm/hugetlb_shm_group` 匹配的 supplemental group。需要按 namespace 控制用量時，可在 ResourceQuota 中使用 `hugepages-<size>` 資源名。

更多欄位與排程條件見 [Kubernetes Manage HugePages](https://kubernetes.io/docs/tasks/manage-hugepages/scheduling-hugepages/) 和[資源管理文件](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#huge-pages)。
