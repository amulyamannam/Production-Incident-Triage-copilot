---
id: RB-007
title: RDS Multi-AZ failover, elevated write latency
component: rds
severity_typical: SEV2
signals: [latency, failover, replica-lag]
---

## Symptom

Application logs show a burst of connection errors lasting 60-120 seconds, followed by
recovery. CloudWatch shows an RDS `Multi-AZ failover` event in the same window.

## Likely root cause

This is expected Multi-AZ failover behavior (patching, underlying hardware failure, or a
manual failover). The brief connection error burst is the application reconnecting to
the new primary endpoint. It is not itself a bug; the question is whether the
application's retry/backoff logic handled it gracefully.

## Recommended action

1. Confirm the failover event in the RDS console/CloudTrail to rule out an unplanned
   outage versus routine maintenance.
2. Check whether the application's database client uses the cluster endpoint (which
   re-resolves automatically) rather than a cached IP.
3. If the error burst lasted significantly longer than ~120 seconds, investigate
   connection pool reconnect storms; many app instances reconnecting simultaneously can
   itself create a secondary incident.
4. No data loss is expected in a Multi-AZ synchronous failover; if any write
   acknowledgment errors were logged, escalate for data-integrity review.

## Anti-pattern to avoid

Do not treat every failover as an incident requiring a postmortem. Distinguish planned
maintenance failovers (visible in the RDS maintenance window) from unplanned ones before
paging anyone further.
