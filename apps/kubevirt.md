# KubeVirt：在 Kubernetes 管理虚拟机

KubeVirt 将 VM 的期望状态交给 Kubernetes API 与控制器协调，并非把 VM 转成普通容器。适合希望在同一控制面管理容器和虚拟机的场景；它增加节点级虚拟化、存储、网络与升级责任。本文以 KubeVirt **v1.9.0** 为固定示例，不能据此推断其受 Kubernetes v1.37 支持：上游发布资料未声明该组合的兼容矩阵。

## VM、VMI 与控制器

`VirtualMachine`（VM）是可持久化的管理对象，定义模板及开关机策略；`VirtualMachineInstance`（VMI）代表一次正在运行的虚拟机实例。VM 控制器依据 VM 期望状态建立/停止 VMI；删除 VMI 不等于删除 VM，VM 可能再次创建实例。直接创建的 VMI 没有 VM 的持久生命周期管理。

Operator 安装 CRD、RBAC、部署与升级 KubeVirt 控制面；virt-controller 负责调和 VM/VMI 等对象；virt-handler 在节点上协调 VM 生命周期；virt-launcher Pod 承载单一 VMI 的 libvirt/QEMU 运行环境。virt-api 提供扩展 API。launcher 是虚拟机的承载 Pod，不表示 guest OS 与容器共享内核。

## 版本与节点前提

截点 2026-10-05 已核实的 KubeVirt 稳定版为 **v1.9.0**（GitHub Release，2026-07-30）。v1.9.0 官方 release assets 提供匹配安装清单和 virtctl；不要混用其他版本的 CRD、operator 或客户端。上游未在所查发布说明声明 Kubernetes v1.37 支持，故组合兼容性为未知，需自行在隔离测试集群验收。Kubernetes 版本基线见[本手册版本说明](../setup/kubernetes-v1.37.md)。

运行 VM 的 Linux worker 必须具备硬件虚拟化能力（通常 x86_64 VT-x/AMD-V）、BIOS/UEFI 已启用相应扩展，并由内核提供 KVM（`/dev/kvm`）。调度节点需有足够 CPU、内存；guest vCPU/内存请求仍受节点调度资源约束。使用 host-passthrough CPU 会要求迁移目标具有兼容 CPU 特性，限制跨节点迁移；不能把 live migration 当成所有 VM 都可用。不要以默认软件模拟或放宽宿主安全策略来掩盖 KVM 缺失。先核对发行版内核、KVM 模块、SELinux/AppArmor 与 KubeVirt 官方先决条件。

存储依赖具体 StorageClass/CSI 的访问模式和拓扑。VM 根盘可用 DataVolume（需先安装 CDI）或 PVC；迁移还要求可迁移磁盘与适合并发挂载的共享存储配置。RWO 块盘、local PV 或节点绑定卷通常无法满足跨节点迁移；不要假定 CDI 自动提供存储后端。

## 隔离实验室安装

以下命令只适用于专用、可丢弃且具备硬体 KVM 的实验丛集；**不会在本手册环境执行**。先审阅 release YAML、映像来源、权限及资源影响，并确认丛集版本相容性；不要直接套用未审查的远端档案。

