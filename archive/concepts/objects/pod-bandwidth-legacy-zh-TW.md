> HISTORICAL: 這些 kubenet 頻寬註解與 `cbr0` traffic-control 操作綁定舊網路設定，不是通用的 Kubernetes v1.37 指引。使用前請先確認特定網路外掛及節點設定仍支援。內容取自 `zh-TW/concepts/objects/pod.md`。

## 限制網路頻寬

可以透過在 Pod 加入 `kubernetes.io/ingress-bandwidth` 和 `kubernetes.io/egress-bandwidth` 這兩個 annotation 來限制 Pod 的網路頻寬。

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

> **僅 kubenet 支援限制頻寬**
>
> 目前只有 kubenet 網路外掛支援限制網路頻寬，其他 CNI 網路外掛暫不支援這項功能。

kubenet 的網路頻寬限制其實是透過 `tc` 實作：

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
