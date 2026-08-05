# Proposed NNEXORIS Customer API Contracts

Status: design contract only. These endpoints are not considered implemented
until the NNEXORIS Cloud repository and deployed API are verified.

## Conventions

All requests use HTTPS, JSON, `Accept-Language`, `X-App-Version`, non-sensitive
`X-Device-Id`, and a unique `X-Correlation-Id`. Protected routes also require
`Authorization: Bearer <access-token>`. The server echoes the correlation ID.
Mutation responses include authoritative resource versions where relevant.

Errors use:

```json
{"code":"INSUFFICIENT_FUNDS","message":"Safe localized fallback","correlationId":"uuid","details":{}}
```

Common codes are `VALIDATION_ERROR` (400), `UNAUTHORIZED` (401), `FORBIDDEN`
(403), `NOT_FOUND` (404), `CONFLICT` (409), `RATE_LIMITED` (429), and
`INTERNAL_ERROR` (500). Clients may retry GET after transport/408/429/5xx with
backoff. A mutation is retryable only with the same `Idempotency-Key` and only
where explicitly stated. A key identifies one semantic operation, not one HTTP
attempt.

## Authentication and profile

### `POST /api/customer/auth/register`

- Auth: none. Headers: common; registration rate limits apply.
- Request: `{"email":"customer@example.com","password":"...","displayName":"Customer","vehicle":{"plateNumber":"ABC1234","registrationNumber":"..."}}`
- Response `201`: `{"customer":{"id":"cus_1","email":"customer@example.com","displayName":"Customer","emailVerified":false},"tokens":{"accessToken":"...","refreshToken":"...","accessTokenExpiresAt":"2026-08-01T18:00:00Z"}}`
- Failures: `EMAIL_ALREADY_EXISTS`, `WEAK_PASSWORD`, `INVALID_VEHICLE_DATA`, common validation/rate limits.
- Idempotency/retry: optional key recommended; retry only with the same key.

### `POST /api/customer/auth/login`

- Auth: none. Request: `{"email":"customer@example.com","password":"..."}`.
- Response `200`: same session shape as registration with authoritative customer.
- Failures: `INVALID_CREDENTIALS`, `ACCOUNT_DISABLED`, `RATE_LIMITED`.
- Idempotency/retry: no key; a user may manually retry after an indeterminate transport failure.

### `POST /api/customer/auth/refresh`

- Auth: refresh token in JSON: `{"refreshToken":"..."}`; never in query/logs.
- Response `200`: rotated `AuthTokens`. Failures: `INVALID_REFRESH_TOKEN`,
  `REFRESH_TOKEN_REUSED`, `SESSION_REVOKED`.
- Idempotency/retry: Cloud must define a short replay grace for the same token;
  client serializes refresh and does not loop.

### `POST /api/customer/auth/logout`

- Auth: bearer. Request may include `{"allSessions":false}`; response `204`.
- Failures: only common auth/server failures; local credentials are cleared even
  if remote revocation cannot be confirmed.
- Idempotency/retry: naturally idempotent; safe to retry.

### `POST /api/customer/auth/verify-email`

- Auth: bearer. Request: `{"code":"123456"}`.
- Response `200`: authoritative `Customer` with `emailVerified:true`.
- Failures: `INVALID_VERIFICATION_CODE`, `CODE_EXPIRED`, `TOO_MANY_ATTEMPTS`.
- Idempotency/retry: repeated successful verification is safe; transport retry allowed.

### `GET /api/customer/profile`

- Auth: bearer. Response `200`: `{"id":"cus_1","email":"...","displayName":"...","emailVerified":true,"phoneNumber":null}`.
- Failures: common auth/not-found. Idempotency: read-only and retryable.

## Stations

### `GET /api/customer/stations`

- Auth: bearer. Optional query: `latitude`, `longitude`, `cursor`; location can be omitted.
- Response `200`: array/page of stations containing `id`, `name`, `logoUrl`,
  optional server-calculated `distanceMeters`, `location`, `operatingStatus`,
  `fuelPrices`, `operatingHours`, availability booleans, and `services`.
- Example: `[{"id":"st_1","name":"NNEXORIS Station","location":{"latitude":24.7,"longitude":46.7,"address":"Riyadh"},"operatingStatus":"open","fuelPrices":[],"services":[],"selfServiceAvailable":true,"appFuelingAvailable":true}]`
- Failures: `INVALID_LOCATION`, common. Read-only and retryable. Location refusal is not an error.

### `GET /api/customer/stations/{stationId}`

- Auth: bearer. Response `200`: one full Station object.
- Failures: `STATION_NOT_FOUND`, `STATION_NOT_VISIBLE`. Read-only and retryable.

### `GET /api/customer/stations/{stationId}/fuel-prices`

- Auth: bearer. Response `200`: `[{"product":{"id":"fp_91","code":"GASOLINE_91","name":"Gasoline 91"},"unitPrice":2.18,"currency":"SAR","effectiveAt":"2026-08-01T00:00:00Z"}]`.
- Failures: station common errors. Read-only and retryable; price is display data
  until Cloud locks it into a fueling session.

## Wallet

### `GET /api/customer/wallet`

- Auth: bearer. Response `200`: `{"id":"wal_1","balance":{"available":250.00,"reserved":0.00,"currency":"SAR","version":42}}`.
- Failures: `WALLET_NOT_FOUND`, common. Read-only and retryable. Local arithmetic never replaces this value.

