# NNEXORIS Customer App

Standalone Flutter client for NNEXORIS customers on Android and iOS.

## Code path

`/home/petrob-2027/Nnexoris-Edge/nnexoris-customer-app`

The folder is self-contained and can later be moved to its own Git repository.
The Android platform project is present. Flutter is not installed on this Linux
host, so dependency resolution, analyzer, tests, and signed builds must be run
on the Windows Flutter workstation. Product and integration decisions are
recorded in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), endpoints in
[docs/API_CONTRACTS.md](docs/API_CONTRACTS.md), and the threat model in
[docs/SECURITY.md](docs/SECURITY.md).

## Product boundary

The mobile app is an untrusted client. It never:

- changes wallet balances directly;
- sends raw serial frames;
- talks directly to a dispenser;
- decides that a payment succeeded;
- closes or settles a fueling transaction.

All financial and hardware decisions are made by NNEXORIS Cloud. Cloud sends a
signed, idempotent authorization to the station's `nnexoris-edge`; Edge verifies
the nozzle and physical state before touching the dispenser.

## Implemented packages

- `lib/app`: routing, themes and localization
- `lib/core`: API, secure storage, errors, logging and shared UI
- `lib/features/authentication`: registration, login and rotating sessions
- `lib/features/profile`: customer and vehicle information
- `lib/features/stations`: live stations, distance, fuels and branding
- `lib/features/wallet`: balance, top-up and immutable ledger history
- `lib/features/qr_scanner`: Cloud-resolved QR references
- `lib/features/fueling`: selection, authorization state and live fueling
- `lib/core/realtime`: authenticated SSE with reconnect and REST reconciliation
- `lib/features/settings`: theme, language, privacy and security

## Commands (after Flutter SDK installation)

```bash
cd nnexoris-customer-app
flutter pub get
flutter gen-l10n
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
flutter build apk --debug --dart-define=APP_ENV=production
flutter run --dart-define=APP_ENV=development \
  --dart-define=API_BASE_URL=http://localhost:8080/api/v1/customer/ \
  --dart-define=WS_BASE_URL=ws://localhost:8080/api/v1/customer/realtime
```

`APP_ENV=production` defaults to
`https://customer-api.nnexoris.com/api/v1/customer/` and
`wss://customer-api.nnexoris.com/api/v1/customer/realtime`. Staging requires
explicit HTTPS/WSS values. Do not place secrets in `--dart-define`; the app
contains no Cloud or Edge signing keys.

For a production release, create `android/key.properties` locally with
`storeFile`, `storePassword`, `keyAlias`, and `keyPassword`, then run:

```bash
flutter build appbundle --release \
  --dart-define=APP_ENV=production \
  --dart-define=ENABLE_LOGGING=false
```

Release builds fail closed when that private signing configuration is absent.
