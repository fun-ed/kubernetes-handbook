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

本手冊的當前操作說明以 Kubernetes v1.37.1 為準。升級前請核對目標發行版的版本、元件版本和 API 相容性。Kubernetes 專案維護最近三個次要版本分支；v1.19 及之後的版本通常獲得約一年的補丁支援。實際支援狀態以[發行版頁面](https://kubernetes.io/releases/)為準。

### 歷史版本釋出記錄（2017 至 2019 年，不代表當前支援狀態）

| Kubernetes version | Release month | End-of-life-month |
| :--- | :--- | :--- |
| v1.6.x | March 2017 | December 2017 |
| v1.7.x | June 2017 | March 2018 |
| v1.8.x | September 2017 | June 2018 |
| v1.9.x | December 2017 | September 2018 |
| v1.10.x | March 2018 | December 2018 |
| v1.11.x | June 2018 | March 2019 |
## 參考文件

* [What is Kubernetes?](https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/)
* [HOW CUSTOMERS ARE REALLY USING KUBERNETES](https://apprenda.com/blog/customers-really-using-kubernetes/)
