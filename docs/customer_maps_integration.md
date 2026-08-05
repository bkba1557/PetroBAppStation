# Customer maps integration

## Confirmed production paths (read-only inspection)

- Raspberry Pi edge repository: `/home/petrob-2027/Nnexoris-Edge`
- Raspberry customer mirror: `/home/petrob-2027/Nnexoris-Edge/production-cloud-customer`
- Raspberry customer Flutter mirror: `/home/petrob-2027/Nnexoris-Edge/nnexoris-customer-app`
- Cloud application: `/opt/nnexoris-cloud`
- Cloud customer station API: `/opt/nnexoris-cloud/app/customer_api/stations.py`
- Cloud maps settings/API: `/opt/nnexoris-cloud/app/maps/routes.py`

No Raspberry Pi or cloud files were changed while implementing this feature.

## Local implementation paths

- Flutter stations UI: `lib/features/stations/presentation/stations_page.dart`
- Device location: `lib/features/stations/data/device_location_service.dart`
- Google Maps navigation URL: `lib/features/stations/data/station_navigation_service.dart`
- Route Matrix client: `lib/features/stations/data/station_repository_impl.dart`
- Customer backend patch: `cloud_patch/app/customer_api/stations.py`
- Fuel-code patch: `cloud_patch/app/customer_api/fuel_codes.py`

The backend patch adds `POST /api/v1/customer/stations/route-matrix`. It groups
stations by company, reads the existing protected Google server credential, and
calls Google Routes `computeRouteMatrix` with traffic-aware driving enabled.
The server key is never returned to the mobile application.

## Google Cloud configuration

Enable these APIs in the Google Cloud project:

1. Maps SDK for iOS
2. Maps SDK for Android
3. Routes API

Use separate restricted keys:

- `GOOGLE_MAPS_IOS_API_KEY`: restrict to iOS bundle `com.nnexoris.customer`.
- `GOOGLE_MAPS_ANDROID_API_KEY`: restrict to Android package
  `com.nnexoris.customer` and the production signing certificate SHA-1.
- `GOOGLE_MAPS_SERVER_API_KEY`: restrict to the Routes API and the cloud
  server's public IP. The existing encrypted Maps server credential can also
  be used through the cloud Maps settings page.

Add `GOOGLE_MAPS_IOS_API_KEY` as a protected Codemagic environment variable.
For Android builds, expose `GOOGLE_MAPS_ANDROID_API_KEY` as an environment or
Gradle property.

## Deployment boundary

The files under `cloud_patch/` are staging patches only. Apply them to
`/opt/nnexoris-cloud` and restart/test the cloud customer service only after
explicit production-change approval. Do not deploy the customer route endpoint
to the Raspberry Pi.
