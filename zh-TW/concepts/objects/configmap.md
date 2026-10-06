# ConfigMap

應用程式的執行可能會依賴一些設定，而這些設定又是可能會隨著需求產生變化的，如果我們的應用程式架構不是應用和設定分離的，那麼就會存在當我們需要去修改某些設定項的屬性時需要重新建置映像檔檔案的窘境。現在，ConfigMap元件可以很好的幫助我們實現應用和設定分離，避免因為修改設定項而重新建置映像檔。

ConfigMap 用於儲存設定資料的鍵值對，可以用來儲存單個屬性，也可以用來儲存設定檔案。ConfigMap 跟 Secret 很類似，但它可以更方便地處理不包含敏感資訊的字串。

## API 版本對照表

| Kubernetes 版本 | Core API 版本 |
| :--- | :--- |
| v1.5+ | core/v1 |

## ConfigMap 建立

可以使用 `kubectl create configmap` 從檔案、目錄或者 key-value 字串建立等建立 ConfigMap。也可以透過 `kubectl create -f file` 建立。

### 從 key-value 字串建立

```bash
$ kubectl create configmap special-config --from-literal=special.how=very
configmap "special-config" created
$ kubectl get configmap special-config -o go-template='{{.data}}'
map[special.how:very]
```

### 從 env 檔案建立

```bash
$ echo -e "a=b\nc=d" | tee config.env
a=b
c=d
$ kubectl create configmap special-config --from-env-file=config.env
configmap "special-config" created
$ kubectl get configmap special-config -o go-template='{{.data}}'
map[a:b c:d]
```

### 從目錄建立

```bash
$ mkdir config
$ echo a>config/a
$ echo b>config/b
$ kubectl create configmap special-config --from-file=config/
configmap "special-config" created
$ kubectl get configmap special-config -o go-template='{{.data}}'
map[a:a
 b:b
]
```

### 從檔案 Yaml/Json 檔案建立

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: special-config
  namespace: default
data:
  special.how: very
  special.type: charm
```

```bash
$ kubectl create  -f  config.yaml
configmap "special-config" created
```

## ConfigMap 使用

ConfigMap 可以透過三種方式在 Pod 中使用：設定環境變數、設定容器命令列引數，或將檔案或目錄直接掛載為 Volume。

> **注意**
>
> * ConfigMap 必須在 Pod 引用它之前建立
> * 使用 `envFrom` 時，將會自動忽略無效的鍵
> * Pod 只能使用同一個命名空間內的 ConfigMap

首先建立 ConfigMap：

```bash
$ kubectl create configmap special-config --from-literal=special.how=very --from-literal=special.type=charm
$ kubectl create configmap env-config --from-literal=log_level=INFO
```

### 用作環境變數

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
    - name: test-container
      image: busybox:1.37.0
      command: ["/bin/sh", "-c", "env"]
      env:
        - name: SPECIAL_LEVEL_KEY
          valueFrom:
            configMapKeyRef:
              name: special-config
              key: special.how
        - name: SPECIAL_TYPE_KEY
          valueFrom:
            configMapKeyRef:
              name: special-config
              key: special.type
      envFrom:
        - configMapRef:
            name: env-config
  restartPolicy: Never
```

當 Pod 結束後會輸出

```text
SPECIAL_LEVEL_KEY=very
SPECIAL_TYPE_KEY=charm
log_level=INFO
```

### 用作命令列引數

將 ConfigMap 用作命令列引數時，需要先把 ConfigMap 的資料儲存在環境變數中，然後透過 `$(VAR_NAME)` 的方式引用環境變數.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dapi-test-pod
spec:
  containers:
    - name: test-container
      image: busybox:1.37.0
      command: ["/bin/sh", "-c", "echo $(SPECIAL_LEVEL_KEY) $(SPECIAL_TYPE_KEY)" ]
      env:
        - name: SPECIAL_LEVEL_KEY
          valueFrom:
            configMapKeyRef:
              name: special-config
              key: special.how
        - name: SPECIAL_TYPE_KEY
          valueFrom:
            configMapKeyRef:
              name: special-config
              key: special.type
  restartPolicy: Never
