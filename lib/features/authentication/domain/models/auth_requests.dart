import 'package:equatable/equatable.dart';

class LoginRequest extends Equatable {
  const LoginRequest({required this.email, required this.password});

  final String email;
  final String password;

  Map<String, dynamic> toJson() => {'email': email, 'password': password};

  @override
  List<Object> get props => [email, password];
}

class RegisterRequest extends Equatable {
  const RegisterRequest({
    required this.email,
    required this.mobile,
    required this.password,
  });

  final String email;
  final String mobile;
  final String password;

  Map<String, dynamic> toJson() => {
    'email': email,
    'mobile': mobile,
    'password': password,
  };

  @override
  List<Object> get props => [email, mobile, password];
}

class ResetPasswordRequest extends Equatable {
  const ResetPasswordRequest({required this.token, required this.newPassword});

  final String token;
  final String newPassword;

  Map<String, dynamic> toJson() => {'token': token, 'newPassword': newPassword};

  @override
  List<Object> get props => [token, newPassword];
}
