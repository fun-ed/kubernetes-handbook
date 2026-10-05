# 排错工具

## Kubernetes API 与工作负载

优先使用 `kubectl` 查看 API 对象、Events 和容器日志：

```bash
kubectl get pods -A -o wide
kubectl describe pod <pod-name> -n <namespace>
kubectl get events -n <namespace> --sort-by=.metadata.creationTimestamp
kubectl logs <pod-name> -n <namespace> -c <container-name> --previous --timestamps
```

确认 Namespace 和容器名称后再执行命令。排查 Service 时检查 selector、EndpointSlices 及 NetworkPolicy；不要假设数据平面由某一种 kube-proxy 模式实现。

## CRI 运行时与节点

容器运行时排错使用 CRI 工具，而不是 Docker 专用命令。`crictl` 应在授权的节点管理环境中运行，并配置为连接该节点实际使用的 CRI endpoint：

```bash
sudo crictl info
sudo crictl pods
sudo crictl ps -a
sudo crictl images
```

不同运行时、发行版的服务名称、socket 和日志路径不同；按其维护文档检查。节点系统服务可通过发行版提供的受控访问方式读取 `journalctl` 日志。不要在普通工作负载中挂载 Docker socket、CRI socket、主机根目录或 `/var/lib` 运行时数据目录。

## 网络与性能工具

* `tcpdump`：在获准的节点或受控调试环境中分析网络流量；抓包可能包含敏感数据。
* `iproute2`、iptables/nftables 或 IPVS 工具：仅用于检查集群实际采用的数据平面实现；不要跨实现复制规则或直接修改主机转发策略。
* `perf` 和受维护的性能分析工具：需要节点权限，使用前遵循组织的权限、审计和数据保留要求。

安装或使用第三方代理、eBPF 探针、可视化 Dashboard 前，应确认其项目仍受维护、兼容当前 Kubernetes/内核/CRI 版本、权限满足最小化原则，并使用经过审核的部署流程。

## 节点调试安全

Kubelet、CNI 和内核日志通常需要节点级权限。优先使用云服务商或发行版提供的受控管理通道；不要为排错给节点分配公网 IP，也不要下载并直接运行未经审核的 `kubectl-node-shell` 插件。`kubectl debug node` 等调试流程可能创建高权限资源，只能在获得授权并理解其主机访问范围后使用。

## 历史工具说明

本页旧版 Docker Socket、sysdig 的 `apt-key` 安装命令及 Weave Scope 公开 `LoadBalancer` 安装清单不适合作为 Kubernetes v1.37 的通用建议。不要照搬旧清单；评估第三方工具时，查阅其当前维护状态、发行版本和安全说明。

更多信息请参阅 [kubectl 参考](https://kubernetes.io/docs/reference/kubectl/)和 [集群排错指南](https://kubernetes.io/docs/tasks/debug/debug-cluster/)。
