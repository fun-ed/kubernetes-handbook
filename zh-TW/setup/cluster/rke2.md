# 使用 RKE2 部署 Kubernetes v1.37.1

本頁說明使用 RKE2 **v1.37.1+rke2r1** 部署 Linux Kubernetes 叢集。RKE2 是整合控制平面、containerd 與預設 CNI 的 Kubernetes 發行版；不要另外安裝或替換 Kubernetes 控制平面、kubelet、containerd 等上游二進位檔。本文的版本快照截至 **2026-10-05**，不代表已在本機或生產叢集執行過安裝。

RKE2 官方 release 清單中，截至快照日最高 Kubernetes minor 為 v1.37。v1.37.1+rke2r1 於 2026-09-30T16:49:06Z 發布，GitHub 標記 `prerelease=false`、`draft=false`。其 `+rke2r1` 是 RKE2 發行修訂版，不是預發布標記；不能把它與 `-rc` 預發布版本混為一談。RKE2 的 `stable` 通道是建議用於生產環境的通道；`latest` 著重較早試用新功能，尚未經過同等社群穩定化。本指南固定 RKE2 版本，避免安裝時通道指向變動。

該 RKE2 release 註明隨附 Kubernetes **v1.37.1**、etcd **v3.7.1-k3s3**、containerd **v2.3.4-k3s1**、runc **v1.4.3**、CoreDNS **v1.14.7**、metrics-server **v0.9.0**、Traefik **v3.7.13**。預設 Canal 組合為 Flannel **v0.28.9** 與 Calico **v3.32.2**；release 另列可選 Calico **v3.32.2**、Cilium **v1.20.2**。這些是該 RKE2 發行版本打包的元件版本，不代表每個可選外掛程式都預設安裝，也不是上游元件的最新版本或通用相容性認證。本文以預設 Canal 為例，不自行安裝第二套 CNI。

## 1. 檢查 Linux 主機與網路

