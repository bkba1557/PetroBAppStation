import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:nnexoris_customer/app/router/app_routes.dart';
import 'package:nnexoris_customer/core/localization/localization_extension.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/auth_requests.dart';
import 'package:nnexoris_customer/features/authentication/presentation/auth_controller.dart';
import 'package:nnexoris_customer/features/authentication/presentation/auth_state.dart';
import 'package:nnexoris_customer/features/authentication/presentation/widgets/auth_layout.dart';

class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _showPassword = false;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(authStateProvider);
    final loading = state.status == AuthStatus.loading;

    return AuthLayout(
      title: context.l10n.authWelcomeBack,
      subtitle: context.l10n.authLoginSubtitle,
      backgroundGlowOffset: 90,
      footer: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(context.l10n.noAccount),
          TextButton(
            onPressed: () => context.go(AppRoutes.register),
            child: Text(context.l10n.register),
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
                autofillHints: const [AutofillHints.email],
                textInputAction: TextInputAction.next,
                validator: (value) => value == null || !value.contains('@')
                    ? context.l10n.emailValidation
                    : null,
              ),
              const SizedBox(height: 15),
              AuthTextField(
                controller: _password,
                label: context.l10n.password,
                icon: Icons.lock_outline_rounded,
                obscureText: !_showPassword,
                autofillHints: const [AutofillHints.password],
                textInputAction: TextInputAction.done,
                onToggleVisibility: () =>
                    setState(() => _showPassword = !_showPassword),
                validator: (value) => value == null || value.length < 8
                    ? context.l10n.passwordValidation
                    : null,
              ),
              if (state.status == AuthStatus.failure &&
                  state.failure != null) ...[
                const SizedBox(height: 14),
                _ErrorBanner(
                  message: _failureMessage(context, state.failure!.messageKey),
                ),
              ],
              const SizedBox(height: 22),
              AuthPrimaryButton(
                label: context.l10n.login,
                loading: loading,
                onPressed: _submit,
              ),
              const SizedBox(height: 14),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.verified_user_outlined,
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
    ref
        .read(authStateProvider.notifier)
        .login(
          LoginRequest(email: _email.text.trim(), password: _password.text),
        );
  }

  String _failureMessage(BuildContext context, String messageKey) =>
      switch (messageKey) {
        'errorInvalidCredentials' => context.l10n.errorInvalidCredentials,
        'errorEmailVerificationRequired' =>
          context.l10n.errorEmailVerificationRequired,
        'errorOffline' => context.l10n.errorOffline,
        'errorSessionExpired' => context.l10n.errorSessionExpired,
        _ => context.l10n.errorUnexpected,
      };
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(12),
    decoration: BoxDecoration(
      color: Theme.of(context).colorScheme.errorContainer,
      borderRadius: BorderRadius.circular(14),
    ),
    child: Row(
      children: [
        Icon(
          Icons.error_outline_rounded,
          color: Theme.of(context).colorScheme.onErrorContainer,
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            message,
            style: TextStyle(
              color: Theme.of(context).colorScheme.onErrorContainer,
            ),
          ),
        ),
      ],
    ),
  );
}
