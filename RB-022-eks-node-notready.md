---
id: RB-022
title: EKS node NotReady, kubelet disk pressure
component: eks
severity_typical: SEV3
signals: [node-not-ready, disk-pressure, pod-eviction]
---

## Symptom

`kubectl get nodes` shows one or more nodes in `NotReady` state. Pod evictions are
visible in `kubectl get events`. Node conditions show `DiskPressure: True`.

## Likely root cause

Container image layers, logs, or ephemeral storage have filled the node's root volume.
Common causes: a misconfigured log shipper not rotating logs, a runaway job writing to
local disk, or too many unused images accumulating without garbage collection.

## Recommended action

1. `kubectl describe node <node>` to confirm `DiskPressure` and check `kubelet`
   image/container GC thresholds.
2. SSM into the node (or use SSM Session Manager) and check `df -h` / `du -sh
   /var/lib/docker` or `/var/lib/containerd`.
3. If a single misbehaving pod is the cause, cordon and drain the node, then
   investigate the offending workload's log/disk usage before letting it reschedule.
4. Consider lowering `kubelet` image GC thresholds or increasing node root volume size
   if this recurs across the fleet rather than on one node.

## Anti-pattern to avoid

Do not simply terminate and replace the node without checking whether the disk-pressure
cause is workload-specific. If it's a fleet-wide misconfiguration, the replacement node
will hit the same condition again within hours.
