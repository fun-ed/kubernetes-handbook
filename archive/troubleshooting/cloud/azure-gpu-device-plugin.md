# Azure GPU：旧版 NVIDIA 设备插件配置

> **历史内容，不适用于当前 AKS 或 Kubernetes v1.36/v1.37。** 下方 DaemonSet 使用已移除的 `extensions/v1beta1` API、旧版 NVIDIA Device Plugin 镜像 `nvidia/k8s-device-plugin:1.10`、已弃用的 critical-pod annotation 和旧节点标签。请勿将此清单应用到集群，也不要只替换镜像标签后继续使用。
>
> 原内容摘自本仓库的 [Azure troubleshooting 章节](https://github.com/fun-ed/kubernetes-handbook/blob/main/troubleshooting/cloud/azure.md)，仅保留作为历史记录。本仓库及原文沿用根目录的 [CC BY-NC-SA 4.0 许可](../../../LICENSE)及原有署名。

## 原始问题

旧章节记录的现象是：在 AKS 集群运行 GPU 工作负载时，Pod 无法调度，Node 容量中的 `nvidia.com/gpu` 显示为 0。其原有建议是重新部署下面的 nvidia-gpu 设备插件 DaemonSet。该建议和配置均已过时，不可作为排查或修复步骤。

## 原始清单（仅供历史查阅）

```yaml
apiVersion: extensions/v1beta1
kind: DaemonSet
metadata:
  labels:
    kubernetes.io/cluster-service: "true"
  name: nvidia-device-plugin
  namespace: kube-system
spec:
  template:
    metadata:
      # Mark this pod as a critical add-on; when enabled, the critical add-on scheduler
      # reserves resources for critical add-on pods so that they can be rescheduled after
      # a failure.  This annotation works in tandem with the toleration below.
      annotations:
        scheduler.alpha.kubernetes.io/critical-pod: ""
      labels:
        name: nvidia-device-plugin-ds
    spec:
      tolerations:
      # Allow this pod to be rescheduled while the node is in "critical add-ons only" mode.
      # This, along with the annotation above marks this pod as a critical add-on.
      - key: CriticalAddonsOnly
        operator: Exists
      containers:
      - image: nvidia/k8s-device-plugin:1.10
        name: nvidia-device-plugin-ctr
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
        volumeMounts:
          - name: device-plugin
            mountPath: /var/lib/kubelet/device-plugins
      volumes:
        - name: device-plugin
          hostPath:
            path: /var/lib/kubelet/device-plugins
      nodeSelector:
        beta.kubernetes.io/os: linux
        accelerator: nvidia
```

## 当前排查入口

请从当前版的 [Kubernetes GPU 工作负载指南](../../../setup/addon-list/gpu.md)开始，按与集群版本、节点操作系统、GPU 型号、驱动和 AKS 管理方式相匹配的说明处理。AKS 支持的 GPU 节点池、驱动和设备插件流程以 [Microsoft Learn 的 AKS GPU 官方说明](https://learn.microsoft.com/en-us/azure/aks/use-nvidia-gpu)为准；不要从本归档清单推断当前安装方式。
