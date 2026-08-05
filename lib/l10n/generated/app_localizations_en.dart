// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appName => 'PetroB';

  @override
  String get welcome => 'Welcome';

  @override
  String get emptyDashboard =>
      'Your wallet and transactions will appear here after your first operation';

  @override
  String get login => 'Sign in';

  @override
  String get register => 'Create account';

  @override
  String get email => 'Email';

  @override
  String get password => 'Password';

  @override
  String get authWelcomeBack => 'Welcome back';

  @override
  String get authLoginSubtitle =>
      'Sign in to manage your wallet and fuel with confidence';

  @override
  String get authRegisterTitle => 'Create your account';

  @override
  String get authRegisterSubtitle =>
      'A smarter, simpler way to manage every journey';

  @override
  String get mobileNumber => 'Mobile number';

  @override
  String get confirmPassword => 'Confirm password';

  @override
  String get emailValidation => 'Enter a valid email address';

  @override
  String get mobileValidation => 'Enter a valid mobile number';

  @override
  String get passwordValidation => 'Password must be at least 8 characters';

  @override
  String get passwordMismatch => 'Passwords do not match';

  @override
  String get passwordHint => 'Use at least 8 characters for a secure password.';

  @override
  String get noAccount => 'New to PetroB?';

  @override
  String get alreadyHaveAccount => 'Already have an account?';

  @override
  String get secureAuthCaption =>
      'Your data is protected with secure encryption';

  @override
  String get showPassword => 'Show password';

  @override
  String get hidePassword => 'Hide password';

  @override
  String get displayName => 'Full name';

  @override
  String get plateNumber => 'Vehicle plate number';

  @override
  String get registrationNumber => 'Vehicle registration number';

  @override
  String get home => 'Home';

  @override
  String get stations => 'Stations';

  @override
  String get stationDetails => 'Station details';

  @override
  String get searchStations => 'Search by station name or location';

  @override
  String get stationsLoadFailed => 'Could not load stations';

  @override
  String get noStations => 'No stations are currently available';

  @override
  String get noSearchResults => 'No matching results';

  @override
  String get fuelingAvailable => 'Fueling is available';

  @override
  String get browsePricesAvailable =>
      'Station and prices are available to browse';

  @override
  String get companySelfServiceDisabledMessage =>
      'Self-service is not enabled for this company.';

  @override
  String get stationSelfServiceDisabledMessage =>
      'Self-service is not enabled at this station.';

  @override
  String get stationMaintenanceMessage =>
      'Self-service is temporarily unavailable for maintenance.';

  @override
  String get hardwareFuelingDisabledMessage =>
      'You can view the station and prices, but starting fueling in the app has not been enabled yet.';

  @override
  String get edgeOfflineMessage => 'The station device is currently offline.';

  @override
  String get noCompatibleNozzleMessage =>
      'No nozzle is available for the selected fuel type.';

  @override
  String get fuelPriceUnavailableMessage =>
      'The fuel price is currently unavailable.';

  @override
  String get outsideScheduleMessage =>
      'Self-service is unavailable outside the configured operating hours.';

  @override
  String get availabilityUnknownMessage =>
      'Fueling availability is currently unknown.';

  @override
  String get fuelPrices => 'Fuel prices';

  @override
  String get noFuelPrices => 'No active fuel prices are currently available.';

  @override
  String get lastUpdated => 'Last updated';

  @override
  String get startFueling => 'Start fueling';

  @override
  String get fuelGasoline91 => 'Gasoline 91';

  @override
  String get fuelGasoline95 => 'Gasoline 95';

  @override
  String get fuelDiesel => 'Diesel';

  @override
  String get fuelKerosene => 'Kerosene';

  @override
  String get fuelLpg => 'LPG';

  @override
  String get fuelOther => 'Other fuel';

  @override
  String get wallet => 'Wallet';

  @override
  String get topUp => 'Top up';

  @override
  String get transactions => 'Transactions';

  @override
  String get scanQr => 'Scan QR';

  @override
  String get scanQrHint =>
      'The scanned reference will be verified by NNEXORIS Cloud before fueling.';

  @override
  String get fuelingSetup => 'Fueling setup';

  @override
  String get fuelingProgress => 'Fueling progress';

  @override
  String get vehicles => 'Vehicles';

  @override
  String get profile => 'Profile';

  @override
  String get settings => 'Settings';

  @override
  String get verifyEmail => 'Verify email';

  @override
  String get verifyEmailHint =>
      'Verify your email before starting a fueling session.';

  @override
  String get onboardingTitle => 'Fuel securely with NNEXORIS';

  @override
  String get continueLabel => 'Continue';

  @override
  String get lightTheme => 'Light';

  @override
  String get darkTheme => 'Dark';

  @override
  String get systemTheme => 'System';

  @override
  String get language => 'Language';

  @override
  String get arabic => 'Arabic';

  @override
  String get english => 'English';

  @override
  String get logout => 'Sign out';

  @override
  String get loading => 'Loading';

  @override
  String get comingSoon => 'This section is ready for Cloud API integration.';

  @override
  String get offlineNotice => 'You are offline. New fueling cannot start.';

  @override
  String get errorUnexpected => 'Something went wrong. Try again safely.';

  @override
  String get errorInvalidCredentials => 'Email or password is incorrect.';

  @override
  String get errorEmailVerificationRequired =>
      'Email verification is required.';

  @override
  String get errorInsufficientFunds => 'Wallet balance is insufficient.';

  @override
  String get errorOffline => 'Cloud connection is unavailable.';

  @override
  String get errorSessionExpired => 'Your session expired. Sign in again.';
}