### `GET /api/customer/wallet/transactions`

- Auth: bearer. Optional `cursor`. Response `200`: transaction page, e.g.
  `[{"id":"txn_1","type":"topUp","amount":100.0,"currency":"SAR","createdAt":"2026-08-01T12:00:00Z"}]` plus pagination metadata in the final Cloud schema.
- Failures: common. Read-only and retryable.

### `POST /api/customer/wallet/topups`

- Auth: bearer. `Idempotency-Key` required.
- Request: `{"amount":100.0,"currency":"SAR","paymentMethodId":"pm_1","returnUrl":"nnexoris://wallet/topup"}`.
- Response `201`: `{"id":"top_1","amount":100.0,"status":"pendingPayment","paymentRedirectUrl":"https://provider.example/..."}`.
- Failures: `INVALID_AMOUNT`, `PAYMENT_METHOD_UNAVAILABLE`, `TOPUP_LIMIT_EXCEEDED`, `IDEMPOTENCY_CONFLICT`.
- Retry: only same body and key. A redirect/SDK success does not mean `paid`; Cloud webhook confirmation does.

### `GET /api/customer/wallet/topups/{topupId}`

- Auth: bearer and resource ownership. Response `200`: top-up with one of
  `created`, `pendingPayment`, `paid`, `failed`, `cancelled`, `expired`, `refunded`.
- Failures: `TOPUP_NOT_FOUND`, common. Read-only and retryable.

## QR resolution

### `POST /api/customer/qr/resolve`

- Auth: bearer. Request: `{"token":"opaque-scanned-reference"}`. Never log the full token.
- Response `200`: `{"valid":true,"resolution":{"resolutionId":"qrr_1","stationId":"st_1","pumpId":"pump_2","nozzleId":"noz_3","fuelProductId":"fp_91","expiresAt":"2026-08-01T18:01:00Z","singleUse":true}}`.
- Failures: `QR_INVALID`, `QR_EXPIRED`, `QR_ALREADY_USED`, `NOZZLE_UNAVAILABLE`,
  `STATION_OFFLINE`, `PRODUCT_MISMATCH`.
- Idempotency/retry: resolution itself may be retried briefly with the same token;
  it never authorizes hardware and Cloud owns consumption semantics.

## Fueling sessions

### `POST /api/customer/fueling-sessions`

- Auth: verified-email bearer. `Idempotency-Key` required.
- Fixed request: `{"qrResolutionId":"qrr_1","requestedMode":"fixedAmount","requestedAmount":100.0}`.
- Fill-up request: `{"qrResolutionId":"qrr_1","requestedMode":"fillUp"}`;
  Cloud chooses and returns `maximumAuthorizationAmount`.
- Response `201`: full `FuelingSession`, initially `created` or a subsequent
  authoritative state, including IDs, amounts, volume, unit price, timestamps,
  status and failure fields.
- Failures: `EMAIL_VERIFICATION_REQUIRED`, `ACTIVE_SESSION_EXISTS`,
  `INSUFFICIENT_FUNDS`, `QR_INVALID`, `STATION_OFFLINE`, `NOZZLE_BUSY`,
  `IDEMPOTENCY_CONFLICT`.
- Retry: same request and key only. Never create a new key to recover an unknown result.

### `GET /api/customer/fueling-sessions/{sessionId}`

- Auth: bearer and ownership. Response `200`: complete authoritative session.
- Failures: `FUELING_SESSION_NOT_FOUND`, common. Read-only and retryable. This is
  mandatory reconciliation after realtime reconnect.

### `POST /api/customer/fueling-sessions/{sessionId}/cancel`

- Auth: bearer and ownership. `Idempotency-Key` required; optional request
  `{"reason":"customer_requested"}`.
- Response `200`: session state. Cancellation is a request, not proof the pump
  stopped; Cloud may return `stopping`, `cancelled`, or conflict.
- Failures: `SESSION_NOT_CANCELLABLE`, `DISPENSING_ALREADY_COMPLETED`,
  `IDEMPOTENCY_CONFLICT`. Retry only with the same key.

### `GET /api/customer/fueling-sessions/{sessionId}/events`

- Auth: bearer and ownership. Headers include `Accept: text/event-stream`; query
  or `Last-Event-ID` resumes after a known event.
- Event data: `{"eventId":"evt_7","eventType":"fueling.progress","entityId":"ses_1","sequence":7,"occurredAt":"2026-08-01T18:00:07Z","payload":{"dispensedAmount":32.4,"dispensedVolume":13.72}}`.
- Event types: `fueling.session.updated`, `fueling.authorized`,
  `fueling.started`, `fueling.progress`, `fueling.stopped`, `fueling.completed`,
  `fueling.settled`, `fueling.failed`, `wallet.balance.updated`, and
  `wallet.reservation.updated`.
- Failures: auth/ownership, `EVENT_CURSOR_EXPIRED`. Reconnect with backoff; fetch
  session REST state before trusting resumed progress. Old/duplicate sequences are ignored.

## Server invariants

Cloud must atomically prevent multiple active sessions for a customer/nozzle,
bind resolution to station/pump/nozzle/product, reserve before authorization,
sign an expiring non-replayable Edge command, capture only actual reported value,
release the remainder exactly once, and publish monotonically ordered entity
events. Flutter guards are UX only and do not satisfy these invariants.
