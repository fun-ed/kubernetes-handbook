# Historical Kubebuilder v1 workflow

This material was moved from `concepts/objects/customresourcedefinition.md`. It documents Kubebuilder 1.0.1, the retired `dep` tool, removed CRD status workarounds, and old project layouts. Do not use these commands for current projects. The source was part of this handbook; consult the current [Kubebuilder book](https://book.kubebuilder.io/) and the versioned [Kubebuilder project](https://github.com/kubernetes-sigs/kubebuilder) for supported workflows.

```bash
VERSION=1.0.1
wget https://github.com/kubernetes-sigs/kubebuilder/releases/download/v${VERSION}/kubebuilder_${VERSION}_linux_amd64.tar.gz
go get -u github.com/golang/dep/cmd/dep
go get github.com/kubernetes-sigs/kustomize
mkdir -p $GOPATH/src/demo
kubebuilder init --domain k8s.io --license apache2 --owner "The Kubernetes Authors"
kubebuilder create api --group ships --version v1beta1 --kind Sloop
make install
make run
kubectl apply -f config/samples/ships_v1beta1_sloop.yaml
export IMG=feisky/demo-crd:v1
make docker-build
make docker-push
make deploy
```

The original page also suggested manually editing CRD `.status.storedVersions` to work around API validation and manually rewriting Kustomize resource globs. Those workarounds are obsolete and must not be applied.
