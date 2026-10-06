# 分散式負載測試

原範例依賴 TenxCloud 私有映像檔、舊 Google Container Registry 映像檔、ReplicationController，以及 `serviceName/servicePort` 形式的舊 Ingress schema。它們沒有按 Kubernetes v1.37 驗證，且舊映像檔來源不能視為當前可用；這些命令和 YAML 不應直接部署，已從操作步驟中移除。

[Locust 官方文件](https://docs.locust.io/en/stable/running-distributed.html)描述當前 master/worker 分散式模型。為 Kubernetes 設計測試時，按所選 Locust release 和應用映像檔建立 master 與 worker Deployment，並使用叢集內 Service 供 worker 存取 master、另一個 Service 指向被測應用。只在需要從叢集外開啟 Web UI 時設定入口；新建 Ingress 應使用 `networking.k8s.io/v1`，並先部署/驗證受支援的 Ingress controller。

可按以下順序準備測試，不要將未經核實的舊清單應用到叢集：

1. 選定受支援的 Locust release，建置並發布固定版本或 digest 的 master/worker 映像檔；應用映像檔、依賴、使用者指令碼和目標主機設定應一致。
2. 在隔離的測試環境中部署工作負載，設定最小權限、請求/限制和 worker 到 master 的網路策略；測試 UI 不應未經認證暴露到公網。
3. 根據容量逐步擴充套件 worker Deployment。將 `locust-worker` 替換為實際 Deployment 名稱：

   ```bash
   kubectl scale deployment/locust-worker --replicas=5 -n load-test
   kubectl rollout status deployment/locust-worker -n load-test
   ```

4. 記錄 Kubernetes、被測應用和 Locust 的版本/digest、worker 數量、節點規格、資源設定、測試資料及目標同時執行的請求數量。逐步增加負載並設定請求速率、持續時間和停止條件，避免把負載誤指向生產服務或壓垮共享叢集。

舊章中關於 Traefik v1 Ingress 欄位的說明也已過時；當前 Ingress 範例見[Traefik 安裝章節](traefik-ingress-installation.md)。實際執行引數、master/worker flags、容器映像檔和使用者指令碼的分發方式以[Locust 當前文件](https://docs.locust.io/en/stable/running-distributed.html)為準。