RKE2 Linux 節點需使用 systemd，官方概述支援使用 systemd 與 iptables/nftables 的 Linux 發行版；若要求 SUSE 支援認證，請依[該 Kubernetes minor 的 SUSE RKE2 支援矩陣](https://www.suse.com/suse-rke2/support-matrix/all-supported-versions/rke2-v1-37/)核對精確 OS 版本。官方最低建議為 2 CPU、4 GB RAM，並建議至少 4 CPU、8 GB RAM；控制平面/etcd 節點使用 SSD 較合適。每節點 hostname 必須唯一。安裝程序需要 root 或 sudo。

若核心支援 AppArmor，安裝前備妥 AppArmor 工具（通常為 `apparmor-parser` 套件）。若 NetworkManager 正在執行，依官方說明設定它忽略由 CNI 管理的網路介面；否則它可能干擾 Pod 網路。先規劃不與主機、VPC/VNet、VPN、Pod CIDR 或 Service CIDR 重疊的網段，並依所選 CNI 調整核心轉送與防火牆。

防火牆應限縮來源至叢集節點及必要管理網段，不要將節點互連或 overlay 連接埠暴露到公網：

| 連接埠 | 協定 | 方向／用途 |
| --- | --- | --- |
| 6443 | TCP | 所有節點至 server；Kubernetes API |
| 9345 | TCP | 所有節點至 server；RKE2 supervisor／節點註冊 |
| 2379 | TCP | 僅 server 節點互通；etcd client |
| 2380 | TCP | 僅 server 節點互通；etcd peer |
| 2381 | TCP | server 節點間（依監控需求）；etcd metrics |
| 10250 | TCP | 節點間（依監控需求）；kubelet metrics |
| 30000–32767 | TCP | 節點間及必要用戶端；NodePort 服務（僅需使用時開啟） |
| 8472 | UDP | 所有節點互通；預設 Canal 的 VXLAN，限制來源為節點 |
| 9099 | TCP | 所有節點互通；預設 Canal 健康檢查 |

WireGuard CNI 組態使用 UDP 51820（IPv4）及 51821（IPv6/雙堆疊）。更換 CNI 後，依其官方文件重核連接埠；不要因為通用表列有連接埠就全部開放。參考 RKE2 [Requirements](https://docs.rke2.io/install/requirements) 與[網路需求](https://docs.rke2.io/install/requirements#networking)。

## 2. 檢查安裝程序並固定版本

RKE2 官方安裝器支援以 `INSTALL_RKE2_VERSION` 固定 GitHub release 版本，預設 `stable` 通道和 `latest` 通道有不同穩定程度。先下載安裝器至檔案並檢視，不要未檢查就直接 pipe 執行；再在每台主機明確指定版本及 server/agent 類型。以下命令是供讀者在自行準備的主機上使用，不會在本文件檢查期間執行：

```bash
curl -fsSLo /tmp/install-rke2.sh https://get.rke2.io
less /tmp/install-rke2.sh

# 第一台控制平面節點
sudo env INSTALL_RKE2_VERSION='v1.37.1+rke2r1' \
  INSTALL_RKE2_TYPE=server sh /tmp/install-rke2.sh

# worker 節點改用此類型；在該節點執行
sudo env INSTALL_RKE2_VERSION='v1.37.1+rke2r1' \
  INSTALL_RKE2_TYPE=agent sh /tmp/install-rke2.sh
```

安裝器會安裝所選類型的 systemd 服務與 RKE2 二進位檔，並準備 RKE2 自己管理的 Kubernetes 元件與 containerd。不要額外套用 kubeadm、上游 Kubernetes 套件儲存庫或獨立 containerd 設定來覆寫這些元件。若需要離線安裝或驗證來源，使用 release 頁面提供的相同版本與架構資產、驗證資訊，依[官方安裝文件](https://docs.rke2.io/install/quickstart)準備；不要從不同版本混搭映像檔。

## 3. 建立設定檔並啟動 server

RKE2 預設讀取 `/etc/rancher/rke2/config.yaml`。從儲存庫根目錄執行以下命令，將本書的[server 範例設定檔](samples/rke2/server-config.yaml)複製到目標位置；確認目標檔案權限為 `0600`，再替換 `REPLACE_WITH...` 佔位值後啟動服務。`token` 是叢集敏感憑證；RKE2 也使用 server token 加密 datastore 中的 bootstrap 資料，必須透過秘密管理系統產生並保存真正的高熵值，不能沿用文件中的佔位字串。

```bash
sudo install -d -m 0700 /etc/rancher/rke2
sudo install -m 0600 ./zh-TW/setup/cluster/samples/rke2/server-config.yaml /etc/rancher/rke2/config.yaml
sudoedit /etc/rancher/rke2/config.yaml
sudo chmod 0600 /etc/rancher/rke2/config.yaml
sudo systemctl enable --now rke2-server
sudo journalctl -u rke2-server -f
```

範例設定明確加入預期用來連線的穩定 API DNS 名稱作為 `tls-san`。請將它改成實際負載平衡器 DNS/IP；不要以忽略 TLS 驗證替代正確 SAN。多 server 高可用叢集須以奇數台 server 維持 etcd quorum，所有 server 的關鍵叢集設定須一致，且應按[官方 HA 指南](https://docs.rke2.io/install/ha)規劃穩定 endpoint、etcd、負載平衡與憑證。單節點教學設定不等於高可用設計。

## 4. 加入 agent 節點

每台 agent 建立 `/etc/rancher/rke2/config.yaml`，填入可連線的 server endpoint 與 server 建立的 join token；從儲存庫根目錄使用[agent 設定檔](samples/rke2/agent-config.yaml)複製範本，或透過安全方式將範本內容傳送到節點。替換佔位值後，設定檔必須由 root 擁有且權限設為 `0600`；不要複製到公開位置或提交到版本庫。

```bash
sudo install -d -m 0700 /etc/rancher/rke2
sudo install -m 0600 ./zh-TW/setup/cluster/samples/rke2/agent-config.yaml /etc/rancher/rke2/config.yaml
sudoedit /etc/rancher/rke2/config.yaml
sudo chmod 0600 /etc/rancher/rke2/config.yaml
sudo systemctl enable --now rke2-agent
sudo journalctl -u rke2-agent -f
```

server token 可透過受控方式從 server 取得，預設 token 檔在 `/var/lib/rancher/rke2/server/node-token`；不要把真實 token 放入指令歷史、工單或文件。確保 agent 的 `server` 指向正確 endpoint，TCP 9345 及 6443 可連線。節點名稱必須唯一。

## 5. kubeconfig 與基本檢查

server 啟動後會寫出管理 kubeconfig `/etc/rancher/rke2/rke2.yaml`。這是高權限憑證，應只供授權管理者使用；可直接以 root 執行隨附的 kubectl，或複製到專用的管理設定檔，設定明確的 `0600` 權限及 owner。不要為了方便將來源檔或 kubeconfig 開成 `0644`，也不要提交至版本庫。以下範例使用獨立 kubeconfig，不會覆寫使用者現有的 `$HOME/.kube/config` 或目前的 context：

```bash
sudo install -d -m 0700 -o "$USER" -g "$(id -gn)" "$HOME/.kube"
sudo install -m 0600 -o "$USER" -g "$(id -gn)" \
  /etc/rancher/rke2/rke2.yaml "$HOME/.kube/rke2-admin.conf"
```

由非 server 主機連線時，先把 kubeconfig 內的 loopback API 位址改成 server SAN 中的受信任 DNS/IP，再透過安全通道傳送並保護該檔。下列僅供讀者自行確認部署完成後的叢集狀態，本文未連線或執行於任何使用者叢集：

```bash
kubectl --kubeconfig "$HOME/.kube/rke2-admin.conf" version
kubectl --kubeconfig "$HOME/.kube/rke2-admin.conf" get nodes -o wide
kubectl --kubeconfig "$HOME/.kube/rke2-admin.conf" get pods -A
kubectl --kubeconfig "$HOME/.kube/rke2-admin.conf" get --raw='/readyz?verbose'
```

確認節點 `Ready`，系統 Pod 與 DNS 健康，且實際使用的 CNI、儲存、服務路由、防火牆和工作負載均符合環境需求。`kubectl get`/`readyz` 只檢查控制平面與資源狀態，不能取代業務流量、網路策略、持久卷或災難復原測試。

## 6. 備份與升級

embedded etcd 的排程快照預設於每日 00:00 與 12:00 執行，每台 server 本機保留 5 份。依 RKE2 [備份與還原文件](https://docs.rke2.io/datastore/backup_restore)設計額外備份至受控異地儲存，並定期演練還原。快照以外，另保存 RKE2 設定、憑證，以及 server token 的安全副本；缺少建立快照的 server token 可能無法解密 bootstrap 資料。外部 datastore 不適用 embedded-etcd 快照程序，須使用該 datastore 自己的備份方式。

RKE2 官方[手動升級程序](https://docs.rke2.io/upgrades/manual)要求先逐台升級 server，再升級 agent；server 每次只升一台並確認健康。規劃 Kubernetes 升級時不可略過中間 minor，遵循上游 version skew 及各版 RKE2 文件；跨 minor 升級前先確認版本支援、release notes、CNI 與附加元件相容，取得並驗證 etcd 快照和回復程序。不要把更新到同一通道的最新版視為可直接跳級，也不要在本章把 server/agent 版本混搭當示範。本文沒有執行升級、建立叢集或還原操作。

## 參考來源

- [RKE2 v1.37.1+rke2r1 官方 release 與隨附元件版本](https://github.com/rancher/rke2/releases/tag/v1.37.1%2Brke2r1)
- [RKE2 releases API](https://api.github.com/repos/rancher/rke2/releases?per_page=100)（截至 2026-10-05 的 release 狀態與發布時間）
- [RKE2 requirements：Linux、硬體及連接埠](https://docs.rke2.io/install/requirements)
- [RKE2 Quick Start](https://docs.rke2.io/install/quickstart)
- [RKE2 configuration options](https://docs.rke2.io/install/configuration)
- [Server configuration reference](https://docs.rke2.io/reference/server_config)
- [SUSE RKE2 v1.37 support matrix](https://www.suse.com/suse-rke2/support-matrix/all-supported-versions/rke2-v1-37/)
- [RKE2 backup and restore](https://docs.rke2.io/datastore/backup_restore)
- [RKE2 manual upgrades](https://docs.rke2.io/upgrades/manual)
