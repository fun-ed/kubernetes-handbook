# 证书检查与轮换

kubeadm 集群的当前命令使用 `kubeadm certs`，不再使用 `kubeadm alpha certs`。先确认备份和恢复步骤，再在控制平面节点逐台轮换。`kubeadm certs` 不能管理外部 CA 签发的证书。

## 检查证书

```bash
kubeadm certs check-expiration
openssl x509 -noout -dates -in /etc/kubernetes/pki/apiserver.crt
```

`check-expiration` 检查 kubeadm 管理的控制平面证书和 kubeconfig 中嵌入的客户端证书。kubelet 客户端证书使用 kubelet 证书轮换流程，不在该命令列出的证书中。外部管理证书应由组织的 CA 流程续签。

## kubeadm 管理证书的手动轮换

`kubeadm certs renew` 使用节点本地 CA 证书和密钥，并以现有证书属性为准。将 PKI 与 kubeconfig 备份到受保护的位置后，在每个控制平面节点分别运行：

```bash
backup_dir="/root/kubernetes-cert-backup-$(date +%Y%m%d%H%M%S)"
sudo mkdir -m 0700 "$backup_dir"
sudo cp -a /etc/kubernetes/pki /etc/kubernetes/*.conf "$backup_dir/"
sudo kubeadm certs renew all
sudo kubeadm certs check-expiration
```

更新后需要重启读取这些证书的静态 Pod。按[官方 kubeadm 证书说明](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/)逐个临时移走并放回 `/etc/kubernetes/manifests/` 中对应的 manifest，等待 kubelet 检查周期完成，再确认 API server、scheduler、controller-manager 和本地 etcd 状态正常。多控制平面集群逐台操作，并保持 API endpoint 可用。

如果管理员从 `admin.conf` 复制了 `$HOME/.kube/config`，还需在续签后更新该副本：

```bash
sudo cp /etc/kubernetes/admin.conf "$HOME/.kube/config"
sudo chown "$(id -u):$(id -g)" "$HOME/.kube/config"
```

CA 私钥不在证书有效期内自动轮换。CA 轮换需要单独规划客户端信任、组件证书和回滚窗口，不要把 `kubeadm certs renew all` 当作 CA 更新。

## kubelet 客户端证书自动轮换

kubeadm 默认配置 kubelet 客户端证书轮换。控制平面证书续签与 kubelet CSR 审批是不同流程。检查节点的 `kubelet.conf`、`/var/lib/kubelet/pki/` 和 `CertificateSigningRequest` 状态；不要给当前 kubelet 增加 `--experimental-cluster-signing-duration` 或旧 feature gate。

## 参考

- [Kubernetes：Certificate Management with kubeadm](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/)
- [Kubelet Certificate Rotation](https://kubernetes.io/docs/tasks/tls/certificate-rotation/)
- [PKI certificates and requirements](https://kubernetes.io/docs/setup/best-practices/certificates/)

本章旧的 `kubeadm alpha certs`、`kubeadm alpha kubeconfig`、Kubernetes v1.15 升级命令和 experimental flag 已不适用于当前集群，不要照旧片段执行。
