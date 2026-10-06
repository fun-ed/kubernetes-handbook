# 使用 RKE2 部署 Kubernetes v1.37.1

本页说明使用 RKE2 **v1.37.1+rke2r1** 部署 Linux Kubernetes 集群。RKE2 是整合控制平面、containerd 与默认 CNI 的 Kubernetes 发行版；不要另外安装或替换 Kubernetes 控制平面、kubelet、containerd 等上游二进制文件。本文的版本快照截至 **2026-10-05**，不代表已在本机或生产集群执行过安装。

RKE2 官方 release 清单中，截至快照日最高 Kubernetes minor 为 v1.37。v1.37.1+rke2r1 于 2026-09-30T16:49:06Z 发布，GitHub 标记 `prerelease=false`、`draft=false`。其中 `+rke2r1` 是 RKE2 发行修订版，不是预发布标记；不能把它与 `-rc` 预发布版本混为一谈。RKE2 的 `stable` 通道是建议用于生产环境的通道；`latest` 侧重较早试用新功能，尚未经过同等社区稳定化。本指南固定 RKE2 版本，避免安装时通道指向变动。

该 RKE2 release 说明随附 Kubernetes **v1.37.1**、etcd **v3.7.1-k3s3**、containerd **v2.3.4-k3s1**、runc **v1.4.3**、CoreDNS **v1.14.7**、metrics-server **v0.9.0**、Traefik **v3.7.13**。默认 Canal 组合为 Flannel **v0.28.9** 与 Calico **v3.32.2**；release 另列可选 Calico **v3.32.2**、Cilium **v1.20.2**。这些是该 RKE2 发行版本打包的组件版本，不代表每个可选插件都默认安装，也不是上游组件的最新版本或通用兼容性认证。本文以默认 Canal 为例，不自行安装第二套 CNI。

## 1. 检查 Linux 主机与网络

