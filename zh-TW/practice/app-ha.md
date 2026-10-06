# 應用高可用

## 應用高可用的一般原則

* 應用遵循 [The Twelve-Factor App](https://12factor.net/zh_cn/)
* 使用 Service 和多副本 Pod 部署應用
* 多副本透過反親和性避免單節點故障導致應用異常
* 使用 PodDisruptionBudget 避免驅逐導致的應用不可用
* 使用 preStopHook 和健康檢查探針保證服務平滑更新

## 優雅關閉

為 Pod 設定 terminationGracePeriodSeconds，並透過 preStop 鉤子延遲關閉容器應用以避免 `kubectl drain` 等事件發生時導致的應用中斷：

```yaml
restartPolicy: Always
terminationGracePeriodSeconds: 30
containers:
- image: nginx:1.30.5
  lifecycle:
    preStop:
      exec:
        command: [
          "sh", "-c",
          # Introduce a delay to the shutdown sequence to wait for the
          # pod eviction event to propagate. Then, gracefully shutdown
          # nginx.
          "sleep 5 && /usr/sbin/nginx -s quit",
        ]
```

詳細的原理可以參考下面這個系列文章

* [1. Zero Downtime Server Updates For Your Kubernetes Cluster](https://blog.gruntwork.io/zero-downtime-server-updates-for-your-kubernetes-cluster-902009df5b33)
* [2. Gracefully Shutting Down Pods in a Kubernetes Cluster](https://blog.gruntwork.io/gracefully-shutting-down-pods-in-a-kubernetes-cluster-328aecec90d)
* [3. Delaying Shutdown to Wait for Pod Deletion Propagation](https://blog.gruntwork.io/delaying-shutdown-to-wait-for-pod-deletion-propagation-445f779a8304)
* [4. Avoiding Outages in your Kubernetes Cluster using PodDisruptionBudgets](https://blog.gruntwork.io/avoiding-outages-in-your-kubernetes-cluster-using-poddisruptionbudgets-ef6a4baa5085)

## 參考文件

* [Kubernetes Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
* [Kubernetes PodDisruptionBudget](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)
