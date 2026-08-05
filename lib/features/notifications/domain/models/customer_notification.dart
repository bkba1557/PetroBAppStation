import 'package:equatable/equatable.dart';

class CustomerNotification extends Equatable {
  const CustomerNotification({
    required this.id,
    required this.type,
    required this.title,
    required this.body,
    required this.createdAt,
    required this.read,
  });
  final String id;
  final String type;
  final String title;
  final String body;
  final DateTime createdAt;
  final bool read;
  @override
  List<Object> get props => [id, type, title, body, createdAt, read];
}
