# SecurityContext

Security Context 用於限制容器程序權限，降低容器對宿主機和其他工作負載的影響。

常用設定方法包括：

* Container-level Security Context：應用到指定容器
* Pod-level Security Context：應用到 Pod 內所有容器，並影響部分卷行為
* Pod Security Admission：透過 Pod Security Standards 在 namespace 層實施 Pod 安全策略

## Container-level Security Context

[Container-level Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/) 僅應用到指定的容器上，並且不會影響 Volume。比如設定容器執行在特權模式：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hello-world
spec:
  containers:
    - name: hello-world-container
      image: busybox:1.37.0
      command: ["sh", "-c", "sleep 3600"]
      securityContext:
        # privileged 会授予容器扩大的宿主机权限；仅在可信测试集群中演示。
        privileged: true
```

## Pod-level Security Context

[Pod-level Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/) 應用到 Pod 內所有容器，並且還會影響 Volume（包括 fsGroup 和 selinuxOptions）。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hello-world
spec:
  containers:
  - name: hello-world-container
    image: busybox:1.37.0
    command: ["sh", "-c", "sleep 3600"]
  securityContext:
    fsGroup: 1234
    supplementalGroups: [5678]
    seLinuxOptions:
      level: "s0:c123,c456"
```

Kubernetes v1.31 引入 `supplementalGroupsPolicy` Alpha；該欄位在 v1.33 成為 Beta，並於 v1.35 達到 GA。當前版本無需啟用 feature gate。
### 背景：容器映像檔中的隱式組成員身分

預設情況下，Kubernetes 會將 Pod 中指定的組資訊與容器映像檔中 `/etc/group` 檔案定義的組資訊進行**合併**。這種隱式合併可能帶來安全風險，因為：

- 策略引擎無法檢測或驗證這些隱式 GID（它們不在 Pod 清單中）
- 可能導致意外的存取控制問題，特別是在存取卷時

### supplementalGroupsPolicy 欄位

該欄位允許控制 Kubernetes 如何計算 Pod 內容器程序的補充組。可用的策略包括：

- **Merge**（預設）：容器主使用者在 `/etc/group` 中定義的組成員身分將被合併。這是向後相容的預設行為。
- **Strict**：僅將 `fsGroup`、`supplementalGroups` 或 `runAsGroup` 中指定的組 ID 作為補充組附加到容器程序。忽略容器主使用者在 `/etc/group` 中定義的組成員身分。

### 範例：使用 Strict 策略

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: strict-supplementalgroups-policy
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
    supplementalGroups: [4000]
    supplementalGroupsPolicy: Strict
  containers:
  - name: ctr
    image: registry.k8s.io/e2e-test-images/agnhost:2.45
    command: [ "sh", "-c", "sleep 1h" ]
    securityContext:
      allowPrivilegeEscalation: false
```

使用 `Strict` 策略時，容器中 `id` 命令的輸出將只包含明確指定的組：
```
uid=1000 gid=3000 groups=3000,4000
```

### Runtime 支援

使用 `supplementalGroupsPolicy: Strict` 前，確認節點所用 CRI 執行時與 kubelet 版本都支援該功能。節點可透過 `.status.features.supplementalGroupsPolicy` 報告執行時能力：

### Pod 狀態中的程序身分資訊

該特性還透過 `.status.containerStatuses[].user.linux` 欄位暴露附加到容器第一個程序的程序身分：

```yaml
status:
  containerStatuses:
  - name: ctr
    user:
      linux:
        gid: 3000
        supplementalGroups:
        - 3000
        - 4000
        uid: 1000
```

## User Namespaces（使用者命名空間）

`UserNamespacesSupport` 在 Kubernetes v1.37 仍為 Beta，且 feature gate 自 v1.33 起預設開啟。Linux Pod 可透過設定 `spec.hostUsers: false` 請求使用者命名空間；這並不表示所有執行時、核心、檔案系統或儲存外掛組合都支援該 Pod 設定。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: userns-pod
spec:
  hostUsers: false
  containers:
  - name: shell
    image: busybox:1.37.0
    command: ["sleep", "3600"]
    securityContext:
      runAsUser: 0
```

使用者命名空間將容器內的使用者 ID 與主機使用者 ID 對映隔離。部署前請依據所用容器執行時、核心、卷型別及 Kubernetes 版本文件驗證具體限制；不要將其視為對容器逃逸或宿主機存取的完整防護。

### 相容性說明

使用者命名空間是否可用取決於目標 Kubernetes 版本、CRI 執行時、Linux 核心與卷外掛的組合。將 Pod 部署到目標節點前，參閱當前 [User Namespaces 文件](https://kubernetes.io/docs/concepts/workloads/pods/user-namespaces/)並驗證所需的檔案系統和卷能力。

## PodSecurityPolicy（已移除）

PodSecurityPolicy（PSP）在 v1.21 棄用，並於 v1.25 從 Kubernetes 移除。舊 PSP API YAML、feature gate 和 admission 設定在 v1.37 不可用，不要應用本頁歷史 PSP 範例。

新叢集可使用內建的 [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) 與 [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)；需要更細粒度策略時，再評估與叢集相容的策略控制器。

## SELinux

SELinux \(Security-Enhanced Linux\) 是一種強制存取控制（mandatory access control）的實現。它的作法是以最小權限原則（principle of least privilege）為基礎，在 Linux 核心中使用 Linux 安全模組（Linux Security Modules）。SELinux 主要由美國國家安全域性開發，並於 2000 年 12 月 22 日發行給開放原始碼的開發社群。

可以透過 runcon 來為程序設定安全策略，ls 和 ps 的 - Z 引數可以檢視檔案或程序的安全策略。

SELinux 的節點策略由作業系統管理員管理，不應透過關閉 SELinux 來繞過容器或卷存取問題。先檢查節點策略與執行時日誌，再按發行版和儲存外掛文件排查：

```bash
getenforce
sestatus
```

### 範例

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hello-world
spec:
  containers:
  - image: busybox:1.37.0
    name: test-container
    command: ["sleep", "3600"]
    volumeMounts:
    - mountPath: /mounted_volume
      name: test-volume
  restartPolicy: Never
  securityContext:
    seLinuxOptions:
      level: "s0:c2,c3"
  volumes:
  - name: test-volume
    emptyDir: {}
```

SELinux 標籤的應用方式取決於節點設定和卷型別。當前 containerd、CRI-O 等執行時的實現細節不同；不要依賴舊 Docker `HostConfig.Binds` 路徑或範例主機目錄作為通用介面。

## 參考文件

* [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)
