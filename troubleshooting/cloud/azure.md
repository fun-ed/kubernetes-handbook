# Azure／AKS 排错

本页以 Kubernetes v1.36／v1.37 为基准，整理可从 Kubernetes API 与受支持的 Azure 工具进行的只读初查。AKS 托管控制平面、AKS 节点、使用外部 Azure Cloud Controller Manager 的自管集群，其组件与可访问日志不同；请勿将一种部署方式的 Pod 名称、标签、Cloud Provider 配置或修复步骤套用到另一种环境。

旧版 Azure in-tree cloud provider、ServiceNodeExclusion alpha feature gate、旧式 Service Principal 凭证命令与旧 AKS 隧道／Periscope 操作已移至[历史归档](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/troubleshooting/cloud/azure.md)。该文件只供追溯，不是当前修复流程。

## LoadBalancer Service 一直 Pending 或无法连接

先检查 Service 的事件、地址、端口与流量策略；以下命令只读取 Kubernetes API：

```bash
NAMESPACE='<namespace>'
SERVICE='<service-name>'
kubectl describe service "$SERVICE" -n "$NAMESPACE"
kubectl get service "$SERVICE" -n "$NAMESPACE" -o yaml
kubectl get endpointslices -n "$NAMESPACE" -l "kubernetes.io/service-name=$SERVICE" -o wide
kubectl get pods -n "$NAMESPACE" -o wide
```

若没有可用的 EndpointSlice 后端，先检查 Service selector、Pod readiness 与 targetPort；若有后端但外部仍无法连接，核对 AKS Load Balancer SKU／前端 IP、探测状态、NSG／路由及所用流量策略，并从集群内与外部客户端分别测试。`externalTrafficPolicy: Local` 等设置会影响节点是否有本地就绪端点及探测结果；不要只凭单一 NodePort 测试判定整个 Load Balancer 故障。根据 AKS 集群版本查看 Azure 控制平面事件与诊断数据；托管控制平面日志不一定能通过 `kubectl logs kube-controller-manager` 访问。

AKS 当前负载均衡器设置与排错请依 [Azure Kubernetes Service 文档](https://learn.microsoft.com/azure/aks/configure-load-balancer-standard)及[AKS 疑难排解](https://learn.microsoft.com/azure/aks/troubleshooting)核对。不要直接编辑云端 NSG、路由表或负载均衡器作为排错捷径；先确认集群／Service 配置及组织变更流程。

## Pod 到 Pod、Service 或 Azure 资源的连接异常

```bash
kubectl get nodes -o wide
kubectl -n kube-system get pods -o wide
kubectl get networkpolicies -A
kubectl get services -A
kubectl get endpointslices -A
```

比对故障 Pod 与目的端的 Node、Pod IP、Service 端口及相关 NetworkPolicy。AKS 网络模式、CNI、Pod／Service CIDR 和网络插件版本会改变数据包路径；在获准的节点管理通道检查对应 CNI 日志与 Azure 网络诊断数据。不要套用旧版 Azure CNI/kubenet 假设、手动添加 Pod CIDR 路由或停用主机防火墙。

## Node 未注册、NotReady 或云端初始化未完成

```bash
kubectl get nodes -o wide
kubectl describe node '<node-name>'
kubectl get events -A --sort-by=.metadata.creationTimestamp
```

检查 Node Conditions、taint 和 Events，并根据集群管理方式查看 AKS 节点健康／升级状态；自管集群则经批准的节点管理通道检查 kubelet、CRI runtime 与外部 cloud-controller-manager 的日志和权限。`node.cloudprovider.kubernetes.io/uninitialized` taint 表示云端初始化尚未完成，但不代表应手动移除 taint 或任意新增 toleration。托管控制平面不一定公开 CCM Pod；不要使用旧版 selector 查找假设存在的组件。

## AKS GPU Node 未报告 `nvidia.com/gpu`

```bash
kubectl describe node '<gpu-node>'
kubectl get pods -A -o wide
```

确认 `Capacity`／`Allocatable`、Node Pool VM SKU／OS、GPU 管理模式，以及 AKS 管理的驱动或所选 GPU Operator／Device Plugin 状态。依 [AKS NVIDIA GPU 指南](https://learn.microsoft.com/azure/aks/use-nvidia-gpu)与本手册[GPU 工作负载指南](../../setup/addon-list/gpu.md)逐一比对，不要部署旧版设备插件清单或只替换镜像标签。旧版 `extensions/v1beta1` DaemonSet 示例另存于[历史归档](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/troubleshooting/cloud/azure-gpu-device-plugin.md)，不可套用。

## 凭证、配额及 Azure 控制平面错误

使用 AKS 时，先从 Azure Portal／Azure CLI 的集群 Activity log、诊断设置与支持工具查看失败操作、配额及身份标识错误。自管 Azure cloud-controller-manager／CSI driver 则检查该组件使用的托管标识或工作负载身份、最小必要 RBAC、API 错误码及资源提供程序配额。不要在命令行、日志或 YAML 中输入／输出 client secret、SAS token 或 bearer token；凭证轮换依照 Microsoft 当前身份标识文档与组织的密钥管理流程执行。

## 持久卷问题

先检查 PVC、PV、StorageClass 与 CSI 组件事件；Azure Disk／Azure Files 的当前故障排查见[Azure Disk CSI](../pv/azuredisk.md)及[Azure Files CSI](../pv/azurefile.md)指南。AKS 存储类型与云端操作还须核对当前的 [AKS 疑难排解文档](https://learn.microsoft.com/azure/aks/troubleshooting)。

## 参考文档

- [AKS 疑难排解](https://learn.microsoft.com/azure/aks/troubleshooting)
- [AKS Standard Load Balancer](https://learn.microsoft.com/azure/aks/configure-load-balancer-standard)
- [AKS NVIDIA GPU 工作负载](https://learn.microsoft.com/azure/aks/use-nvidia-gpu)
- [Kubernetes Service](https://kubernetes.io/docs/concepts/services-networking/service/)
