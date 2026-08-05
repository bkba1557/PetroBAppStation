// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Arabic (`ar`).
class AppLocalizationsAr extends AppLocalizations {
  AppLocalizationsAr([String locale = 'ar']) : super(locale);

  @override
  String get appName => 'PetroB';

  @override
  String get welcome => 'مرحبًا بك';

  @override
  String get emptyDashboard => 'ستظهر معاملاتك ومحفظتك هنا بعد أول عملية';

  @override
  String get login => 'تسجيل الدخول';

  @override
  String get register => 'إنشاء حساب';

  @override
  String get email => 'البريد الإلكتروني';

  @override
  String get password => 'كلمة المرور';

  @override
  String get authWelcomeBack => 'مرحبًا بعودتك';

  @override
  String get authLoginSubtitle =>
      'سجّل دخولك لإدارة محفظتك والتزوّد بالوقود بكل ثقة';

  @override
  String get authRegisterTitle => 'أنشئ حسابك';

  @override
  String get authRegisterSubtitle => 'تجربة أذكى وأسهل لإدارة كل رحلة';

  @override
  String get mobileNumber => 'رقم الجوال';

  @override
  String get confirmPassword => 'تأكيد كلمة المرور';

  @override
  String get emailValidation => 'أدخل بريدًا إلكترونيًا صحيحًا';

  @override
  String get mobileValidation => 'أدخل رقم جوال صحيحًا';

  @override
  String get passwordValidation => 'يجب ألا تقل كلمة المرور عن 8 أحرف';

  @override
  String get passwordMismatch => 'كلمتا المرور غير متطابقتين';

  @override
  String get passwordHint => 'استخدم 8 أحرف على الأقل لإنشاء كلمة مرور آمنة.';

  @override
  String get noAccount => 'جديد في PetroB؟';

  @override
  String get alreadyHaveAccount => 'لديك حساب بالفعل؟';

  @override
  String get secureAuthCaption => 'بياناتك محمية بتشفير آمن';

  @override
  String get showPassword => 'إظهار كلمة المرور';

  @override
  String get hidePassword => 'إخفاء كلمة المرور';

  @override
  String get displayName => 'الاسم الكامل';

  @override
  String get plateNumber => 'رقم لوحة السيارة';

  @override
  String get registrationNumber => 'رقم الاستمارة';

  @override
  String get home => 'الرئيسية';

  @override
  String get stations => 'المحطات';

  @override
  String get stationDetails => 'تفاصيل المحطة';

  @override
  String get searchStations => 'ابحث باسم المحطة أو الموقع';

  @override
  String get stationsLoadFailed => 'تعذر تحميل المحطات';

  @override
  String get noStations => 'لا توجد محطات متاحة حاليًا';

  @override
  String get noSearchResults => 'لا توجد نتائج مطابقة';

  @override
  String get fuelingAvailable => 'التعبئة متاحة';

  @override
  String get browsePricesAvailable => 'المحطة والأسعار متاحة للتصفح';

  @override
  String get companySelfServiceDisabledMessage =>
      'الخدمات الذاتية غير مفعلة لهذه الشركة.';

  @override
  String get stationSelfServiceDisabledMessage =>
      'الخدمات الذاتية غير مفعلة في هذه المحطة.';

  @override
  String get stationMaintenanceMessage =>
      'الخدمات الذاتية متوقفة مؤقتًا للصيانة.';

  @override
  String get hardwareFuelingDisabledMessage =>
      'يمكنك مشاهدة المحطة والأسعار، لكن بدء التعبئة عبر التطبيق لم يُفعّل بعد.';

  @override
  String get edgeOfflineMessage => 'جهاز المحطة غير متصل حاليًا.';

  @override
  String get noCompatibleNozzleMessage =>
      'لا توجد فوهة متاحة لنوع الوقود المحدد.';

  @override
  String get fuelPriceUnavailableMessage => 'سعر الوقود غير متاح حاليًا.';

  @override
  String get outsideScheduleMessage =>
      'الخدمات الذاتية غير متاحة خارج أوقات التشغيل المحددة.';

  @override
  String get availabilityUnknownMessage => 'حالة التعبئة غير متاحة حاليًا.';

  @override
  String get fuelPrices => 'أسعار الوقود';

  @override
  String get noFuelPrices => 'لا توجد أسعار وقود فعالة حاليًا.';

  @override
  String get lastUpdated => 'آخر تحديث';

  @override
  String get startFueling => 'بدء التعبئة';

  @override
  String get fuelGasoline91 => 'بنزين 91';

  @override
  String get fuelGasoline95 => 'بنزين 95';

  @override
  String get fuelDiesel => 'ديزل';

  @override
  String get fuelKerosene => 'كيروسين';

  @override
  String get fuelLpg => 'غاز بترولي مسال';

  @override
  String get fuelOther => 'وقود آخر';

  @override
  String get wallet => 'المحفظة';

  @override
  String get topUp => 'شحن الرصيد';

  @override
  String get transactions => 'المعاملات';

  @override
  String get scanQr => 'مسح QR';

  @override
  String get scanQrHint =>
      'سيتم التحقق من الرمز عبر سحابة NNEXORIS قبل بدء التعبئة.';

  @override
  String get fuelingSetup => 'إعداد التعبئة';

  @override
  String get fuelingProgress => 'تقدم التعبئة';

  @override
  String get vehicles => 'المركبات';

  @override
  String get profile => 'الملف الشخصي';

  @override
  String get settings => 'الإعدادات';

  @override
  String get verifyEmail => 'تأكيد البريد';

  @override
  String get verifyEmailHint => 'أكد بريدك الإلكتروني قبل بدء جلسة تعبئة.';

  @override
  String get onboardingTitle => 'عبّئ بأمان مع NNEXORIS';

  @override
  String get continueLabel => 'متابعة';

  @override
  String get lightTheme => 'فاتح';

  @override
  String get darkTheme => 'داكن';

  @override
  String get systemTheme => 'النظام';

  @override
  String get language => 'اللغة';

  @override
  String get arabic => 'العربية';

  @override
  String get english => 'الإنجليزية';

  @override
  String get logout => 'تسجيل الخروج';

  @override
  String get loading => 'جارٍ التحميل';

  @override
  String get comingSoon => 'هذا القسم جاهز للربط مع واجهات السحابة.';

  @override
  String get offlineNotice => 'لا يوجد اتصال. لا يمكن بدء تعبئة جديدة.';

  @override
  String get errorUnexpected => 'حدث خطأ. حاول مرة أخرى بأمان.';

  @override
  String get errorInvalidCredentials => 'البريد أو كلمة المرور غير صحيحة.';

  @override
  String get errorEmailVerificationRequired => 'يلزم تأكيد البريد الإلكتروني.';

  @override
  String get errorInsufficientFunds => 'رصيد المحفظة غير كافٍ.';

  @override
  String get errorOffline => 'الاتصال بالسحابة غير متاح.';

  @override
  String get errorSessionExpired => 'انتهت الجلسة. سجّل الدخول مجددًا.';
}
