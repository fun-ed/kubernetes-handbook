# 分布式负载测试

原示例依赖 TenxCloud 私有镜像、旧 Google Container Registry 镜像、ReplicationController，以及 `serviceName/servicePort` 形式的旧 Ingress schema。它们没有按 Kubernetes v1.37 验证，且旧镜像来源不能视为当前可用；这些命令和 YAML 不应直接部署，已从操作步骤中移除。

[Locust 官方文档](https://docs.locust.io/en/stable/running-distributed.html)描述当前 master/worker 分布式模型。为 Kubernetes 设计测试时，按所选 Locust release 和应用镜像创建 master 与 worker Deployment，并使用集群内 Service 供 worker 访问 master、另一个 Service 指向被测应用。只在需要从集群外打开 Web UI 时配置入口；新建 Ingress 应使用 `networking.k8s.io/v1`，并先部署/验证受支持的 Ingress controller。

可按以下顺序准备测试，不要将未经核实的旧清单应用到集群：

1. 选定受支持的 Locust release，构建并发布固定版本或 digest 的 master/worker 镜像；应用镜像、依赖、用户脚本和目标主机配置应一致。
2. 在隔离的测试环境中部署工作负载，配置最小权限、请求/限制和 worker 到 master 的网络策略；测试 UI 不应未经认证暴露到公网。
3. 根据容量逐步扩展 worker Deployment。将 `locust-worker` 替换为实际 Deployment 名称：

   ```bash
   kubectl scale deployment/locust-worker --replicas=5 -n load-test
   kubectl rollout status deployment/locust-worker -n load-test
   ```

4. 记录 Kubernetes、被测应用和 Locust 的版本/digest、worker 数量、节点规格、资源设置、测试数据及目标并发量。逐步增加负载并设置请求速率、持续时间和停止条件，避免把负载误指向生产服务或压垮共享集群。

旧章中关于 Traefik v1 Ingress 字段的说明也已过时；当前 Ingress 示例见[Traefik 安装章节](traefik-ingress-installation.md)。实际运行参数、master/worker flags、容器镜像和用户脚本的分发方式以[Locust 当前文档](https://docs.locust.io/en/stable/running-distributed.html)为准。
