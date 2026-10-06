# 雲服務商擴充套件

雲服務商整合讓 Kubernetes 控制平面可以查詢雲例項、設定雲路由，或為 `LoadBalancer` 型別的 Service 建立負載平衡器。自 Kubernetes 1.29 起，核心元件預設不再啟用內建雲服務商實現；叢集需要使用雲服務商維護的外部整合。詳見 [Cloud Controller Manager 管理文件](https://kubernetes.io/docs/tasks/administer-cluster/running-cloud-controller/)和[雲服務商整合變更說明](https://kubernetes.io/blog/2023/12/14/cloud-provider-integration-changes/)。

## 元件職責與設定

使用外部 Cloud Controller Manager（CCM）時，各元件的設定並不相同：

| 元件 | 外部雲服務商設定 |
| --- | --- |
| `kubelet` | 設定 `--cloud-provider=external`。節點註冊時會帶有 `node.cloudprovider.kubernetes.io/uninitialized:NoSchedule` 汙點，等待外部 CCM 初始化節點。 |
| `kube-controller-manager` | 設定 `--cloud-provider=external`，將雲服務商控制邏輯交給外部 CCM。其他 Kubernetes 控制器仍由該元件執行。 |
| `kube-apiserver` | 外部 CCM 部署不需要設定雲服務商選項。不要再設定 `PersistentVolumeLabel` 准入外掛；Kubernetes 1.37 的准入控制器列表中已不包含該外掛。 |
| 外部 CCM | 由雲服務商單獨提供並部署。CCM 使用其實現要求的服務商名稱、設定檔案、憑證和其他引數，不能把 `external` 當作 CCM 的服務商名稱。 |

`PersistentVolumeClaimResize` 是 API Server 的准入控制器，不是 CCM 的功能。外部 CCM 通常負責其實現的節點、Service 負載平衡器和路由控制器；支援的功能由具體服務商決定。CCM 不替代 Kubernetes 的卷控制器，也不負責 CSI 驅動的卷生命週期。持久卷整合應按雲服務商的 CSI 驅動文件設定。

Kubernetes 自帶的控制平面容器映像檔應使用與叢集版本相符的釋出版本。例如，執行 Kubernetes v1.37.1 時，Kubernetes 提供的控制平面映像檔應取自 v1.37.1 釋出版。外部 CCM 的映像檔和版本由雲服務商維護，不保證與 Kubernetes 版本號相同。按服務商相容性說明選擇版本，並在部署中固定到服務商釋出的版本或映像檔摘要；不要使用 `latest`，也不要把 Kubernetes 版本號當作 CCM 的版本號。

## 節點初始化與 CCM 部署

啟用 `--cloud-provider=external` 後，節點在 CCM 完成初始化前帶有 `NoSchedule` 汙點。CCM 必須能在啟動階段執行，並由節點控制器填入服務商所需的節點資訊後移除該汙點。若 CCM 以 Pod 執行，其服務賬號、RBAC、節點選擇器和容忍度都應按服務商提供的部署清單設定。只有在網路初始化順序要求時才使用 `hostNetwork`，不要把它當作通用必需項。

下面僅展示 Pod 模板中的相關欄位，不是可直接部署的清單。將映像檔佔位符替換為服務商明確支援、與叢集版本相容的映像檔引用。多副本部署時按服務商文件設定 Leader Election。

```yaml
spec:
  template:
    spec:
      serviceAccountName: cloud-controller-manager
      tolerations:
      - key: node.cloudprovider.kubernetes.io/uninitialized
        operator: Exists
        effect: NoSchedule
      containers:
      - name: cloud-controller-manager
        image: ${PROVIDER_CCM_IMAGE}
        args:
        - --cloud-provider=<provider-name>
        - --leader-elect=true
```

如果叢集的控制平面節點還有其他汙點，CCM Pod 也需要服務商清單指定的對應容忍度。不要直接授予 `cluster-admin`；使用雲服務商為 CCM 提供的最小權限 RBAC 規則。

## 開發 Cloud Controller Manager

自定義 CCM 需要實現 Kubernetes [cloud-provider 介面](https://github.com/kubernetes/cloud-provider/blob/release-1.37/cloud.go)，再按[開發 Cloud Controller Manager 文件](https://kubernetes.io/docs/tasks/administer-cluster/developing-cloud-controller-manager/)建置和部署。服務商實現、設定引數與釋出映像檔由各自專案維護。
