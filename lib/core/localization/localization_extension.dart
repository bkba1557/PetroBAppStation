import 'package:flutter/widgets.dart';
import 'package:nnexoris_customer/l10n/generated/app_localizations.dart';

extension LocalizationContext on BuildContext {
  AppLocalizations get l10n => AppLocalizations.of(this);
}
