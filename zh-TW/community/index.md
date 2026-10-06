# 開發指南

## 開發環境

開發 Kubernetes 時，應以所檢出原始碼版本的建置指令碼和開發者文件為準。Kubernetes v1.37.1 要求 Go 至少為 1.26.0；具體 Go 工具鏈及其他依賴以該版本的 [`build/dependencies.yaml`](https://github.com/kubernetes/kubernetes/blob/v1.37.1/build/dependencies.yaml) 和建置指令碼為準。

```bash
git clone https://github.com/kubernetes/kubernetes.git
cd kubernetes
git checkout v1.37.1
```

不要使用本頁舊版範例中的 Docker Engine 1.13、Go 1.10、etcd 3.2 或 `apt-key` 安裝步驟。Kubernetes 使用 CRI 執行時；開發環境所需工具、建置和本地叢集流程可能隨原始碼版本變化，請遵循 [Kubernetes 儲存庫開發文件](https://github.com/kubernetes/kubernetes/tree/v1.37.1) 與 [Contributor Guide](https://www.kubernetes.dev/docs/)。若要啟動本地叢集，請先閱讀該版本的 `hack/local-up-cluster.sh` 說明，並在隔離的開發環境中執行。

## 測試

單元測試和整合測試的目標、引數及所需工具，應按正在修改的分支文件執行。基礎命令和測試範圍見[測試指南](testing.md)及上游 [SIG Testing 文件](https://github.com/kubernetes/community/tree/master/contributors/devel/sig-testing)。

修改程式碼時應一併新增或更新相應測試；端到端測試需要滿足對應叢集、平台和環境要求，不能將本地單元測試結果視為叢集相容性驗證。

## 貢獻流程

貢獻程式碼、文件、測試或 issue 處理均可幫助 Kubernetes 社群。開始前請閱讀 [Contributor Guide](https://www.kubernetes.dev/docs/)、[程式碼約定](https://github.com/kubernetes/community/blob/master/contributors/guide/coding-conventions.md)和對應 SIG 的開發指南。Pull Request 應針對明確的問題，附上相應測試說明，並遵循當前儲存庫的審查與提交要求。

釋出分支修復、cherry-pick 及釋出經理審批流程會隨釋出週期變化；不要沿用本文舊版 `release-1.7`、Hub 或過期 Bot 操作範例。請按 [Kubernetes Release SIG](https://github.com/kubernetes/sig-release) 和當前釋出分支的貢獻指南操作。

## 參考

* [Kubernetes Contributor Community](https://kubernetes.io/community/)
* [Kubernetes Contributor Guide](https://www.kubernetes.dev/docs/)
* [Kubernetes 開發者文件](https://github.com/kubernetes/community/tree/master/contributors/devel)
* [Kubernetes 測試文件](https://github.com/kubernetes/community/tree/master/contributors/devel/sig-testing)
* [Special Interest Groups](https://github.com/kubernetes/community/blob/master/sig-list.md)
* [Kubernetes TestGrid](https://testgrid.k8s.io/)
