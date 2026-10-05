# Apache Spark on Kubernetes

本章旧版内容描述的是 Spark 2.2、KubeSpark 旧镜像，以及 Kubernetes 示例仓库中的手工 Spark Master/ReplicationController 部署。那些镜像、API 和命令不是 Kubernetes v1.37 的安装指南，已从当前操作步骤中移除。
原章提到 Spark 2.3 的 Kubernetes 原生提交方式，同时保留了 Spark 2.2/KubeSpark 镜像示例；这两个历史路径不能混合使用。

Spark 可通过 Kubernetes 原生调度后端运行 Driver 和 Executor Pod。Apache Spark 4.2.0 当前上游文档要求 Kubernetes v1.34 或更新版本，因此 Kubernetes v1.37.1 满足其文档中的最低版本要求；仍应核对实际客户端依赖、发行版和插件的兼容性。[Spark 官方 Kubernetes 指南](https://spark.apache.org/docs/latest/running-on-kubernetes.html)

## 提交 Spark 应用

使用与提交工具版本一致的 Spark 镜像，并确保镜像中包含 Spark 本身、应用依赖和提交的 `local:///` 路径所指向的 JAR。Apache Spark 发布了 `apache/spark:<version>` 镜像；生产工作负载应按组织的供应链策略固定镜像 digest。

下面以 Spark 4.2.0 的 SparkPi 为模板。替换 API server 地址、namespace 和镜像内真实存在的 JAR 路径；提交端凭据和 Driver 的 Kubernetes 权限都必须按最小权限配置。

```bash
K8S_API_SERVER="https://api.example.com:6443" # 替换为目标集群地址
JAR_IN_IMAGE="/opt/spark/examples/jars/spark-examples_2.13-4.2.0.jar" # 确认该文件包含在所用镜像中

./bin/spark-submit \
  --master "k8s://$K8S_API_SERVER" \
  --deploy-mode cluster \
  --name spark-pi \
  --class org.apache.spark.examples.SparkPi \
  --conf spark.executor.instances=5 \
  --conf spark.kubernetes.namespace=research \
  --conf spark.kubernetes.container.image=apache/spark:4.2.0 \
  "local://$JAR_IN_IMAGE"
```

`local:///` URI 指向 Driver/Executor 容器镜像中的本地路径，而不是提交端磁盘上的路径。Driver 使用的 Kubernetes 身份需要有运行该应用所需的 Pod、Service、ConfigMap 等 namespace 级权限；不要为了方便绑定 `cluster-admin`。提交环境还须能访问 API server，集群 DNS 和节点到镜像仓库的网络应正常。

```bash
kubectl get pods -n research
```

Spark 直接创建 Driver 和 Executor Pod，不需要先安装本章旧示例中的 Spark Master Service。容器镜像的 Java、Scala、Spark 和应用二进制版本必须相互兼容；自定义 Dockerfile、认证、存储、Secrets、网络、安全和资源配置请按对应 Spark release 的[完整文档](https://spark.apache.org/docs/latest/running-on-kubernetes.html)核对。
