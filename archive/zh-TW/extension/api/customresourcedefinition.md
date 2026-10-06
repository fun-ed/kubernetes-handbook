# CRD 範例與舊工具鏈（封存）

> 歷史材料，包含 Kubernetes v1.22 起已移除的 `apiextensions.k8s.io/v1beta1` manifest 與 Kubebuilder 1.0.1 工具鏈；不得用於目前叢集。原始段落及範例保留如下。

## 歷史 CRD 範例（v1beta1，已移除）

下面的例子會建立一個 `/apis/stable.example.com/v1/namespaces/<namespace>/crontabs/…` 的自定義 API：

```yaml
apiVersion: apiextensions.k8s.io/v1beta1
kind: CustomResourceDefinition
metadata:
  # name must match the spec fields below, and be in the form: <plural>.<group>
  name: crontabs.stable.example.com
spec:
  # group name to use for REST API: /apis/<group>/<version>
  group: stable.example.com
  # versions to use for REST API: /apis/<group>/<version>
  versions:
  - name: v1beta1
    # Each version can be enabled/disabled by Served flag.
    served: true
    # One and only one version must be marked as the storage version.
    storage: true
  - name: v1
    served: true
    storage: false
  # either Namespaced or Cluster
  scope: Namespaced
  names:
    # plural name to be used in the URL: /apis/<group>/<version>/<plural>
    plural: crontabs
    # singular name to be used as an alias on the CLI and for display
    singular: crontab
    # kind is normally the CamelCased singular type. Your resource manifests use this.
    kind: CronTab
    # shortNames allow shorter string to match your resource on the CLI
    shortNames:
    - ct
```

API 建立好後，就可以建立具體的 CronTab 物件了

```bash
$ cat my-cronjob.yaml
apiVersion: "stable.example.com/v1"
kind: CronTab
metadata:
  name: my-new-cron-object
spec:
  cronSpec: "* * * * /5"
  image: my-awesome-cron-image

$ kubectl create -f my-crontab.yaml
crontab "my-new-cron-object" created

$ kubectl get crontab
NAME                 KIND
my-new-cron-object   CronTab.v1.stable.example.com
$ kubectl get crontab my-new-cron-object -o yaml
apiVersion: stable.example.com/v1
kind: CronTab
metadata:
  creationTimestamp: 2017-07-03T19:00:56Z
  name: my-new-cron-object
  namespace: default
  resourceVersion: "20630"
  selfLink: /apis/stable.example.com/v1/namespaces/default/crontabs/my-new-cron-object
  uid: 5c82083e-5fbd-11e7-a204-42010a8c0002
spec:
  cronSpec: '* * * * /5'
  image: my-awesome-cron-image
```

## Validation（歷史 v1beta1 範例）

> 以下 `validation` 欄位佈局和 `CustomResourceValidation` feature gate 屬於 Kubernetes v1.22 之前的歷史範例，不適用於 v1.37.1。當前 validation 必須放在 `spec.versions[].schema.openAPIV3Schema`，範例見本文開頭。

比如下面的 CRD 要求

* `spec.cronSpec` 必須是匹配正規表示式的字串
* `spec.replicas` 必須是從 1 到 10 的整數

```yaml
apiVersion: apiextensions.k8s.io/v1beta1
kind: CustomResourceDefinition
metadata:
  name: crontabs.stable.example.com
spec:
  group: stable.example.com
  version: v1
  scope: Namespaced
  names:
    plural: crontabs
    singular: crontab
    kind: CronTab
    shortNames:
    - ct
  validation:
   # openAPIV3Schema is the schema for validating custom objects.
    openAPIV3Schema:
      properties:
        spec:
          properties:
            cronSpec:
              type: string
              pattern: '^(\d+|\*)(/\d+)?(\s+(\d+|\*)(/\d+)?){4}$'
            replicas:
              type: integer
              minimum: 1
              maximum: 10
```

這樣，在建立下面的 CronTab 時

```yaml
apiVersion: "stable.example.com/v1"
kind: CronTab
metadata:
  name: my-new-cron-object
spec:
  cronSpec: "* * * *"
  image: my-awesome-cron-image
  replicas: 15
```

