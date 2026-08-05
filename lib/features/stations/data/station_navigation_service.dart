import 'package:nnexoris_customer/features/stations/domain/models/station.dart';
import 'package:url_launcher/url_launcher.dart';

class StationNavigationService {
  const StationNavigationService();

  Future<bool> navigateTo(Station station) => launchUrl(
    Uri.https('www.google.com', '/maps/dir/', {
      'api': '1',
      'destination':
          '${station.location.latitude},${station.location.longitude}',
      'travelmode': 'driving',
      'dir_action': 'navigate',
    }),
    mode: LaunchMode.externalApplication,
  );
}
