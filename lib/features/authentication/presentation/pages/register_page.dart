import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:nnexoris_customer/app/router/app_routes.dart';
import 'package:nnexoris_customer/core/localization/localization_extension.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/auth_requests.dart';
import 'package:nnexoris_customer/features/authentication/presentation/auth_controller.dart';
import 'package:nnexoris_customer/features/authentication/presentation/auth_state.dart';
import 'package:nnexoris_customer/features/authentication/presentation/widgets/auth_layout.dart';

class RegisterPage extends ConsumerStatefulWidget {
  const RegisterPage({super.key});

  @override
  ConsumerState<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends ConsumerState<RegisterPage> {
  final _formKey = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  final _password = TextEditingController();
  final _confirm = TextEditingController();
  bool _showPassword = false;
  bool _showConfirm = false;

  @override
  void dispose() {
    _email.dispose();
    _phone.dispose();
    _password.dispose();
    _confirm.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(authStateProvider);
    final loading = state.status == AuthStatus.loading;

    return AuthLayout(
      title: context.l10n.authRegisterTitle,
      subtitle: context.l10n.authRegisterSubtitle,
      formWidthFactor: 0.92,
      logoSize: 90,
      contentTopSpacing: 30,
      footer: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(context.l10n.alreadyHaveAccount),
          TextButton(
            onPressed: () => context.go(AppRoutes.login),
            child: Text(context.l10n.login),
          ),
        ],
      ),
      child: AutofillGroup(
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              AuthTextField(
                controller: _email,
                label: context.l10n.email,
                icon: Icons.alternate_email_rounded,
                keyboardType: TextInputType.emailAddress,
                autofillHints: const [AutofillHints.newUsername],
                textInputAction: TextInputAction.next,
                validator: (value) => value == null || !value.contains('@')
                    ? context.l10n.emailValidation
                    : null,
              ),
              const SizedBox(height: 10),
              AuthTextField(
                controller: _phone,
                label: context.l10n.mobileNumber,
                icon: Icons.phone_iphone_rounded,
                keyboardType: TextInputType.phone,
                autofillHints: const [AutofillHints.telephoneNumberNational],
                textInputAction: TextInputAction.next,
                prefix: const Padding(
                  padding: EdgeInsetsDirectional.only(end: 8),
                  child: Text('+966'),
                ),
                validator: (value) =>
                    value == null ||
                        value.replaceAll(RegExp(r'[^0-9]'), '').length < 9
                    ? context.l10n.mobileValidation
                    : null,
              ),
              const SizedBox(height: 10),
              AuthTextField(
                controller: _password,
                label: context.l10n.password,
                icon: Icons.lock_outline_rounded,
                obscureText: !_showPassword,
                autofillHints: const [AutofillHints.newPassword],
                textInputAction: TextInputAction.next,
                onToggleVisibility: () =>
                    setState(() => _showPassword = !_showPassword),
                validator: (value) => value == null || value.length < 8
                    ? context.l10n.passwordValidation
                    : null,
              ),
              const SizedBox(height: 10),
              AuthTextField(
                controller: _confirm,
                label: context.l10n.confirmPassword,
                icon: Icons.lock_reset_rounded,
                obscureText: !_showConfirm,
                autofillHints: const [AutofillHints.newPassword],
                textInputAction: TextInputAction.done,
                onToggleVisibility: () =>
                    setState(() => _showConfirm = !_showConfirm),
                validator: (value) => value != _password.text
                    ? context.l10n.passwordMismatch
                    : null,
              ),
              const SizedBox(height: 8),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    Icons.info_outline_rounded,
                    size: 17,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  const SizedBox(width: 7),
                  Expanded(
                    child: Text(
                      context.l10n.passwordHint,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ),
                ],
              ),
              if (state.status == AuthStatus.failure &&
                  state.failure != null) ...[
                const SizedBox(height: 14),
                Text(
                  context.l10n.errorUnexpected,
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ],
              const SizedBox(height: 16),
              AuthPrimaryButton(
                label: context.l10n.register,
                loading: loading,
                onPressed: _submit,
                height: 52,
              ),
              const SizedBox(height: 10),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.shield_outlined,
                    size: 17,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  const SizedBox(width: 7),
                  Flexible(
                    child: Text(
                      context.l10n.secureAuthCaption,
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    final digits = _phone.text.replaceAll(RegExp(r'[^0-9]'), '');
    final local = digits.startsWith('0') ? digits.substring(1) : digits;
    ref
        .read(authStateProvider.notifier)
        .register(
          RegisterRequest(
            email: _email.text.trim(),
            mobile: '+966$local',
            password: _password.text,
          ),
        );
  }
}
