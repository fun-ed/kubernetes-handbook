# Istio 安装与数据平面选择

截至 2026-10-05，Istio **1.31.1** 是本手册资料截点前的最新稳定版。Istio 官方支持表只列出 Kubernetes **1.32–1.36**，没有列出 Kubernetes v1.37。由于本手册目标为 Kubernetes v1.37.1，当前没有上游兼容证据支持在该集群安装 Istio 1.31.1。以下命令只供受支持版本的测试集群评估；请等待 Istio 官方支持表覆盖 v1.37 或取得平台供应商的明确兼容声明。

来源：[Istio 1.31.1 发布页](https://github.com/istio/istio/releases/tag/1.31.1)、[支持版本表](https://istio.io/latest/docs/releases/supported-releases/)。

## 下载固定版本并检查客户端

Istio 官方 release archive 包含 `istioctl`、配置 profile 和示例。下面将下载器固定到 1.31.1，而不是自动跟随未来的最新版本：

```bash
ISTIO_VERSION=1.31.1
curl -L https://istio.io/downloadIstio | ISTIO_VERSION="$ISTIO_VERSION" sh -
cd "istio-${ISTIO_VERSION}"
export PATH="$PWD/bin:$PATH"
istioctl version
```

首次在任何目标集群安装前，查看该版本支持表、平台说明和 profile。不要把当前 Kubernetes v1.37.1 集群当作上述受支持测试环境。

## Sidecar 模式

在官方支持的测试集群中安装 Istio 后，为要注入 Envoy 的 namespace 设置标签。`istioctl install` 会安装控制平面与所选 profile 的组件：

```bash
istioctl install --set profile=demo --skip-confirmation
kubectl label namespace default istio-injection=enabled
```

后续在 `default` namespace 创建的适用 Pod 会由 webhook 注入 Envoy sidecar。应用部署前确认镜像、探针、端口命名和资源请求；启用注入不会替代服务身份、授权策略或网络策略配置。`demo` profile 只用于评估，不是生产 profile。

## Ambient 模式

在支持的集群中使用 ambient profile 安装节点代理 `ztunnel` 和 CNI 组件，然后显式标记 namespace：

```bash
istioctl install --set profile=ambient --skip-confirmation
kubectl label namespace default istio.io/dataplane-mode=ambient
```

Ambient 模式不向每个 Pod 注入 sidecar。`ztunnel` 提供 L4 mesh 功能；需要 L7 路由或策略的服务还需部署 waypoint。按[ambient 指南](https://istio.io/latest/docs/ambient/getting-started/)安装和配置 waypoint，并核对当前 release 的支持范围。

## 检查与清理

```bash
istioctl analyze --all-namespaces
istioctl proxy-status
kubectl get pods -n istio-system
```

评估结束后按当前版本的官方[卸载说明](https://istio.io/latest/docs/setup/install/istioctl/#uninstall-istio)清理。不要直接删除 `istio-system` 中单个控制平面组件来完成卸载。

旧的 Helm 2/Tiller 安装命令、Mixer、Galley、`istioctl kube-inject`、servicegraph 和旧 ServiceGraph 页面已从当前安装流程移除；对应技术说明只作为早期 Istio 历史材料保留在各自页面。
