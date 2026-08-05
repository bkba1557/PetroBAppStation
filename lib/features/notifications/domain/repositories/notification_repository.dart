import 'package:nnexoris_customer/features/notifications/domain/models/customer_notification.dart';

abstract interface class NotificationRepository {
  Future<List<CustomerNotification>> getNotifications({String? cursor});
  Future<void> markRead(String notificationId);
}
