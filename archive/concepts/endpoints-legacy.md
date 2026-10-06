# 歷史 Endpoints API 範例

本頁保存從 `concepts/objects/service.md` 移出的 `Endpoints` API 與 client-go 呼叫範例。Kubernetes v1.33 起 Endpoints API 已棄用；新程式應使用 `discovery.k8s.io/v1` EndpointSlices。官方說明：[Endpoints deprecation](https://kubernetes.io/blog/2025/04/24/endpoints-deprecation/)。

```yaml
apiVersion: v1
kind: Endpoints
metadata:
  name: my-service
subsets:
- addresses:
  - ip: 1.2.3.4
  ports:
  - port: 9376
```

```go
endpoints, err := clientset.CoreV1().Endpoints(namespace).Get(ctx, serviceName, metav1.GetOptions{})
```
