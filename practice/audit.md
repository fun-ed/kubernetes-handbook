# Kubernetes API 审计

Kubernetes audit records 记录 API 请求的时间、主体、资源和响应结果。Kubernetes v1.37 的策略 API 为 `audit.k8s.io/v1`，通过 API server 的 `--audit-policy-file` 启用；日志与 webhook 是两种后端。Advanced Auditing 已稳定，不要再设置 `AdvancedAuditing` feature gate。

官方资料：[Auditing](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)、[Audit policy API](https://kubernetes.io/docs/reference/config-api/apiserver-audit.v1/)。

## v1.37 审计策略

规则按顺序匹配，第一条匹配规则决定事件级别。下面的策略跳过 `RequestReceived` 阶段、排除 kube-proxy 的常见 endpoints/services watch，并记录 Secret 与 ConfigMap 的 metadata、应用资源的变更请求和其他请求的 metadata。它不会记录 Secret 请求体。

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages:
  - RequestReceived
rules:
  - level: None
    users: ["system:kube-proxy"]
    verbs: ["watch"]
    resources:
      - group: ""
        resources: ["endpoints", "services"]
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets", "configmaps"]
  - level: Request
    resources:
      - group: "apps"
        resources: ["deployments", "daemonsets", "statefulsets"]
  - level: Metadata
```

按审计需求调整级别与资源清单。`Metadata` 不包含请求或响应 body；`Request` 会记录请求 body。除非确有需要，不要对 Secret、ConfigMap 或其他敏感 API 记录 body。

## kube-apiserver 后端参数

日志 backend 需要将策略和日志路径挂载到每个 API server 节点，并配置保留和轮转。kubeadm 集群中的 API server 通常是 static Pod；更新前备份 manifest 与策略文件，并按控制平面维护流程逐台操作：

```text
--audit-policy-file=/etc/kubernetes/audit-policy.yaml
--audit-log-path=/var/log/kubernetes/audit/audit.log
--audit-log-maxage=30
--audit-log-maxbackup=10
--audit-log-maxsize=100
```

确保静态 Pod 的 volume mount 能读到策略文件并可写入持久化日志目录。集中采集前设置访问控制、加密传输、保留期限和告警；审计日志可能包含用户身份、对象 metadata 与请求内容。

Webhook backend 使用 `--audit-webhook-config-file`，需单独保护 kubeconfig、验证 TLS，并设置合理的批处理和失败行为。日志与 webhook 不应在未评估 API server 资源消耗和审计丢失风险时直接切换。

## 旧示例说明

本页原有的 v1.7 两行文本日志、`audit.k8s.io/v1alpha1` webhook 配置、旧 GCE 审计策略和 `AdvancedAuditing` gate 均为历史材料，不是 Kubernetes v1.37 的事件格式或配置方式。
