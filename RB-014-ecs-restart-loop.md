---
id: RB-014
title: ECS task restart loop, dependency timeout
component: ecs
severity_typical: SEV2
signals: [latency, restart, healthcheck-fail]
---

## Symptom

ECS service shows repeated task stops/starts. CloudWatch shows p99 latency spike
preceding each restart. Health checks fail just before each task is killed.

## Likely root cause

Health check timeout is shorter than the time it takes the task to respond once a
downstream dependency (commonly the RDS connection pool, or a third-party API) is
saturated or slow. The orchestrator interprets the slow response as unhealthy and kills
the task, which does not fix the underlying saturation. It just removes capacity and
makes the remaining tasks' load worse.

## Recommended action

1. Check downstream dependency health BEFORE scaling out. Scaling will not fix a
   saturated connection pool or a slow third-party dependency, it will make it worse.
2. Inspect RDS `DatabaseConnections` and `CPUUtilization` for the same time window.
3. If connection pool exhaustion is confirmed, raise `max_connections` cautiously or
   introduce a connection pooler (RDS Proxy) rather than scaling ECS tasks.
4. If a third-party dependency is slow, apply a circuit breaker / timeout budget at the
   application layer rather than relying on the orchestrator's health check as a circuit
   breaker.

## Anti-pattern to avoid

Do not roll back a recent deploy as a first response unless the timing correlates
exactly with the deploy. Precedent: INC-0042, a rollback alone did not resolve this
pattern because the root cause was a downstream dependency, not the application code.
