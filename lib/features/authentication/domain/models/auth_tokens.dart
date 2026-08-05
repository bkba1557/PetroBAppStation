import 'package:equatable/equatable.dart';

class AuthTokens extends Equatable {
  const AuthTokens({
    required this.accessToken,
    required this.refreshToken,
    required this.accessTokenExpiresAt,
  });

  final String accessToken;
  final String refreshToken;
  final DateTime accessTokenExpiresAt;

  bool get isAccessTokenExpired =>
      DateTime.now().toUtc().isAfter(accessTokenExpiresAt.toUtc());

  factory AuthTokens.fromJson(Map<String, dynamic> json) => AuthTokens(
    accessToken: (json['accessToken'] ?? json['access_token']) as String,
    refreshToken: (json['refreshToken'] ?? json['refresh_token']) as String,
    accessTokenExpiresAt: DateTime.parse(
      (json['accessTokenExpiresAt'] ?? json['access_token_expires_at'])
          as String,
    ),
  );

  Map<String, dynamic> toJson() => {
    'accessToken': accessToken,
    'refreshToken': refreshToken,
    'accessTokenExpiresAt': accessTokenExpiresAt.toUtc().toIso8601String(),
  };

  @override
  List<Object?> get props => [accessToken, refreshToken, accessTokenExpiresAt];
}
