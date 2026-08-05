import 'package:connectivity_plus/connectivity_plus.dart';

enum NetworkConnectionState { connecting, online, offline, reconnecting }

abstract interface class NetworkInfo {
  Future<bool> get isConnected;
  Stream<NetworkConnectionState> get changes;
}

class ConnectivityNetworkInfo implements NetworkInfo {
  ConnectivityNetworkInfo(this._connectivity);

  final Connectivity _connectivity;

  bool _hasNetwork(List<ConnectivityResult> results) =>
      results.any((result) => result != ConnectivityResult.none);

  @override
  Future<bool> get isConnected async =>
      _hasNetwork(await _connectivity.checkConnectivity());

  @override
  Stream<NetworkConnectionState> get changes => _connectivity
      .onConnectivityChanged
      .map(
        (results) => _hasNetwork(results)
            ? NetworkConnectionState.online
            : NetworkConnectionState.offline,
      )
      .distinct();
}
