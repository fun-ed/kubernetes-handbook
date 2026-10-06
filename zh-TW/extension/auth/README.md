# 存取控制

Kubernetes API Server 依次進行認證、授權和准入控制。認證確定請求身分，授權決定該身分能否執行請求；授權透過後，准入控制器才會檢查請求。

無論請求來自叢集內外，都要遵循 API Server 的認證與授權設定；HTTP 本身不會讓請求繞過這些檢查。不要透過明文 HTTP 存取 API Server，應使用 TLS，並為客戶端設定明確身分和最小權限。

![](../../.gitbook/assets/authentication%20%282%29.png)

## 認證

Kubernetes 為服務賬號提供 API 物件，但不直接管理普通使用者。客戶端請求由 API Server 設定的認證機制處理；無法識別的請求可能作為匿名請求繼續處理，具體取決於叢集設定。認證失敗會返回 HTTP 401。

## 授權

API Server 根據使用者、組、請求方法、資源和命名空間等屬性判斷是否允許請求。請求未獲授權時會返回 HTTP 403；只有獲准的請求才會進入准入控制階段。

RBAC 是 Kubernetes 常用的授權機制，本文的 [RBAC 授權](rbac.md)介紹其角色和綁定物件。不要設定允許所有請求的授權方式。

## 參考文件

* [認證](https://kubernetes.io/docs/reference/access-authn-authz/authentication/)
* [授權](https://kubernetes.io/docs/reference/access-authn-authz/authorization/)
* [RBAC 授權](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