```bash
export KV=v1.9.0
export KV_RELEASE="https://github.com/kubevirt/kubevirt/releases/download/${KV}"
curl -fsSLo /tmp/kubevirt-operator.yaml "$KV_RELEASE/kubevirt-operator.yaml"
curl -fsSLo /tmp/kubevirt-cr.yaml "$KV_RELEASE/kubevirt-cr.yaml"
# 先检视 operator 清单；dry-run 只验证 API 可接受部分，不验证 KubeVirt 行为。
kubectl apply --dry-run=server -f /tmp/kubevirt-operator.yaml
# 仅在审阅 YAML 并确认是专用丛集后才套用 operator。
kubectl apply -f /tmp/kubevirt-operator.yaml
# Operator 会建立 CRD；先等 CRD 注册，再验证与建立 KubeVirt 自订资源。
kubectl wait --for=condition=Established --timeout=2m crd/kubevirts.kubevirt.io
kubectl apply --dry-run=server -f /tmp/kubevirt-cr.yaml
kubectl apply -f /tmp/kubevirt-cr.yaml
curl -fsSLo /tmp/virtctl "${KV_RELEASE}/virtctl-${KV}-linux-amd64"
chmod 0755 /tmp/virtctl
kubectl -n kubevirt wait kv kubevirt --for=condition=Available --timeout=10m
kubectl -n kubevirt get pods -o wide
/tmp/virtctl version
```
正式下载前请依官方 release assets 核对档名及 checksum；上述 linux-amd64 二进位不适用其他平台。`Available` 表示 operator 回报 KubeVirt 可用，不表示节点皆支援 KVM，也不等于 VM 网路、储存或迁移已验收成功。

## VM 范本与操作

下例使用空白 PVC 磁碟，刻意不提供未核实的 containerDisk 映像标签；需先有名为 `vm-disk` 的 PVC，且其中有可启动 guest 磁碟映像。若无映像，资源不会成为可登入的系统。部署前由管理者依批准的映像流程填入 PVC。`runStrategy: Manual` 允许通过 virtctl 手动开关机。

```yaml
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: lab-vm
  namespace: default
spec:
  runStrategy: Manual
  template:
    metadata:
      labels:
        kubevirt.io/domain: lab-vm
    spec:
      domain:
        resources:
          requests:
            memory: 1Gi
        devices:
          disks:
            - name: rootdisk
              disk:
                bus: virtio
      volumes:
        - name: rootdisk
          persistentVolumeClaim:
            claimName: vm-disk
```

```bash
kubectl apply -f lab-vm.yaml
kubectl get vm,vmi,pod -n default -o wide
kubectl describe vm lab-vm -n default
/tmp/virtctl console lab-vm -n default
/tmp/virtctl stop lab-vm -n default
```

若未预先供应 PVC，建立 VM 会因卷不存在/未绑定而无法启动。`virtctl console` 只在 guest 有序列主控台设定与可用认证时有用；不要把预设认证假定为安全或存在。

## 诊断与维运

```bash
kubectl get kubevirt -n kubevirt
kubectl get pods -n kubevirt -o wide
kubectl get vm,vmi,pvc -A
kubectl describe vmi lab-vm -n default
kubectl get events -n default --sort-by=.lastTimestamp
kubectl get nodes -o wide
```

`Pending` 常见原因是 PVC 未绑定、资源不足或缺少可用 KVM 节点；查看 VMI/Pod events、排程条件、CSI 与 node handler 日志。launcher 建立后仍可能因 guest 磁碟不可启动、网路配置或权限被拒而失败。避免直接删除 operator、CRD 或 PVC 来清错；删除 CRD 可能移除丛集范围的 VM 资源定义。

升级前依官方升级文件逐版确认 operator、CRD、virtctl、CDI 与 VM API 相容性，备份 VM/PVC 与 guest 资料，先在非正式环境演练。回复映像不保证能回复已转换的 CRD 或磁碟格式。限定 RBAC、网路政策、映像来源与节点管理权限；VM 控制面通常具有高权限，不要公开未验证的 API 或 console 服务。

## 官方来源

- [KubeVirt v1.9.0 release 与资产](https://github.com/kubevirt/kubevirt/releases/tag/v1.9.0)
- [KubeVirt 使用者指南](https://kubevirt.io/user-guide/)
- [KubeVirt 安装文件](https://kubevirt.io/user-guide/cluster_admin/installation/)
- [KubeVirt VM 执行策略](https://kubevirt.io/user-guide/compute/run_strategies/)
- [KubeVirt Live Migration](https://kubevirt.io/user-guide/compute/live_migration/)
- [CDI 文件](https://github.com/kubevirt/containerized-data-importer)
