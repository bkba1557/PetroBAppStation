import 'package:equatable/equatable.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/auth_tokens.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/customer.dart';

class AuthSession extends Equatable {
  const AuthSession({required this.customer, required this.tokens});

  final Customer customer;
  final AuthTokens tokens;

  factory AuthSession.fromJson(Map<String, dynamic> json) => AuthSession(
    customer: Customer.fromJson(json['customer'] as Map<String, dynamic>),
    tokens: AuthTokens.fromJson(json['tokens'] as Map<String, dynamic>),
  );

  @override
  List<Object> get props => [customer, tokens];
}
