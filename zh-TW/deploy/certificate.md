# Kubernetes 憑證管理

kubeadm 在初始化叢集時管理控制平面憑證。自訂 CA、外部 CA、憑證輪替和手動產生元件憑證，都必須依目標 Kubernetes 版本、API endpoint、服務網段與元件身分設定；不要重複使用含有舊固定 IP 的憑證主體名稱。

Kubernetes v1.36/v1.37 自建叢集請參考目前的 [kubeadm 憑證管理文件](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/)及所選發行版的 PKI 指南。先在隔離環境核對 SAN、信任鏈、有效期限、私鑰權限及輪替/復原流程。不要只因 openssl 或 CFSSL 指令執行成功，就認定憑證可用於目標叢集。

本儲存庫舊版 CFSSL 指令及固定位址範例已移至[歷史封存](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/deploy/certificate.md)。該範例使用舊式 `go get` 安裝步驟，且未針對 Kubernetes v1.36/v1.37 驗證，不是目前的操作指南。
