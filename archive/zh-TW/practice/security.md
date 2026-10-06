# 安全

從安全的角度來看，Kubernetes 中包含如下圖所示的潛在攻擊面：

![](../../.gitbook/assets/attach-vectors%20%281%29.png)

（圖片來自《Kubernetes Security - Operating Kubernetes Clusters and Applications Safely》）

為了保證叢集以及容器應用的安全，Kubernetes 提供了多種安全機制，限制容器的行為，減少容器和叢集的攻擊面，保證整個系統的安全性。

* Security Context：用 Capabilities、`runAsNonRoot`、只讀根檔案系統、seccomp、SELinux 與 AppArmor 限制容器行為；
* User Namespaces：在支援的 Linux 節點與 CRI runtime 上隔離容器和主機使用者 ID；並非所有 Pod、卷或 runtime 都適用；
* Pod Security Admission（PSA）：用 namespace 標籤實施 Pod Security Standards；PodSecurityPolicy（PSP）已移除；
* Sysctls：容器可設定的核心引數分為安全與非安全項；
* AppArmor：在支援的 Linux 節點上限制應用存取；
* Network Policies：按 CNI 能力控制 Pod 網路存取；
* Seccomp：透過允許列表限制容器應用可執行的系統呼叫。

除此之外，推薦儘量使用較新版本的 Kubernetes，因為它們通常會包含常見安全問題的修復。你可以參考 [kubernetes-announce](https://groups.google.com/forum/#!forum/kubernetes-announce) 來查詢最新的 Kubernetes 釋出情況，也可以參考 [cvedetails.com](https://www.cvedetails.com/version-list/15867/34016/1/Kubernetes-Kubernetes.html) 查詢 Kubernetes 各個版本的 CVE \(Common Vulnerabilities and Exposures\) 列表。
新部署應優先使用穩定 API 與顯式的工作負載安全上下文。PSP 已在 Kubernetes v1.25 移除；當前基線應使用[Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)和[Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)。

## 叢集安全

* Kubernetes 元件（如 kube-apiserver、etcd、kubelet 等）只開放受保護的 API 並啟用 TLS。
* 開啟 RBAC 授權，賦予工作負載最小權限，並啟用 NodeRestriction 准入控制。
  * 需要更豐富的策略時，可評估 OPA/Gatekeeper 等額外策略元件。
* 加密 etcd 中的 Secret，並設定 etcd TLS。
* 禁止 Kubelet 匿名存取和只讀連接埠，啟用客戶端證書輪換。
* 對不需要 API 存取的工作負載關閉 ServiceAccount token 自動掛載；確需存取時使用專用 ServiceAccount 與最小 RBAC 權限。預設投射 token 可自動輪換，不要建立長期有效的 token Secret。
* 透過最小 RBAC 限制 Dashboard 等管理介面，並避免公開管理 endpoint。
* 按對應 Kubernetes 版本執行 CIS Benchmark 等基線檢查，並跟蹤安全公告和 CVE。
* 多租戶環境可按風險評估執行時隔離與服務身分方案；它們不能替代 Kubernetes API authorization 與 NetworkPolicy。

## TLS 安全

為保障 TLS 安全，並避免 [Zombie POODLE and GOLDENDOODLE Vulnerabilities](https://blog.qualys.com/technology/2019/04/22/zombie-poodle-and-goldendoodle-vulnerabilities)，請為 TLS 1.2 禁止 CBC \(Cipher Block Chaining\) 模式。

你可以使用 [https://www.ssllabs.com/](https://www.ssllabs.com/) 來測試 TLS 的安全問題。

## PodSecurityPolicy（已移除）與 Security Context

> 以下 PSP YAML 使用 `extensions/v1beta1` 和 alpha annotation，**無法應用於 Kubernetes v1.37**。PSP 在 v1.25 移除；不要恢復舊 API 或 feature gate。以 PSA namespace 標籤和 Pod 安全上下文替代。

```yaml
apiVersion: extensions/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted
  annotations:
    # Seccomp v1.11 使用 'runtime/default'，而 v1.10 及更早版本使用 'docker/default'
    seccomp.security.alpha.kubernetes.io/allowedProfileNames: 'runtime/default'
    seccomp.security.alpha.kubernetes.io/defaultProfileName:  'runtime/default'
    apparmor.security.beta.kubernetes.io/allowedProfileNames: 'runtime/default'
    apparmor.security.beta.kubernetes.io/defaultProfileName:  'runtime/default'
spec:
  privileged: false
  # Required to prevent escalations to root.
  allowPrivilegeEscalation: false
  # This is redundant with non-root + disallow privilege escalation,
  # but we can provide it for defense in depth.
  requiredDropCapabilities:
    - ALL
  # Allow core volume types.
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    # Assume that persistentVolumes set up by the cluster admin are safe to use.
    - 'persistentVolumeClaim'
  hostNetwork: false
  hostIPC: false
  hostPID: false
  runAsUser:
    # Require the container to run without root privileges.
    rule: 'MustRunAsNonRoot'
  seLinux:
    # This policy assumes the nodes are using AppArmor rather than SELinux.
    rule: 'RunAsAny'
  supplementalGroups:
    rule: 'MustRunAs'
    ranges:
      # Forbid adding the root group.
      - min: 1
        max: 65535
  fsGroup:
    rule: 'MustRunAs'
    ranges:
      # Forbid adding the root group.
      - min: 1
        max: 65535
  readOnlyRootFilesystem: false
```

完整參考見[這裡](../../concepts/objects/security-context.md)。
## Pod Security Admission（當前推薦）

在應用 namespace 明確設定 `enforce`、`audit` 和 `warn` 等級，並按需固定策略版本。先使用 `warn`/`audit` 找出不符合項，再啟用 `enforce`，避免阻斷現有部署。PSA 不會像舊 PSP 一樣自動 mutation；工作負載本身應設定必要的安全上下文。

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: restricted-workloads
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: v1.37
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: v1.37
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: v1.37
```

`restricted` 通常要求非 root 使用者、`RuntimeDefault` 或受管的 seccomp profile、禁止提權，並 drop 所有 capabilities（需要時只能新增該級別明確允許的 capability）。
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: restricted-example
  namespace: restricted-workloads
spec:
  securityContext:
    runAsNonRoot: true
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: app
      image: registry.k8s.io/pause:3.10.2
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: ["ALL"]
```

不需要存取 Kubernetes API 的 Pod 應關閉 token 自動掛載；確需存取時，為應用繫結最小 RBAC 權限並使用預設投射、可輪換的 ServiceAccount token。參見[ServiceAccount token 文件](https://kubernetes.io/docs/concepts/security/service-accounts/)。
詳細規則見[Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)、[Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)與[Security Context 文件](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)。

## User Namespaces（使用者名稱空間，v1.36 GA）

User Namespaces 自 Kubernetes v1.36 起為穩定功能（最早於 v1.28 引入），由 Pod 顯式設定 `spec.hostUsers: false` opt in；不是預設啟用。該功能透過 Linux user namespace 隔離容器程序的 UID/GID 與主機 UID/GID，可降低容器逃逸對主機或同節點 Pod 的影響，但不能替代其他安全措施。

這是 Linux-only 功能。官方要求節點及 Pod 卷檔案系統支援 idmapped mounts（實踐中至少 Linux 6.3），OCI runtime 支援 user namespace（runc 1.2+ 或 crun 1.9+）；CRI runtime 支援要求為 containerd 2.0+ 或 CRI-O 1.25+。上線前核對[官方 User Namespaces 指南](https://kubernetes.io/docs/concepts/workloads/pods/user-namespaces/)和每種儲存卷的支援。以下 manifest 中的映像檔名稱是佔位符，需替換為受信任的固定版本。

### 安全最佳實踐

1. **高安全性工作負載**：僅當節點核心、CRI runtime、儲存驅動均符合上方條件且已驗證相容後，才考慮讓 Pod opt-in 使用 user namespace。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-workload
spec:
  hostUsers: false  # 启用用户命名空间
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
  containers:
  - name: app
    image: myapp:latest
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
```

2. **多租戶環境**：user namespace 可限制主機 root 和 capabilities 的作用範圍、降低部分容器逃逸的影響；它不是租戶間完整的安全邊界。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: tenant-app
  labels:
    tenant: tenant-a
spec:
  hostUsers: false
  securityContext:
    runAsUser: 1001
    runAsGroup: 1001
    fsGroup: 1001
  containers:
  - name: app
    image: tenant-app:v1.0
    securityContext:
      runAsNonRoot: true
      allowPrivilegeEscalation: false
```

3. **傳統應用遷移**：對於需要以 root 身分執行的傳統應用，使用者名稱空間允許在不犧牲安全性的情況下執行：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: legacy-app
spec:
  hostUsers: false
  containers:
  - name: legacy
    image: legacy-app:latest
    securityContext:
      runAsUser: 0  # 容器内 root，但映射到主机非特权用户
```

### 安全優勢

- **潛在影響**：將容器 UID/GID 對映到宿主機非特權使用者，可降低部分容器逃逸造成的主機影響；
- **能力範圍**：容器 capabilities 在該 user namespace 外無效或受限，具體行為按 Linux 文件與 runtime 實現驗證；
- **檔案和卷**：所有檔案系統和卷必須支援 idmapped mounts；不同檔案 owner mapping 仍需測試；
### 注意事項
- **核心與檔案系統**：節點及 Pod 卷檔案系統需支援 idmapped mounts；Kubernetes 文件給出的實踐要求至少 Linux 6.3。
- **OCI/CRI runtime**：需支援 user namespace。官方文件列出 runc 1.2+ 或 crun 1.9+，以及 containerd 2.0+ 或 CRI-O 1.25+。
- **卷與應用相容性**：按當前 Kubernetes 文件及 CSI/檔案系統限制驗證；特權操作、host namespace 與不支援的掛載組合可能不可用。

### 部署建議

1. **逐步推廣**：從非關鍵工作負載開始，逐步擴充套件到生產環境
2. **測試驗證**：在啟用前充分測試應用的相容性
3. **監控觀察**：部署後密切監控應用行為和效能指標
4. **策略制定**：為不同型別的工作負載制定使用者名稱空間使用策略

## Supplemental Groups Policy（補充組策略）
本節說明 `supplementalGroupsPolicy: Strict` 如何避免將映像檔 `/etc/group` 中額外組併入容器程序。正式啟用前請檢查官方[安全上下文文件](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)與每個 Node 的 `status.features.supplementalGroupsPolicy`；CRI runtime 需支援該功能。
標題和後續版本描述從 v1.33 Beta 階段的資料整理而來，不代表 v1.37 的功能門控狀態。不要照搬舊 feature-gate 命令；在不支援的節點上，Pod 可能無法啟動。

### 安全風險

預設情況下，Kubernetes 會將容器映像檔中 `/etc/group` 定義的組資訊與 Pod 指定的組資訊**合併**，這可能帶來安全風險：

- **隱式權限提升**：容器可能獲得未在 Pod 清單中宣告的組權限
- **策略繞過**：安全策略引擎無法檢測這些隱式組
- **卷存取風險**：意外的組成員身分可能導致對敏感卷的未授權存取

### 使用 Strict 策略

透過設定 `supplementalGroupsPolicy: Strict`，可以確保只有明確指定的組被附加到容器程序：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
    supplementalGroups: [4000]
    supplementalGroupsPolicy: Strict  # 排除隐式组
  containers:
  - name: app
    image: registry.k8s.io/pause:3.10.2
    securityContext:
      allowPrivilegeEscalation: false
```

### 最佳實踐

1. **預設使用 Strict 策略**：對於新部署的應用，建議預設使用 Strict 策略：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: production-app
spec:
  securityContext:
    supplementalGroupsPolicy: Strict
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 2000
  containers:
  - name: app
    image: registry.k8s.io/pause:3.10.2
```

2. **策略強制執行**：透過准入控制器或 OPA 策略強制所有 Pod 使用 Strict 策略：

```yaml
# OPA Rego 策略示例
deny[msg] {
  input.kind == "Pod"
  not input.spec.securityContext.supplementalGroupsPolicy
  msg := "Pod must specify supplementalGroupsPolicy"
}

deny[msg] {
  input.kind == "Pod"
  input.spec.securityContext.supplementalGroupsPolicy != "Strict"
  msg := "Pod must use supplementalGroupsPolicy: Strict"
}
```

3. **審計現有工作負載**：使用 Pod 狀態中的使用者資訊審計現有工作負載的組成員身分：

```bash
# 查看容器的实际组成员身份
kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[0].user.linux}'
```

4. **逐步遷移策略**：
   - **階段 1**：審計並記錄現有 Pod 的隱式組
   - **階段 2**：在非生產環境測試 Strict 策略
   - **階段 3**：為新應用預設啟用 Strict 策略
   - **階段 4**：逐步遷移現有應用到 Strict 策略

### 升級注意事項

如果您的叢集已經在使用 `supplementalGroupsPolicy: Strict`：

1. **確保 CRI 執行時支援**：
   - containerd v2.0+
   - CRI-O v1.31+

2. **檢查節點支援**：
```bash
kubectl get nodes -o custom-columns=NAME:.metadata.name,SUPPORTED:.status.features.supplementalGroupsPolicy
```

3. **處理不支援的節點**：
   - 升級 CRI 執行時
   - 只有在 Node Feature Discovery 或其他機制已顯式建立相應 label 時，才可用該 label 透過 nodeSelector 避免排程到不支援的節點；`status.features` 不會自動建立該 label。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: strict-policy-pod
spec:
  nodeSelector:
    feature.node.kubernetes.io/supplementalGroupsPolicy: "true"
  securityContext:
    supplementalGroupsPolicy: Strict
  containers:
  - name: app
    image: registry.k8s.io/pause:3.10.2
```

## Sysctls

Sysctls 允許容器設定核心引數，分為安全 Sysctls 和非安全 Sysctls

* 安全 Sysctls：即設定後不影響其他 Pod 的核心選項，只作用在容器 namespace 中，預設開啟。包括以下幾種
  * `kernel.shm_rmid_forced`
  * `net.ipv4.ip_local_port_range`
  * `net.ipv4.tcp_syncookies`
* 非安全 sysctl 可能影響其他 Pod 或節點服務，預設禁止。只有在確認隔離邊界與工作負載需求後，才由管理員按當前 kubelet `allowedUnsafeSysctls` 設定顯式允許；不要使用已淘汰的 `--experimental-allowed-unsafe-sysctls` 或 PSP 設定。
> 以下 PSP/sysctl API 範例是歷史內容：PSP 在 Kubernetes v1.25 移除。非安全 sysctl 應按當前 kubelet 設定與[官方 sysctl 文件](https://kubernetes.io/docs/tasks/administer-cluster/sysctl-cluster/)管理。

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: sysctl-psp
spec:
  allowedUnsafeSysctls:
  - kernel.msg*
  forbiddenSysctls:
  - kernel.shm_rmid_forced
```

而 v1.10 及更早版本則為 Alpha 階段，需要透過 Pod annotation 設定，如：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sysctl-example
  annotations:
    security.alpha.kubernetes.io/sysctls: kernel.shm_rmid_forced=1
    security.alpha.kubernetes.io/unsafe-sysctls: net.ipv4.route.min_pmtu=1000,kernel.msgmax=1 2 3
spec:
  ...
```

## AppArmor

[AppArmor\(Application Armor\)](http://wiki.apparmor.net/index.php/AppArmor_Core_Policy_Reference) 是 Linux 核心的一個安全模組，允許系統管理員將每個程式與一個安全設定檔案關聯，從而限制程式的功能。透過它你可以指定程式可以讀、寫或執行哪些檔案，是否可以開啟網路連接埠等。作為對傳統 Unix 的自主存取控制模組的補充，AppArmor 提供了強制存取控制機制。

在使用 AppArmor 之前需要注意

AppArmor 支援取決於 Linux 節點、核心、profile 與容器執行時。v1.37 欄位和範例見[官方 Security Context 文件](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)；本節早期 PSP annotation、feature gate、Docker-only 要求與舊欄位只作歷史參考。

當前 Pod 使用穩定的 `appArmorProfile` 欄位，不再使用下方舊 annotation：
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: apparmor-example
spec:
  securityContext:
    appArmorProfile:
      type: RuntimeDefault
  containers:
    - name: app
      image: busybox:1.37.0
      command: ["sh", "-c", "sleep 1h"]
```
自定義 `Localhost` profile 必須預先載入到所有可能排程該 Pod 的節點；具體步驟和欄位見[官方 AppArmor 指南](https://kubernetes.io/docs/tutorials/security/apparmor/)。
本節隨後仍保留了 Kubernetes v1.30 前的舊 annotation 範例，僅作為歷史材料。

* `runtime/default`: 使用 Container Runtime 的預設設定
* `localhost/<profile_name>`: 使用已載入到核心的 AppArmor profile

```bash
$ sudo apparmor_parser -q <<EOF
#include <tunables/global>

profile k8s-apparmor-example-deny-write flags=(attach_disconnected) {
  #include <abstractions/base>

  file,

  # Deny all file writes.
  deny /** w,
}
EOF'

$ kubectl create -f /dev/stdin <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: hello-apparmor
  annotations:
    container.apparmor.security.beta.kubernetes.io/hello: localhost/k8s-apparmor-example-deny-write
spec:
  containers:
  - name: hello
    image: busybox
    command: ["sh", "-c", "echo'Hello AppArmor!'&& sleep 1h"]
EOF
pod "hello-apparmor" created

$ kubectl exec hello-apparmor cat /proc/1/attr/current
k8s-apparmor-example-deny-write (enforce)

$ kubectl exec hello-apparmor touch /tmp/test
touch: /tmp/test: Permission denied
error: error executing remote command: command terminated with non-zero exit code: Error executing in Docker Container: 1
```

## Seccomp

[Seccomp](https://www.kernel.org/doc/Documentation/prctl/seccomp_filter.txt) 是 Secure computing mode 的縮寫，它是 Linux 核心提供的一個操作，用於限制一個程序可以執行的系統呼叫．Seccomp 需要有一個設定檔案來指明容器程序允許和禁止執行的系統呼叫。
當前 seccomp 推薦在 Pod 或 container 的 `securityContext` 使用結構化欄位；通常可從預設 profile 開始：

```yaml
securityContext:
  seccompProfile:
    type: RuntimeDefault
```

本節下方的本地 JSON profile、舊 annotation 與 Docker 輸出是歷史設定說明。目錄與 runtime 行為應按當前[kubelet seccomp 文件](https://kubernetes.io/docs/tutorials/security/seccomp/)核對。

在 Kubernetes 中，需要將 seccomp 設定檔案放到 `/var/lib/kubelet/seccomp` 目錄中（可以透過 kubelet 選項 `--seccomp-profile-root` 修改）。比如禁止 chmod 的格式為

```bash
$ cat /var/lib/kubelet/seccomp/chmod.json
{
    "defaultAction": "SCMP_ACT_ALLOW",
    "syscalls": [
        {
            "name": "chmod",
            "action": "SCMP_ACT_ERRNO"
        }
    ]
}
```

舊版 Kubernetes 中的 Seccomp 設定曾處於 Alpha 階段並透過 Pod annotation 指定，包括：

* `security.alpha.kubernetes.io/seccomp/pod`：應用到該 Pod 的所有容器
* `security.alpha.kubernetes.io/seccomp/container/<container name>`：應用到指定容器

而 value 有三個選項

* `runtime/default`: 使用 Container Runtime 的預設設定
* `unconfined`: 允許所有系統呼叫
* `localhost/<profile-name>`: 使用 Node 本地安裝的 seccomp，需要放到 `/var/lib/kubelet/seccomp` 目錄中

比如使用剛才建立的 seccomp 設定：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: trustworthy-pod
  annotations:
    seccomp.security.alpha.kubernetes.io/pod: localhost/chmod
spec:
  containers:
    - name: trustworthy-container
      image: sotrustworthy:latest
```

## kube-bench
> **舊版命令，不可直接用於 v1.37**：本節後面的未固定 `aquasec/kube-bench:latest`、Docker 容器掛載和 handbook `master` Job YAML 未按 Kubernetes v1.37/CIS 基線驗證；不要直接在生產節點或叢集執行。選擇與目標 CIS Kubernetes Benchmark 版本匹配的 kube-bench release，從[上游安裝文件](https://github.com/aquasecurity/kube-bench)獲取當前清單並審查其宿主機掛載、權限和映像檔後再測試。

[kube-bench](https://github.com/aquasecurity/kube-bench) 提供了一個簡單的工具來檢查 Kubernetes 的設定（包括 master 和 node）是否符合最佳的安全實踐（基於 [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes/)）。

是否在生產叢集執行 kube-bench，應結合目標 CIS 基線、發行版、所需宿主機存取與權限、資源許可和變更視窗評估；掃描結果不能替代安全設定審查。

安裝 `kube-bench`：

```bash
$ docker run --rm -v `pwd`:/host aquasec/kube-bench:latest install
$ ./kube-bench <master|node>
```

當然，kube-bench 也可以直接在容器內執行，比如通常對 Master 和 Node 的檢查命令分別為：

```bash
$ kubectl apply -f https://github.com/fun-ed/kubernetes-handbook/raw/main/examples/job-master.yaml
job.batch/kube-bench-master created

$ kubectl apply -f https://github.com/fun-ed/kubernetes-handbook/raw/main/examples/job-node.yaml
job.batch/kube-bench-node created

# Wait for a few seconds for the job to complete
$ kubectl get pods
NAME                      READY   STATUS      RESTARTS   AGE
kube-bench-master-k7jdd   0/1     Completed   0          2m15s
kube-bench-node-p9sl9     0/1     Completed   0          2m15s

# The results are held in the pod's logs
$ kubectl logs kube-bench-master-k7jdd
[INFO] 1 Master Node Security Configuration
[INFO] 1.1 API Server
...
```

## 映像檔拉取憑證（v1.33 時代的歷史狀態）
> 本節起的映像檔憑證說明停留在 v1.33/v1.34 的狀態；其中功能閘門（feature gate）、Alpha/Beta 與「未來計畫」的描述都不適用於 v1.37。請勿照抄本節的功能閘門命令，並以目前的[映像檔文件](https://kubernetes.io/docs/concepts/containers/images/)及[kubelet 憑證提供者文件](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-credential-provider/)為準。
### Kubelet 憑證提供者的服務帳戶權杖整合

Kubernetes v1.33 引入了 **Kubelet 憑證提供者的服務帳戶權杖整合**（Service Account Token Integration for Kubelet Credential Providers，Alpha 功能），這項安全改進允許使用 Pod 專屬的服務帳戶權杖取得映像檔倉庫憑證，因此不必再使用長期有效的映像檔拉取金鑰。

#### 現有問題

目前，Kubernetes 管理員在處理私有容器映像檔拉取時主要有兩種選擇：

1. **儲存在 Kubernetes API 中的映像檔拉取金鑰**
   - 這些金鑰通常是長期有效的，因為很難輪換
   - 必須顯式附加到服務帳戶或 Pod
   - 金鑰洩露可能導致未授權的映像檔存取

2. **Kubelet 憑證提供程式**
   - 這些提供程式在節點級別動態獲取憑證
   - 在節點上執行的任何 Pod 都可以存取相同的憑證
   - 沒有按工作負載隔離，增加了安全風險

這兩種方法都不符合**最小權限**和**臨時認證**的原則，給 Kubernetes 留下了安全缺口。

#### 解決方案

新的增強功能使 kubelet 憑證提供程式能夠在獲取映像檔倉庫憑證時使用**工作負載身分**。憑證提供程式可以使用服務帳戶權杖來請求與特定 Pod 身分繫結的短期憑證，而不是依賴長期有效的金鑰。

這種方法提供了：

- **特定於工作負載的認證**：映像檔拉取憑證的範圍限定為特定工作負載
- **臨時憑證**：權杖自動輪換，消除了長期有效金鑰的風險
- **無縫整合**：與現有的 Kubernetes 認證機制配合使用，符合雲原生安全最佳實踐

#### 工作原理

1. **憑證提供程式的服務帳戶權杖**
   - Kubelet 為選擇接收服務帳戶權杖進行映像檔拉取的憑證提供程式生成**短期、自動輪換**的服務帳戶權杖
   - 這些權杖符合 OIDC ID 權杖語義
   - 權杖作為 `CredentialProviderRequest` 的一部分提供給憑證提供程式

2. **映像檔倉庫認證流程**
   - 當 Pod 啟動時，kubelet 從**憑證提供程式**請求憑證
   - 如果憑證提供程式已選擇加入，kubelet 為 Pod 生成**服務帳戶權杖**
   - **服務帳戶權杖包含在 `CredentialProviderRequest` 中**
   - 憑證提供程式使用此權杖進行身分驗證，並從倉庫（如 AWS ECR、GCP Artifact Registry、Azure ACR）交換**臨時映像檔拉取憑證**
   - kubelet 然後使用這些憑證代表 Pod 拉取映像檔

#### 優勢

- **安全性**：消除長期有效的映像檔拉取金鑰，減少攻擊面
- **細粒度存取控制**：憑證繫結到單個工作負載，而不是整個節點或叢集
- **操作簡化**：管理員無需手動管理和輪換映像檔拉取金鑰
- **合規性改進**：幫助組織滿足禁止在叢集中使用持久憑證的安全策略

#### 如何啟用

要嘗試此功能：

1. **確保執行 Kubernetes v1.33 或更高版本**
2. **在 kubelet 上啟用 `ServiceAccountTokenForKubeletCredentialProviders` 特性門控**
   ```bash
   kubelet --feature-gates=ServiceAccountTokenForKubeletCredentialProviders=true
   ```
3. **確保憑證提供程式支援**：修改或更新憑證提供程式以使用服務帳戶權杖進行身分驗證
4. **更新憑證提供程式設定**：透過設定 `tokenAttributes` 欄位，選擇為憑證提供程式接收服務帳戶權杖
5. **部署 Pod**：使用憑證提供程式從私有倉庫拉取映像檔

#### 未來計劃

對於 Kubernetes **v1.34**，預計此功能將升級為 **Beta** 版本，同時將專注於：

- 實施**快取機制**以提高權杖生成的效能
- 為憑證提供程式提供更多**靈活性**，以決定返回給 kubelet 的倉庫憑證如何快取
- 使該功能與 [Ensure Secret Pulled Images](https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/2535-ensure-secret-pulled-images) 配合工作

更多資訊可以參考：
- [服務帳戶權杖用於映像檔拉取文件](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-credential-provider/#service-account-token-for-image-pulls)
- [KEP-4412](https://kep.k8s.io/4412) 跟蹤進展

## 映像檔拉取安全（v1.33 新特性）

### Ensure Secret Pulled Images（確保私密映像檔拉取安全）

Kubernetes v1.33 引入了 **Ensure Secret Pulled Images**（Alpha 特性），這是一個重要的安全改進，解決了容器映像檔存取的潛在安全漏洞。

#### 現有安全問題

在 v1.33 之前，Kubernetes 存在一個映像檔存取安全漏洞：
- 當一個 Pod 使用私有映像檔拉取憑證成功拉取映像檔後，該映像檔會儲存在節點上
- 同一節點上的其他 Pod（即使沒有相應的映像檔拉取憑證）也能存取這些私有映像檔
- 這違反了最小權限原則，可能導致敏感映像檔的未授權存取

#### 解決方案

新的 `KubeletEnsureSecretPulledImages` 特性門控啟用後，Kubelet 會驗證 Pod 的映像檔拉取憑證：

- **憑證驗證**：即使映像檔已存在於節點上，Kubelet 也會驗證請求 Pod 的憑證
- **憑證匹配**：只有使用相同憑證（或來自同一 Secret）的 Pod 才能重用已拉取的映像檔
- **相容性**：支援所有映像檔拉取策略（`IfNotPresent`、`Never`、`Always`）

#### 工作原理

1. **首次映像檔拉取**：
   - Pod 請求私有映像檔
   - Kubelet 記錄拉取意圖
   - 從 Pod 的 imagePullSecret 提取憑證
   - 從映像檔倉庫拉取映像檔
   - 建立包含憑證詳情的成功拉取記錄

2. **後續映像檔請求**：
   - Kubelet 檢查新 Pod 的憑證
   - 如果憑證與先前成功拉取的記錄匹配，允許使用映像檔
   - 如果憑證不匹配，嘗試新的映像檔倉庫拉取

#### 如何啟用

要啟用此安全特性：

1. **在 Kubelet 上啟用特性門控**：
   ```bash
   kubelet --feature-gates=KubeletEnsureSecretPulledImages=true
   ```

2. **設定 Pod 使用映像檔拉取金鑰**：
   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: secure-private-image
   spec:
     containers:
     - name: app
       image: private-registry.example.com/myapp:v1.0
     imagePullSecrets:
     - name: my-registry-secret
   ```

#### 安全優勢

- **存取控制增強**：防止未授權 Pod 存取私有映像檔
- **最小權限原則**：確保只有具備適當憑證的 Pod 才能使用特定映像檔
- **多租戶安全**：提高多租戶環境中的映像檔隔離性
- **合規性改進**：幫助滿足嚴格的安全合規要求

## 映像檔安全（舊版工具整合）
> 下方 Clair、`go get` 與 `apt-key` 命令來自舊工具鏈，只作歷史整合思路；不要按這些命令部署生產掃描器。請核對掃描器當前受支援的 release、安裝源和映像檔掃描資料庫設定。

### Clair

[Clair](https://github.com/coreos/clair/) 是 CoreOS 開源的容器安全工具，用來靜態分析映像檔中潛在的安全問題。推薦將 Clair 整合到 Devops 流程中，自動對所有映像檔進行安全掃描。

安裝 Clair 的方法為：

```bash
git clone https://github.com/coreos/clair
cd clair/contrib/helm
helm dependency update clair
helm install clair
```

Clair 專案本身只提供了 API，在實際使用中還需要一個[客戶端（或整合Clair的服務）](https://quay.github.io/clair/howto/deployment.html)配合使用。比如，使用 [reg](https://github.com/genuinetools/reg) 的方法為

```bash
# Install
$ go get github.com/genuinetools/reg

# Vulnerability Reports
$ reg vulns --clair https://clair.j3ss.co r.j3ss.co/chrome

# Generating Static Website for a Registry
$ $ reg server --clair https://clair.j3ss.co
```

### trivy

[trivy](https://github.com/aquasecurity/trivy) 是 Aqua Security 開源的容器漏洞掃描工具。相對於 Clair 來說，使用起來更為簡單，可以更方便整合到 CI 中。

```bash
# Install
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install -y trivy

# Image Scanning
trivy python:3.4-alpine
```

### 其他工具

其他映像檔安全掃描工具還有：

* [National Vulnerability Database](https://nvd.nist.gov/)
* [OpenSCAP tools](https://www.open-scap.org/tools/)
* [coreos/clair](https://github.com/coreos/clair)
* [aquasecurity/microscanner](https://github.com/aquasecurity/microscanner)
* [Docker Registry Server](https://docs.docker.com/registry/deploying/)
* [GitLab Container Registry](https://docs.gitlab.com/ee/user/project/container_registry.html)
* [Red Hat Quay container registry](https://www.openshift.com/products/quay)
* [Amazon Elastic Container Registry](https://aws.amazon.com/ecr/)
* [theupdateframework/notary](https://github.com/theupdateframework/notary)
* [weaveworks/flux](https://github.com/weaveworks/flux)
* [IBM/portieris](https://github.com/IBM/portieris)
* [Grafeas](https://grafeas.io/)
* [in-toto](https://in-toto.github.io/)

## 安全工具

開源產品：

* [falco](https://github.com/falcosecurity/falco)：容器執行時安全行為監控工具。
* [docker-bench-security](https://github.com/docker/docker-bench-security)：Docker 環境安全檢查工具。
* [kube-hunter](https://github.com/aquasecurity/kube-hunter)：Kubernetes 叢集滲透測試工具。
* [https://github.com/shyiko/kubesec](https://github.com/shyiko/kubesec)
* [Istio](https://istio.io/)
* [Linkerd](https://linkerd.io/)
* [Open Vulnerability and Assessment Language](https://oval.mitre.org/index.html)
* [jetstack/cert-manager](https://github.com/jetstack/cert-manager/)
* [Kata Containers](https://katacontainers.io/)
* [google/gvisor](https://github.com/google/gvisor)
* [SPIFFE](https://spiffe.io/)
* [Open Policy Agent](https://www.openpolicyagent.org/)

商業產品

* [Twistlock](https://www.twistlock.com/)
* [Aqua Container Security Platform](https://www.aquasec.com/)
* [Sysdig Secure](https://sysdig.com/products/secure/)
* [Neuvector](https://neuvector.com/)

## 參考文件

* [Securing a Kubernetes cluster](https://kubernetes.io/docs/tasks/administer-cluster/securing-a-cluster/)
* [kube-bench](https://github.com/aquasecurity/kube-bench)
* [Kubernetes Security - Operating Kubernetes Clusters and Applications Safely](https://kubernetes-security.info)
* [Kubernetes Security - Best Practice Guide](https://github.com/freach/kubernetes-security-best-practice)
