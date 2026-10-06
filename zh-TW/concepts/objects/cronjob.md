# CronJob

CronJob 即定時任務，就類似於 Linux 系統的 crontab，在指定的時間週期執行指定的任務。

## API 版本

| API version | 狀態 |
| :--- | :--- |
| `batch/v1` | 當前版本；v1.21 起穩定 |
| `batch/v1beta1`、`batch/v2alpha1` | 歷史版本，已從當前 Kubernetes 版本移除 |

## CronJob Spec

* `.spec.schedule` 指定任務執行週期，格式同 [Cron](https://en.wikipedia.org/wiki/Cron)
* `.spec.jobTemplate` 指定需要執行的任務，格式同 [Job](job.md)
* `.spec.startingDeadlineSeconds` 指定任務開始的截止期限
* `.spec.concurrencyPolicy` 指定任務的並行策略，支援 Allow、Forbid 和 Replace 三個選項

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

## 參考文件

* [Cron Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
