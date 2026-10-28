---
id: RB-031
title: Imminent TLS certificate expiry on public ALB listener
component: networking
severity_typical: SEV3
signals: [cert-expiry, tls, alb]
---

## Symptom

ACM or external monitoring shows a certificate attached to a public-facing ALB listener
expiring within 14 days. No customer-facing errors yet.

## Likely root cause

Certificate was provisioned outside of ACM's auto-renewal path (e.g. imported
third-party cert), or DNS validation records for ACM auto-renewal were removed/changed,
breaking automatic renewal.

## Recommended action

1. Check if the certificate is ACM-managed with DNS validation; if so, confirm the
   validation CNAME record still exists in Route 53. A deleted record silently breaks
   auto-renewal.
2. If it's an imported certificate, begin manual renewal immediately; do not wait, since
   imported certs have no auto-renewal path at all.
3. Add a CloudWatch alarm on ACM `DaysToExpiry` if one does not already exist, to avoid
   relying on manual tracking.

## Anti-pattern to avoid

Do not assume "ACM-issued" means "auto-renews forever". Auto-renewal silently fails if
the underlying DNS validation record is altered, and there is no loud failure signal
until the cert is close to expiry.
