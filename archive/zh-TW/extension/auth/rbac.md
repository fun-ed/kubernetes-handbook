# RBAC 不安全歷史範例（封存）

> 以下為歷史權限範例，包含可能將 cluster-admin 授予所有 ServiceAccount 的命令；不得在叢集執行。

## ABAC 遷移範例（不安全的歷史說明）

以下內容只用於說明舊 ABAC 叢集與 RBAC 叢集的權限差異，不是遷移操作步驟。ABAC 規則可能授予寬泛權限；在多個授權器組成的鏈中，任一授權器允許請求時，請求就會獲准，RBAC 不會收窄 ABAC 已允許的權限。新設定應使用 RBAC 並授予應用所需的最小權限。

下面的命令是舊版範例，**不安全且已過時，請勿執行**。它使用 `nginx:latest` 和 `curl -k`（跳過 TLS 證書校驗），也假設 Pod 能讀取長期有效的 ServiceAccount Token。現代叢集通常為 Pod 投射可輪換的短期權杖，應用仍須獲得相應授權。

```bash
# HISTORICAL AND UNSAFE. Do not run this example.
$ kubectl run nginx --image=nginx:latest
$ kubectl exec -it $(kubectl get pods -o jsonpath='{.items[0].metadata.name}') bash
$ apt-get update && apt-get install -y curl
$ curl -ik \
  -H "Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
  https://kubernetes/api/v1/namespaces/default/pods
```

## 寬泛的 cluster-admin 繫結（不安全的歷史範例）

將 `cluster-admin` 授予 `system:serviceaccounts` 會讓所有名稱空間中的所有 ServiceAccount 都獲得叢集管理員權限。**這會造成嚴重的安全風險，以下命令僅作歷史記錄，切勿在叢集中執行。**

```bash
# HISTORICAL AND UNSAFE. Do not run this example.
kubectl create clusterrolebinding permissive-binding \
  --clusterrole=cluster-admin \
  --user=admin \
  --user=kubelet \
  --group=system:serviceaccounts
```
