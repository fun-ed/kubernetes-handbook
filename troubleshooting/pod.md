# Pod 排错

先明确 Pod 所在的 Namespace 和容器名称，再查看当前配置、Events 与容器日志。Events 通常能区分调度、卷挂载、镜像拉取、沙箱网络和容器启动错误。

```bash
kubectl get pod <pod-name> -n <namespace> -o wide
kubectl describe pod <pod-name> -n <namespace>
kubectl get events -n <namespace> --sort-by=.metadata.creationTimestamp
kubectl logs <pod-name> -n <namespace> -c <container-name> --timestamps
kubectl logs <pod-name> -n <namespace> -c <container-name> --previous --timestamps
```

`--previous` 适用于已重启的容器；如 Pod 有多个容器，必须指定正确的 `-c`。

## Pod 处于 Pending

查看 `kubectl describe pod` 中的调度事件和 PVC 状态。常见原因包括：

* 可分配 CPU、内存、临时存储或扩展资源不足，或 Namespace 的 ResourceQuota/LimitRange 拒绝请求；
* `nodeSelector`、亲和性、污点容忍、拓扑约束或 HostPort 限制没有符合条件的节点；
* 绑定的 PersistentVolumeClaim 尚未绑定或无法挂载。

根据 Events 及相应资源状态调整 Pod 请求或集群配置；不要仅为使 Pod 调度而删除其他工作负载。

## Pod 处于 Waiting、ContainerCreating 或 ImagePullBackOff

首先查看 Pod Events。卷挂载错误应检查 PVC、StorageClass、CSI 驱动和 Secret；沙箱或网络错误应查看目标 Node 上实际 CRI 运行时及 CNI 插件的受控日志。不要根据单条旧 `cni0` 错误就删除网桥、清空 IPAM 状态或重启所有节点网络。

镜像拉取失败时，核对镜像仓库地址、标签/digest、集群到仓库的网络连通性、证书以及 `imagePullSecrets` 是否在正确的 Namespace 中。私有仓库凭证应由 Secret 安全地提供给 Pod；不要把密码写在命令行历史、清单或日志中。

可通过发行版授权的节点访问方式检查实际 CRI runtime，并用 `crictl info`、`crictl images` 及运行时日志辅助诊断。`crictl pull <image>` 是节点运行时拉取连通性检查；除非另行配置凭证，它不会复现 kubelet 使用 Pod `imagePullSecrets` 的身份验证流程，也不能替代 Pod Events。

## Pod 处于 CrashLoopBackOff

使用 `kubectl logs --previous` 查看上一次容器退出前的日志，并检查 `kubectl describe pod` 中的退出码、探针失败、OOMKilled 状态、资源限制和 Events。需要进入容器时，Pod 必须正在运行且允许执行：

```bash
kubectl exec -it <pod-name> -n <namespace> -c <container-name> -- /bin/sh
```

若容器没有 shell 或很快退出，请按集群批准的调试流程使用临时调试容器或调试 Pod；不要为了查看节点日志把 Docker socket、主机根目录或运行时数据目录挂载进普通工作负载。

## Pod 创建失败

检查 API 错误、Namespace ResourceQuota/LimitRange、ConfigMap、Secret、PVC、ServiceAccount/RBAC，以及集群的 [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) 策略。PodSecurityPolicy 已从 Kubernetes 移除，不能用旧 PSP 清单或 admission 插件配置修复当前集群。

## Pod 长时间处于 Terminating 或 Unknown

先检查 Node 是否 Ready、kubelet 是否仍与 API Server 通信、卷是否正在卸载，以及控制器和 Pod finalizers 的所有者。节点失联时，API 对象消失并不等于节点上的进程已停止。

不要常规使用 `--force --grace-period=0` 删除 Pod，也不要手动删除 finalizers。只有在确认原节点已被安全隔离、存储/工作负载不会产生重复写入，并遵循 StatefulSet 或应用自身恢复流程后，才由有权限的管理员考虑强制删除。

## 历史示例说明

本页旧版日志和命令曾依赖 Docker Engine、`docker://` 容器 ID、`/var/lib/docker`、容器化 kubelet 或固定的 CNI 网桥；这些细节不是 Kubernetes v1.37 的通用接口。当前节点检查应使用集群发行版支持的 CRI 工具、CNI/CSI 组件文档和受控节点访问途径。

更多信息请参阅 [Debug Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/) 和 [Troubleshooting Applications](https://kubernetes.io/docs/tasks/debug/debug-application/)。
