> HISTORICAL: The kubenet bandwidth annotations and `cbr0` traffic-control procedure are tied to legacy networking setups and are not general v1.37 guidance. Do not apply them without verifying support in the exact network plugin and node configuration. Preserved from `concepts/objects/pod.md`.

## 限制网络带宽

可以通过给 Pod 增加 `kubernetes.io/ingress-bandwidth` 和 `kubernetes.io/egress-bandwidth` 这两个 annotation 来限制 Pod 的网络带宽


```yaml
apiVersion: v1
kind: Pod
metadata:
  name: qos
  annotations:
    kubernetes.io/ingress-bandwidth: 3M
    kubernetes.io/egress-bandwidth: 4M
spec:
  containers:
  - name: iperf3
    image: networkstatic/iperf3
    command:
    - iperf3
    - -s
```

> **仅 kubenet 支持限制带宽**
>
> 目前只有 kubenet 网络插件支持限制网络带宽，其他 CNI 网络插件暂不支持这个功能。


kubenet 的网络带宽限制其实是通过 tc 来实现的

```bash
# setup qdisc (only once)
tc qdisc add dev cbr0 root handle 1: htb default 30
# download rate
tc class add dev cbr0 parent 1: classid 1:2 htb rate 3Mbit
tc filter add dev cbr0 protocol ip parent 1:0 prio 1 u32 match ip dst 10.1.0.3/32 flowid 1:2
# upload rate
tc class add dev cbr0 parent 1: classid 1:3 htb rate 4Mbit
tc filter add dev cbr0 protocol ip parent 1:0 prio 1 u32 match ip src 10.1.0.3/32 flowid 1:3
```