RKE2 Linux 节点需使用 systemd；官方概述支持使用 systemd 与 iptables/nftables 的 Linux 发行版。若要求 SUSE 支持认证，请依[该 Kubernetes minor 的 SUSE RKE2 支持矩阵](https://www.suse.com/suse-rke2/support-matrix/all-supported-versions/rke2-v1-37/)核对具体 OS 版本。官方最低建议为 2 CPU、4 GB RAM，并建议至少 4 CPU、8 GB RAM；控制平面/etcd 节点使用 SSD 较合适。每个节点的 hostname 必须唯一。安装程序需要 root 或 sudo。

若内核支持 AppArmor，安装前备妥 AppArmor 工具（通常为 `apparmor-parser` 软件包）。若 NetworkManager 正在运行，依官方说明配置它忽略由 CNI 管理的网络接口；否则它可能干扰 Pod 网络。先规划不与主机、VPC/VNet、VPN、Pod CIDR 或 Service CIDR 重叠的网段，并依所选 CNI 调整内核转发与防火墙。

防火墙应限制来源为集群节点及必要管理网段，不要将节点互连或 overlay 端口暴露到公网：

| 端口 | 协议 | 方向／用途 |
| --- | --- | --- |
| 6443 | TCP | 所有节点至 server；Kubernetes API |
| 9345 | TCP | 所有节点至 server；RKE2 supervisor／节点注册 |
| 2379 | TCP | 仅 server 节点互通；etcd client |
| 2380 | TCP | 仅 server 节点互通；etcd peer |
| 2381 | TCP | server 节点之间（依监控需求）；etcd metrics |
| 10250 | TCP | 节点之间（依监控需求）；kubelet metrics |
| 30000–32767 | TCP | 节点之间及必要客户端；NodePort 服务（仅在需要时开放） |
| 8472 | UDP | 所有节点互通；默认 Canal 的 VXLAN，仅限节点来源 |
| 9099 | TCP | 所有节点互通；默认 Canal 健康检查 |

WireGuard CNI 配置使用 UDP 51820（IPv4）及 51821（IPv6/双栈）。更换 CNI 后，依其官方文档重新核对端口；不要因为通用表列出端口就全部开放。参考 RKE2 [Requirements](https://docs.rke2.io/install/requirements) 与[网络需求](https://docs.rke2.io/install/requirements#networking)。

## 2. 检查安装程序并固定版本

RKE2 官方安装器支持使用 `INSTALL_RKE2_VERSION` 固定 GitHub release 版本；默认 `stable` 通道和 `latest` 通道的稳定程度不同。先将安装器下载到文件并检查，不要未经检查就直接通过 pipe 执行；然后在每台主机上明确指定版本及 server/agent 类型。以下命令供读者在自行准备的主机上使用；本次文档更新没有执行这些命令：

```bash
curl -fsSLo /tmp/install-rke2.sh https://get.rke2.io
less /tmp/install-rke2.sh

# 第一台控制平面节点
sudo env INSTALL_RKE2_VERSION='v1.37.1+rke2r1' \
  INSTALL_RKE2_TYPE=server sh /tmp/install-rke2.sh

# worker 节点改用此类型；在该节点执行
sudo env INSTALL_RKE2_VERSION='v1.37.1+rke2r1' \
  INSTALL_RKE2_TYPE=agent sh /tmp/install-rke2.sh
```

安装器会安装所选类型的 systemd 服务与 RKE2 二进制文件，并准备由 RKE2 管理的 Kubernetes 组件与 containerd。不要另外套用 kubeadm、上游 Kubernetes 软件包仓库或独立 containerd 配置来覆盖这些组件。若需要离线安装或验证来源，请使用 release 页面提供的相同版本与架构资产、校验信息，依[官方安装文档](https://docs.rke2.io/install/quickstart)准备；不要混用不同版本的镜像。

## 3. 创建配置文件并启动 server

RKE2 默认读取 `/etc/rancher/rke2/config.yaml`。从仓库根目录执行以下命令，将本书的[server 示例配置文件](samples/rke2/server-config.yaml)复制到目标位置；确认目标文件权限为 `0600`，再替换 `REPLACE_WITH...` 占位值后启动服务。`token` 是集群敏感凭证；RKE2 也使用 server token 加密 datastore 中的 bootstrap 数据，必须通过密钥管理系统生成并保存真正的高熵值，不能沿用文档中的占位字符串。

```bash
sudo install -d -m 0700 /etc/rancher/rke2
sudo install -m 0600 ./setup/cluster/samples/rke2/server-config.yaml /etc/rancher/rke2/config.yaml
sudoedit /etc/rancher/rke2/config.yaml
sudo chmod 0600 /etc/rancher/rke2/config.yaml
sudo systemctl enable --now rke2-server
sudo journalctl -u rke2-server -f
```

示例配置明确加入预期连接的稳定 API DNS 名称作为 `tls-san`。请将它改为实际负载均衡器 DNS/IP；不要以忽略 TLS 验证代替正确 SAN。多 server 高可用集群须以奇数台 server 维持 etcd quorum，所有 server 的关键集群配置须一致，并应按[官方 HA 指南](https://docs.rke2.io/install/ha)规划稳定 endpoint、etcd、负载均衡与证书。单节点教学配置不等于高可用设计。

## 4. 加入 agent 节点

每台 agent 创建 `/etc/rancher/rke2/config.yaml`，填入可达的 server endpoint 与 server 创建的 join token；从仓库根目录使用[agent 配置文件](samples/rke2/agent-config.yaml)复制模板，或通过安全方式将模板内容传送到节点。替换占位值后，配置文件必须由 root 拥有且权限设为 `0600`；不要复制到公开位置或提交到版本库。

```bash
sudo install -d -m 0700 /etc/rancher/rke2
sudo install -m 0600 ./setup/cluster/samples/rke2/agent-config.yaml /etc/rancher/rke2/config.yaml
sudoedit /etc/rancher/rke2/config.yaml
sudo chmod 0600 /etc/rancher/rke2/config.yaml
sudo systemctl enable --now rke2-agent
sudo journalctl -u rke2-agent -f
```

server token 可通过受控方式从 server 获取，默认 token 文件位于 `/var/lib/rancher/rke2/server/node-token`；不要将真实 token 放入命令历史、工单或文档。确保 agent 的 `server` 指向正确 endpoint，TCP 9345 及 6443 可达。节点名称必须唯一。

## 5. kubeconfig 与基本检查

server 启动后会写出管理 kubeconfig `/etc/rancher/rke2/rke2.yaml`。这是高权限凭证，应仅供获授权的管理员使用；可以直接以 root 执行随附的 kubectl，或复制到专用的管理配置文件，设置明确的 `0600` 权限及 owner。不要为方便将来源文件或 kubeconfig 改为 `0644`，也不要提交到版本库。下面的示例使用独立 kubeconfig，不覆盖用户现有的 `$HOME/.kube/config` 或当前 context：

```bash
sudo install -d -m 0700 -o "$USER" -g "$(id -gn)" "$HOME/.kube"
sudo install -m 0600 -o "$USER" -g "$(id -gn)" \
  /etc/rancher/rke2/rke2.yaml "$HOME/.kube/rke2-admin.conf"
```

从非 server 主机连接时，先将 kubeconfig 中的 loopback API 地址改为 server SAN 中可信的 DNS/IP，再通过安全通道传送并保护该文件。以下命令仅供读者自行检查部署完成后的集群状态，本次文档更新未连接或操作任何用户集群：

```bash
kubectl --kubeconfig "$HOME/.kube/rke2-admin.conf" version
kubectl --kubeconfig "$HOME/.kube/rke2-admin.conf" get nodes -o wide
kubectl --kubeconfig "$HOME/.kube/rke2-admin.conf" get pods -A
kubectl --kubeconfig "$HOME/.kube/rke2-admin.conf" get --raw='/readyz?verbose'
```

确认节点为 `Ready`，系统 Pod 与 DNS 健康，且实际使用的 CNI、存储、服务路由、防火墙和工作负载均符合环境需求。`kubectl get`/`readyz` 只检查控制平面与资源状态，不能替代业务流量、网络策略、持久卷或灾难恢复测试。

## 6. 备份与升级

embedded etcd 的计划快照默认于每日 00:00 与 12:00 执行，每台 server 本地保留 5 份。依 RKE2 [备份与恢复文档](https://docs.rke2.io/datastore/backup_restore)设计额外备份至受控异地存储，并定期演练恢复。快照之外，还要安全保存 RKE2 配置、证书及 server token 副本；缺少创建快照时使用的 server token，可能无法解密 bootstrap 数据。外部 datastore 不适用 embedded-etcd 快照流程，须使用该 datastore 自身的备份方式。

RKE2 官方[手动升级流程](https://docs.rke2.io/upgrades/manual)要求先逐台升级 server，再升级 agent；server 每次只升级一台并确认健康。规划 Kubernetes 升级时不可跳过中间 minor，遵循上游 version skew 政策及各版 RKE2 文档；跨 minor 升级前先确认版本支持、release notes、CNI 与附加组件兼容性，并取得及验证 etcd 快照和恢复流程。不要把更新到同一通道最新版视为可以直接跳级，也不要在本章将 server/agent 版本混用作为示例。本文没有执行升级、创建集群或恢复操作。

## 参考来源

- [RKE2 v1.37.1+rke2r1 官方 release 与随附组件版本](https://github.com/rancher/rke2/releases/tag/v1.37.1%2Brke2r1)
- [RKE2 releases API](https://api.github.com/repos/rancher/rke2/releases?per_page=100)（截至 2026-10-05 的 release 状态与发布时间）
- [RKE2 requirements：Linux、硬件及端口](https://docs.rke2.io/install/requirements)
- [RKE2 Quick Start](https://docs.rke2.io/install/quickstart)
- [RKE2 configuration options](https://docs.rke2.io/install/configuration)
- [Server configuration reference](https://docs.rke2.io/reference/server_config)
- [SUSE RKE2 v1.37 support matrix](https://www.suse.com/suse-rke2/support-matrix/all-supported-versions/rke2-v1-37/)
- [RKE2 backup and restore](https://docs.rke2.io/datastore/backup_restore)
- [RKE2 manual upgrades](https://docs.rke2.io/upgrades/manual)
