# PETRO B iOS release

The iOS application uses bundle identifier `com.nnexoris.customer`, iOS 13.0
as its minimum deployment target, and the production customer API selected by
`APP_ENV=production`.

## One-time Apple setup

1. Create the app identifier `com.nnexoris.customer` in the Apple Developer
   portal.
2. Create the PETRO B app record in App Store Connect with the same bundle ID.
3. Create an App Store Connect API key with permission to manage builds and
   releases. Keep the `.p8` key private.
4. Complete App Privacy, age rating, support URL, privacy-policy URL, pricing,
   category, screenshots, review contact, and export-compliance answers in App
   Store Connect. The project declares that it does not use non-exempt
   encryption.

## Codemagic configuration

Connect the Git repository to Codemagic, then create an encrypted variable
group named `appstore_credentials` containing:

- `APP_STORE_CONNECT_PRIVATE_KEY`: the complete contents of the `.p8` file.
- `APP_STORE_CONNECT_KEY_IDENTIFIER`: the API key ID.
- `APP_STORE_CONNECT_ISSUER_ID`: the API issuer ID.

The repository includes two manual workflows:

- `ios-testflight` builds, signs, and uploads a production-configured build to
  TestFlight.
- `ios-production` builds, signs, and submits a production-configured build to
  App Store Connect with manual release after Apple approval.

Codemagic uses its monotonically increasing `CM_BUILD_NUMBER` as the Apple build
number. Change the semantic version in `pubspec.yaml` for each App Store version.

## Release checks

Before starting either workflow:

- Confirm the production API and WebSocket health.
- Confirm the App Store privacy answers match `ios/Runner/PrivacyInfo.xcprivacy`
  and actual server-side data handling.
- Test account creation, quick login, station browsing, wallet display, QR scan,
  session cancellation, Arabic/English switching, and light/dark modes on a real
  iPhone.
- Review Apple screenshots and metadata; the first App Store version may require
  completing submission metadata manually in App Store Connect.

Never place API secrets, Apple credentials, or payment secrets in Dart defines
or committed files.
