# Pod 排錯

先明確 Pod 所在的 Namespace 和容器名稱，再檢視當前設定、Events 與容器日誌。Events 通常能區分排程、卷掛載、映像檔拉取、沙箱網路和容器啟動錯誤。

```bash
kubectl get pod <pod-name> -n <namespace> -o wide
kubectl describe pod <pod-name> -n <namespace>
kubectl get events -n <namespace> --sort-by=.metadata.creationTimestamp
kubectl logs <pod-name> -n <namespace> -c <container-name> --timestamps
kubectl logs <pod-name> -n <namespace> -c <container-name> --previous --timestamps
```

`--previous` 適用於已重啟的容器；如 Pod 有多個容器，必須指定正確的 `-c`。

## Pod 處於 Pending

檢視 `kubectl describe pod` 中的排程事件和 PVC 狀態。常見原因包括：

* 可分配 CPU、記憶體、臨時儲存或擴充套件資源不足，或 Namespace 的 ResourceQuota/LimitRange 拒絕請求；
* `nodeSelector`、親和性、汙點容忍、拓撲約束或 HostPort 限制沒有符合條件的節點；
* 綁定的 PersistentVolumeClaim 尚未綁定或無法掛載。

根據 Events 及相應資源狀態調整 Pod 請求或叢集設定；不要僅為使 Pod 排程而刪除其他工作負載。

## Pod 處於 Waiting、ContainerCreating 或 ImagePullBackOff

首先檢視 Pod Events。卷掛載錯誤應檢查 PVC、StorageClass、CSI 驅動和 Secret；沙箱或網路錯誤應檢視目標 Node 上實際 CRI 執行時及 CNI 外掛的受控日誌。不要根據單條舊 `cni0` 錯誤就刪除網橋、清空 IPAM 狀態或重啟所有節點網路。

映像檔拉取失敗時，核對映像檔登錄站位址、標籤/digest、叢集到儲存庫的網路連通性、證書以及 `imagePullSecrets` 是否在正確的 Namespace 中。私有儲存庫憑證應由 Secret 安全地提供給 Pod；不要把密碼寫在命令列歷史、清單或日誌中。

可透過發行版授權的節點存取方式檢查實際 CRI runtime，並用 `crictl info`、`crictl images` 及執行時日誌輔助診斷。`crictl pull <image>` 是節點執行時拉取連通性檢查；除非另行設定憑證，它不會復現 kubelet 使用 Pod `imagePullSecrets` 的身分驗證流程，也不能替代 Pod Events。

## Pod 處於 CrashLoopBackOff

使用 `kubectl logs --previous` 檢視上一次容器退出前的日誌，並檢查 `kubectl describe pod` 中的退出碼、探針失敗、OOMKilled 狀態、資源限制和 Events。需要進入容器時，Pod 必須正在執行且允許執行：

```bash
kubectl exec -it <pod-name> -n <namespace> -c <container-name> -- /bin/sh
```

若容器沒有 shell 或很快退出，請按叢集批准的除錯流程使用臨時除錯容器或除錯 Pod；不要為了檢視節點日誌把 Docker socket、主機根目錄或執行時資料目錄掛載進普通工作負載。

## Pod 建立失敗

檢查 API 錯誤、Namespace ResourceQuota/LimitRange、ConfigMap、Secret、PVC、ServiceAccount/RBAC，以及叢集的 [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) 策略。PodSecurityPolicy 已從 Kubernetes 移除，不能用舊 PSP 清單或 admission 外掛設定修復當前叢集。

## Pod 長時間處於 Terminating 或 Unknown

先檢查 Node 是否 Ready、kubelet 是否仍與 API Server 通訊、卷是否正在解除安裝，以及控制器和 Pod finalizers 的所有者。節點失聯時，API 物件消失並不等於節點上的程序已停止。

不要常規使用 `--force --grace-period=0` 刪除 Pod，也不要手動刪除 finalizers。只有在確認原節點已被安全隔離、儲存/工作負載不會產生重複寫入，並遵循 StatefulSet 或應用自身恢復流程後，才由有權限的管理員考慮強制刪除。

## 歷史範例說明

本頁舊版日誌和命令曾依賴 Docker Engine、`docker://` 容器 ID、`/var/lib/docker`、容器化 kubelet 或固定的 CNI 網橋；這些細節不是 Kubernetes v1.37 的通用介面。當前節點檢查應使用叢集發行版支援的 CRI 工具、CNI/CSI 元件文件和受控節點存取途徑。

更多資訊請參閱 [Debug Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/) 和 [Troubleshooting Applications](https://kubernetes.io/docs/tasks/debug/debug-application/)。
