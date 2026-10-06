# 證書檢查與輪換

kubeadm 叢集的當前命令使用 `kubeadm certs`，不再使用 `kubeadm alpha certs`。先確認備份和恢復步驟，再在控制平面節點逐臺輪換。`kubeadm certs` 不能管理外部 CA 簽發的證書。

## 檢查證書

```bash
kubeadm certs check-expiration
openssl x509 -noout -dates -in /etc/kubernetes/pki/apiserver.crt
```

`check-expiration` 檢查 kubeadm 管理的控制平面證書和 kubeconfig 中嵌入的客戶端證書。kubelet 客戶端證書使用 kubelet 證書輪換流程，不在該命令列出的證書中。外部管理證書應由組織的 CA 流程續簽。

## kubeadm 管理證書的手動輪換

`kubeadm certs renew` 使用節點本地 CA 證書和金鑰，並以現有證書屬性為準。將 PKI 與 kubeconfig 備份到受保護的位置後，在每個控制平面節點分別執行：

```bash
backup_dir="/root/kubernetes-cert-backup-$(date +%Y%m%d%H%M%S)"
sudo mkdir -m 0700 "$backup_dir"
sudo cp -a /etc/kubernetes/pki /etc/kubernetes/*.conf "$backup_dir/"
sudo kubeadm certs renew all
sudo kubeadm certs check-expiration
```

更新後需要重啟讀取這些證書的靜態 Pod。按[官方 kubeadm 證書說明](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/)逐個臨時移走並放回 `/etc/kubernetes/manifests/` 中對應的 manifest，等待 kubelet 檢查週期完成，再確認 API server、scheduler、controller-manager 和本地 etcd 狀態正常。多控制平面叢集逐臺操作，並保持 API endpoint 可用。

如果管理員從 `admin.conf` 複製了 `$HOME/.kube/config`，還需在續簽後更新該副本：

```bash
sudo cp /etc/kubernetes/admin.conf "$HOME/.kube/config"
sudo chown "$(id -u):$(id -g)" "$HOME/.kube/config"
```

CA 私鑰不在證書有效期內自動輪換。CA 輪換需要單獨規劃客戶端信任、元件證書和回復視窗，不要把 `kubeadm certs renew all` 當作 CA 更新。

## kubelet 客戶端證書自動輪換

kubeadm 預設設定 kubelet 客戶端證書輪換。控制平面證書續簽與 kubelet CSR 審批是不同流程。檢查節點的 `kubelet.conf`、`/var/lib/kubelet/pki/` 和 `CertificateSigningRequest` 狀態；不要給當前 kubelet 增加 `--experimental-cluster-signing-duration` 或舊 feature gate。

## 參考

- [Kubernetes：Certificate Management with kubeadm](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/)
- [Kubelet Certificate Rotation](https://kubernetes.io/docs/tasks/tls/certificate-rotation/)
- [PKI certificates and requirements](https://kubernetes.io/docs/setup/best-practices/certificates/)

本章舊的 `kubeadm alpha certs`、`kubeadm alpha kubeconfig`、Kubernetes v1.15 升級命令和 experimental flag 已不適用於當前叢集，不要照舊片段執行。
