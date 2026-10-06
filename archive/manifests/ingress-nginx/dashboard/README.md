# Ingress NGINX dashboard example (historical)

This configuration exposes the old Kubernetes Dashboard through the retired Ingress NGINX setup. It is historical and must not be applied; the basic-auth example is not a substitute for a supported authentication boundary.

For the current Traefik example, the administrative API/dashboard is disabled by default. If needed, enable it only with an appropriate private access design and use `kubectl port-forward` rather than exposing it through a public Ingress. See the [manifests overview](../../../../manifests/README.md).
