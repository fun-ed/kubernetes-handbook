# 云服务商扩展

云服务商集成让 Kubernetes 控制平面可以查询云实例、配置云路由，或为 `LoadBalancer` 类型的 Service 创建负载均衡器。自 Kubernetes 1.29 起，核心组件默认不再启用内置云服务商实现；集群需要使用云服务商维护的外部集成。详见 [Cloud Controller Manager 管理文档](https://kubernetes.io/docs/tasks/administer-cluster/running-cloud-controller/)和[云服务商集成变更说明](https://kubernetes.io/blog/2023/12/14/cloud-provider-integration-changes/)。

## 组件职责与配置

使用外部 Cloud Controller Manager（CCM）时，各组件的设置并不相同：

| 组件 | 外部云服务商配置 |
| --- | --- |
| `kubelet` | 设置 `--cloud-provider=external`。节点注册时会带有 `node.cloudprovider.kubernetes.io/uninitialized:NoSchedule` 污点，等待外部 CCM 初始化节点。 |
| `kube-controller-manager` | 设置 `--cloud-provider=external`，将云服务商控制逻辑交给外部 CCM。其他 Kubernetes 控制器仍由该组件运行。 |
| `kube-apiserver` | 外部 CCM 部署不需要设置云服务商选项。不要再配置 `PersistentVolumeLabel` 准入插件；Kubernetes 1.37 的准入控制器列表中已不包含该插件。 |
| 外部 CCM | 由云服务商单独提供并部署。CCM 使用其实现要求的服务商名称、配置文件、凭证和其他参数，不能把 `external` 当作 CCM 的服务商名称。 |

`PersistentVolumeClaimResize` 是 API Server 的准入控制器，不是 CCM 的功能。外部 CCM 通常负责其实现的节点、Service 负载均衡器和路由控制器；支持的功能由具体服务商决定。CCM 不替代 Kubernetes 的卷控制器，也不负责 CSI 驱动的卷生命周期。持久卷集成应按云服务商的 CSI 驱动文档配置。

Kubernetes 自带的控制平面容器镜像应使用与集群版本相符的发布版本。例如，运行 Kubernetes v1.37.1 时，Kubernetes 提供的控制平面镜像应取自 v1.37.1 发布版。外部 CCM 的镜像和版本由云服务商维护，不保证与 Kubernetes 版本号相同。按服务商兼容性说明选择版本，并在部署中固定到服务商发布的版本或镜像摘要；不要使用 `latest`，也不要把 Kubernetes 版本号当作 CCM 的版本号。

## 节点初始化与 CCM 部署

启用 `--cloud-provider=external` 后，节点在 CCM 完成初始化前带有 `NoSchedule` 污点。CCM 必须能在启动阶段运行，并由节点控制器填入服务商所需的节点信息后移除该污点。若 CCM 以 Pod 运行，其服务账号、RBAC、节点选择器和容忍度都应按服务商提供的部署清单配置。只有在网络初始化顺序要求时才使用 `hostNetwork`，不要把它当作通用必需项。

下面仅展示 Pod 模板中的相关字段，不是可直接部署的清单。将镜像占位符替换为服务商明确支持、与集群版本兼容的镜像引用。多副本部署时按服务商文档配置 Leader Election。

```yaml
spec:
  template:
    spec:
      serviceAccountName: cloud-controller-manager
      tolerations:
      - key: node.cloudprovider.kubernetes.io/uninitialized
        operator: Exists
        effect: NoSchedule
      containers:
      - name: cloud-controller-manager
        image: ${PROVIDER_CCM_IMAGE}
        args:
        - --cloud-provider=<provider-name>
        - --leader-elect=true
```

如果集群的控制平面节点还有其他污点，CCM Pod 也需要服务商清单指定的对应容忍度。不要直接授予 `cluster-admin`；使用云服务商为 CCM 提供的最小权限 RBAC 规则。

## 开发 Cloud Controller Manager

自定义 CCM 需要实现 Kubernetes [cloud-provider 接口](https://github.com/kubernetes/cloud-provider/blob/release-1.37/cloud.go)，再按[开发 Cloud Controller Manager 文档](https://kubernetes.io/docs/tasks/administer-cluster/developing-cloud-controller-manager/)构建和部署。服务商实现、配置参数与发布镜像由各自项目维护。
