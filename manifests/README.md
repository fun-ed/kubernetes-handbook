# Manifest status and Kubernetes compatibility

This directory contains both current examples and archived snapshots. Do **not** recursively apply `manifests/` or a directory that contains historical resources. Apply only the individual examples you have reviewed and configured for your cluster.

The target baseline is Kubernetes v1.37.1. A current API schema or image tag does not by itself prove that a controller or addon supports Kubernetes 1.37. Check the linked upstream compatibility guidance before production use. The pinned project releases and source evidence are collected in [`setup/component-versions.md`](../setup/component-versions.md).

## Current or modernized examples

| Path | Contents and prerequisites | Compatibility notes |
| --- | --- | --- |
| `kubedns/coredns.yaml` | CoreDNS v1.14.6 based on the Kubernetes v1.37.1 kubeadm addon source. | Uses `clusterIP: 10.96.0.10`, the kubeadm default; adjust for a different Service CIDR. [Upstream source](https://github.com/kubernetes/kubernetes/blob/v1.37.1/cluster/addons/dns/coredns/coredns.yaml.base). |
| `metrics-server/` | Metrics Server v0.9.0 release components; apply the six manifests together. | Upstream documents Kubernetes v1.34+ compatibility, including v1.37. Exposes `metrics.k8s.io/v1beta1`; this is for resource metrics and `kubectl top`, not a full monitoring stack. [Release manifest](https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.9.0/components.yaml). |
| `node-problem-detector/npd.yaml` | Node Problem Detector v1.36.0 source/config; intentionally overrides the release deployment YAML's stale v0.8.19 pin with the published v1.36.0 image. | The v1.36.0 source supports the configured `--config.system-log-monitor` option and JSON monitor paths; the binding uses Kubernetes' built-in `system:node-problem-detector` role. The registry OCI index publishes linux/amd64 and linux/arm64. Kubernetes v1.37 compatibility remains unverified. [CLI source](https://github.com/kubernetes/node-problem-detector/blob/v1.36.0/cmd/options/options.go), [registry index](https://registry.k8s.io/v2/node-problem-detector/node-problem-detector/manifests/v1.36.0), [Kubernetes role source](https://github.com/kubernetes/kubernetes/blob/v1.37.1/plugin/pkg/auth/authorizer/rbac/bootstrappolicy/policy.go). |
| `traefik-ingress/traefik-deployment.yaml`, `traefik-ingress/traefik-rbac.yaml` | Traefik v3.7.13 using the Kubernetes Gateway provider. Dashboard/API is not exposed by these manifests. | The v3.7.13 tagged docs specify Gateway API v1.6.1. A basic HTTP/HTTPS smoke test with v1.6.2 CRDs on kind Kubernetes v1.37.1 passed; this does not extend upstream support or certify other features. See the [validation record](../setup/kubernetes-v1.37.md). The Service uses `LoadBalancer`, which requires a working external/cloud load-balancer implementation. [Provider docs](https://raw.githubusercontent.com/traefik/traefik/v3.7.13/docs/content/reference/install-configuration/providers/kubernetes/kubernetes-gateway.md). |
| `gateway-api/` | Standard examples use Gateway API v1.6.2: `GatewayClass`, `Gateway`, `HTTPRoute`, and `ListenerSet` are `gateway.networking.k8s.io/v1`. See the [directory README](gateway-api/README.md) for install order and per-file prerequisites. | CRDs are APIs, not a controller. Kubernetes v1.37/controller compatibility and controller support for individual features must be verified separately. `retry-budget.yaml` uses experimental `gateway.networking.x-k8s.io/v1alpha1 XBackendTrafficPolicy`; install the experimental CRDs and a controller that implements it. `cors-policy.yaml` is historical and must not be applied. |
| `ingress-nginx/cert-manager/cluster-issuer.yaml` | Current `cert-manager.io/v1` `ClusterIssuer`, using the beta Gateway API HTTP-01 solver. Replace `user@example.com` before use. | Requires Gateway API CRDs and a compatible Gateway/controller before cert-manager starts, with cert-manager configured using `config.gatewayAPI.enabled=true`. The example targets `default/example-gateway`; Certificates in other namespaces require the Gateway listener to allow those route namespaces. cert-manager v1.21.2 documents support through Kubernetes v1.36; v1.37 support is unverified. [Release bundle](https://github.com/cert-manager/cert-manager/releases/download/v1.21.2/cert-manager.yaml), [Gateway solver requirements](https://cert-manager.io/docs/configuration/acme/http01/). |
| `test/my-nginx.yaml`, `test/nginx-pod.yaml` | Current Deployment/Pod examples using the official `nginx:1.30.5-alpine3.24` stable image tag. | Simple workload examples; adjust resource settings and image policy for your environment. [Official image tags](https://hub.docker.com/_/nginx). |
| `test/rolling-update-test/rolling-update-test.yaml` | Current Deployment schema and selector/labels. | The image is a private-registry placeholder. Build and publish it and configure image access before applying; it is not a directly runnable public-image example. |

## Historical resources: do not apply

The YAML files listed below have a `HISTORICAL` marker near the start of each file. JSON files cannot carry YAML comments; their status is recorded here. These files remain only as historical/reference material and are excluded from current examples.

| Path | Why historical | Current direction |
| --- | --- | --- |
| `addon-manager/` | Legacy addon-manager controller. | Use Kubernetes distribution/component-specific lifecycle management. |
| `dashboard/kubernetes-dashboard.yaml` | Retired legacy Dashboard installation. | Use a maintained dashboard project only after reviewing its security model; avoid public unauthenticated exposure. |
| `fluentd-elasticsearch/` | Old Elasticsearch/Kibana/Fluentd deployment and obsolete API/runtime assumptions. | Select a maintained logging backend and verify its Kubernetes, storage, and security requirements; no v1.37 replacement is pinned here. |
| `glusterfs/` (including JSON files) | Legacy GlusterFS/in-tree storage examples. | Use a maintained CSI storage driver appropriate to the backend and Kubernetes version. |
| `heapster/` | Retired Heapster and bundled Grafana/InfluxDB resources. | Metrics Server provides resource metrics; choose a separate maintained monitoring stack for time-series monitoring. |
| `ingress-nginx/` except `cert-manager/cluster-issuer.yaml` | Legacy Ingress NGINX, kube-lego, and dashboard examples; several contain removed Ingress APIs. | See the Gateway API/Traefik example above, while checking the documented controller compatibility caveats. |
| `kubedns/kube-dns.yaml` | Superseded kube-dns addon manifest. | Use the current `kubedns/coredns.yaml` example or your distribution's DNS addon. |
| `prometheus/` | Old CoreOS chart commands and NGINX Ingress/auth resources. | Install a maintained Prometheus or Prometheus Operator release and verify its compatibility directly; no v1.37 monitoring chart is pinned here. |
| `systemd/` | Historical host-managed control-plane and Docker/dockershim service units. | Use the current distribution's supported node lifecycle and CRI setup; kubeadm commonly manages control-plane static Pods. |
| `test/filebeat-test.yaml`, `test/logstash-test.yaml` | Legacy logging test workloads. | Use the maintained logging backend's current integration examples. |
| `traefik-ingress/ui.yaml` | Exposes a legacy administrative UI through obsolete Ingress configuration. | The current Traefik example keeps the dashboard/API disabled; if enabled, keep it private and access it through a controlled method such as port-forwarding. |
| `gateway-api/v1.3-features/cors-policy.yaml` | `CORSPolicy` is not served by Gateway API v1.6.2 Standard or Experimental CRDs. | Use only a controller-specific CORS feature documented by the selected implementation. |

The directory names are retained for historical continuity; in particular, `gateway-api/v1.3-features/` contains both current examples and the explicitly historical CORS sample. Read its README and select files individually.

## Upstream source references

- [Kubernetes v1.37.1 CoreDNS addon source](https://github.com/kubernetes/kubernetes/blob/v1.37.1/cluster/addons/dns/coredns/coredns.yaml.base)
- [Metrics Server v0.9.0 release](https://github.com/kubernetes-sigs/metrics-server/releases/tag/v0.9.0)
- [Node Problem Detector v1.36.0 deployment](https://raw.githubusercontent.com/kubernetes/node-problem-detector/v1.36.0/deployment/node-problem-detector.yaml), [config](https://raw.githubusercontent.com/kubernetes/node-problem-detector/v1.36.0/deployment/node-problem-detector-config.yaml), [RBAC](https://raw.githubusercontent.com/kubernetes/node-problem-detector/v1.36.0/deployment/rbac.yaml), [CLI options](https://github.com/kubernetes/node-problem-detector/blob/v1.36.0/cmd/options/options.go), and [registry OCI index](https://registry.k8s.io/v2/node-problem-detector/node-problem-detector/manifests/v1.36.0)
- [Gateway API v1.6.2 release](https://github.com/kubernetes-sigs/gateway-api/releases/tag/v1.6.2)
- [cert-manager v1.21.2 release](https://github.com/cert-manager/cert-manager/releases/tag/v1.21.2)
- [Traefik v3.7.13 Gateway provider documentation](https://raw.githubusercontent.com/traefik/traefik/v3.7.13/docs/content/reference/install-configuration/providers/kubernetes/kubernetes-gateway.md)
