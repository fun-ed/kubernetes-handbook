# Kubernetes 容器除錯

容器映像檔可能不包含 shell 或診斷工具。對執行在 Kubernetes 中的 Pod，優先使用 `kubectl logs`、`kubectl describe`、`kubectl exec` 與 ephemeral debug container；不要假定叢集節點透過 Docker Engine 管理容器。現代節點使用 CRI runtime，舊 dockershim 已移除。

## 除錯正在執行的容器

在支援的 runtime 上向現有 Pod 新增臨時除錯容器：

```bash
kubectl debug -it pod/<pod-name> \
  --image=busybox:1.37.0 \
  --target=<container-name> -- sh
```

`--target` 需要 runtime 支援程序命名空間目標；若不可用，檢視 Pod 日誌/事件，或使用下方副本除錯方式。Ephemeral container 與原 Pod 共用網路上下文，並作為 Pod spec 的一部分留存；不要把敏感資料複製到非受信任映像檔，也不要為方便排錯預設授予 `SYS_ADMIN` 或 privileged 權限。

## CrashLoop / 無法啟動的容器

對於反覆崩潰或無法 `exec` 的容器，可建立除錯副本：

```bash
kubectl debug <pod-name> -it \
  --copy-to=<debug-pod-name> \
  --container=debugger \
  --image=busybox:1.37.0 -- /bin/sh
```

副本可能繼承原 Pod 的卷、環境變數、ServiceAccount 或 Secret 掛載。先檢查複製出的 spec，避免把生產憑證暴露給除錯容器；確認完成後刪除除錯副本。

## 常用檢查

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name> --all-containers
kubectl logs <pod-name> -c <container-name> --previous
kubectl exec -it <pod-name> -c <container-name> -- sh
kubectl get events --sort-by=.lastTimestamp
```

若應用容器缺少 shell，使用官方 [kubectl debug 指南](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/)選擇 ephemeral container 或副本模式。請按叢集授權、Pod Security Admission 與 audit policy 管理除錯權限並記錄操作。

## 本地 Docker 容器

原文的 Docker daemon、共享 container PID/network namespace、Alpine 3.5 和手工 `SYS_ADMIN`/`SYS_PTRACE` 範例只適用於本機 Docker Engine 除錯，且有較高權限風險；它們不適用於 CRI 管理的 Kubernetes Pod。不要把 `docker run --pid=container:...` 當作 Kubernetes 工作負載的除錯命令。