會報驗證失敗的錯誤：

```bash
The CronTab "my-new-cron-object" is invalid: []: Invalid value: map[string]interface {}{"apiVersion":"stable.example.com/v1", "kind":"CronTab", "metadata":map[string]interface {}{"name":"my-new-cron-object", "namespace":"default", "deletionTimestamp":interface {}(nil), "deletionGracePeriodSeconds":(*int64)(nil), "creationTimestamp":"2017-09-05T05:20:07Z", "uid":"e14d79e7-91f9-11e7-a598-f0761cb232d1", "selfLink":"","clusterName":""}, "spec":map[string]interface {}{"cronSpec":"* * * *", "image":"my-awesome-cron-image", "replicas":15}}:
validation failure list:
spec.cronSpec in body should match '^(\d+|\*)(/\d+)?(\s+(\d+|\*)(/\d+)?){4}$'
spec.replicas in body should be less than or equal to 10
```

## Subresources（歷史 v1beta1 範例）

以下 `/status` 和 `/scale` 說明記錄舊版本的功能階段；當前 `v1` 子資源欄位位於對應的 `spec.versions[].subresources`，不需啟用舊 feature gate，見本文開頭的清單。

> v1.10 版本使用前需要在 `kube-apiserver` 開啟 `--feature-gates=CustomResourceSubresources=true`。

```yaml
# resourcedefinition.yaml
apiVersion: apiextensions.k8s.io/v1beta1
kind: CustomResourceDefinition
metadata:
  name: crontabs.stable.example.com
spec:
  group: stable.example.com
  version: v1
  scope: Namespaced
  names:
    plural: crontabs
    singular: crontab
    kind: CronTab
    shortNames:
    - ct
  # subresources describes the subresources for custom resources.
  subresources:
    # status enables the status subresource.
    status: {}
    # scale enables the scale subresource.
    scale:
      # specReplicasPath defines the JSONPath inside of a custom resource that corresponds to Scale.Spec.Replicas.
      specReplicasPath: .spec.replicas
      # statusReplicasPath defines the JSONPath inside of a custom resource that corresponds to Scale.Status.Replicas.
      statusReplicasPath: .status.replicas
      # labelSelectorPath defines the JSONPath inside of a custom resource that corresponds to Scale.Status.Selector.
      labelSelectorPath: .status.labelSelector
```

```bash
$ kubectl create -f resourcedefinition.yaml
$ kubectl create -f- <<EOF
apiVersion: "stable.example.com/v1"
kind: CronTab
metadata:
  name: my-new-cron-object
spec:
  cronSpec: "* * * * */5"
  image: my-awesome-cron-image
  replicas: 3
EOF

$ kubectl scale --replicas=5 crontabs/my-new-cron-object
crontabs "my-new-cron-object" scaled

$ kubectl get crontabs my-new-cron-object -o jsonpath='{.spec.replicas}'
5
```

## Categories（歷史 v1beta1 範例）

Categories 用來將 CRD 物件分組，這樣就可以使用 `kubectl get <category-name>` 來查詢屬於該組的所有物件。

下面的 CRD manifest 僅作舊 `v1beta1` schema 樣例，不能部署到 v1.37.1。`categories` 能力仍可在當前 CRD 的 `spec.names.categories` 中使用。

```yaml

# resourcedefinition.yaml
apiVersion: apiextensions.k8s.io/v1beta1
kind: CustomResourceDefinition
metadata:
  name: crontabs.stable.example.com
spec:
  group: stable.example.com
  version: v1
  scope: Namespaced
  names:
    plural: crontabs
    singular: crontab
    kind: CronTab
    shortNames:
    - ct
    # categories is a list of grouped resources the custom resource belongs to.
    categories:
    - all
```

```yaml
# my-crontab.yaml
apiVersion: "stable.example.com/v1"
kind: CronTab
metadata:
  name: my-new-cron-object
spec:
  cronSpec: "* * * * */5"
  image: my-awesome-cron-image
```

```bash
$ kubectl create -f resourcedefinition.yaml
$ kubectl create -f my-crontab.yaml
$ kubectl get all
NAME                          AGE
crontabs/my-new-cron-object   3s
```

