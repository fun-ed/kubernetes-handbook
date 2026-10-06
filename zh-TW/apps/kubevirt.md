# KubeVirt：在 Kubernetes 管理虛擬機

KubeVirt 將 VM 的期望狀態交給 Kubernetes API 與控制器協調，不是把 VM 轉成一般容器。適合希望在同一控制平面管理容器與虛擬機的情境；但會增加節點虛擬化、儲存、網路及升級責任。本文以 KubeVirt **v1.9.0** 作為固定範例，不能據此推論該版本受 Kubernetes v1.37 支援：上游發布資訊未提供此組合的相容性矩陣。

## VM、VMI 與控制器

`VirtualMachine`（VM）是持久化的管理物件，定義範本與開關機策略；`VirtualMachineInstance`（VMI）代表正在執行的一次虛擬機執行個體。VM 控制器依據 VM 的期望狀態建立／停止 VMI；刪除 VMI 不等於刪除 VM，VM 可能重新建立執行個體。直接建立的 VMI 沒有 VM 的持久生命週期管理。

Operator 安裝 CRD、RBAC、部署及升級 KubeVirt 控制平面；virt-controller 負責調和 VM/VMI 等物件；virt-handler 在節點上協調 VM 生命週期；virt-launcher Pod 承載單一 VMI 的 libvirt/QEMU 執行環境。virt-api 提供擴充 API。launcher 是虛擬機的承載 Pod，不代表 guest OS 與容器共用核心。

## 版本與節點前提

截至 2026-10-05 已核實的 KubeVirt 穩定版為 **v1.9.0**（GitHub Release，2026-07-30）。v1.9.0 官方 release assets 提供相符的安裝清單及 virtctl；不可混用其他版本的 CRD、operator 或用戶端。上游在已查閱的發布資訊中未聲明支援 Kubernetes v1.37，因此相容性未知，須在隔離測試叢集自行驗收。Kubernetes 版本基線請參閱[本手冊版本說明](../setup/kubernetes-v1.37.md)。

執行 VM 的 Linux worker 必須具備硬體虛擬化能力（通常為 x86_64 VT-x/AMD-V）、BIOS/UEFI 已啟用相應擴充，並由核心提供 KVM（`/dev/kvm`）。排程節點須有足夠 CPU、記憶體；guest vCPU/記憶體請求仍受節點可排程資源限制。使用 host-passthrough CPU 會要求遷移目標具備相容 CPU 特性，限制跨節點遷移；不能假定所有 VM 都可 live migration。不要以預設軟體模擬或放寬宿主安全政策掩蓋 KVM 不可用。先核對發行版核心、KVM 模組、SELinux/AppArmor 與 KubeVirt 官方前提。

儲存取決於 StorageClass/CSI 的存取模式及拓撲。VM 根磁碟可使用 DataVolume（須先安裝 CDI）或 PVC；遷移還需要可遷移的磁碟，以及適合併行掛載的共享儲存設定。RWO 區塊磁碟、local PV 或節點綁定卷通常無法滿足跨節點遷移；不要假定 CDI 會自動提供儲存後端。

## 隔離實驗室安裝

下列命令只適用於專用、可丟棄且具備硬體 KVM 的實驗叢集；**不會在本手冊環境執行**。先審閱 release YAML、映像來源、權限及資源影響，並確認叢集版本相容性；不要直接套用未審查的遠端檔案。

```bash
export KV=v1.9.0
export KV_RELEASE="https://github.com/kubevirt/kubevirt/releases/download/${KV}"
curl -fsSLo /tmp/kubevirt-operator.yaml "$KV_RELEASE/kubevirt-operator.yaml"
curl -fsSLo /tmp/kubevirt-cr.yaml "$KV_RELEASE/kubevirt-cr.yaml"
# 先檢視；server-side dry-run 僅驗證 Kubernetes API 可接受部分，不驗證 KubeVirt 行為。
kubectl apply --dry-run=server -f /tmp/kubevirt-operator.yaml
# 僅在審閱 YAML 並確認是專用叢集後才套用 operator。
kubectl apply -f /tmp/kubevirt-operator.yaml
# Operator 會建立 CRD；先等 CRD 註冊，再驗證與建立 KubeVirt 自訂資源。
kubectl wait --for=condition=Established --timeout=2m crd/kubevirts.kubevirt.io
kubectl apply --dry-run=server -f /tmp/kubevirt-cr.yaml
kubectl apply -f /tmp/kubevirt-cr.yaml
curl -fsSLo /tmp/virtctl "${KV_RELEASE}/virtctl-${KV}-linux-amd64"
chmod 0755 /tmp/virtctl
kubectl -n kubevirt wait kv kubevirt --for=condition=Available --timeout=10m
kubectl -n kubevirt get pods -o wide
/tmp/virtctl version
```

正式下載前請依官方 release assets 核對檔名及 checksum；上述 linux-amd64 二進位不適用其他平台。`Available` 代表 operator 回報 KubeVirt 可用，不表示所有節點皆支援 KVM，也不等於 VM 網路、儲存或遷移已通過驗收。

## VM 範本與操作

下例使用空白 PVC 磁碟，刻意不提供未核實的 containerDisk 映像標籤；須先有名為 `vm-disk` 的 PVC，且其中含可開機的 guest 磁碟映像。若沒有映像，資源不會成為可登入的系統。部署前由管理者依核准的映像流程填妥 PVC。`runStrategy: Manual` 允許透過 virtctl 手動開關機。

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

若未事先提供 PVC，VM 會因磁碟不存在／尚未綁定而無法啟動。只有 guest 設定序列主控台及可用認證時，`virtctl console` 才有用途；不要假設預設認證安全或存在。

## 診斷與維運

```bash
kubectl get kubevirt -n kubevirt
kubectl get pods -n kubevirt -o wide
kubectl get vm,vmi,pvc -A
kubectl describe vmi lab-vm -n default
kubectl get events -n default --sort-by=.lastTimestamp
kubectl get nodes -o wide
```

`Pending` 常見原因包括 PVC 尚未綁定、資源不足或沒有可用 KVM 節點；檢查 VMI/Pod events、排程條件、CSI 及 node handler 日誌。launcher 建立後仍可能因 guest 磁碟無法開機、網路設定或權限遭拒而失敗。避免直接刪除 operator、CRD 或 PVC 排除錯誤；刪除 CRD 可能移除叢集範圍的 VM 資源定義。

升級前依官方升級文件逐版確認 operator、CRD、virtctl、CDI 與 VM API 相容性，備份 VM/PVC 與 guest 資料，並先在非正式環境演練。回復映像不保證能還原已轉換的 CRD 或磁碟格式。限制 RBAC、網路政策、映像來源及節點管理權限；VM 控制平面通常具高權限，不要公開未驗證的 API 或主控台服務。

## 官方來源

- [KubeVirt v1.9.0 release 與資產](https://github.com/kubevirt/kubevirt/releases/tag/v1.9.0)
- [KubeVirt 使用者指南](https://kubevirt.io/user-guide/)
- [KubeVirt 安裝文件](https://kubevirt.io/user-guide/cluster_admin/installation/)
- [KubeVirt VM 執行策略](https://kubevirt.io/user-guide/compute/run_strategies/)
- [KubeVirt Live Migration](https://kubevirt.io/user-guide/compute/live_migration/)
- [CDI 文件](https://github.com/kubevirt/containerized-data-importer)
