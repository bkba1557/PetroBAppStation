import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_ar.dart';
import 'app_localizations_en.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'generated/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('ar'),
    Locale('en'),
  ];

  /// No description provided for @appName.
  ///
  /// In ar, this message translates to:
  /// **'PetroB'**
  String get appName;

  /// No description provided for @welcome.
  ///
  /// In ar, this message translates to:
  /// **'مرحبًا بك'**
  String get welcome;

  /// No description provided for @emptyDashboard.
  ///
  /// In ar, this message translates to:
  /// **'ستظهر معاملاتك ومحفظتك هنا بعد أول عملية'**
  String get emptyDashboard;

  /// No description provided for @login.
  ///
  /// In ar, this message translates to:
  /// **'تسجيل الدخول'**
  String get login;

  /// No description provided for @register.
  ///
  /// In ar, this message translates to:
  /// **'إنشاء حساب'**
  String get register;

  /// No description provided for @email.
  ///
  /// In ar, this message translates to:
  /// **'البريد الإلكتروني'**
  String get email;

  /// No description provided for @password.
  ///
  /// In ar, this message translates to:
  /// **'كلمة المرور'**
  String get password;

  /// No description provided for @authWelcomeBack.
  ///
  /// In ar, this message translates to:
  /// **'مرحبًا بعودتك'**
  String get authWelcomeBack;

  /// No description provided for @authLoginSubtitle.
  ///
  /// In ar, this message translates to:
  /// **'سجّل دخولك لإدارة محفظتك والتزوّد بالوقود بكل ثقة'**
  String get authLoginSubtitle;

  /// No description provided for @authRegisterTitle.
  ///
  /// In ar, this message translates to:
  /// **'أنشئ حسابك'**
  String get authRegisterTitle;

  /// No description provided for @authRegisterSubtitle.
  ///
  /// In ar, this message translates to:
  /// **'تجربة أذكى وأسهل لإدارة كل رحلة'**
  String get authRegisterSubtitle;

  /// No description provided for @mobileNumber.
  ///
  /// In ar, this message translates to:
  /// **'رقم الجوال'**
  String get mobileNumber;

  /// No description provided for @confirmPassword.
  ///
  /// In ar, this message translates to:
  /// **'تأكيد كلمة المرور'**
  String get confirmPassword;

  /// No description provided for @emailValidation.
  ///
  /// In ar, this message translates to:
  /// **'أدخل بريدًا إلكترونيًا صحيحًا'**
  String get emailValidation;

  /// No description provided for @mobileValidation.
  ///
  /// In ar, this message translates to:
  /// **'أدخل رقم جوال صحيحًا'**
  String get mobileValidation;

  /// No description provided for @passwordValidation.
  ///
  /// In ar, this message translates to:
  /// **'يجب ألا تقل كلمة المرور عن 8 أحرف'**
  String get passwordValidation;

  /// No description provided for @passwordMismatch.
  ///
  /// In ar, this message translates to:
  /// **'كلمتا المرور غير متطابقتين'**
  String get passwordMismatch;

  /// No description provided for @passwordHint.
  ///
  /// In ar, this message translates to:
  /// **'استخدم 8 أحرف على الأقل لإنشاء كلمة مرور آمنة.'**
  String get passwordHint;

  /// No description provided for @noAccount.
  ///
  /// In ar, this message translates to:
  /// **'جديد في PetroB؟'**
  String get noAccount;

  /// No description provided for @alreadyHaveAccount.
  ///
  /// In ar, this message translates to:
  /// **'لديك حساب بالفعل؟'**
  String get alreadyHaveAccount;

  /// No description provided for @secureAuthCaption.
  ///
  /// In ar, this message translates to:
  /// **'بياناتك محمية بتشفير آمن'**
  String get secureAuthCaption;

  /// No description provided for @showPassword.
  ///
  /// In ar, this message translates to:
  /// **'إظهار كلمة المرور'**
  String get showPassword;

  /// No description provided for @hidePassword.
  ///
  /// In ar, this message translates to:
  /// **'إخفاء كلمة المرور'**
  String get hidePassword;

  /// No description provided for @displayName.
  ///
  /// In ar, this message translates to:
  /// **'الاسم الكامل'**
  String get displayName;

  /// No description provided for @plateNumber.
  ///
  /// In ar, this message translates to:
  /// **'رقم لوحة السيارة'**
  String get plateNumber;

  /// No description provided for @registrationNumber.
  ///
  /// In ar, this message translates to:
  /// **'رقم الاستمارة'**
  String get registrationNumber;

  /// No description provided for @home.
  ///
  /// In ar, this message translates to:
  /// **'الرئيسية'**
  String get home;

  /// No description provided for @stations.
  ///
  /// In ar, this message translates to:
  /// **'المحطات'**
  String get stations;

  /// No description provided for @stationDetails.
  ///
  /// In ar, this message translates to:
  /// **'تفاصيل المحطة'**
  String get stationDetails;

  /// No description provided for @searchStations.
  ///
  /// In ar, this message translates to:
  /// **'ابحث باسم المحطة أو الموقع'**
  String get searchStations;

  /// No description provided for @stationsLoadFailed.
  ///
  /// In ar, this message translates to:
  /// **'تعذر تحميل المحطات'**
  String get stationsLoadFailed;

  /// No description provided for @noStations.
  ///
  /// In ar, this message translates to:
  /// **'لا توجد محطات متاحة حاليًا'**
  String get noStations;

  /// No description provided for @noSearchResults.
  ///
  /// In ar, this message translates to:
  /// **'لا توجد نتائج مطابقة'**
  String get noSearchResults;

  /// No description provided for @fuelingAvailable.
  ///
  /// In ar, this message translates to:
  /// **'التعبئة متاحة'**
  String get fuelingAvailable;

  /// No description provided for @browsePricesAvailable.
  ///
  /// In ar, this message translates to:
  /// **'المحطة والأسعار متاحة للتصفح'**
  String get browsePricesAvailable;

  /// No description provided for @companySelfServiceDisabledMessage.
  ///
  /// In ar, this message translates to:
  /// **'الخدمات الذاتية غير مفعلة لهذه الشركة.'**
  String get companySelfServiceDisabledMessage;

  /// No description provided for @stationSelfServiceDisabledMessage.
  ///
  /// In ar, this message translates to:
  /// **'الخدمات الذاتية غير مفعلة في هذه المحطة.'**
  String get stationSelfServiceDisabledMessage;

  /// No description provided for @stationMaintenanceMessage.
  ///
  /// In ar, this message translates to:
  /// **'الخدمات الذاتية متوقفة مؤقتًا للصيانة.'**
  String get stationMaintenanceMessage;

  /// No description provided for @hardwareFuelingDisabledMessage.
  ///
  /// In ar, this message translates to:
  /// **'يمكنك مشاهدة المحطة والأسعار، لكن بدء التعبئة عبر التطبيق لم يُفعّل بعد.'**
  String get hardwareFuelingDisabledMessage;

  /// No description provided for @edgeOfflineMessage.
  ///
  /// In ar, this message translates to:
  /// **'جهاز المحطة غير متصل حاليًا.'**
  String get edgeOfflineMessage;

  /// No description provided for @noCompatibleNozzleMessage.
  ///
  /// In ar, this message translates to:
  /// **'لا توجد فوهة متاحة لنوع الوقود المحدد.'**
  String get noCompatibleNozzleMessage;

  /// No description provided for @fuelPriceUnavailableMessage.
  ///
  /// In ar, this message translates to:
  /// **'سعر الوقود غير متاح حاليًا.'**
  String get fuelPriceUnavailableMessage;

  /// No description provided for @outsideScheduleMessage.
  ///
  /// In ar, this message translates to:
  /// **'الخدمات الذاتية غير متاحة خارج أوقات التشغيل المحددة.'**
  String get outsideScheduleMessage;

  /// No description provided for @availabilityUnknownMessage.
  ///
  /// In ar, this message translates to:
  /// **'حالة التعبئة غير متاحة حاليًا.'**
  String get availabilityUnknownMessage;

  /// No description provided for @fuelPrices.
  ///
  /// In ar, this message translates to:
  /// **'أسعار الوقود'**
  String get fuelPrices;

  /// No description provided for @noFuelPrices.
  ///
  /// In ar, this message translates to:
  /// **'لا توجد أسعار وقود فعالة حاليًا.'**
  String get noFuelPrices;

  /// No description provided for @lastUpdated.
  ///
  /// In ar, this message translates to:
  /// **'آخر تحديث'**
  String get lastUpdated;

  /// No description provided for @startFueling.
  ///
  /// In ar, this message translates to:
  /// **'بدء التعبئة'**
  String get startFueling;

  /// No description provided for @fuelGasoline91.
  ///
  /// In ar, this message translates to:
  /// **'بنزين 91'**
  String get fuelGasoline91;

  /// No description provided for @fuelGasoline95.
  ///
  /// In ar, this message translates to:
  /// **'بنزين 95'**
  String get fuelGasoline95;

  /// No description provided for @fuelDiesel.
  ///
  /// In ar, this message translates to:
  /// **'ديزل'**
  String get fuelDiesel;

  /// No description provided for @fuelKerosene.
  ///
  /// In ar, this message translates to:
  /// **'كيروسين'**
  String get fuelKerosene;

  /// No description provided for @fuelLpg.
  ///
  /// In ar, this message translates to:
  /// **'غاز بترولي مسال'**
  String get fuelLpg;

  /// No description provided for @fuelOther.
  ///
  /// In ar, this message translates to:
  /// **'وقود آخر'**
  String get fuelOther;

  /// No description provided for @wallet.
  ///
  /// In ar, this message translates to:
  /// **'المحفظة'**
  String get wallet;

  /// No description provided for @topUp.
  ///
  /// In ar, this message translates to:
  /// **'شحن الرصيد'**
  String get topUp;

  /// No description provided for @transactions.
  ///
  /// In ar, this message translates to:
  /// **'المعاملات'**
  String get transactions;

  /// No description provided for @scanQr.
  ///
  /// In ar, this message translates to:
  /// **'مسح QR'**
  String get scanQr;

  /// No description provided for @scanQrHint.
  ///
  /// In ar, this message translates to:
  /// **'سيتم التحقق من الرمز عبر سحابة NNEXORIS قبل بدء التعبئة.'**
  String get scanQrHint;

  /// No description provided for @fuelingSetup.
  ///
  /// In ar, this message translates to:
  /// **'إعداد التعبئة'**
  String get fuelingSetup;

  /// No description provided for @fuelingProgress.
  ///
  /// In ar, this message translates to:
  /// **'تقدم التعبئة'**
  String get fuelingProgress;

  /// No description provided for @vehicles.
  ///
  /// In ar, this message translates to:
  /// **'المركبات'**
  String get vehicles;

  /// No description provided for @profile.
  ///
  /// In ar, this message translates to:
  /// **'الملف الشخصي'**
  String get profile;

  /// No description provided for @settings.
  ///
  /// In ar, this message translates to:
  /// **'الإعدادات'**
  String get settings;

  /// No description provided for @verifyEmail.
  ///
  /// In ar, this message translates to:
  /// **'تأكيد البريد'**
  String get verifyEmail;

  /// No description provided for @verifyEmailHint.
  ///
  /// In ar, this message translates to:
  /// **'أكد بريدك الإلكتروني قبل بدء جلسة تعبئة.'**
  String get verifyEmailHint;

  /// No description provided for @onboardingTitle.
  ///
  /// In ar, this message translates to:
  /// **'عبّئ بأمان مع NNEXORIS'**
  String get onboardingTitle;

  /// No description provided for @continueLabel.
  ///
  /// In ar, this message translates to:
  /// **'متابعة'**
  String get continueLabel;

  /// No description provided for @lightTheme.
  ///
  /// In ar, this message translates to:
  /// **'فاتح'**
  String get lightTheme;

  /// No description provided for @darkTheme.
  ///
  /// In ar, this message translates to:
  /// **'داكن'**
  String get darkTheme;

  /// No description provided for @systemTheme.
  ///
  /// In ar, this message translates to:
  /// **'النظام'**
  String get systemTheme;

  /// No description provided for @language.
  ///
  /// In ar, this message translates to:
  /// **'اللغة'**
  String get language;

  /// No description provided for @arabic.
  ///
  /// In ar, this message translates to:
  /// **'العربية'**
  String get arabic;

  /// No description provided for @english.
  ///
  /// In ar, this message translates to:
  /// **'الإنجليزية'**
  String get english;

  /// No description provided for @logout.
  ///
  /// In ar, this message translates to:
  /// **'تسجيل الخروج'**
  String get logout;

  /// No description provided for @loading.
  ///
  /// In ar, this message translates to:
  /// **'جارٍ التحميل'**
  String get loading;

  /// No description provided for @comingSoon.
  ///
  /// In ar, this message translates to:
  /// **'هذا القسم جاهز للربط مع واجهات السحابة.'**
  String get comingSoon;

  /// No description provided for @offlineNotice.
  ///
  /// In ar, this message translates to:
  /// **'لا يوجد اتصال. لا يمكن بدء تعبئة جديدة.'**
  String get offlineNotice;

  /// No description provided for @errorUnexpected.
  ///
  /// In ar, this message translates to:
  /// **'حدث خطأ. حاول مرة أخرى بأمان.'**
  String get errorUnexpected;

  /// No description provided for @errorInvalidCredentials.
  ///
  /// In ar, this message translates to:
  /// **'البريد أو كلمة المرور غير صحيحة.'**
  String get errorInvalidCredentials;

  /// No description provided for @errorEmailVerificationRequired.
  ///
  /// In ar, this message translates to:
  /// **'يلزم تأكيد البريد الإلكتروني.'**
  String get errorEmailVerificationRequired;

  /// No description provided for @errorInsufficientFunds.
  ///
  /// In ar, this message translates to:
  /// **'رصيد المحفظة غير كافٍ.'**
  String get errorInsufficientFunds;

  /// No description provided for @errorOffline.
  ///
  /// In ar, this message translates to:
  /// **'الاتصال بالسحابة غير متاح.'**
  String get errorOffline;

  /// No description provided for @errorSessionExpired.
  ///
  /// In ar, this message translates to:
  /// **'انتهت الجلسة. سجّل الدخول مجددًا.'**
  String get errorSessionExpired;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['ar', 'en'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'ar':
      return AppLocalizationsAr();
    case 'en':
      return AppLocalizationsEn();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