## CRD 控制器

在使用 CRD 擴充套件 Kubernetes API 時，通常還需要實現一個新建資源的控制器，監聽新資源的變化情況，並作進一步的處理。

[https://github.com/kubernetes/sample-controller](https://github.com/kubernetes/sample-controller) 提供了一個 CRD 控制器的範例，包括

* 如何註冊資源 `Foo`
* 如何建立、刪除和查詢 `Foo` 物件
* 如何監聽 `Foo` 資源物件的變化情況

## Kubebuilder（歷史 Kubebuilder 1.0.1 範例）

從上面的例項中可以看到從頭構建一個 CRD 控制器並不容易，需要對 Kubernetes 的 API 有深入瞭解，並且RBAC 整合、映像檔構建、持續整合和部署等都需要很大工作量。

[kubebuilder](https://github.com/kubernetes-sigs/kubebuilder) 正是為解決這個問題而生，為 CRD 控制器提供了一個簡單易用的框架，並可直接生成映像檔構建、持續整合、持續部署等所需的資原始檔。

> 以下 Kubebuilder 1.0.1 / `dep` / `go get` 安裝與專案佈局只說明舊工具鏈，不適用於當前 controller-runtime 版本。當前專案應按 [Kubebuilder 官方文件](https://book.kubebuilder.io/)選擇與 Kubernetes/client-go 相容的工具和依賴版本；不要執行下方舊安裝命令。

```bash
# Install kubebuilder
VERSION=1.0.1
wget https://github.com/kubernetes-sigs/kubebuilder/releases/download/v${VERSION}/kubebuilder_${VERSION}_linux_amd64.tar.gz
tar zxvf kubebuilder_${VERSION}_linux_amd64.tar.gz
sudo mv kubebuilder_${VERSION}_linux_amd64 /usr/local/kubebuilder
export PATH=$PATH:/usr/local/kubebuilder/bin

# Install dep kustomize
go get -u github.com/golang/dep/cmd/dep
go get github.com/kubernetes-sigs/kustomize
```

### 使用方法

#### 初始化專案

```bash
mkdir -p $GOPATH/src/demo
cd $GOPATH/src/demo
kubebuilder init --domain k8s.io --license apache2 --owner "The Kubernetes Authors"
```

#### 建立 API

```bash
kubebuilder create api --group ships --version v1beta1 --kind Sloop
```

然後按照實際需要修改 `pkg/apis/ship/v1beta1/sloop_types.go` 和 `pkg/controller/sloop/sloop_controller.go` 增加業務邏輯。

#### 本地執行測試

```bash
make install
make run
```

> 如果碰到錯誤 `ValidationError(CustomResourceDefinition.status): missing required field "storedVersions" in io.k8s.apiextensions-apiserver.pkg.apis.apiextensions.v1beta1.CustomResourceDefinitionStatus]`，可以手動修改 `config/crds/ships_v1beta1_sloop.yaml`:
>
> \`\`\`yaml status: acceptedNames: kind: "" plural: "" conditions: \[\] storedVersions: \[\]
>
> 然後執行 `kubectl apply -f config/crds` 建立 CRD。

然後就可以用 `ships.k8s.io/v1beta1` 來建立 Kind 為 `Sloop` 的資源了，比如

```bash
kubectl apply -f config/samples/ships_v1beta1_sloop.yaml
```

#### 構建映像檔並部署控制器

```bash
# 替换 IMG 为你自己的
export IMG=feisky/demo-crd:v1
make docker-build
make docker-push
make deploy
```

> kustomize 已經不再支援萬用字元，因而上述 `make deploy` 可能會碰到 `Load from path ../rbac/*.yaml failed` 錯誤，解決方法是手動修改 `config/default/kustomization.yaml`:
>
> resources:
>
> * ../rbac/rbac\_role.yaml
> * ../rbac/rbac\_role\_binding.yaml
> * ../manager/manager.yaml
>
> 然後執行 `kustomize build config/default | kubectl apply -f -` 部署，預設部署到 `demo-system` namespace 中。

#### 文件和測試

```bash
# run unit tests
make test

# generate docs
kubebuilder docs
```
