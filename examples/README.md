# Kubernetes Examples

These manifests target Kubernetes v1.37.1. They are teaching examples, not a
single installable stack: do not apply the entire directory. Check each
example's comments and prerequisites, then select individual files for a
disposable cluster.

Core Kubernetes component pins and source evidence are tracked in
[`../setup/component-versions.md`](../setup/component-versions.md).

## Validate before applying

For a built-in resource, use a v1.37.1 test cluster and server-side dry-run:

```sh
kubectl --context "$KUBE_CONTEXT" apply --dry-run=server -f examples/deployment.yaml
```

This validates against that cluster's API without persisting the object. It
still requires access to the API and can invoke admission webhooks. Offline
schema validation is also possible with
`kubeconform -strict -kubernetes-version 1.37.1 <manifest>`. Custom resources
need their CRD schemas (or installed CRDs for server-side validation), and
feature-gated examples need the relevant feature enabled. Neither check proves
that a workload's external images, credentials, storage, or services exist.

## Examples with additional requirements

- `hpa.yaml` and `hpa-memory.yaml` target the `nginx` Deployment in
  `deployment.yaml` and require a functioning metrics API, commonly
  metrics-server. The Deployment includes CPU and memory requests.
- `network-policy/` needs a CNI that enforces NetworkPolicy; its access and
  no-access Pods are one-shot connectivity checks.
- `service.yaml` selects Pods labeled `app: nginx`; its second port also
  requires an application listening on container port 8080.
- `indexed-job-with-backoff.yaml` and `job-success-policy-v1.33.yaml` use Job
  features that are stable and enabled by default in v1.37.1.
- `lifecycle-v1.33.yaml` mixes stable lifecycle sleep examples with
  `stopSignal`, which is still alpha in v1.37 and requires the
  `ContainerStopSignals` feature gate. Skip those resources unless the gate is
  enabled on the cluster components that handle Pods.
- `user-namespace.yaml` uses stable Pod user namespaces (`hostUsers: false`,
  stable since v1.36); it requires a Linux cluster that supports user
  namespaces. Its ConfigMap, Secret, PVC, and custom-image examples have
  placeholders or external prerequisites. The PostgreSQL 18 sample stores data
  under `/var/lib/postgresql`.
- `seccomp.yaml` requires the supplied `prevent-chmod` profile at
  `/var/lib/kubelet/seccomp/prevent-chmod` on every eligible node.
- `calico/calico-packet-logs.yaml` is a Calico-specific custom resource and
  DaemonSet: use Calico 3.33.0 with its CRDs and logging configured. Its
  opt-in policy selects only endpoints carrying the `packet-log-demo` label.
  Add that label deliberately before applying it; matching TCP/UDP ingress
  and egress traffic is logged and allowed.
- `service-without-selector.yaml` demonstrates a manually managed EndpointSlice.
  Replace its documentation-only `192.0.2.10` address with one reachable by
  clients.
- The former generic RDP LoadBalancer example was archived because port 3389
  could become publicly reachable; use only provider-specific private access
  controls. The [historical manifest](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/examples/rdp.yaml)
  is not a current deployment recipe.
- `pod-secret.yaml` and `image-scret.yaml` require a real private registry and
  credentials. Replace the example registry values and keep real credentials
  out of manifests and source control.
- `multi-container-patterns.yaml` is a five-pattern teaching template. Custom
  app/proxy images and referenced ConfigMaps, Secrets, and services are
  placeholders; its NGINX, Fluent Bit, Alpine, and BusyBox tags are real images.
  Replace the documentation-only Git repository URL before using sidecar-init.
  The former metrics-adapter block was removed because its image tag was
  unavailable and the Kubernetes SIGS adapter does not convert JSON files to
  Prometheus metrics; see the [archived source version](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/examples/multi-container-patterns.yaml).
