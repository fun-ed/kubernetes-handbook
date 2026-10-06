# 映像檔與套件來源
+
## Kubernetes 官方映像檔登錄站
+
Kubernetes v1.37 使用 `registry.k8s.io` 釋出控制面和官方專案映像檔。映像檔名稱應從 Kubernetes 對應版本的部署文件或元件釋出材料獲取。例如，v1.37.1 kubeadm 使用的 pause 映像檔為 `registry.k8s.io/pause:3.10.2`：
+
```bash
crictl pull registry.k8s.io/pause:3.10.2
crictl pull registry.k8s.io/kube-apiserver:v1.37.1
```
+
控制面映像檔版本由 Kubernetes 釋出和 kubeadm 設定決定，不要僅根據上游元件的最新版本替換。`registry.k8s.io` 下的映像檔並非全部由同一個團隊維護，部署前請核對該元件的官方版本與支援範圍。
+
## Kubernetes 套件儲存庫
+
Kubernetes apt/rpm 套件使用 `pkgs.k8s.io`，每個 Kubernetes minor 版本有單獨的套件儲存庫。v1.37 的安裝步驟和簽名金鑰見[Kubernetes 官方 kubeadm 安裝指南](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)。
+
Debian/Ubuntu 僅需按官方文件新增 v1.37 儲存庫。下面的 URL 是官方 apt 源；安裝前應閱讀當前官方指南並驗證簽名金鑰：
+
```text
https://pkgs.k8s.io/core:/stable:/v1.37/deb/
```
+
不要再使用 `apt.kubernetes.io`、`yum.kubernetes.io` 或早期的 Azure 映像檔代理作為 Kubernetes 當前套件來源。舊儲存庫已經凍結，內容可能隨時撤下。
+
## 其他 registry 與映像檔代理
+
容器映像檔代理、區域 registry 和私有快取由其營運者維護，無法保證服務持續可用、內容完整或與上游同步。部署前應自行確認：
+
- 代理是否允許目標環境存取，且明確支援所需的 registry 和映像檔路徑。
- 拉取的版本或 digest 是否與上游發布資料一致。
- 代理的驗證、TLS、映像檔保留與故障復原策略是否符合叢集需求。
+
不要將未驗證的第三方代理改寫為公用映像檔名稱，也不要假設 Docker Hub、GitHub Container Registry、Quay 或雲端廠商 registry 的映像檔路徑會長期不變。
+
## Helm Chart 來源
+
Helm Charts 可以釋出在 OCI registry 或傳統 Helm repository。Helm 官方文件推薦使用 Artifact Hub 查詢來源；發現 Chart 後應審查維護狀態、Chart 版本、容器映像檔和 RBAC。舊的 `stable` 與 `incubator` Chart 儲存庫已不再是 Helm 的當前預設源。
