# 使用者管理

根據[Kubernetes 認證](../../extension/auth/authentication.md)文件，Kubernetes 本身並不直接提供使用者管理的特性，不支援 User 物件，更不會儲存 User 物件。但是它支援一系列的外掛，比如 X509 證書、OpenID、Webhook等，使用者可以基於這些外掛跟外部的使用者管理系統進行對接，再配合 RBAC 實現權限管理的機制。

實際上，你也可以使用 Certificate Signing Request \(CSR\) 或者 ServiceAccount 來建立和管理受限的使用者。

## Certificate Signing Request \(CSR\)

Kubernetes 提供了 `certificates.k8s.io` API，可讓您設定由您控制的證書頒發機構（CA）簽名的TLS證書，工作負載可以使用這些CA和證書來建立信任。

> Kubernetes controller manager 提供了一個簽名者的預設實現。 要啟用它，請將`--cluster-signing-cert-file` 和 `--cluster-signing-key-file` 引數傳遞給 controller manager，並設定具有證書頒發機構的金鑰對的路徑。

假設已經為 kubectl 設定好了管理員 kubeconfig，以下是透過 openssl 和 CSR 建立一個新使用者設定的步驟。

```bash
NAMESPACE=${NAMESPACE:-"default"}
USER_NAME=${USER_NAME:-"user1"}
GROUP_NAME=${GROUP_NAME:-"group1"}
SERVER_URL=$(kubectl cluster-info | awk '/Kubernetes master/{print $NF}' | sed $'s,\x1b\\[[0-9;]*[a-zA-Z],,g')

# create client key and cert
openssl genrsa -out $USER_NAME.key 2048
openssl req -new -key $USER_NAME.key -out $USER_NAME.csr -subj "/CN=$USER_NAME/O=$GROUP_NAME"

# Sign the client certificates
CERTIFICATE_NAME=$USER_NAME-$NAMESPACE
cat <<EOF | kubectl create -f -
apiVersion: certificates.k8s.io/v1beta1
kind: CertificateSigningRequest
metadata:
  name: $CERTIFICATE_NAME
spec:
  groups:
  - system:authenticated
  request: $(cat $USER_NAME.csr | base64 | tr -d '\n')
  usages:
  - digital signature
  - key encipherment
  - client auth
EOF
kubectl certificate approve $CERTIFICATE_NAME
kubectl get csr $CERTIFICATE_NAME -o jsonpath='{.status.certificate}'  | base64 --decode > $USER_NAME.crt

# setup RBAC Roles
cat <<EOF | kubectl create -f -
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  namespace: $NAMESPACE
  name: $USER_NAME-role
rules:
  - apiGroups:
    - ''
    - extensions
    - apps
    - batch
    resources:
    - '*'
    verbs:
    - '*'
EOF

# bind role to the user
kubectl create rolebinding $USER_NAME-rolebinding --user=$USER_NAME --namespace=$NAMESPACE --role=$USER_NAME-role

# setup kubectl
kubectl config set-cluster $USER_NAME --server="$SERVER_URL" --insecure-skip-tls-verify
kubectl config set-credentials $USER_NAME --client-certificate=$USER_NAME.crt --client-key=$USER_NAME.key
kubectl config set-context $USER_NAME --cluster=$USER_NAME --user=$USER_NAME --namespace=$NAMESPACE
kubectl config use-context $USER_NAME
```

## ServiceAccount

ServiceAccount 是 Kubernetes 自動生成的，並會自動掛載到容器的 `/var/run/secrets/kubernetes.io/serviceaccount` 目錄中。

在認證時，ServiceAccount 的使用者名稱格式為 `system:serviceaccount:(NAMESPACE):(SERVICEACCOUNT)`，並從屬於兩個 group：`system:serviceaccounts` 和 `system:serviceaccounts:(NAMESPACE)`。

### Pod 內部存取 API

在 Pod 內部，你可以透過下面的方式來存取 API：

```bash
$ TOKEN=$(cat /run/secrets/kubernetes.io/serviceaccount/token)
$ CACERT=/run/secrets/kubernetes.io/serviceaccount/ca.crt
$ curl --cacert $CACERT --header "Authorization: Bearer $TOKEN"  https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT/api
{
  "kind": "APIVersions",
  "versions": [
    "v1"
  ],
  "serverAddressByClientCIDRs": [
    {
      "clientCIDR": "0.0.0.0/0",
      "serverAddress": "10.0.1.149:443"
    }
  ]
}
```

### kubectl 存取 API

假設已經為 kubectl 設定好了管理員 kubeconfig，以下是透過 ServiceAccount 建立一個新使用者設定的步驟。

```bash
NAMESPACE=${NAMESPACE:-"default"}
SERVICE_ACCOUNT_NAME=${SERVICE_ACCOUNT_NAME:-"demo"}
SERVER_URL=$(kubectl cluster-info | awk '/Kubernetes master/{print $NF}' | sed $'s,\x1b\\[[0-9;]*[a-zA-Z],,g')

# create sa
kubectl -n $NAMESPACE create sa $SERVICE_ACCOUNT_NAME

# get secret and token
secret=$(kubectl -n $NAMESPACE get sa $SERVICE_ACCOUNT_NAME -o jsonpath='{.secrets[0].name}')
token=$(kubectl -n $NAMESPACE get secret $secret -o jsonpath='{.data.token}' | base64 -d)
kubectl -n $NAMESPACE get secret $secret -o jsonpath='{.data.ca\.crt}' | base64 --decode > ca.crt

# setup RBAC Roles
cat <<EOF | kubectl create -f -
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  namespace: $NAMESPACE
  name: $SERVICE_ACCOUNT_NAME-role
rules:
  - apiGroups:
    - ''
    - extensions
    - apps
    - batch
    resources:
    - '*'
    verbs:
    - '*'
EOF

# bind sa to the role
kubectl create rolebinding $SERVICE_ACCOUNT_NAME-rolebinding --serviceaccount=$NAMESPACE:$SERVICE_ACCOUNT_NAME --namespace=$NAMESPACE --role=$SERVICE_ACCOUNT_NAME-role

# setup kubectl
kubectl config set-cluster $SERVICE_ACCOUNT_NAME --embed-certs=true --server=${SERVER_URL} --certificate-authority=./ca.crt
kubectl config set-credentials $SERVICE_ACCOUNT_NAME --token=$token
kubectl config set-context $SERVICE_ACCOUNT_NAME --cluster=$SERVICE_ACCOUNT_NAME --user=$SERVICE_ACCOUNT_NAME --namespace=$NAMESPACE
kubectl config use-context $SERVICE_ACCOUNT_NAME
```
