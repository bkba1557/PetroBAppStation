import 'package:equatable/equatable.dart';

class Customer extends Equatable {
  const Customer({
    required this.id,
    required this.email,
    required this.displayName,
    required this.emailVerified,
    this.phoneNumber,
  });

  final String id;
  final String email;
  final String displayName;
  final bool emailVerified;
  final String? phoneNumber;

  factory Customer.fromJson(Map<String, dynamic> json) => Customer(
    id: json['id'] as String,
    email: json['email'] as String,
    displayName: (json['displayName'] ?? json['display_name'] ?? '') as String,
    emailVerified:
        (json['emailVerified'] ?? json['email_verified'] ?? false) as bool,
    phoneNumber: (json['phoneNumber'] ?? json['phone_number']) as String?,
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'email': email,
    'displayName': displayName,
    'emailVerified': emailVerified,
    if (phoneNumber != null) 'phoneNumber': phoneNumber,
  };

  @override
  List<Object?> get props => [
    id,
    email,
    displayName,
    emailVerified,
    phoneNumber,
  ];
}
