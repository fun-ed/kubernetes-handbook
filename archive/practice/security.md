# 安全

从安全的角度来看，Kubernetes 中包含如下图所示的潜在攻击面：

![](../../.gitbook/assets/attach-vectors%20%281%29.png)

（图片来自《Kubernetes Security - Operating Kubernetes Clusters and Applications Safely》）

为了保证集群以及容器应用的安全，Kubernetes 提供了多种安全机制，限制容器的行为，减少容器和集群的攻击面，保证整个系统的安全性。

* Security Context：用 Capabilities、`runAsNonRoot`、只读根文件系统、seccomp、SELinux 与 AppArmor 限制容器行为；
* User Namespaces：在支持的 Linux 节点与 CRI runtime 上隔离容器和主机用户 ID；并非所有 Pod、卷或 runtime 都适用；
* Pod Security Admission（PSA）：用 namespace 标签实施 Pod Security Standards；PodSecurityPolicy（PSP）已移除；
* Sysctls：容器可设置的内核参数分为安全与非安全项；
* AppArmor：在支持的 Linux 节点上限制应用访问；
* Network Policies：按 CNI 能力控制 Pod 网络访问；
* Seccomp：通过允许列表限制容器应用可执行的系统调用。

除此之外，推荐尽量使用较新版本的 Kubernetes，因为它们通常会包含常见安全问题的修复。你可以参考 [kubernetes-announce](https://groups.google.com/forum/#!forum/kubernetes-announce) 来查询最新的 Kubernetes 发布情况，也可以参考 [cvedetails.com](https://www.cvedetails.com/version-list/15867/34016/1/Kubernetes-Kubernetes.html) 查询 Kubernetes 各个版本的 CVE \(Common Vulnerabilities and Exposures\) 列表。
新部署应优先使用稳定 API 与显式的工作负载安全上下文。PSP 已在 Kubernetes v1.25 移除；当前基线应使用[Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)和[Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)。

## 集群安全

* Kubernetes 组件（如 kube-apiserver、etcd、kubelet 等）只开放受保护的 API 并启用 TLS。
* 开启 RBAC 授权，赋予工作负载最小权限，并启用 NodeRestriction 准入控制。
  * 需要更丰富的策略时，可评估 OPA/Gatekeeper 等额外策略组件。
* 加密 etcd 中的 Secret，并配置 etcd TLS。
* 禁止 Kubelet 匿名访问和只读端口，启用客户端证书轮换。
* 对不需要 API 访问的工作负载关闭 ServiceAccount token 自动挂载；确需访问时使用专用 ServiceAccount 与最小 RBAC 权限。默认投射 token 可自动轮换，不要创建长期有效的 token Secret。
* 通过最小 RBAC 限制 Dashboard 等管理界面，并避免公开管理 endpoint。
* 按对应 Kubernetes 版本运行 CIS Benchmark 等基线检查，并跟踪安全公告和 CVE。
* 多租户环境可按风险评估运行时隔离与服务身份方案；它们不能替代 Kubernetes API authorization 与 NetworkPolicy。

## TLS 安全

为保障 TLS 安全，并避免 [Zombie POODLE and GOLDENDOODLE Vulnerabilities](https://blog.qualys.com/technology/2019/04/22/zombie-poodle-and-goldendoodle-vulnerabilities)，请为 TLS 1.2 禁止 CBC \(Cipher Block Chaining\) 模式。

你可以使用 [https://www.ssllabs.com/](https://www.ssllabs.com/) 来测试 TLS 的安全问题。

## PodSecurityPolicy（已移除）与 Security Context

> 以下 PSP YAML 使用 `extensions/v1beta1` 和 alpha annotation，**无法应用于 Kubernetes v1.37**。PSP 在 v1.25 移除；不要恢复旧 API 或 feature gate。以 PSA namespace 标签和 Pod 安全上下文替代。

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

完整参考见[这里](../../concepts/objects/security-context.md)。
## Pod Security Admission（当前推荐）

在应用 namespace 明确设置 `enforce`、`audit` 和 `warn` 等级，并按需固定策略版本。先使用 `warn`/`audit` 找出不符合项，再启用 `enforce`，避免阻断现有部署。PSA 不会像旧 PSP 一样自动 mutation；工作负载本身应设置必要的安全上下文。

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

`restricted` 通常要求非 root 用户、`RuntimeDefault` 或受管的 seccomp profile、禁止提权，并 drop 所有 capabilities（需要时只能添加该级别明确允许的 capability）。
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

不需要访问 Kubernetes API 的 Pod 应关闭 token 自动挂载；确需访问时，为应用绑定最小 RBAC 权限并使用默认投射、可轮换的 ServiceAccount token。参见[ServiceAccount token 文档](https://kubernetes.io/docs/concepts/security/service-accounts/)。
详细规则见[Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)、[Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)与[Security Context 文档](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)。

## User Namespaces（用户命名空间，v1.36 GA）

User Namespaces 自 Kubernetes v1.36 起为稳定功能（最早于 v1.28 引入），由 Pod 显式设置 `spec.hostUsers: false` opt in；不是默认启用。该功能通过 Linux user namespace 隔离容器进程的 UID/GID 与主机 UID/GID，可降低容器逃逸对主机或同节点 Pod 的影响，但不能替代其他安全措施。

这是 Linux-only 功能。官方要求节点及 Pod 卷文件系统支持 idmapped mounts（实践中至少 Linux 6.3），OCI runtime 支持 user namespace（runc 1.2+ 或 crun 1.9+）；CRI runtime 支持要求为 containerd 2.0+ 或 CRI-O 1.25+。上线前核对[官方 User Namespaces 指南](https://kubernetes.io/docs/concepts/workloads/pods/user-namespaces/)和每种存储卷的支持。以下 manifest 中的镜像名是占位符，需替换为受信任的固定版本。

### 安全最佳实践

1. **高安全性工作负载**：仅当节点内核、CRI runtime、存储驱动均符合上方条件且已验证兼容后，才考虑让 Pod opt-in 使用 user namespace。

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

2. **多租户环境**：user namespace 可限制主机 root 和 capabilities 的作用范围、降低部分容器逃逸的影响；它不是租户间完整的安全边界。

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

3. **传统应用迁移**：对于需要以 root 身份运行的传统应用，用户命名空间允许在不牺牲安全性的情况下运行：

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

### 安全优势

- **潜在影响**：将容器 UID/GID 映射到宿主机非特权用户，可降低部分容器逃逸造成的主机影响；
- **能力范围**：容器 capabilities 在该 user namespace 外无效或受限，具体行为按 Linux 文档与 runtime 实现验证；
- **文件和卷**：所有文件系统和卷必须支持 idmapped mounts；不同文件 owner mapping 仍需测试；
### 注意事项
- **内核与文件系统**：节点及 Pod 卷文件系统需支持 idmapped mounts；Kubernetes 文档给出的实践要求至少 Linux 6.3。
- **OCI/CRI runtime**：需支持 user namespace。官方文档列出 runc 1.2+ 或 crun 1.9+，以及 containerd 2.0+ 或 CRI-O 1.25+。
- **卷与应用兼容性**：按当前 Kubernetes 文档及 CSI/文件系统限制验证；特权操作、host namespace 与不支持的挂载组合可能不可用。

### 部署建议

1. **逐步推广**：从非关键工作负载开始，逐步扩展到生产环境
2. **测试验证**：在启用前充分测试应用的兼容性
3. **监控观察**：部署后密切监控应用行为和性能指标
4. **策略制定**：为不同类型的工作负载制定用户命名空间使用策略

## Supplemental Groups Policy（补充组策略）
本节说明 `supplementalGroupsPolicy: Strict` 如何避免将镜像 `/etc/group` 中额外组并入容器进程。正式启用前请检查官方[安全上下文文档](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)与每个 Node 的 `status.features.supplementalGroupsPolicy`；CRI runtime 需支持该功能。
标题和后续版本描述从 v1.33 Beta 阶段的资料整理而来，不代表 v1.37 的功能门控状态。不要照搬旧 feature-gate 命令；在不支持的节点上，Pod 可能无法启动。

### 安全风险

默认情况下，Kubernetes 会将容器镜像中 `/etc/group` 定义的组信息与 Pod 指定的组信息**合并**，这可能带来安全风险：

- **隐式权限提升**：容器可能获得未在 Pod 清单中声明的组权限
- **策略绕过**：安全策略引擎无法检测这些隐式组
- **卷访问风险**：意外的组成员身份可能导致对敏感卷的未授权访问

### 使用 Strict 策略

通过设置 `supplementalGroupsPolicy: Strict`，可以确保只有明确指定的组被附加到容器进程：

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

### 最佳实践

1. **默认使用 Strict 策略**：对于新部署的应用，建议默认使用 Strict 策略：

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

2. **策略强制执行**：通过准入控制器或 OPA 策略强制所有 Pod 使用 Strict 策略：

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

3. **审计现有工作负载**：使用 Pod 状态中的用户信息审计现有工作负载的组成员身份：

```bash
# 查看容器的实际组成员身份
kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[0].user.linux}'
```

4. **逐步迁移策略**：
   - **阶段 1**：审计并记录现有 Pod 的隐式组
   - **阶段 2**：在非生产环境测试 Strict 策略
   - **阶段 3**：为新应用默认启用 Strict 策略
   - **阶段 4**：逐步迁移现有应用到 Strict 策略

### 升级注意事项

如果您的集群已经在使用 `supplementalGroupsPolicy: Strict`：

1. **确保 CRI 运行时支持**：
   - containerd v2.0+
   - CRI-O v1.31+

2. **检查节点支持**：
```bash
kubectl get nodes -o custom-columns=NAME:.metadata.name,SUPPORTED:.status.features.supplementalGroupsPolicy
```

3. **处理不支持的节点**：
   - 升级 CRI 运行时
   - 只有在 Node Feature Discovery 或其他机制已显式创建相应 label 时，才可用该 label 通过 nodeSelector 避免调度到不支持的节点；`status.features` 不会自动创建该 label。

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

Sysctls 允许容器设置内核参数，分为安全 Sysctls 和非安全 Sysctls

* 安全 Sysctls：即设置后不影响其他 Pod 的内核选项，只作用在容器 namespace 中，默认开启。包括以下几种
  * `kernel.shm_rmid_forced`
  * `net.ipv4.ip_local_port_range`
  * `net.ipv4.tcp_syncookies`
* 非安全 sysctl 可能影响其他 Pod 或节点服务，默认禁止。只有在确认隔离边界与工作负载需求后，才由管理员按当前 kubelet `allowedUnsafeSysctls` 配置显式允许；不要使用已淘汰的 `--experimental-allowed-unsafe-sysctls` 或 PSP 配置。
> 以下 PSP/sysctl API 示例是历史内容：PSP 在 Kubernetes v1.25 移除。非安全 sysctl 应按当前 kubelet 配置与[官方 sysctl 文档](https://kubernetes.io/docs/tasks/administer-cluster/sysctl-cluster/)管理。

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

而 v1.10 及更早版本则为 Alpha 阶段，需要通过 Pod annotation 设置，如：

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

[AppArmor\(Application Armor\)](http://wiki.apparmor.net/index.php/AppArmor_Core_Policy_Reference) 是 Linux 内核的一个安全模块，允许系统管理员将每个程序与一个安全配置文件关联，从而限制程序的功能。通过它你可以指定程序可以读、写或运行哪些文件，是否可以打开网络端口等。作为对传统 Unix 的自主访问控制模块的补充，AppArmor 提供了强制访问控制机制。

在使用 AppArmor 之前需要注意

AppArmor 支持取决于 Linux 节点、内核、profile 与容器运行时。v1.37 字段和示例见[官方 Security Context 文档](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)；本节早期 PSP annotation、feature gate、Docker-only 要求与旧字段只作历史参考。

当前 Pod 使用稳定的 `appArmorProfile` 字段，不再使用下方旧 annotation：
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
自定义 `Localhost` profile 必须预先加载到所有可能调度该 Pod 的节点；具体步骤和字段见[官方 AppArmor 指南](https://kubernetes.io/docs/tutorials/security/apparmor/)。
本节随后仍保留了 Kubernetes v1.30 前的旧 annotation 示例，仅作为历史材料。

* `runtime/default`: 使用 Container Runtime 的默认配置
* `localhost/<profile_name>`: 使用已加载到内核的 AppArmor profile

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

[Seccomp](https://www.kernel.org/doc/Documentation/prctl/seccomp_filter.txt) 是 Secure computing mode 的缩写，它是 Linux 内核提供的一个操作，用于限制一个进程可以执行的系统调用．Seccomp 需要有一个配置文件来指明容器进程允许和禁止执行的系统调用。
当前 seccomp 推荐在 Pod 或 container 的 `securityContext` 使用结构化字段；通常可从默认 profile 开始：

```yaml
securityContext:
  seccompProfile:
    type: RuntimeDefault
```

本节下方的本地 JSON profile、旧 annotation 与 Docker 输出是历史配置说明。目录与 runtime 行为应按当前[kubelet seccomp 文档](https://kubernetes.io/docs/tutorials/security/seccomp/)核对。

在 Kubernetes 中，需要将 seccomp 配置文件放到 `/var/lib/kubelet/seccomp` 目录中（可以通过 kubelet 选项 `--seccomp-profile-root` 修改）。比如禁止 chmod 的格式为

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

旧版 Kubernetes 中的 Seccomp 配置曾处于 Alpha 阶段并通过 Pod annotation 指定，包括：

* `security.alpha.kubernetes.io/seccomp/pod`：应用到该 Pod 的所有容器
* `security.alpha.kubernetes.io/seccomp/container/<container name>`：应用到指定容器

而 value 有三个选项

* `runtime/default`: 使用 Container Runtime 的默认配置
* `unconfined`: 允许所有系统调用
* `localhost/<profile-name>`: 使用 Node 本地安装的 seccomp，需要放到 `/var/lib/kubelet/seccomp` 目录中

比如使用刚才创建的 seccomp 配置：

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
> **旧版命令，不可直接用于 v1.37**：本节后面的未固定 `aquasec/kube-bench:latest`、Docker 容器挂载和 handbook `master` Job YAML 未按 Kubernetes v1.37/CIS 基线验证；不要直接在生产节点或集群运行。选择与目标 CIS Kubernetes Benchmark 版本匹配的 kube-bench release，从[上游安装文档](https://github.com/aquasecurity/kube-bench)获取当前清单并审查其宿主机挂载、权限和镜像后再测试。

[kube-bench](https://github.com/aquasecurity/kube-bench) 提供了一个简单的工具来检查 Kubernetes 的配置（包括 master 和 node）是否符合最佳的安全实践（基于 [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes/)）。

是否在生产集群运行 kube-bench，应结合目标 CIS 基线、发行版、所需宿主机访问与权限、资源许可和变更窗口评估；扫描结果不能替代安全配置审查。

安装 `kube-bench`：

```bash
$ docker run --rm -v `pwd`:/host aquasec/kube-bench:latest install
$ ./kube-bench <master|node>
```

当然，kube-bench 也可以直接在容器内运行，比如通常对 Master 和 Node 的检查命令分别为：

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

## 镜像拉取凭据（v1.33 时代的历史状态）
> 从本节开始的镜像凭据说明冻结在 v1.33/v1.34 状态，feature gate、Alpha/Beta 和“未来计划”描述均不代表 v1.37。**不要照抄本节里的 feature-gate 命令**；请以当前[镜像文档](https://kubernetes.io/docs/concepts/containers/images/)及[kubelet credential provider 文档](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-credential-provider/)为准。
### Service Account Token Integration for Kubelet Credential Providers

Kubernetes v1.33 引入了 **Service Account Token Integration for Kubelet Credential Providers**（Alpha 特性），这是一个重要的安全改进，允许使用 Pod 特定的服务账户令牌来获取镜像仓库凭证，从而消除了对长期有效的镜像拉取密钥的需求。

#### 现有问题

目前，Kubernetes 管理员在处理私有容器镜像拉取时主要有两种选择：

1. **存储在 Kubernetes API 中的镜像拉取密钥**
   - 这些密钥通常是长期有效的，因为很难轮换
   - 必须显式附加到服务账户或 Pod
   - 密钥泄露可能导致未授权的镜像访问

2. **Kubelet 凭证提供程序**
   - 这些提供程序在节点级别动态获取凭证
   - 在节点上运行的任何 Pod 都可以访问相同的凭证
   - 没有按工作负载隔离，增加了安全风险

这两种方法都不符合**最小权限**和**临时认证**的原则，给 Kubernetes 留下了安全缺口。

#### 解决方案

新的增强功能使 kubelet 凭证提供程序能够在获取镜像仓库凭证时使用**工作负载身份**。凭证提供程序可以使用服务账户令牌来请求与特定 Pod 身份绑定的短期凭证，而不是依赖长期有效的密钥。

这种方法提供了：

- **特定于工作负载的认证**：镜像拉取凭证的范围限定为特定工作负载
- **临时凭证**：令牌自动轮换，消除了长期有效密钥的风险
- **无缝集成**：与现有的 Kubernetes 认证机制配合使用，符合云原生安全最佳实践

#### 工作原理

1. **凭证提供程序的服务账户令牌**
   - Kubelet 为选择接收服务账户令牌进行镜像拉取的凭证提供程序生成**短期、自动轮换**的服务账户令牌
   - 这些令牌符合 OIDC ID 令牌语义
   - 令牌作为 `CredentialProviderRequest` 的一部分提供给凭证提供程序

2. **镜像仓库认证流程**
   - 当 Pod 启动时，kubelet 从**凭证提供程序**请求凭证
   - 如果凭证提供程序已选择加入，kubelet 为 Pod 生成**服务账户令牌**
   - **服务账户令牌包含在 `CredentialProviderRequest` 中**
   - 凭证提供程序使用此令牌进行身份验证，并从仓库（如 AWS ECR、GCP Artifact Registry、Azure ACR）交换**临时镜像拉取凭证**
   - kubelet 然后使用这些凭证代表 Pod 拉取镜像

#### 优势

- **安全性**：消除长期有效的镜像拉取密钥，减少攻击面
- **细粒度访问控制**：凭证绑定到单个工作负载，而不是整个节点或集群
- **操作简化**：管理员无需手动管理和轮换镜像拉取密钥
- **合规性改进**：帮助组织满足禁止在集群中使用持久凭证的安全策略

#### 如何启用

要尝试此功能：

1. **确保运行 Kubernetes v1.33 或更高版本**
2. **在 kubelet 上启用 `ServiceAccountTokenForKubeletCredentialProviders` 特性门控**
   ```bash
   kubelet --feature-gates=ServiceAccountTokenForKubeletCredentialProviders=true
   ```
3. **确保凭证提供程序支持**：修改或更新凭证提供程序以使用服务账户令牌进行身份验证
4. **更新凭证提供程序配置**：通过配置 `tokenAttributes` 字段，选择为凭证提供程序接收服务账户令牌
5. **部署 Pod**：使用凭证提供程序从私有仓库拉取镜像

#### 未来计划

对于 Kubernetes **v1.34**，预计此功能将升级为 **Beta** 版本，同时将专注于：

- 实施**缓存机制**以提高令牌生成的性能
- 为凭证提供程序提供更多**灵活性**，以决定返回给 kubelet 的仓库凭证如何缓存
- 使该功能与 [Ensure Secret Pulled Images](https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/2535-ensure-secret-pulled-images) 配合工作

更多信息可以参考：
- [服务账户令牌用于镜像拉取文档](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-credential-provider/#service-account-token-for-image-pulls)
- [KEP-4412](https://kep.k8s.io/4412) 跟踪进展

## 镜像拉取安全（v1.33 新特性）

### Ensure Secret Pulled Images（确保私密镜像拉取安全）

Kubernetes v1.33 引入了 **Ensure Secret Pulled Images**（Alpha 特性），这是一个重要的安全改进，解决了容器镜像访问的潜在安全漏洞。

#### 现有安全问题

在 v1.33 之前，Kubernetes 存在一个镜像访问安全漏洞：
- 当一个 Pod 使用私有镜像拉取凭证成功拉取镜像后，该镜像会存储在节点上
- 同一节点上的其他 Pod（即使没有相应的镜像拉取凭证）也能访问这些私有镜像
- 这违反了最小权限原则，可能导致敏感镜像的未授权访问

#### 解决方案

新的 `KubeletEnsureSecretPulledImages` 特性门控启用后，Kubelet 会验证 Pod 的镜像拉取凭证：

- **凭证验证**：即使镜像已存在于节点上，Kubelet 也会验证请求 Pod 的凭证
- **凭证匹配**：只有使用相同凭证（或来自同一 Secret）的 Pod 才能重用已拉取的镜像
- **兼容性**：支持所有镜像拉取策略（`IfNotPresent`、`Never`、`Always`）

#### 工作原理

1. **首次镜像拉取**：
   - Pod 请求私有镜像
   - Kubelet 记录拉取意图
   - 从 Pod 的 imagePullSecret 提取凭证
   - 从镜像仓库拉取镜像
   - 创建包含凭证详情的成功拉取记录

2. **后续镜像请求**：
   - Kubelet 检查新 Pod 的凭证
   - 如果凭证与先前成功拉取的记录匹配，允许使用镜像
   - 如果凭证不匹配，尝试新的镜像仓库拉取

#### 如何启用

要启用此安全特性：

1. **在 Kubelet 上启用特性门控**：
   ```bash
   kubelet --feature-gates=KubeletEnsureSecretPulledImages=true
   ```

2. **配置 Pod 使用镜像拉取密钥**：
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

#### 安全优势

- **访问控制增强**：防止未授权 Pod 访问私有镜像
- **最小权限原则**：确保只有具备适当凭证的 Pod 才能使用特定镜像
- **多租户安全**：提高多租户环境中的镜像隔离性
- **合规性改进**：帮助满足严格的安全合规要求

## 镜像安全（旧版工具集成）
> 下方 Clair、`go get` 与 `apt-key` 命令来自旧工具链，只作历史集成思路；不要按这些命令部署生产扫描器。请核对扫描器当前受支持的 release、安装源和镜像扫描数据库设置。

### Clair

[Clair](https://github.com/coreos/clair/) 是 CoreOS 开源的容器安全工具，用来静态分析镜像中潜在的安全问题。推荐将 Clair 集成到 Devops 流程中，自动对所有镜像进行安全扫描。

安装 Clair 的方法为：

```bash
git clone https://github.com/coreos/clair
cd clair/contrib/helm
helm dependency update clair
helm install clair
```

Clair 项目本身只提供了 API，在实际使用中还需要一个[客户端（或集成Clair的服务）](https://quay.github.io/clair/howto/deployment.html)配合使用。比如，使用 [reg](https://github.com/genuinetools/reg) 的方法为

```bash
# Install
$ go get github.com/genuinetools/reg

# Vulnerability Reports
$ reg vulns --clair https://clair.j3ss.co r.j3ss.co/chrome

# Generating Static Website for a Registry
$ $ reg server --clair https://clair.j3ss.co
```

### trivy

[trivy](https://github.com/aquasecurity/trivy) 是 Aqua Security 开源的容器漏洞扫描工具。相对于 Clair 来说，使用起来更为简单，可以更方便集成到 CI 中。

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

其他镜像安全扫描工具还有：

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

开源产品：

* [falco](https://github.com/falcosecurity/falco)：容器运行时安全行为监控工具。
* [docker-bench-security](https://github.com/docker/docker-bench-security)：Docker 环境安全检查工具。
* [kube-hunter](https://github.com/aquasecurity/kube-hunter)：Kubernetes 集群渗透测试工具。
* [https://github.com/shyiko/kubesec](https://github.com/shyiko/kubesec)
* [Istio](https://istio.io/)
* [Linkerd](https://linkerd.io/)
* [Open Vulnerability and Assessment Language](https://oval.mitre.org/index.html)
* [jetstack/cert-manager](https://github.com/jetstack/cert-manager/)
* [Kata Containers](https://katacontainers.io/)
* [google/gvisor](https://github.com/google/gvisor)
* [SPIFFE](https://spiffe.io/)
* [Open Policy Agent](https://www.openpolicyagent.org/)

商业产品

* [Twistlock](https://www.twistlock.com/)
* [Aqua Container Security Platform](https://www.aquasec.com/)
* [Sysdig Secure](https://sysdig.com/products/secure/)
* [Neuvector](https://neuvector.com/)

## 参考文档

* [Securing a Kubernetes cluster](https://kubernetes.io/docs/tasks/administer-cluster/securing-a-cluster/)
* [kube-bench](https://github.com/aquasecurity/kube-bench)
* [Kubernetes Security - Operating Kubernetes Clusters and Applications Safely](https://kubernetes-security.info)
* [Kubernetes Security - Best Practice Guide](https://github.com/freach/kubernetes-security-best-practice)
