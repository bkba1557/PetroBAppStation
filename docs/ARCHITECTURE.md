# NNEXORIS Customer App Architecture

## 1. Services and trust boundaries

```text
Flutter App
    |
    | HTTPS + short-lived access token
    v
NNEXORIS Customer API
    |-- Customer Identity and Vehicles
    |-- Station Discovery
    |-- Wallet and Payment Gateway
    |-- Fuel Authorization Orchestrator
    |-- WebSocket/SSE Live Session Gateway
    |
    | signed idempotent hardware command
    v
NNEXORIS Cloud Control Plane
    |
    v
nnexoris-edge -> dispenser/nozzle
```

The Customer API belongs in NNEXORIS Cloud, not on Edge. Edge remains the only
component allowed to communicate with station hardware.

## 2. Customer identity

Registration collects email, password, vehicle plate and registration number.
Cloud policy determines whether email verification is mandatory for fueling or
wallet operations; the mobile guard mirrors that policy only for UX. Vehicle data
is encrypted at rest and masked in logs. Customer identity is separate from
staff IAM, with its own roles, tokens, rate limits and session revocation.

Recommended controls:

- Argon2id password hashes and verified email;
- short-lived access token plus rotating refresh token;
- refresh-token reuse detection and device/session management;
- optional biometric unlock for the locally stored refresh credential;
- login, registration and QR rate limiting;
- no vehicle registration number in telemetry or analytics.

## 3. Wallet model

Never store only a mutable `balance` field. Use an immutable double-entry
ledger in minor currency units. The visible balance is derived from posted
credits minus posted debits and active holds.

Core records:

- wallet account;
- ledger transaction and balanced ledger entries;
- payment intent and authoritative gateway webhook;
- fueling hold, settlement and release;
- refund and dispute records;
- idempotency key on every monetary mutation.

Top-up becomes available only after a signed payment-gateway webhook. The app's
success page is informational and cannot credit the wallet.

## 4. Stations and distance

Cloud publishes active customer-visible stations with coordinates, company
branding/logo, supported fuel products, live availability and current prices.
The app requests location only through `LocationService`; Cloud or an approved
geospatial provider supplies the displayed distance. No naive coordinate math is
used. Manual station browsing remains available when location is denied.

A newly activated station appears automatically because the app consumes the
station catalog API; no mobile release is required. Location is not stored as
history unless the customer explicitly consents.

## 5. Fueling state machine

```text
created -> qrVerified -> fundsReservationPending -> fundsReserved
        -> awaitingNozzle -> authorizationPending -> authorizationSent
        -> authorized -> dispensing -> stopping -> completed
        -> settlementPending -> settled

Terminal alternatives: cancelled, failed, expired.
Only `settled` is a successful financial outcome. Every terminal state settles
or releases the hold exactly once in Cloud.
```

For a fixed amount, Cloud places a hold for that amount. For `FULL`, Cloud
places a configurable maximum hold based on station policy and wallet balance.
After the dispenser reports final liters and amount, Cloud debits the actual
amount and releases the unused remainder.

## 6. Customer QR flow

Printed QR codes contain an opaque public nozzle identifier and version, not a
serial address or a reusable authorization. After scan, Cloud verifies:

- authenticated and verified customer;
- sufficient available balance and active hold;
- customer proximity/geofence and selected station;
- station and Edge heartbeat freshness;
- nozzle mapping, product match and live physical availability;
- no other active authorization for the customer or nozzle;
- QR version and nozzle record are active.

Only then does Cloud create a signed, expiring, idempotent authorization for
Edge. Edge verifies the staged configuration, address, fuel, amount/preset,
expiry and current nozzle state before sending the dispenser command.

## 7. Attendant QR flow

The attendant uses a staff surface, not the customer app. It creates a dynamic,
single-use QR session bound to employee, station and a 60-second expiry. The
customer scans it and approves wallet use. The attendant then selects an
available nozzle whose fuel matches the approved product. Cloud applies the
same hold and hardware authorization flow. A screenshot or reused QR is
rejected.

## 8. Live fueling

The app subscribes to a scoped WebSocket/SSE channel using the fueling session
ID. It receives server-generated states, liters, amount, unit price and final
settlement. The phone never calculates the financial total. Reconnect uses the
latest event sequence so updates are ordered and replay-safe.

## 9. Failure rules

- New fueling is denied when Cloud, Edge or nozzle telemetry is stale.
- Gateway timeouts do not credit a wallet; webhook reconciliation decides.
- Hardware timeout releases the hold unless dispensing was observed.
- Once dispensing is observed, settlement uses durable Edge meter events.
- Duplicate button taps, QR scans, callbacks and Edge acknowledgements share
  idempotency keys and cannot double debit or double authorize.
- A product/nozzle mismatch is always rejected; it is never auto-corrected.

## 10. Application structure

```text
lib/app       composition, router, localization and theme
lib/core      environment, HTTP, security, storage and realtime transport
lib/features  feature-owned data/domain/presentation code
lib/shared    reusable UI and shared types only
```

Feature-first Clean Architecture is used at system boundaries. Domain models
do not import Flutter, repositories do not depend on widgets or `BuildContext`,
and presentation consumes repository providers through Riverpod. Small features
are not split into empty use-case layers.

See `API_CONTRACTS.md` for the proposed unversioned customer API. It is not
claimed as implemented until the NNEXORIS Cloud repository is audited.

## 11. Runtime and state ownership

- Riverpod owns authentication, theme, locale, network/realtime connection, and
  repository injection. There are no global mutable application states.
- REST is authoritative after launch and after every realtime reconnect.
- WebSocket is the default event transport; SSE conforms to the same
  `RealtimeClient` boundary. Ordered events are filtered by entity sequence and
  event ID. Bounded REST polling is the final degradation mode.
- Cached values may be displayed as stale. No financial or fueling mutation is
  queued offline.

## 12. Responsibility boundaries

Flutter owns UI, authentication requests, QR capture, station/wallet/session
display, realtime consumption, and secure token storage. It never calculates an
authoritative balance, signs hardware commands, chooses dispenser protocols,
computes BCC/CRC, talks to RS485, or confirms payment/final liters independently.

Cloud owns identity, the ledger, holds, settlement, QR resolution, validation,
idempotency, signed Edge commands, payment-webhook truth, and customer events.

Edge verifies signed Cloud commands, prevents local replay, operates and reads
the dispenser, persists in-flight events, and safely resumes Cloud delivery. It
does not trust the customer phone.

## 13. Delivery phases

1. Flutter design system, Arabic/English, themes, onboarding and empty dashboard.
2. Customer auth, verified email, profile, vehicles and secure sessions.
3. Live station catalog, logos, location permission and distance sorting.
4. Wallet ledger, sandbox payment gateway, webhooks and transaction history.
5. QR issuance/scan, fueling holds and a simulated dispenser state machine.
6. Signed Cloud-to-Edge authorization behind a feature flag at one test nozzle.
7. Live telemetry, settlement, refunds, attendant flow and operational tooling.
8. Security review, load/failure testing, Play Store/TestFlight releases and a
   controlled station pilot before production rollout.
