# SecurityContext

Security Context 用于限制容器进程权限，降低容器对宿主机和其他工作负载的影响。

常用配置方法包括：

* Container-level Security Context：应用到指定容器
* Pod-level Security Context：应用到 Pod 内所有容器，并影响部分卷行为
* Pod Security Admission：通过 Pod Security Standards 在 namespace 层实施 Pod 安全策略

## Container-level Security Context

[Container-level Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/) 仅应用到指定的容器上，并且不会影响 Volume。比如设置容器运行在特权模式：

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

[Pod-level Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/) 应用到 Pod 内所有容器，并且还会影响 Volume（包括 fsGroup 和 selinuxOptions）。

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

Kubernetes v1.31 引入 `supplementalGroupsPolicy` Alpha；该字段在 v1.33 成为 Beta，并于 v1.35 达到 GA。当前版本无需启用 feature gate。
### 背景：容器镜像中的隐式组成员身份

默认情况下，Kubernetes 会将 Pod 中指定的组信息与容器镜像中 `/etc/group` 文件定义的组信息进行**合并**。这种隐式合并可能带来安全风险，因为：

- 策略引擎无法检测或验证这些隐式 GID（它们不在 Pod 清单中）
- 可能导致意外的访问控制问题，特别是在访问卷时

### supplementalGroupsPolicy 字段

该字段允许控制 Kubernetes 如何计算 Pod 内容器进程的补充组。可用的策略包括：

- **Merge**（默认）：容器主用户在 `/etc/group` 中定义的组成员身份将被合并。这是向后兼容的默认行为。
- **Strict**：仅将 `fsGroup`、`supplementalGroups` 或 `runAsGroup` 中指定的组 ID 作为补充组附加到容器进程。忽略容器主用户在 `/etc/group` 中定义的组成员身份。

### 示例：使用 Strict 策略

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

使用 `Strict` 策略时，容器中 `id` 命令的输出将只包含明确指定的组：
```
uid=1000 gid=3000 groups=3000,4000
```

### Runtime 支持

使用 `supplementalGroupsPolicy: Strict` 前，确认节点所用 CRI 运行时与 kubelet 版本都支持该功能。节点可通过 `.status.features.supplementalGroupsPolicy` 报告运行时能力：

### Pod 状态中的进程身份信息

该特性还通过 `.status.containerStatuses[].user.linux` 字段暴露附加到容器第一个进程的进程身份：

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

## User Namespaces（用户命名空间）

`UserNamespacesSupport` 在 Kubernetes v1.37 仍为 Beta，且 feature gate 自 v1.33 起默认开启。Linux Pod 可通过设置 `spec.hostUsers: false` 请求用户命名空间；这并不表示所有运行时、内核、文件系统或存储插件组合都支持该 Pod 配置。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: userns-pod
spec:
  hostUsers: false
  containers:
  - name: shell
    image: busybox:1.36
    command: ["sleep", "3600"]
    securityContext:
      runAsUser: 0
```

用户命名空间将容器内的用户 ID 与主机用户 ID 映射隔离。部署前请依据所用容器运行时、内核、卷类型及 Kubernetes 版本文档验证具体限制；不要将其视为对容器逃逸或宿主机访问的完整防护。

### 兼容性说明

用户命名空间是否可用取决于目标 Kubernetes 版本、CRI 运行时、Linux 内核与卷插件的组合。将 Pod 部署到目标节点前，参阅当前 [User Namespaces 文档](https://kubernetes.io/docs/concepts/workloads/pods/user-namespaces/)并验证所需的文件系统和卷能力。

## PodSecurityPolicy（已移除）

PodSecurityPolicy（PSP）在 v1.21 弃用，并于 v1.25 从 Kubernetes 移除。旧 PSP API YAML、feature gate 和 admission 配置在 v1.37 不可用，不要应用本页历史 PSP 示例。

新集群可使用内置的 [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) 与 [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)；需要更细粒度策略时，再评估与集群兼容的策略控制器。

## SELinux

SELinux \(Security-Enhanced Linux\) 是一种强制访问控制（mandatory access control）的实现。它的作法是以最小权限原则（principle of least privilege）为基础，在 Linux 核心中使用 Linux 安全模块（Linux Security Modules）。SELinux 主要由美国国家安全局开发，并于 2000 年 12 月 22 日发行给开放源代码的开发社区。

可以通过 runcon 来为进程设置安全策略，ls 和 ps 的 - Z 参数可以查看文件或进程的安全策略。

SELinux 的节点策略由操作系统管理员管理，不应通过关闭 SELinux 来绕过容器或卷访问问题。先检查节点策略与运行时日志，再按发行版和存储插件文档排查：

```bash
getenforce
sestatus
```

### 示例

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hello-world
spec:
  containers:
  - image: busybox:1.36
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

SELinux 标签的应用方式取决于节点配置和卷类型。当前 containerd、CRI-O 等运行时的实现细节不同；不要依赖旧 Docker `HostConfig.Binds` 路径或示例主机目录作为通用接口。

## 参考文档

* [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)
