# Kubernetes 容器调试

容器镜像可能不包含 shell 或诊断工具。对运行在 Kubernetes 中的 Pod，优先使用 `kubectl logs`、`kubectl describe`、`kubectl exec` 与 ephemeral debug container；不要假定集群节点通过 Docker Engine 管理容器。现代节点使用 CRI runtime，旧 dockershim 已移除。

## 调试正在运行的容器

在支持的 runtime 上向现有 Pod 添加临时调试容器：

```bash
kubectl debug -it pod/<pod-name> \
  --image=busybox:1.36.1 \
  --target=<container-name> -- sh
```

`--target` 需要 runtime 支持进程命名空间目标；若不可用，查看 Pod 日志/事件，或使用下方副本调试方式。Ephemeral container 与原 Pod 共用网络上下文，并作为 Pod spec 的一部分留存；不要把敏感数据复制到非受信任镜像，也不要为方便排错默认授予 `SYS_ADMIN` 或 privileged 权限。

## CrashLoop / 无法启动的容器

对于反复崩溃或无法 `exec` 的容器，可创建调试副本：

```bash
kubectl debug <pod-name> -it \
  --copy-to=<debug-pod-name> \
  --container=debugger \
  --image=busybox:1.36.1 -- /bin/sh
```

副本可能继承原 Pod 的卷、环境变量、ServiceAccount 或 Secret 挂载。先检查复制出的 spec，避免把生产凭据暴露给调试容器；确认完成后删除调试副本。

## 常用检查

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name> --all-containers
kubectl logs <pod-name> -c <container-name> --previous
kubectl exec -it <pod-name> -c <container-name> -- sh
kubectl get events --sort-by=.lastTimestamp
```

若应用容器缺少 shell，使用官方 [kubectl debug 指南](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/)选择 ephemeral container 或副本模式。请按集群授权、Pod Security Admission 与 audit policy 管理调试权限并记录操作。

## 本地 Docker 容器

原文的 Docker daemon、共享 container PID/network namespace、Alpine 3.5 和手工 `SYS_ADMIN`/`SYS_PTRACE` 示例只适用于本机 Docker Engine 调试，且有较高权限风险；它们不适用于 CRI 管理的 Kubernetes Pod。不要把 `docker run --pid=container:...` 当作 Kubernetes 工作负载的调试命令。
