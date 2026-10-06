# Ingress NGINX (historical)

> **Historical configuration:** the controller and manifests under `ingress-nginx/` are legacy examples, not a supported deployment path. Do not run the install commands from older revisions or recursively apply this directory.

Most resources under `ingress-nginx/` use retired controller conventions or obsolete Ingress APIs. The exception is `cert-manager/cluster-issuer.yaml`, a current `cert-manager.io/v1` resource; its setup and compatibility caveats are below. See the [manifests overview](../../../manifests/README.md) and [Gateway API instructions](../../../manifests/gateway-api/README.md).

## Active exception: cert-manager ClusterIssuer

This current resource uses the beta Gateway API HTTP-01 solver. Install the Gateway API Standard CRDs and a compatible controller first, then install cert-manager v1.21.2 with Gateway API support enabled:

```sh
helm upgrade --install cert-manager oci://quay.io/jetstack/charts/cert-manager \
  --version v1.21.2 \
  --namespace cert-manager --create-namespace \
  --set crds.enabled=true \
  --set config.gatewayAPI.enabled=true
```

Apply `cert-manager/cluster-issuer.yaml` only after the Gateway controller and cert-manager are ready. Replace its placeholder email. The configured Gateway is `default/example-gateway`; its HTTP listener must allow routes from the Certificate's namespace. cert-manager v1.21.2's documented Kubernetes support ends at v1.36, so Kubernetes v1.37 remains unverified.

The maintained example in this repository is Gateway API with Traefik under [`manifests/traefik-ingress/`](../../../manifests/traefik-ingress). It does not imply that every Gateway API feature or controller is compatible with Kubernetes 1.37.
