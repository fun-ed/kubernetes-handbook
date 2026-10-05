# Windows 排错

本章介绍 Windows 容器异常的排错方法。

## 安全访问 Windows Node

Node 管理优先使用云平台控制台、受控 Bastion 或组织批准的远程管理通道。不要把 RDP 3389 端口直接暴露到公网。

如在隔离测试环境中确需通过 Service 转发，可使用 [`examples/rdp.yaml`](../examples/rdp.yaml) 中的无 selector Service 与手工维护的 EndpointSlice。清单中的 `192.0.2.10` 为文档示例地址，应用前必须替换为 Node 的私网 IP；同时在云防火墙或负载均衡器侧将来源限制为可信管理网段：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: rdp-to-node
spec:
  type: LoadBalancer
  ports:
  - name: rdp
    protocol: TCP
    port: 3389
    targetPort: 3389
---
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: rdp-to-node-1
  labels:
    kubernetes.io/service-name: rdp-to-node
    endpointslice.kubernetes.io/managed-by: handbook-manual
addressType: IPv4
endpoints:
- addresses:
  - "192.0.2.10"
ports:
- name: rdp
  protocol: TCP
  port: 3389
```

```bash
kubectl apply -f examples/rdp.yaml
kubectl get service rdp-to-node
kubectl get endpointslices -l kubernetes.io/service-name=rdp-to-node
```

该 EndpointSlice 只记录网络后端，不会验证 Node 的 RDP 服务是否运行，也不会自动限制访问来源。仅在具备私有负载均衡器和网络访问控制的隔离环境中使用此模式。

## Windows 容器镜像与主机版本

Windows 容器镜像必须与 Node 的 Windows 版本和隔离模式兼容。部署前查阅 Microsoft 当前的[容器版本兼容性文档](https://learn.microsoft.com/en-us/virtualization/windowscontainers/deploy-containers/version-compatibility)，并在 `kubectl describe pod` 的 Events 与 kubelet 日志中确认实际错误。

本页旧版 Windows Server 1709/1803 镜像标签是历史记录，不是当前可用镜像建议；不要将这些旧标签用于新集群。

## Windows Pod DNS 或网络异常

先检查 Pod Events、CoreDNS 状态、EndpointSlices、Windows Node 状态以及所用 CNI/kube-proxy 实现的日志：

```bash
kubectl describe pod <pod-name>
kubectl -n kube-system get pods
kubectl -n kube-system get service
kubectl -n kube-system get endpointslices -l kubernetes.io/service-name=kube-dns
kubectl get nodes -o wide
```

Windows 网络依赖主机版本、HNS、网络插件及 Kubernetes 发行版。针对特定版本查阅平台供应商当前的 Windows 网络排错文档；不要直接运行会删除 HNS 网络或策略、重启所有 Node 服务、或将 DNS 服务器改成固定集群 IP 的旧脚本。

## HNS 或 kube-proxy 旧版错误

本节原有的 `KB4089848` 和 Windows 10 1803 安装步骤是 2018 年的历史故障记录，不适用于当前 Windows Server Node。遇到 HNS 或 kube-proxy 错误时，记录 Windows build、Kubernetes/kube-proxy 版本和网络插件版本，并按这些版本对应的 Microsoft 与发行版文档排查；不要下载或安装本页中的旧更新包。

## Windows Pod 无法访问 ServiceAccount Secret

本节所关联的 Moby issue 是旧版 Windows 容器的历史问题。遇到当前故障时，先检查目标 Pod 的投射 token volume、服务账户配置、Windows build 与运行时版本，并参考当前 Kubernetes 与运行时文档，不要仅凭旧版 issue 升级主机。

## Windows Node 的 Service 可达性

从 Windows Pod 与 Node 主机分别测试 Service 的可达性，并检查后端 EndpointSlices、kube-proxy 或替代实现以及 CNI/HNS 日志。Node 主机、Pod 和远程客户端的流量路径可能不同；不要将旧版协议栈限制外推到所有当前网络实现。

## Docker 18.03 / kubelet v1.12 API 版本错误（历史记录）

本节记录的是 Kubernetes v1.12 与 Docker 18.03 的旧版客户端 API 不兼容问题。Docker Engine 已不是 Kubernetes 的内置 CRI 运行时；不要将 `DOCKER_API_VERSION` 环境变量 workaround 用于当前 containerd、CRI-O 或其他 CRI 运行时。

## 参考文档

* [Kubernetes On Windows - Troubleshooting Kubernetes](https://docs.microsoft.com/en-us/virtualization/windowscontainers/kubernetes/common-problems)
* [Debug Networking issues on Windows](https://github.com/microsoft/SDN/tree/master/Kubernetes/windows/debug)

