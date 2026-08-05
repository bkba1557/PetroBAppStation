import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:nnexoris_customer/core/errors/error_mapper.dart';
import 'package:nnexoris_customer/core/providers.dart';
import 'package:nnexoris_customer/core/security/quick_login_service.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/auth_requests.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/customer.dart';
import 'package:nnexoris_customer/features/authentication/presentation/auth_state.dart';

final authStateProvider = NotifierProvider<AuthController, AuthState>(
  AuthController.new,
);

class AuthController extends Notifier<AuthState> {
  bool _isInitialRestore = true;

  @override
  AuthState build() {
    Future<void>.microtask(restoreSession);
    return const AuthState();
  }

  Future<void> restoreSession() async {
    final minimumSplash = _isInitialRestore
        ? Future<void>.delayed(const Duration(milliseconds: 2500))
        : Future<void>.value();
    _isInitialRestore = false;
    final tokens = await ref.read(tokenManagerProvider).readTokens();
    if (tokens == null) {
      await minimumSplash;
      state = const AuthState(status: AuthStatus.unauthenticated);
      return;
    }
    if (await ref.read(quickLoginServiceProvider).isEnabled()) {
      await minimumSplash;
      state = const AuthState(status: AuthStatus.quickLoginRequired);
      return;
    }
    await _restoreCloudSession(minimumDelay: minimumSplash);
  }

  Future<void> _restoreCloudSession({Future<void>? minimumDelay}) async {
    state = const AuthState(status: AuthStatus.loading);
    try {
      final customer = await ref.read(authRepositoryProvider).getCurrentUser();
      await minimumDelay;
      _setCustomer(customer);
    } on Object catch (error) {
      await minimumDelay;
      await ref.read(tokenManagerProvider).clear();
      state = AuthState(
        status: AuthStatus.unauthenticated,
        failure: ErrorMapper.toFailure(error),
      );
    }
  }

  Future<QuickLoginResult> unlockWithPin(String pin) async {
    final result = await ref.read(quickLoginServiceProvider).verify(pin);
    if (result == QuickLoginResult.success) {
      await _restoreCloudSession();
    }
    return result;
  }

  Future<void> login(LoginRequest request) async {
    state = const AuthState(status: AuthStatus.loading);
    try {
      final session = await ref.read(authRepositoryProvider).login(request);
      _setCustomer(session.customer);
    } on Object catch (error) {
      state = AuthState(
        status: AuthStatus.failure,
        failure: ErrorMapper.toFailure(error),
      );
    }
  }

  Future<void> register(RegisterRequest request) async {
    state = const AuthState(status: AuthStatus.loading);
    try {
      final session = await ref.read(authRepositoryProvider).register(request);
      _setCustomer(session.customer);
    } on Object catch (error) {
      state = AuthState(
        status: AuthStatus.failure,
        failure: ErrorMapper.toFailure(error),
      );
    }
  }

  Future<void> logout() async {
    await ref.read(authRepositoryProvider).logout();
    state = const AuthState(status: AuthStatus.unauthenticated);
  }

  void _setCustomer(Customer customer) {
    state = AuthState(
      status: customer.emailVerified
          ? AuthStatus.authenticated
          : AuthStatus.emailVerificationRequired,
      customer: customer,
    );
    unawaited(
      ref
          .read(quickLoginServiceProvider)
          .updateDisplayName(customer.displayName),
    );
  }
}
