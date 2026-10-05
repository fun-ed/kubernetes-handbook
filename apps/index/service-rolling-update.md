# Deployment 滚动升级

Deployment 通过滚动替换 ReplicaSet 中的 Pod 发布新版本。准备兼容的应用版本、健康检查、资源请求与回滚路径后，再更新 Deployment 的 Pod template。

## Kubernetes v1.37 示例

`apps/v1` Deployment 必须包含与 Pod template labels 匹配的 `spec.selector`。将镜像名改为组织实际 registry 中固定版本的应用，并确保 tag/digest 已推送：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello
  namespace: default
spec:
  replicas: 3
  revisionHistoryLimit: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: hello
  template:
    metadata:
      labels:
        app: hello
    spec:
      containers:
        - name: hello
          image: registry.example.com/team/hello:v2
          ports:
            - name: http
              containerPort: 8080
          readinessProbe:
            httpGet:
              path: /
              port: http
            periodSeconds: 5
```

对外流量通过 selector 指向相同标签的 Service；滚动升级不能替代应用级兼容性检查。特别是数据库 schema 变更，应采用新旧版本并存的迁移策略。

```bash
kubectl apply -f deployment.yaml
kubectl rollout status deployment/hello
kubectl rollout history deployment/hello
```

更新镜像时使用已发布、受信任的版本：

```bash
kubectl set image deployment/hello \
  hello=registry.example.com/team/hello:v3
kubectl rollout status deployment/hello
```

发现问题时回滚到上一个 revision，并检查事件、日志和新旧 ReplicaSet：

```bash
kubectl rollout undo deployment/hello
kubectl rollout history deployment/hello
kubectl get replicasets,pods -l app=hello
```

通过 `maxUnavailable` 与 `maxSurge` 控制升级期间的容量。Readiness probe 应只在实例可提供服务时成功；还应设置合理的 `terminationGracePeriodSeconds` 与 `preStop` 行为，保护正在处理的请求。

## 旧示例说明

原章节中的 `extensions/v1beta1` Deployment、未选择器校验的模板、Traefik 旧 `serviceName/servicePort` Ingress、Alpine 3.5 镜像和固定私有测试 registry 均为历史内容，不可直接用于 Kubernetes v1.37。ReplicationController 的旧 `kubectl rollingupdate` 操作也不应作为当前发布方法；新部署优先使用 Deployment。
