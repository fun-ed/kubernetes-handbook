# Historical ServiceAccount token Secret output

This output was moved from `concepts/objects/secret.md`. It describes pre-v1.24 automatically generated long-lived token Secrets and an old kubelet host path layout. Kubernetes no longer auto-creates a token Secret for every ServiceAccount. Do not create or mount a long-lived token Secret for routine workloads. Use the projected, rotating ServiceAccount token described in the [current ServiceAccount documentation](https://kubernetes.io/docs/concepts/security/service-accounts/).

```text
NAME                  TYPE                                  DATA      AGE
default-token-cty7p   kubernetes.io/service-account-token   3         45d
```

Old mount output:

```text
ca.crt    namespace  token
```

The original page also showed host paths under `/var/lib/kubelet/pods/.../volumes/kubernetes.io~secret/` and a bearer-token file. Those paths are node implementation details and must not be used to retrieve credentials.
