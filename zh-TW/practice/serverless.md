# Serverless

Serverless，即無伺服器架構，將大家從伺服器中解放了出來，只需要關注業務邏輯本身。使用者只需要關注資料和業務邏輯，無需維護伺服器，也不需要關心繫統的容量和擴容。Serverless 本質上是一種更簡單易用的 PaaS，包含兩種含義：

僅依賴雲端服務來管理業務邏輯和狀態的應用或服務，一般稱為 BaaS \(Backend as a Service\) 事件驅動且短時執行應用或服務，其主要邏輯由開發者完成，但由第三方管理（比如 AWS Lambda），一般稱為 FaaS \(Function as a Service\)。目前大火的 Serverless 一般是指 FaaS。

引入 serverless 可以給應用開發者帶來明顯的好處

* 使用者無需設定和管理伺服器
* 使用者服務不需要基於特定框架或軟體庫
* 部署簡單，只需要將程式碼上傳到 serverless 平台即可
* 完全自動化的橫向擴充套件
* 事件觸發，比如 http 請求觸發、檔案更新觸發、時間觸發、訊息觸發等
* 低成本，比如 AWS Lambda 按執行時間和觸發次數收費，在程式碼未執行時無需付費

當然，serverless 也並非銀彈，也有其特有的侷限性

* 無狀態，服務的任何程序內或主機狀態均無法被後續呼叫所使用，需要藉助外部資料庫或網路儲存管理狀態
* 每次函式呼叫的時間一般都有限制，比如 AWS Lambda 限制每個函式最長只能執行 5 分鐘
* 啟動延遲，特別是應用不活躍或者突發流量的情況下延遲尤為明顯
* 平台依賴，比如服務發現、監控、除錯、API Gateway 等都依賴於 serverless 平台提供的功能

## 開源框架

* OpenFaas: [https://github.com/openfaas/faas](https://github.com/openfaas/faas)
* Fission: [https://github.com/fission/fission](https://github.com/fission/fission)
* Kubeless: [https://github.com/kubeless/kubeless](https://github.com/kubeless/kubeless)
* OpenWhisk: [https://github.com/apache/incubator-openwhisk](https://github.com/apache/incubator-openwhisk)
* Fn: [https://fnproject.io/](https://fnproject.io/)

## 商業產品

* AWS Lambda: [http://docs.aws.amazon.com/lambda/latest/dg/welcome.html](http://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
* AWS Fargate: [https://aws.amazon.com/cn/fargate/](https://aws.amazon.com/cn/fargate/)
* Azure Container Instance \(ACI\): [https://azure.microsoft.com/zh-cn/services/container-instances/](https://azure.microsoft.com/zh-cn/services/container-instances/)
* Azure Functions: [https://azure.microsoft.com/zh-cn/services/functions/](https://azure.microsoft.com/zh-cn/services/functions/)
* Google Cloud Functions: [https://cloud.google.com/functions/](https://cloud.google.com/functions/)
* Huawei CCI: [https://www.huaweicloud.com/product/cci.html](https://www.huaweicloud.com/product/cci.html)
* Aliyun Serverless Kubernetes: [https://help.aliyun.com/document\_detail/71480.html](https://help.aliyun.com/document_detail/71480.html)

很多商業產品也可以與 Kubernetes 進行無縫整合，即透過 [Virtual Kubelet](https://github.com/virtual-kubelet/virtual-kubelet) 將商業 Serverless 產品（如 ACI 和 Fargate等）作為 Kubernetes 叢集的一個無限 Node 使用，這樣就無需考慮 Node 數量的問題。

![](../.gitbook/assets/virtual-kubelet%20%282%29.png)

## 參考文件

* [Awesome Serverless](https://github.com/anaibol/awesome-serverless)
* [AWS Lambda](http://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
* [Serverless Architectures](https://martinfowler.com/articles/serverless.html)
* [TNS Guide to Serverless Technologies](http://thenewstack.io/tns-guide-serverless-technologies-best-frameworks-platforms-tools/)
* [Serverless blogs and posts](https://github.com/JustServerless/awesome-serverless)
