# Kubernetes API 審計

Kubernetes audit records 記錄 API 請求的時間、主體、資源和響應結果。Kubernetes v1.37 的策略 API 為 `audit.k8s.io/v1`，透過 API server 的 `--audit-policy-file` 啟用；日誌與 webhook 是兩種後端。Advanced Auditing 已穩定，不要再設定 `AdvancedAuditing` feature gate。

官方資料：[Auditing](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)、[Audit policy API](https://kubernetes.io/docs/reference/config-api/apiserver-audit.v1/)。

## v1.37 審計策略

規則按順序匹配，第一條匹配規則決定事件級別。下面的策略跳過 `RequestReceived` 階段、排除 kube-proxy 的常見 endpoints/services watch，並記錄 Secret 與 ConfigMap 的 metadata、應用資源的變更請求和其他請求的 metadata。它不會記錄 Secret 請求體。

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

按審計需求調整級別與資源清單。`Metadata` 不包含請求或響應 body；`Request` 會記錄請求 body。除非確有需要，不要對 Secret、ConfigMap 或其他敏感 API 記錄 body。

## kube-apiserver 後端引數

日誌 backend 需要將策略和日誌路徑掛載到每個 API server 節點，並設定保留和輪轉。kubeadm 叢集中的 API server 通常是 static Pod；更新前備份 manifest 與策略檔案，並按控制平面維護流程逐臺操作：

```text
--audit-policy-file=/etc/kubernetes/audit-policy.yaml
--audit-log-path=/var/log/kubernetes/audit/audit.log
--audit-log-maxage=30
--audit-log-maxbackup=10
--audit-log-maxsize=100
```

確保靜態 Pod 的 volume mount 能讀到策略檔案並可寫入持久化日誌目錄。集中採集前設定存取控制、加密傳輸、保留期限和告警；審計日誌可能包含使用者身分、物件 metadata 與請求內容。

Webhook backend 使用 `--audit-webhook-config-file`，需單獨保護 kubeconfig、驗證 TLS，並設定合理的批處理和失敗行為。日誌與 webhook 不應在未評估 API server 資源消耗和審計丟失風險時直接切換。

## 舊範例說明

本頁原有的 v1.7 兩行文字日誌、`audit.k8s.io/v1alpha1` webhook 設定、舊 GCE 審計策略和 `AdvancedAuditing` gate 均為歷史材料，不是 Kubernetes v1.37 的事件格式或設定方式。
