# CronJob

CronJob 即定时任务，就类似于 Linux 系统的 crontab，在指定的时间周期运行指定的任务。

## API 版本

| API version | 状态 |
| :--- | :--- |
| `batch/v1` | 当前版本；v1.21 起稳定 |
| `batch/v1beta1`、`batch/v2alpha1` | 历史版本，已从当前 Kubernetes 版本移除 |

## CronJob Spec

* `.spec.schedule` 指定任务运行周期，格式同 [Cron](https://en.wikipedia.org/wiki/Cron)
* `.spec.jobTemplate` 指定需要运行的任务，格式同 [Job](job.md)
* `.spec.startingDeadlineSeconds` 指定任务开始的截止期限
* `.spec.concurrencyPolicy` 指定任务的并发策略，支持 Allow、Forbid 和 Replace 三个选项

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: hello
spec:
  schedule: "*/1 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: hello
            image: busybox:1.37.0
            imagePullPolicy: IfNotPresent
            command:
            - /bin/sh
            - -c
            - date; echo Hello from the Kubernetes cluster
          restartPolicy: OnFailure
```

```bash
# kubectl run 当前用于创建 Pod，不用于创建 CronJob。
kubectl create cronjob hello --image=busybox:1.37.0 --schedule="*/1 * * * *" -- \
  /bin/sh -c "date; echo Hello from the Kubernetes cluster"

kubectl get cronjob hello
kubectl get jobs --selector=cronjob-name=hello

# 删除 CronJob 会停止后续调度；是否删除已创建的 Job 取决于级联删除选项。
kubectl delete cronjob hello
```

## 参考文档

* [Cron Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
