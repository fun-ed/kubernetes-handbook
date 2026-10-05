# kubeadm

`kubeadm` 是构建符合 Kubernetes 最佳实践的集群的工具，负责引导控制平面、配置基础组件，并生成 Node 加入集群所需的凭证与命令。具体安装步骤和约束取决于操作系统、CRI 运行时与网络插件；Kubernetes v1.37.1 集群请使用对应版本的 [kubeadm 安装与管理指南](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/)。

## 组件与集群初始化

`kubeadm` 集群需要兼容的 CRI 运行时、kubelet、kubeadm、控制平面组件以及一个能执行 NetworkPolicy 的 CNI 网络插件。kubeadm 会检查环境并部署控制平面静态 Pod；集群 DNS 通常由 CoreDNS 提供。CNI 具体配置由网络插件负责。

不要套用本页旧版的 Docker Engine/Frakti、手写 CNI bridge 配置、未固定的 Flannel/Weave 清单、Calico v3.1 安装 URL 或 `--kubernetes-version stable` 示例。网络插件选择和 Pod CIDR 必须与发行版及集群网络规划相符。

## Node 加入

集群初始化成功后，kubeadm 会输出加入命令。只在目标 Node 上使用该集群当前生成的命令，并按官方指南保护临时 bootstrap token 与发现凭证；不要从 kubeadm token 列表中筛选后复用长期凭证。

## 重置与移除

`kubeadm reset` 会更改本机集群状态，并不保证清理 CNI、用户数据、持久卷、云资源或其他集群外资源。执行前应确认目标节点、备份需求及发行版清理流程；不要把它当作通用的集群卸载命令。

* [kubeadm 安装集群](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)
* [kubeadm 参考文档](https://kubernetes.io/docs/reference/setup-tools/kubeadm/)
* [kubeadm 官方源代码](https://github.com/kubernetes/kubernetes/tree/v1.37.1/cmd/kubeadm)
