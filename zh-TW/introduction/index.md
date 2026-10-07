# Kubernetes 簡介

Kubernetes 是谷歌開源的容器叢集管理系統，是 Google 多年大規模容器管理技術 Borg 的開源版本，主要功能包括：

* 基於容器的應用部署、維護和滾動升級
* 負載平衡和服務發現
* 跨機器和跨地區的叢集排程
* 自動伸縮
* 無狀態服務和有狀態服務
* 廣泛的 Volume 支援
* 外掛機制保證擴充套件性

Kubernetes 發展非常迅速，已經成為容器編排領域的領導者。

## Kubernetes 是一個平台

Kubernetes 提供了很多的功能，它可以簡化應用程式的工作流，加快開發速度。通常，一個成功的應用編排系統需要有較強的自動化能力，這也是為什麼 Kubernetes 被設計作為建置元件和工具的生態系統平台，以便更輕鬆地部署、擴充套件和管理應用程式。

使用者可以使用 Label 以自己的方式組織管理資源，還可以使用 Annotation 來自定義資源的描述資訊，比如為管理工具提供狀態檢查等。

此外，Kubernetes 控制器也是建置在跟開發人員和使用者使用的相同的 API 之上。使用者還可以編寫自己的控制器和排程器，也可以透過各種外掛機制擴充套件系統的功能。

這種設計使得可以方便地在 Kubernetes 之上建置各種應用系統。

## Kubernetes 不是什麼

Kubernetes 不是一個傳統意義上，包羅永珍的 PaaS \(平台即服務\) 系統。它給使用者預留了選擇的自由。

* 不限制支援的應用程式型別，它不插手應用程式框架, 也不限制支援的語言 \(如 Java, Python, Ruby 等\)，只要應用符合 [12 因素](http://12factor.net/) 即可。Kubernetes 旨在支援極其多樣化的工作負載，包括無狀態、有狀態和資料處理工作負載。只要應用可以在容器中執行，那麼它就可以很好的在 Kubernetes 上執行。
* 不提供內建的中介軟體 \(如訊息中介軟體\)、資料處理框架 \(如 Spark\)、資料庫 \(如 mysql\) 或叢集儲存系統 \(如 Ceph\) 等。這些應用直接執行在 Kubernetes 之上。
* 不提供點選即部署的服務市場。
* 不直接部署程式碼，也不會建置您的應用程式，但您可以在 Kubernetes 之上建置需要的持續整合 \(CI\) 工作流。
* 允許使用者選擇自己的日誌、監控和告警系統。
* 不提供應用程式設定語言或系統 \(如 [jsonnet](https://github.com/google/jsonnet)\)。
* 不提供機器設定、維護、管理或自愈系統。

另外，已經有很多 PaaS 系統執行在 Kubernetes 之上，如 [Openshift](https://github.com/openshift/origin), [Deis](http://deis.io/) 和 [Eldarion](http://eldarion.cloud/) 等。 您也可以建置自己的 PaaS 系統，或者只使用 Kubernetes 管理您的容器應用。

當然了，Kubernetes 不僅僅是一個 “編排系統”，它消除了編排的需要。Kubernetes 透過宣告式的 API 和一系列獨立、可組合的控制器保證了應用總是在期望的狀態，而使用者並不需要關心中間狀態是如何轉換的。這使得整個系統更容易使用，而且更強大、更可靠、更具彈性和可擴充套件性。

## 核心元件

Kubernetes 叢集由控制平面和工作節點組成。控制平面透過 API Server 管理宣告式資源；etcd 儲存叢集狀態，controller manager 和 scheduler 推動實際狀態接近期望狀態。每個工作節點執行 kubelet，並透過 CRI 與容器執行時通訊。容器網路由 CNI 外掛設定，持久卷由 CSI 驅動提供。

常見的叢集網路元件還包括 kube-proxy（除非網路實現自行提供 Service 代理）和 CoreDNS。Kubernetes 不內建通用監控、日誌平台或多叢集控制平面。metrics-server 等元件由叢集發行版或運維人員單獨選擇和維護。

![](../.gitbook/assets/architecture%20%2810%29.png)

## Kubernetes 版本

本節說明版本，不保證每個附加元件都支援表列版本。以下內容以本手冊 **Kubernetes v1.37.1 / 2026-10-05 快照**，且 **v1.37 為最新次版本分支**為前提。Kubernetes 專案維護最新次版本分支及前兩個分支：

| 釋出分支 | 此快照中的狀態 |
| --- | --- |
| v1.37 | 最新維護中的次版本分支；本手冊基線為 v1.37.1。 |
| v1.36 | 前一個維護中的次版本分支。 |
| v1.35 | 前兩個維護中的次版本分支。 |

這三個分支不是對未來三個版本的相容承諾。補丁版本及生命週期日期會變動，請查看[官方 Kubernetes 釋出頁面](https://kubernetes.io/releases/)確認最新補丁與支援狀態。Kubernetes 1.19 及更新版本通常有約一年的補丁支援，實際以官方政策為準。本手冊保留舊版本內容，供了解歷史設計與協助遷移；封存內容或舊範例不是目前的部署指引。

### v1.37 API server 的元件版本偏差

下表以**穩態時所有 kube-apiserver 都是 v1.37.x**為基準；HA 升級期間短暫混跑的情況另列於第一列。表中列出上游版本偏差允許範圍，不代表建議任意混用補丁版本。請遵循[官方版本偏差策略](https://kubernetes.io/releases/version-skew-policy/)及部署工具更嚴格的規則。

| 元件 | 允許的次版本 |
| --- | --- |
| HA 叢集中的 kube-apiserver | 僅在升級過渡期間可混用 v1.36 與 v1.37；各執行個體間最多相差一個次版本。 |
| kubelet | v1.34–v1.37。版本不得高於任何 API server。 |
| kube-proxy | v1.34–v1.37，且與同一節點上的 kubelet 最多相差三個次版本。版本不得高於任何 API server。 |
| kube-controller-manager、kube-scheduler、cloud-controller-manager | v1.36–v1.37；版本不得高於其通訊對象中的任何 API server。 |
| kubectl | v1.36–v1.38，比 API server 最多舊或新一個次版本。此偏差範圍不代表 v1.38 已釋出。 |

HA 升級期間若 API server 混用不同版本，其他元件的允許範圍會縮小：必須逐一符合每個 API server 的版本偏差限制，不能只比對最新版本。升級不得跳過次版本。v1.34 kubelet 雖在 v1.37 API server 的偏差允許範圍內，但這不表示 v1.34 分支仍受官方維護。CNI、CSI 和第三方元件的相容性須另外核對；Kubernetes 元件版本偏差策略不會替它們提供相容性認證。

本手冊基線及各元件的相容性證據，請參閱 [v1.37.1 相容性指南](../setup/kubernetes-v1.37.md)、[元件版本矩陣](../setup/component-versions.md)和[升級指南](../setup/upgrade.md)。

## 參考文件

* [What is Kubernetes?](https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/)
* [HOW CUSTOMERS ARE REALLY USING KUBERNETES](https://apprenda.com/blog/customers-really-using-kubernetes/)