- The old Windows projected-volume manifest was archived because its custom
  `atuvenie/mounttest:1.0` image was last pushed in 2018 and its Windows base
  version is not a verified match for current Windows nodes. See the official
  [projected-volume concept](https://kubernetes.io/docs/concepts/storage/projected-volumes)
  and [Windows container/node compatibility guidance](https://kubernetes.io/docs/concepts/windows/intro/).
- `ssh.yaml` is a host-networked debug shell, not an SSH server. Replace its
  node name and use `kubectl exec -it node-debug-shell -- /bin/sh` on a trusted
  cluster.
- `host-volume.yaml` requires `/data` to exist on the selected node.
  `netns-volume.yaml` uses host networking, host namespaces, and a privileged
  container; only use it on a disposable, trusted node.
- `admin-service-account.yaml` grants effective cluster-admin privileges.
  Avoid creating this account in shared or production clusters.
- `evaluate-pod-creation.sh` creates and deletes a Pod and Service. Inspect it
  and use only in an isolated test cluster.

## Historical examples

Examples marked `HISTORICAL:` have been moved out of the current validation roots. They include the Kubernetes v1.13 kube-bench jobs and provider-specific NodeLocal DNS configurations. See the [archive index](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/index.md) for original paths, files, and reasons; do not apply them as Kubernetes v1.36/v1.37 defaults.

## Image pins

The NGINX stable pin is `1.30.5`, released 2026-09-15 with the security fix
recorded as CVE-2026-90439 in the official
[1.30 changelog](https://nginx.org/en/CHANGES-1.30). The public image tags
below were checked on 2026-10-05. NGINX 1.31.6 is a newer mainline tag, not a
replacement for the stable 1.30 line; BusyBox 1.38.0 is explicitly marked
unstable upstream, so the newest stable BusyBox pin remains 1.37.0. Tags are
more reproducible than `latest`, but are not digest locks; pin image digests as
well when a deployment requires immutable artifacts.

| Image family | Tag used | Upstream source |
| --- | --- | --- |
| NGINX | `1.30.5` | [Official NGINX image](https://hub.docker.com/_/nginx); [1.30 stable changelog](https://nginx.org/en/CHANGES-1.30) |
| Unprivileged NGINX | `1.30.5-alpine3.24` | [NGINX unprivileged image](https://hub.docker.com/r/nginxinc/nginx-unprivileged); [1.30 stable changelog](https://nginx.org/en/CHANGES-1.30) |
| Alpine | `3.24.2` | [Official Alpine image](https://hub.docker.com/_/alpine); [3.24.2 stable release (2026-09-17)](https://www.alpinelinux.org/posts/Alpine-3.21.8-3.22.6-3.23.6-3.24.2-released.html) |
| BusyBox | `1.37.0` | [BusyBox stable release history](https://busybox.net/news.html) (1.38.0 is marked unstable) |
| Python | `3.14.8-slim-trixie` | [Official Python image](https://hub.docker.com/_/python); [3.14.8 release (2026-09-30)](https://www.python.org/downloads/release/python-3148/) |
| Redis | `8.10.2` | [Official Redis image](https://hub.docker.com/_/redis) |
| PostgreSQL | `18.6-alpine3.24` | [Official PostgreSQL image](https://hub.docker.com/_/postgres) |
| TensorFlow | `2.21.0` | [TensorFlow Docker images](https://hub.docker.com/r/tensorflow/tensorflow) |
| Fluent Bit | `5.1.3` | [Container image docs](https://docs.fluentbit.io/manual/installation/downloads/docker); [5.1.3 upstream release (2026-10-01)](https://github.com/fluent/fluent-bit/releases/tag/v5.1.3) |
| NodeLocal DNS cache | `1.26.8` (archived provider-specific manifests) | Registry tag resolves; OCI index lists linux/amd64, arm64, arm/v7, ppc64le, and s390x. [Manifest index](https://registry.k8s.io/v2/dns/k8s-dns-node-cache/manifests/1.26.8) |
| Ubuntu | `26.04` | [Official Ubuntu image](https://hub.docker.com/_/ubuntu) |
| Kubernetes echoserver | `registry.k8s.io/echoserver:1.10` | Registry manifest resolves for linux/amd64; this checks tag availability, not maintenance or workload support. [Manifest](https://registry.k8s.io/v2/echoserver/manifests/1.10) · [Source](https://github.com/kubernetes/kubernetes/tree/master/test/images/echoserver) |