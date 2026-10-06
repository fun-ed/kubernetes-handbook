# 云平台排错

公有云托管 Kubernetes 与在云虚拟机上自行部署的集群，在控制平面日志、云身份、网络、负载均衡和 CSI 存储的管理方式上不同。先确定发行版、Kubernetes 版本、网络模式、云控制器／CSI 驱动及其所有者，再按对应云服务商文档排查；不要假设每个云平台都由 kube-controller-manager 自动为所有 Node 配置 Pod 路由。

## 先收集 Kubernetes 侧证据

```bash
kubectl get nodes -o wide
kubectl get events -A --sort-by=.metadata.creationTimestamp
kubectl get services -A
kubectl get endpointslices -A
kubectl get pods -A -o wide
```

按故障类型进一步查看 Node Conditions、Service/PVC 事件、EndpointSlices、NetworkPolicy、CSI 对象与相关工作负载日志。请避免输出云凭证、ServiceAccount token 或 Secret 内容。

## Node 尚未注册或云端初始化未完成

```bash
kubectl describe node '<node-name>'
kubectl get events -A --sort-by=.metadata.creationTimestamp
```

检查 Node Conditions、taint、事件和注册／初始化错误。托管服务通常不允许查看控制平面 Pod 日志；请从云服务商的集群诊断、活动记录及节点管理渠道取得对应证据。外部 cloud-controller-manager 集群才按其发布版文档检查 CCM 部署、启动参数、身份权限和日志。`node.cloudprovider.kubernetes.io/uninitialized` taint 表示云端初始化尚未完成，不应以手动删除 taint 代替修复。

## 网络、Service 与负载均衡

对照 Pod/Node 地址、Service 端口、EndpointSlices、NetworkPolicy 与实际 CNI/Service 数据平面，确认故障发生在集群内、节点间还是云网络边界。云提供商管理的路由、NSG／防火墙、负载均衡探测、IP 配额和私有端点须使用该平台的当前诊断工具及权限流程；不要套用通用假设或直接改写云资源。

## 持久化存储

检查 PVC、PV、StorageClass、VolumeAttachment、CSI driver/controller/node 状态和 Events。核对所选 CSI 驱动的身份权限、区域／拓扑、配额、网络与后端状态；不要将历史 in-tree 插件参数或 Secret 授权示例用于当前 CSI 驱动。

## 云平台专页

- [Azure／AKS 排错](azure.md)
- [Kubernetes 网络排错](../network.md)
- [持久卷排错](../pv/)

不同云平台的控制平面可见度、网络实现和诊断接口各有差异；本章没有列出未经验证的通用云端修复命令。
