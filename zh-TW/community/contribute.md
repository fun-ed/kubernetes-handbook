# 社群貢獻

Kubernetes 支援以許多種方式來貢獻社群，包括彙報程式碼缺陷、提交問題修復和功能實現、新增或修復文件、協助使用者解決問題等等。

## 社群結構

Kubernetes 社群由三部分組成

* [Steering Committee](https://github.com/kubernetes/community/tree/master/committee-steering)
* [Special Interest Groups (SIGs)](https://github.com/kubernetes/community/blob/master/sig-list.md)
* Working Groups：請透過對應 SIG 的社群資料查詢當前仍活躍的工作組

![SIG-diagram.png](../.gitbook/assets/SIG-diagram.png)

## 向 Kubernetes 主線貢獻

修改 Kubernetes 程式碼、測試或文件時，應遵循 [Contributor Guide](https://www.kubernetes.dev/docs/) 與上游儲存庫的貢獻說明。提交小而聚焦的 Pull Request，解釋變更原因，遵循當前的程式碼/API/kubectl 約定，並在提交說明中報告適用的測試結果。測試目標及執行方式會隨原始碼版本調整，參見[測試指南](testing.md)。

## 釋出分支修復

釋出分支修復和 cherry-pick 需遵循當前 Kubernetes Release SIG 流程、目標分支的貢獻說明及釋出經理審批要求。支援維護的分支列表和審批人會隨時間變化；不要照搬舊範例中的 `release-1.7`、Hub 安裝方式或舊 PR/Bot 流程。請查閱 [Kubernetes Release SIG](https://github.com/kubernetes/sig-release) 及當前釋出週期的[釋出經理資訊](https://github.com/kubernetes/sig-release/blob/master/release-managers.md)。

## 參考文件

如果在社群貢獻中碰到問題，可以參考以下指南

* [**Kubernetes Contributor Community**](https://kubernetes.io/community/)
* [**Kubernetes Contributor Guide**](https://github.com/kubernetes/community/tree/master/contributors/guide)
* [**Kubernetes Developer Guide**](https://github.com/kubernetes/community/tree/master/contributors/devel)
* [**Kubernetes Contributor Documentation**](https://www.kubernetes.dev/docs/)
* [Special Interest Groups](https://github.com/kubernetes/community)
* [Feature Tracking and Backlog](https://github.com/kubernetes/features)
* [Community Expectations](https://github.com/kubernetes/community/blob/master/contributors/guide/expectations.md)
* [Kubernetes release managers](https://github.com/kubernetes/sig-release/blob/master/release-managers.md)
