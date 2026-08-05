import 'package:equatable/equatable.dart';
import 'package:nnexoris_customer/core/errors/failure.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/customer.dart';

enum AuthStatus {
  initial,
  loading,
  quickLoginRequired,
  authenticated,
  unauthenticated,
  emailVerificationRequired,
  refreshing,
  failure,
}

class AuthState extends Equatable {
  const AuthState({
    this.status = AuthStatus.initial,
    this.customer,
    this.failure,
  });

  final AuthStatus status;
  final Customer? customer;
  final Failure? failure;

  bool get isAuthenticated =>
      customer != null &&
      (status == AuthStatus.authenticated ||
          status == AuthStatus.emailVerificationRequired ||
          status == AuthStatus.refreshing);

  AuthState copyWith({
    AuthStatus? status,
    Customer? customer,
    Failure? failure,
  }) => AuthState(
    status: status ?? this.status,
    customer: customer ?? this.customer,
    failure: failure,
  );

  @override
  List<Object?> get props => [status, customer, failure];
}
