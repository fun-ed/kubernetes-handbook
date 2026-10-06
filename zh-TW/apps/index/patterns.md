# 一般準則
> 本頁的 Docker Engine 命令用於本地容器示範，並不表示 Kubernetes v1.37 節點使用 Docker Engine；叢集節點應設定相容 CRI 的執行時。映像檔標籤僅供範例，生產建置應使用受維護的基礎映像檔並按供應鏈策略固定 digest。

* 分離建置和執行環境
* 使用 `dumb-init` 等方式避免容器 PID 1 留下殭屍程序
* 不推薦直接使用Pod，而是推薦使用Deployment/DaemonSet等
* 不推薦在容器中使用後臺程序，而是推薦將程序前臺執行，並使用探針保證服務確實在執行中
* 推薦容器中應用日誌打到stdout和stderr，方便日誌外掛的處理
* 由於容器採用了COW，大量資料寫入有可能會有效能問題，推薦將資料寫入到Volume中
* 不推薦生產環境映像檔使用`latest`標籤，但開發環境推薦使用並設定`imagePullPolicy`為`Always`
* 推薦使用Readiness探針檢測服務是否真正執行起來了
* 使用`activeDeadlineSeconds`避免快速失敗的Job無限重啟
* 引入多容器模式（Sidecar、Ambassador、Adapter等）處理代理、請求速率控制和連線控制等問題

## 分離建置和執行環境

注意分離建置和執行環境，直接透過Dockerfile建置的映像檔不僅體積大，包含了很多執行時不必要的包，並且還容易引入安全隱患，如包含了應用的原始碼。

可以使用[Docker 多階段建置](https://docs.docker.com/build/building/multi-stage/)來簡化這個步驟。

```dockerfile
# 生产环境请将 builder 和 runtime 镜像固定到经审查的 digest。
FROM golang:1.27.1-bookworm AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY app.go .
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -o /out/app .

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /out/app /app
USER nonroot:nonroot
ENTRYPOINT ["/app"]
```

## 殭屍程序和孤兒程序

* 孤兒程序：一個父程序退出，而它的一個或多個子程序還在執行，那麼那些子程序將成為孤兒程序。孤兒程序將被init程序\(程序號為1\)所收養，並由init程序對它們完成狀態收集工作。
* 殭屍程序：一個程序使用fork建立子程序，如果子程序退出，而父程序並沒有呼叫wait或waitpid獲取子程序的狀態資訊，那麼子程序的程序描述符仍然儲存在系統中。

在容器中，很容易掉進的一個陷阱就是init程序沒有正確處理SIGTERM等退出訊號。這種情景很容易構造出來，比如

```bash
# 首先运行一个容器
$ docker run --rm busybox:1.37.0 sleep 10000

# 打开另外一个terminal
$ ps uax | grep sleep
sasha    14171  0.0  0.0 139736 17744 pts/18   Sl+  13:25   0:00 docker run busybox sleep 10000
root     14221  0.1  0.0   1188     4 ?        Ss   13:25   0:00 sleep 10000

# 接着kill掉第一个进程
$ kill 14171
# 现在会发现sleep进程并没有退出
$ ps uax | grep sleep
root     14221  0.0  0.0   1188     4 ?        Ss   13:25   0:00 sleep 10000
```

解決方法就是保證容器的init程序可以正確處理SIGTERM等退出訊號，比如使用dumb-init

```bash
docker run --rm --init busybox:1.37.0 sleep 10000
```

## 多容器設計模式

### Sidecar 模式（邊車模式）

Sidecar 模式是最常用的多容器模式，透過在Pod中新增輔助容器來擴充套件主應用的功能，而無需修改主應用程式碼。

**使用場景：**

- 日誌收集和轉發
- 監控指標收集
- 網路代理和服務網格
- 設定熱更新
- 安全掃描

**優勢：**

- 職責分離，每個容器專注單一功能
- 可以獨立更新和擴充套件
- 複用性強，可以跨多個應用使用

### Ambassador 模式（大使模式）

Ambassador 模式透過代理容器來簡化主應用對外部服務的存取，處理服務發現、負載平衡、重試邏輯等。

**使用場景：**

- 資料庫連線代理
- 外部API存取代理
- 服務發現和負載平衡
- 連線池管理
- 請求路由和熔斷

**優勢：**

- 簡化應用程式碼，將網路複雜性抽象到代理層
- 可以統一處理連線管理和錯誤重試
- 便於實現橫切關注點

### Adapter 模式（配接器模式）

Adapter 模式用於標準化應用輸出，將應用的輸出轉換為統一的格式或協議。

**使用場景：**

- 監控指標格式轉換
- 日誌格式標準化
- 協議轉換（HTTP到gRPC）
- 資料格式轉換

**優勢：**

- 不修改應用程式碼即可配合不同的監控和日誌系統
- 提供統一的資料格式
- 便於整合遺留系統

### 設定助手模式

透過專門的設定容器來管理應用設定，實現設定的動態更新和熱載入。

**使用場景：**

- 從設定中心拉取設定
- 金鑰管理和輪換
- 環境變數動態更新
- 設定檔案熱過載

**優勢：**

- 設定管理與業務邏輯分離
- 支援設定熱更新
- 統一的設定管理策略

### Sidecar 啟動順序控制最佳實踐

Sidecar Init 容器在 Kubernetes v1.28 以 Alpha 引入、v1.29 升為 Beta，並於 v1.33 達到穩定狀態；啟用狀態與行為請以目標版本文件為準。

**確保 Sidecar 優先啟動的策略：**

1. **使用 startupProbe（推薦）**：最可靠的方法，確保主應用等待 Sidecar 就緒
   ```yaml
   initContainers:
   - name: sidecar
     image: nginx:1.30.5
     restartPolicy: Always
     startupProbe:
       httpGet:
         path: /
         port: 80
       periodSeconds: 3
   ```

2. **應用層依賴處理**：在應用程式碼中實現對 Sidecar 的容錯和重試機制
3. **postStart 鉤子**：使用生命週期鉤子實現自定義等待邏輯
4. **避免錯誤做法**：不要依賴 readinessProbe 或 livenessProbe 來控制啟動順序

### 最佳實踐

1. **合理選擇模式**：根據實際需求選擇合適的多容器模式，避免過度設計
2. **資源管理**：為每個容器設定合適的資源限制，避免資源競爭
3. **生命週期管理**：確保容器間的啟動順序和依賴關係
4. **錯誤處理**：實現容器間的錯誤傳播和重試機制
5. **監控和日誌**：為每個容器設定獨立的監控和日誌收集
6. **啟動依賴控制**：使用 startupProbe 確保 Sidecar 容器優先就緒
7. **容錯設計**：在應用層面實現對 Sidecar 服務的容錯機制

## 參考文件

* [Kubernetes Production Patterns](https://github.com/gravitational/workshop/blob/master/k8sprod.md)
