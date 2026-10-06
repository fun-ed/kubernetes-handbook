# 使用 k0s 部署 Kubernetes v1.36.4

本指南依截至 **2026-10-05** 可查得的最新稳定 k0s 发布版撰写：**v1.36.4+k0s.1**，GitHub Releases API 记录发布时间为 **2026-09-19 21:23:36 UTC**（`draft=false`、`prerelease=false`）。该发行版内建 Kubernetes v1.36.4，不是 v1.37；若要求 v1.37，请选择已发布且明确包含 v1.37 的发行版，不要把 k0s 的发行版号直接改成 v1.37.1。k0s 适合快速建立单节点教学环境、边缘节点或自行管理的 Linux 丛集；本页的单节点做法不适用高可用或正式环境。

> k0s 的 API 与安装方式以其版本化官方文件为准。发行版标签上的 upstream 元件 pin，不等于各元件宣告支援 Kubernetes v1.37。参考[本手册 v1.37.1 适配基线](../kubernetes-v1.37.md)与[元件版本清单](../component-versions.md)。

## 主机前置需求

本例以 Linux、systemd、单一 x86-64/ARM64 主机示范；k0s 官方亦测试多种 Linux 发行版。官方最低估算为 controller+worker 1 vCPU、1 GB RAM、约 2 GB k0s 磁碟空间，实际主机与工作负载需要额外资源。使用 SSD 较适合储存效能。确认 hostname 唯一、主机时间正确、可连线至映像档登录站，且防火墙允许所选部署角色所需的 Kubernetes API（预设 TCP 6443）、k0s API（TCP 9443）及丛集网路流量。详细连接埠与 OS 需求见[k0s 系统需求](https://docs.k0sproject.io/v1.36.4+k0s.1/system-requirements/)及[网路设定](https://docs.k0sproject.io/v1.36.4+k0s.1/networking/)。

k0s 将 containerd 整合在发行版中，不需要另外安装 CRI runtime；不能因此省略 Linux 核心、网路、储存、cgroup 与防火墙需求。单节点教学使用预设 Kube-router CNI、etcd 资料存放区与 systemd 服务。不要在同一丛集另装第二套 CNI。

## 固定版本下载与安装

以下使用官方 GitHub Release asset，不使用会追随最新版本的 `get.k0s.sh` 安装器。API 公布的 Linux amd64 asset SHA-256 为 `18c304d53cdd70095e99c6b859b269b4fef0bb84579d7e7185271a9135694a31`；其他架构请从同一 release API 查核相符 asset 的 SHA-256 后再下载。

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

只有摘要比对成功且版本输出符合预期才继续。摘要是 GitHub Release API asset metadata 提供的值，仍应在可信来源核对发布资讯；正式供应链流程可再依该发行版提供的签章验证步骤检查二进位档。

## 设定并启动单节点丛集

从仓库根目录执行以下命令。本页将控制平面和工作节点放在同一台主机，供隔离的教学用途。范例设定档是 k0s 原生 `ClusterConfig`，不是 Kubernetes API 物件，位于 [`samples/k0s/k0s.yaml`](samples/k0s/k0s.yaml)。CIDR 必须先确认不与主机、VPN、云端 VPC 或其他路由网段重叠；丛集初始化后变更网路 provider 通常需要重新布建。

```bash
sudo install -d -o root -g root -m 0755 /etc/k0s
sudo install -o root -g root -m 0600 setup/cluster/samples/k0s/k0s.yaml /etc/k0s/k0s.yaml
sudo k0s config validate --config /etc/k0s/k0s.yaml
sudo k0s install controller --enable-worker --no-taints -c /etc/k0s/k0s.yaml
sudo k0s start
sudo k0s status
```

`k0s config validate --config` 是 v1.36.4+k0s.1 官方 CLI 支援的本机设定档验证命令；此处未执行主机安装。以 `--enable-worker --no-taints` 让这台 controller 也承载一般工作负载，并保留日后加入 worker 的方式。不要使用 `--single`：官方文件说明它会停用扩充为多节点所需功能。服务由 systemd 管理；systemd 主机可用 `sudo systemctl status k0scontroller` 检查服务。

从 k0s 产生独立 kubeconfig，限制档案权限并明确指定它，避免误用目前使用者的 `kubectl` context：

```bash
install -d -m 0700 "$HOME/.kube"
umask 077
sudo k0s kubeconfig admin > "$HOME/.kube/k0s-admin.conf"
chmod 0600 "$HOME/.kube/k0s-admin.conf"
export KUBECONFIG="$HOME/.kube/k0s-admin.conf"
kubectl get nodes -o wide
kubectl get pods -A
```

管理 kubeconfig 具有高权限；不要提交至版本控制、贴入公开工单或复制到不受信任装置。多丛集操作时使用 `kubectl --kubeconfig "$HOME/.kube/k0s-admin.conf" ...`，再三确认目标丛集。

## 加入 worker 与 token 保护

worker 安装前要先将相同版本的 k0s 二进位档安全地放到该节点，并确认 controller IP、API 连接埠及 k0s 网路连线可达。在 controller 建立有期限的 worker join token，token 是可用于加入丛集的凭证：

```bash
sudo sh -c 'umask 077; k0s token create --role=worker --expiry=24h > /root/k0s-worker-token'
```

透过受保护的管理通道将 token 传给 worker 操作者，不要放入 shell history、聊天、Git 或一般日志；确认使用后删除副本。worker 上以权限受限的 token file 安装：

```bash
sudo k0s install worker --token-file /root/k0s-worker-token
sudo k0s start
```

token 含 bootstrap 认证资料；遗失或外泄时视同凭证泄漏，应依官方 token 管理流程撤销／轮替并检查加入记录。官方步骤见[k0s 多节点手动安装](https://docs.k0sproject.io/v1.36.4+k0s.1/k0s-multi-node/)。

## DNS、网路与工作负载检查

下列命令全部使用上方指定的 k0s kubeconfig。先等待节点与系统 Pod 就绪，再以短期测试 Pod 验证 DNS、Service 网路及工作负载执行；此步骤会建立并删除教学资源。

```bash
kubectl --kubeconfig "$HOME/.kube/k0s-admin.conf" wait --for=condition=Ready nodes --all --timeout=5m
kubectl --kubeconfig "$HOME/.kube/k0s-admin.conf" get pods -A
kubectl --kubeconfig "$HOME/.kube/k0s-admin.conf" run dns-check --image=busybox:1.37.0 --restart=Never --command -- sleep 300
kubectl --kubeconfig "$HOME/.kube/k0s-admin.conf" wait --for=condition=Ready pod/dns-check --timeout=2m
kubectl --kubeconfig "$HOME/.kube/k0s-admin.conf" exec dns-check -- nslookup kubernetes.default.svc.cluster.local
kubectl --kubeconfig "$HOME/.kube/k0s-admin.conf" delete pod dns-check --wait=true
```

若节点或 DNS 未就绪，先查看 `sudo journalctl -u k0scontroller`、`kubectl get pods -A` 和网路/防火墙设定，不要用另一套 CNI 掩盖问题。测试映像档标签是教学例，正式部署应固定经审核的映像档版本或 digest。

## 备份、升级与移除

升级前先阅读该 k0s 版本的升级说明；逐次确认 Kubernetes minor skew、k0s 自动升级相容限制、外挂支援矩阵和升级顺序。在 controller 上建立并异地保管加密备份，并于隔离环境演练还原：

```bash
sudo install -d -m 0700 /var/backups/k0s
sudo k0s backup --save-path=/var/backups/k0s
```

k0s 备份涵盖其管理的凭证、etcd 或 Kine/SQLite 快照、设定及部分 k0s 管理资源；**不含应用程式 PersistentVolume 资料，也不含手动变更或外部资料库内容**。需另外备份应用程式资料、PV、外部 datastore 和丛集外基础设施。不要直接覆盖二进位档或假设降版能回复资料；只依版本化官方[升级](https://docs.k0sproject.io/v1.36.4+k0s.1/upgrade/)及[备份还原](https://docs.k0sproject.io/v1.36.4+k0s.1/backup/)程序规划。

移除 `k0s reset` 会清除服务、资料目录、容器、挂载与网路命名空间，并可能影响主机上其他网路设定；**此命令具破坏性，本指南不自动执行**。只有确认是专用、可销毁的教学主机且已备份需要的资料后，才依官方卸载程序手动操作；不得在共用或正式主机照贴执行。

## 官方来源

- [k0s v1.36.4+k0s.1 GitHub release 与 API 资产](https://github.com/k0sproject/k0s/releases/tag/v1.36.4%2Bk0s.1) · [GitHub Releases API](https://api.github.com/repos/k0sproject/k0s/releases/latest)
- [版本化官方文件](https://docs.k0sproject.io/v1.36.4+k0s.1/) · [设定参考](https://docs.k0sproject.io/v1.36.4+k0s.1/configuration/) · [CLI 设定验证](https://docs.k0sproject.io/v1.36.4+k0s.1/cli/k0s_config_validate/)
- [系统需求](https://docs.k0sproject.io/v1.36.4+k0s.1/system-requirements/) · [单节点快速入门](https://docs.k0sproject.io/v1.36.4+k0s.1/install/) · [备份与还原](https://docs.k0sproject.io/v1.36.4+k0s.1/backup/)
