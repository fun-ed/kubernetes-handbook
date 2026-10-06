# 使用 k0s 部署 Kubernetes v1.36.4

本指南依截至 **2026-10-05** 可查得的最新穩定 k0s 發布版撰寫：**v1.36.4+k0s.1**，GitHub Releases API 記錄發布時間為 **2026-09-19 21:23:36 UTC**（`draft=false`、`prerelease=false`）。該發布版內含 Kubernetes v1.36.4，並非 v1.37；若需求是 v1.37，請選擇已發布且明確包含 v1.37 的發行版，不要只把 k0s 發布版號改成 v1.37.1。k0s 適合快速建立單節點教學環境、邊緣節點或自行管理的 Linux 叢集；本頁的單節點做法不適用於高可用或正式環境。

> k0s 的 API 與安裝方式以其版本化官方文件為準。發布版的 upstream 元件 pin，不等於各元件宣告支援 Kubernetes v1.37。參考[本手冊 v1.37.1 相容性基線](../kubernetes-v1.37.md)與[元件版本清單](../component-versions.md)。

## 主機前置需求

本例以 Linux、systemd、單一 x86-64/ARM64 主機示範；k0s 官方亦測試多種 Linux 發行版。官方最低估算為 controller+worker 1 vCPU、1 GB RAM、約 2 GB k0s 磁碟空間；實際主機及工作負載還需要額外資源。建議使用 SSD 以提升儲存效能。確認 hostname 唯一、主機時間正確、可連線至映像檔登錄站，且防火牆允許所選部署角色所需的 Kubernetes API（預設 TCP 6443）、k0s API（TCP 9443）及叢集網路流量。詳細連接埠與 OS 需求請見[k0s 系統需求](https://docs.k0sproject.io/v1.36.4+k0s.1/system-requirements/)及[網路設定](https://docs.k0sproject.io/v1.36.4+k0s.1/networking/)。

k0s 將 containerd 整合在發布版中，不必另外安裝 CRI 執行環境；但這不代表可以忽略 Linux 核心、網路、儲存、cgroup 與防火牆需求。單節點教學使用預設 Kube-router CNI、etcd 資料存放區與 systemd 服務。不要在同一叢集另行安裝第二套 CNI。

## 固定版本下載與安裝

以下使用官方 GitHub Release asset，不使用會追隨最新版本的 `get.k0s.sh` 安裝器。API 公布的 Linux amd64 asset SHA-256 為 `18c304d53cdd70095e99c6b859b269b4fef0bb84579d7e7185271a9135694a31`；其他平台／架構請先從同一 release API 查核相符 asset 的 SHA-256，再下載。

```bash
set -eu
VERSION='v1.36.4+k0s.1'
ASSET="k0s-${VERSION}-amd64"
URL="https://github.com/k0sproject/k0s/releases/download/${VERSION}/${ASSET}"
curl --fail --location --proto '=https' --tlsv1.2 "$URL" --output k0s
printf '%s  %s\n' '18c304d53cdd70095e99c6b859b269b4fef0bb84579d7e7185271a9135694a31' k0s | sha256sum --check
chmod 0755 k0s
./k0s version
sudo install -o root -g root -m 0755 k0s /usr/local/bin/k0s
```

只有在摘要比對成功且版本輸出符合預期後才繼續。摘要值來自 GitHub Release API asset metadata，仍應透過可信來源核對發布資訊；正式供應鏈流程可再依該發布版提供的簽章驗證步驟檢查二進位檔。

## 設定並啟動單節點叢集

請從儲存庫根目錄執行以下命令。本頁將控制平面與工作節點放在同一台主機，供隔離的教學用途。範例設定檔是 k0s 原生 `ClusterConfig`，不是 Kubernetes API 物件，檔案位於 [`samples/k0s/k0s.yaml`](samples/k0s/k0s.yaml)。CIDR 必須先確認不與主機、VPN、雲端 VPC 或其他路由網段重疊；叢集初始化後變更網路 provider 通常需要重新佈建。

```bash
sudo install -d -o root -g root -m 0755 /etc/k0s
sudo install -o root -g root -m 0600 setup/cluster/samples/k0s/k0s.yaml /etc/k0s/k0s.yaml
sudo k0s config validate --config /etc/k0s/k0s.yaml
sudo k0s install controller --enable-worker --no-taints -c /etc/k0s/k0s.yaml
sudo k0s start
sudo k0s status
```

`k0s config validate --config` 是 v1.36.4+k0s.1 官方 CLI 支援的本機設定檔驗證命令；本指南沒有在主機執行安裝。使用 `--enable-worker --no-taints` 讓該 controller 也承載一般工作負載，並保留日後加入 worker 的方式。不要使用 `--single`：官方文件說明該選項會停用擴充為多節點所需的功能。服務由 systemd 管理；systemd 主機可使用 `sudo systemctl status k0scontroller` 檢查服務。

從 k0s 產生獨立 kubeconfig，限制檔案權限並明確指定它，避免誤用目前使用者的 `kubectl` context：

```bash
install -d -m 0700 "$HOME/.kube"
umask 077
sudo k0s kubeconfig admin > "$HOME/.kube/k0s-admin.conf"
chmod 0600 "$HOME/.kube/k0s-admin.conf"
export KUBECONFIG="$HOME/.kube/k0s-admin.conf"
kubectl get nodes -o wide
kubectl get pods -A
```

管理 kubeconfig 具有高權限；不要提交到版本控制、貼入公開工單或複製到不受信任裝置。多叢集操作時使用 `kubectl --kubeconfig "$HOME/.kube/k0s-admin.conf" ...`，並再次確認目標叢集。

## 加入 worker 與 token 保護

worker 安裝前，先將相同版本的 k0s 二進位檔安全地放到該節點，並確認 controller IP、API 連接埠及 k0s 網路連線可達。在 controller 建立有期限的 worker join token；token 是可用於加入叢集的憑證：

```bash
sudo sh -c 'umask 077; k0s token create --role=worker --expiry=24h > /root/k0s-worker-token'
```

透過受保護的管理通道將 token 傳給 worker 操作者，不要放進 shell history、聊天、Git 或一般日誌；確認使用後刪除副本。worker 上使用權限受限的 token file 安裝：

```bash
sudo k0s install worker --token-file /root/k0s-worker-token
sudo k0s start
```

token 含 bootstrap 認證資料；若遺失或外洩，應視同憑證洩漏，依官方 token 管理流程撤銷／輪替並檢查加入記錄。官方步驟見[k0s 多節點手動安裝](https://docs.k0sproject.io/v1.36.4+k0s.1/k0s-multi-node/)。

## DNS、網路與工作負載檢查

下列命令皆使用上方指定的 k0s kubeconfig。先等待節點與系統 Pod 就緒，再用短期測試 Pod 驗證 DNS、Service 網路與工作負載執行；此步驟會建立並刪除教學資源。

```bash
kubectl --kubeconfig "$HOME/.kube/k0s-admin.conf" wait --for=condition=Ready nodes --all --timeout=5m
kubectl --kubeconfig "$HOME/.kube/k0s-admin.conf" get pods -A
kubectl --kubeconfig "$HOME/.kube/k0s-admin.conf" run dns-check --image=busybox:1.37.0 --restart=Never --command -- sleep 300
kubectl --kubeconfig "$HOME/.kube/k0s-admin.conf" wait --for=condition=Ready pod/dns-check --timeout=2m
kubectl --kubeconfig "$HOME/.kube/k0s-admin.conf" exec dns-check -- nslookup kubernetes.default.svc.cluster.local
kubectl --kubeconfig "$HOME/.kube/k0s-admin.conf" delete pod dns-check --wait=true
```

若節點或 DNS 未就緒，先查看 `sudo journalctl -u k0scontroller`、`kubectl get pods -A` 和網路／防火牆設定，不要用另一套 CNI 掩蓋問題。測試映像檔標籤是教學例；正式部署應固定使用經審核的映像檔版本或 digest。

## 備份、升級與移除

升級前先閱讀該 k0s 版本的升級說明；逐次確認 Kubernetes minor skew、k0s 自動升級相容限制、外掛支援矩陣與升級順序。在 controller 上建立並異地保管加密備份，並於隔離環境演練還原：

```bash
sudo install -d -m 0700 /var/backups/k0s
sudo k0s backup --save-path=/var/backups/k0s
```

k0s 備份涵蓋其管理的憑證、etcd 或 Kine/SQLite 快照、設定與部分 k0s 管理資源；**不含應用程式 PersistentVolume 資料，也不含手動變更或外部資料庫內容**。必須另行備份應用程式資料、PV、外部 datastore 與叢集外基礎設施。不要直接覆蓋二進位檔或假設降版能復原資料；請依版本化官方[升級](https://docs.k0sproject.io/v1.36.4+k0s.1/upgrade/)及[備份還原](https://docs.k0sproject.io/v1.36.4+k0s.1/backup/)程序規劃。

移除 `k0s reset` 會清除服務、資料目錄、容器、掛載與網路命名空間，並可能影響主機上其他網路設定；**此命令具有破壞性，本指南不會自動執行**。只有確認主機專供教學且可銷毀，並已備份所需資料後，才依官方卸載程序手動操作；不可在共用或正式主機直接照貼執行。

## 官方來源

- [k0s v1.36.4+k0s.1 GitHub release 與 API 資產](https://github.com/k0sproject/k0s/releases/tag/v1.36.4%2Bk0s.1) · [GitHub Releases API](https://api.github.com/repos/k0sproject/k0s/releases/latest)
- [版本化官方文件](https://docs.k0sproject.io/v1.36.4+k0s.1/) · [設定參考](https://docs.k0sproject.io/v1.36.4+k0s.1/configuration/) · [CLI 設定驗證](https://docs.k0sproject.io/v1.36.4+k0s.1/cli/k0s_config_validate/)
- [系統需求](https://docs.k0sproject.io/v1.36.4+k0s.1/system-requirements/) · [單節點快速入門](https://docs.k0sproject.io/v1.36.4+k0s.1/install/) · [備份與還原](https://docs.k0sproject.io/v1.36.4+k0s.1/backup/)
