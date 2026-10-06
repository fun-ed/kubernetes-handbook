# Apache Spark on Kubernetes

本章舊版內容描述的是 Spark 2.2、KubeSpark 舊映像檔，以及 Kubernetes 範例儲存庫中的手工 Spark Master/ReplicationController 部署。那些映像檔、API 和命令不是 Kubernetes v1.37 的安裝指南，已從當前操作步驟中移除。
原章提到 Spark 2.3 的 Kubernetes 原生提交方式，同時保留了 Spark 2.2/KubeSpark 映像檔範例；這兩個歷史路徑不能混合使用。

Spark 可透過 Kubernetes 原生排程後端執行 Driver 和 Executor Pod。Apache Spark 4.2.0 當前上游文件要求 Kubernetes v1.34 或更新版本，因此 Kubernetes v1.37.1 滿足其文件中的最低版本要求；仍應核對實際客戶端依賴、發行版和外掛的相容性。[Spark 官方 Kubernetes 指南](https://spark.apache.org/docs/latest/running-on-kubernetes.html)

## 提交 Spark 應用

使用與提交工具版本一致的 Spark 映像檔，並確保映像檔中包含 Spark 本身、應用依賴和提交的 `local:///` 路徑所指向的 JAR。Apache Spark 釋出了 `apache/spark:<version>` 映像檔；生產工作負載應按組織的供應鏈策略固定映像檔 digest。

下面以 Spark 4.2.0 的 SparkPi 為模板。替換 API server 位址、namespace 和映像檔內真實存在的 JAR 路徑；提交端憑證和 Driver 的 Kubernetes 權限都必須按最小權限設定。

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

`local:///` URI 指向 Driver/Executor 容器映像檔中的本地路徑，而不是提交端磁碟上的路徑。Driver 使用的 Kubernetes 身分需要有執行該應用所需的 Pod、Service、ConfigMap 等 namespace 級權限；不要為了方便綁定 `cluster-admin`。提交環境還須能存取 API server，叢集 DNS 和節點到映像檔登錄站的網路應正常。

```bash
kubectl get pods -n research
```

Spark 直接建立 Driver 和 Executor Pod，不需要先安裝本章舊範例中的 Spark Master Service。容器映像檔的 Java、Scala、Spark 和應用二進位版本必須相互相容；自定義 Dockerfile、認證、儲存、Secrets、網路、安全和資源設定請按對應 Spark release 的[完整文件](https://spark.apache.org/docs/latest/running-on-kubernetes.html)核對。
