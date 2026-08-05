# NNEXORIS Customer App Security

## Trust model

The mobile device is an untrusted client. A modified app, rooted device, copied
QR, replayed HTTP request, reordered event, or forged local balance must not be
able to authorize fuel or move money. NNEXORIS Cloud is the business source of
truth. Edge trusts only signed, expiring Cloud commands and remains the hardware
boundary.

## Principal threats and controls

| Threat | Primary control |
|---|---|
| Credential theft | Short access-token lifetime, rotating refresh tokens, secure platform storage, revocation |
| API interception | HTTPS/WSS only in staging/production; standard TLS validation is never bypassed |
| Duplicate debit/authorization | Cloud idempotency plus `Idempotency-Key`; no blind retry of mutations |
| QR copying/replay | Opaque token, Cloud resolution, expiry, one-time use, nozzle/station/product binding |
| Event replay/reordering | `eventId`, per-entity `sequence`, REST reconciliation after reconnect |
| Local data tampering | Cloud-provided balance, price and final session status remain authoritative |
| Sensitive log disclosure | Never log authorization, refresh token, full QR, payment data, or vehicle registration |
| Direct hardware attack from app | No Edge address, serial details, protocol frames, or signing keys in Flutter |
| Double active fueling | Cloud transaction/locking constraint per customer and nozzle |
| Button races | Disable pending actions in UI and enforce idempotency/concurrency in Cloud |

## Data handling

Only access/refresh tokens and minimal session metadata use secure storage. Theme
and locale may use preferences. Passwords, card data, Cloud/Edge private keys,
raw persistent QR values, dispenser protocol details, and internal station IPs
must never be stored. Logout clears all sensitive secure storage. Payment card
collection must be delegated to the payment provider's approved SDK; Cloud
credits the wallet only after validated provider webhook delivery.

Device ID is a random, non-sensitive installation identifier. It is not a
hardware fingerprint and must not be used as sole authentication. Correlation
IDs are random per request and safe error messages do not expose stack traces or
internal topology.

## Availability rules

Cached reads are allowed with a stale indicator. The app cannot start top-up,
reservation, or fueling while Cloud connectivity is unconfirmed. If connectivity
drops during fueling, the UI shows recovery and fetches the official session via
REST after reconnect. It does not infer success from the last local event.

## Component responsibilities

- Flutter: protect tokens, validate input for UX, send requests, render Cloud
  state, suppress sensitive logs, and enforce transport configuration.
- Cloud: authenticate/authorize, own ledger and idempotency, validate QR and live
  station state, serialize concurrent sessions, sign commands, reconcile payment
  webhooks, and produce ordered events.
- Edge: authenticate Cloud, validate signature/expiry/nonce, prevent replay,
  safely control hardware, and durably return progress/results.

Before production, perform mobile threat-model review, API authorization tests,
certificate and release-signing review, dependency scanning, rooted-device risk
decision, penetration testing, and incident/revocation exercises.