```

當 Pod 結束後會輸出

```text
very charm
```

### 使用 volume 將 ConfigMap 作為檔案或目錄直接掛載

將建立的 ConfigMap 直接掛載至 Pod 的 / etc/config 目錄下，其中每一個 key-value 鍵值對都會生成一個檔案，key 為檔名，value 為內容

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: vol-test-pod
spec:
  containers:
    - name: test-container
      image: busybox:1.37.0
      command: ["/bin/sh", "-c", "cat /etc/config/special.how"]
      volumeMounts:
      - name: config-volume
        mountPath: /etc/config
  volumes:
    - name: config-volume
      configMap:
        name: special-config
  restartPolicy: Never
```

當 Pod 結束後會輸出

```text
very
```

將建立的 ConfigMap 中 special.how 這個 key 掛載到 / etc/config 目錄下的一個相對路徑 / keys/special.level。如果存在同名檔案，直接覆蓋。其他的 key 不掛載

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dapi-test-pod
spec:
  containers:
    - name: test-container
      image: busybox:1.37.0
      command: ["/bin/sh","-c","cat /etc/config/keys/special.level"]
      volumeMounts:
      - name: config-volume
        mountPath: /etc/config
  volumes:
    - name: config-volume
      configMap:
        name: special-config
        items:
        - key: special.how
          path: keys/special.level
  restartPolicy: Never
```

當 Pod 結束後會輸出

```text
very
```

ConfigMap 支援同一個目錄下掛載多個 key 和多個目錄。例如下面將 special.how 和 special.type 透過掛載到 / etc/config 下。並且還將 special.how 同時掛載到 / etc/config2 下。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dapi-test-pod
spec:
  containers:
    - name: test-container
      image: busybox:1.37.0
      command: ["/bin/sh","-c","sleep 36000"]
      volumeMounts:
      - name: config-volume
        mountPath: /etc/config
      - name: config-volume2
        mountPath: /etc/config2
  volumes:
    - name: config-volume
      configMap:
        name: special-config
        items:
        - key: special.how
          path: keys/special.level
        - key: special.type
          path: keys/special.type
    - name: config-volume2
      configMap:
        name: special-config
        items:
        - key: special.how
          path: keys/special.level
  restartPolicy: Never
```

```bash
# ls  /etc/config/keys/
special.level  special.type
# ls  /etc/config2/keys/
special.level
# cat  /etc/config/keys/special.level
very
# cat  /etc/config/keys/special.type
charm
```

### 使用 subpath 將 ConfigMap 作為單獨的檔案掛載到目錄

在一般情況下 configmap 掛載檔案時，會先覆蓋掉掛載目錄，然後再將 congfigmap 中的內容作為檔案掛載進行。如果想不對原來的資料夾下的檔案造成覆蓋，只是將 configmap 中的每個 key，按照檔案的方式掛載到目錄下，可以使用 subpath 引數。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dapi-test-pod
spec:
  containers:
    - name: test-container
      image: nginx:1.30.5
      command: ["/bin/sh","-c","sleep 36000"]
      volumeMounts:
      - name: config-volume
        mountPath: /etc/nginx/special.how
        subPath: special.how
  volumes:
    - name: config-volume
      configMap:
        name: special-config
        items:
        - key: special.how
          path: special.how
  restartPolicy: Never
```

```bash
root@dapi-test-pod:/# ls /etc/nginx/
conf.d    fastcgi_params    koi-utf  koi-win  mime.types  modules  nginx.conf  scgi_params    special.how  uwsgi_params  win-utf
root@dapi-test-pod:/# cat /etc/nginx/special.how
very
root@dapi-test-pod:/#
```

## 不可變 ConfigMap

> 不可變 ConfigMap 在 v1.21.0 進入穩定版本。

當叢集包含大量 ConfigMap 和 Secret 時，大量的 watch 事件會急劇增加 kube-apiserver 的負載，並會導致錯誤設定過快傳播到整個叢集。在這種情況中，給不需要經常修改的 ConfigMap 和 Secret 設定 `immutable: true` 就可以避免類似的問題。

不可變 ConfigMap 的好處包括：

* 保護應用，使之免受意外更新所帶來的負面影響。
* 透過大幅降低對 kube-apiserver 的壓力提升叢集效能，這是因為 Kubernetes 會關閉不可變 ConfigMap 的監視操作。

以下是一個可直接套用的不可變 ConfigMap。建立後，`data` 與 `binaryData` 都不能再修改；需要變更設定時，請建立新的 ConfigMap，並更新工作負載引用。

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config-v1
data:
  log_level: "info"
immutable: true
```

## 參考文件

* [ConfigMap](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/)
