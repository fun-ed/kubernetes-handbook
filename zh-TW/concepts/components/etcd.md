# etcd

Kubernetes 使用 etcd 作為保存叢集狀態的一致性鍵值儲存體。在標準控制平面中，API Server 負責讀寫 etcd 內的 Kubernetes 物件。Kubernetes 用戶端、控制器與 `kubectl` 都透過 Kubernetes API 操作資源，不會直接使用 etcd 內部儲存介面。

Kubernetes v1.37.1 的 kubeadm 固定使用 etcd v3.7.0。這是 kubeadm 的預設值，不是所有發行版都必須使用的版本；發行版可能包含不同的 etcd 建置版本。請參閱 v1.37.1 [固定依賴清單](https://github.com/kubernetes/kubernetes/blob/v1.37.1/build/dependencies.yaml)及本手冊的[版本基線](../../setup/kubernetes-v1.37.md)。

## API 存取與 watch

應用程式用戶端應透過 Kubernetes API 列出並 watch 資源。請使用版本化 API discovery 端點或用戶端程式庫，確認叢集提供哪些資源版本。大型資源集合可透過 `limit` 和 `continue` 分頁；用戶端應依回應中的 continuation token 取得後續頁面，不要假設單一回應包含所有資料。

Kubernetes watch 會從 list 的 resource version 之後回報變更。用戶端必須能處理已過期的 resource version，重新執行 list 後再建立 watch。Watch 串流可能中斷，因此用戶端需要重新連線。不要把 watch 當成持久事件紀錄。這些規則屬於 Kubernetes API 契約，不是直接存取 etcd watch 的語義。

請參閱[API 概念](https://kubernetes.io/docs/reference/using-api/api-concepts/)、[API discovery](https://kubernetes.io/docs/concepts/overview/kubernetes-api/#api-groups-and-versioning)及 [client-go list/watch 指南](https://pkg.go.dev/k8s.io/client-go/tools/cache)。

## 維運注意事項

請依 Kubernetes 發行版的拓樸和版本指引，以具備法定人數的叢集執行 etcd。保護 peer 和 client 通訊、限制 etcd 資料目錄存取，並監控資料庫大小、磁碟延遲、叢集法定人數及 defragmentation 需求。定期備份 etcd，並在隔離環境驗證還原程序。請依發行版文件規劃升級順序；不要自行替換其 etcd 二進位檔或變更所儲存的 Kubernetes schema。

請使用官方 [etcd 維運指南](https://etcd.io/docs/v3.7/op-guide/)及發行版專屬的備份與還原指引。Kubernetes 控制平面管理者也應參閱[管理 Kubernetes 的 etcd 叢集](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)。

## 歷史實作說明

本手冊先前說明 etcd v2 事件歷程、v3 內部 watcher 群組、BoltDB 記錄格式、固定配額預設值及舊工具。這些實作細節與限制會隨 etcd 版本而異，不是 Kubernetes API 保證。舊版分析保留於[歷史歸檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/concepts/components/etcd-legacy-analysis-zh-TW.md)；目前實作請查閱對應 etcd 發行版文件。
