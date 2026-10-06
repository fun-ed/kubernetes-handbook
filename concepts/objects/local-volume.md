# Local Persistent Volumes

Local persistent volumes expose storage that is attached to a particular node, such as a locally attached disk or partition. The `local` PersistentVolume type is stable; it is not a Kubernetes alpha or beta feature. A local PV must include node affinity so the scheduler places a Pod on the node that has the storage.

Kubernetes does not dynamically provision local PVs. An administrator or a separate provisioner must prepare the storage and create PV objects. The example below uses static provisioning: create a StorageClass, create a PV for a pre-existing path on a node, then create a PVC and Pod. Replace the example node name and path with the actual node and prepared storage. The capacity in the PV is declared for scheduling and is not a filesystem quota; ensure it accurately reflects the storage you make available.

## StorageClass

`WaitForFirstConsumer` delays binding until a Pod using the claim is scheduled, allowing the scheduler to consider the PV's node affinity.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
```

## PersistentVolume

Prepare `/mnt/disks/ssd1` on `example-node` before creating this PV. The `Retain` reclaim policy leaves the underlying data for an administrator to inspect and reclaim after the claim is released; it does not automatically clean or securely erase the storage.

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: example-local-pv
spec:
  capacity:
    storage: 100Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-storage
  local:
    path: /mnt/disks/ssd1
  nodeAffinity:
    required:
      nodeSelectorTerms:
        - matchExpressions:
            - key: kubernetes.io/hostname
              operator: In
              values:
                - example-node
```

## PersistentVolumeClaim

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: example-local-claim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: local-storage
```

## Pod using the claim

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: local-volume-demo
spec:
  containers:
    - name: web
      image: nginx:1.30.5
      volumeMounts:
        - name: web-content
          mountPath: /usr/share/nginx/html
  volumes:
    - name: web-content
      persistentVolumeClaim:
        claimName: example-local-claim
```

The PV's node affinity constrains placement; do not delete or replace that node, move its storage, or reuse its hostname while the PV is in use. Plan backups and a recovery procedure for node or disk failure: local storage is not replicated by Kubernetes. Before reclaiming a `Retain` PV, verify that the claim and its data are no longer needed.

The upstream [Local Persistent Volumes guide](https://kubernetes.io/docs/concepts/storage/volumes/#local) documents the volume type and scheduling behavior. For automated discovery and management, see the community [sig-storage-local-static-provisioner](https://github.com/kubernetes-sigs/sig-storage-local-static-provisioner); verify its maintenance status and compatibility for your own environment before adopting it. This guide does not assert support for any particular cluster distribution or provisioner version.

The previous v1.7–1.10 tutorial is preserved in the [historical archive](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/concepts/objects/local-volume-legacy.md).
