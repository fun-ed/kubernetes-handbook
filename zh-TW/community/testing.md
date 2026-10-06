# 單元測試和整合測試

Kubernetes 測試工具與可用目標會隨原始碼分支變化。以下命令以 v1.37.1 原始碼樹為上下文；執行前請查閱該版本的建置指令碼以及上游 [SIG Testing 文件](https://github.com/kubernetes/community/tree/master/contributors/devel/sig-testing)。叢集級測試不能替代單元測試，單元測試也不能證明特定發行版或 CRI/CNI 實現的行為。

## 單元測試

單元測試驗證單個 Go package 的邏輯。修改程式碼時，應執行受影響 package 的測試並按專案約定新增或更新測試。

```bash
# 在 Kubernetes v1.37.1 源码树中运行一个 package 的测试
make test WHAT=./pkg/api/validation

# 直接使用 Go 工具运行该 package 的测试
go test ./pkg/api/validation

# 只运行名称匹配的测试
go test ./pkg/api/validation -run '^TestValidatePod$'
```

執行整套單元測試可能耗時較長；檢查目標、並行度、覆蓋率等引數時，以原始碼樹中的測試 Makefile 和開發文件為準，不要假定舊分支的引數在當前分支仍然有效。

## 整合測試

整合測試可能啟動本地 API Server、etcd 和其他元件；需要的二進位、資源與環境依賴應按 v1.37.1 測試文件準備。該分支提供的常見入口為：

```bash
make test-integration
```

執行前檢查目標的資源佔用及清理要求；若只需驗證一個 package，優先選擇其單元測試，避免無必要地啟動完整整合環境。

## 端到端測試

端到端測試需要滿足相應叢集、平台和權限要求。測試可能建立或刪除叢集資源，必須使用專用測試環境，並按照上游 [E2E 測試指南](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-testing/e2e-tests.md)及當前分支說明啟動和清理測試叢集。具體命令、Ginkgo 引數和支援的平台以 v1.37.1 原始碼樹中的文件為準。

Node e2e 與普通叢集 e2e 的依賴不同，也需查閱該版本 [Node e2e 測試指南](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-node/e2e-node-tests.md)。不要沿用本頁歷史的 Federation e2e、GCE 專案變數、舊 `hack/e2e.go` 引數或已過時的 Ginkgo 標誌。

## 參考

* [Kubernetes 測試指南](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-testing/testing.md)
* [E2E 測試](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-testing/e2e-tests.md)
* [Node e2e 測試](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-node/e2e-node-tests.md)
* [如何編寫 e2e 測試](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-testing/writing-good-e2e-tests.md)
